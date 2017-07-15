import elasticsearch
from django.utils.html import strip_tags
from django.utils.text import unescape_entities
from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl import (
    DocType, Keyword, Long, Nested, Object, Text, analysis,
)
from elasticsearch_dsl.connections import connections

from .models import Document, document_url


class ImprovedDocType(DocType):

    @classmethod
    def index_all(cls, index_name, using=None, **kwargs):
        def actions_generator():
            for obj in cls.index_queryset().iterator():
                elastic_data = cls.from_django(obj).to_dict(include_meta=True)
                elastic_data['_index'] = index_name
                yield elastic_data

        client = connections.get_connection(using or cls._doc_type.using)
        cls.init(index_name)
        for ok, item in streaming_bulk(client, actions_generator(), chunk_size=90, **kwargs):
            yield ok, item

    @classmethod
    def index_queryset(cls):
        return cls.model._default_manager.all()

    @classmethod
    def index_object(cls, obj):
        return cls.from_django(obj).save()

    @classmethod
    def unindex_object(cls, obj):
        return cls.get(id=obj.pk).delete()

    @classmethod
    def from_django(cls, obj):
        raise NotImplementedError('You must define a from_django classmethod '
                                  'to map ORM object fields to ES fields')


analysis.Tokenizer._builtins = analysis.TOKENIZERS = frozenset((
    'keyword', 'standard', 'path_hierarchy', 'whitespace'
))


class PathHierarchyTokenizer(analysis.Tokenizer):
    name = 'path_hierarchy'


class WhitespaceTokenizer(analysis.Tokenizer):
    name = 'whitespace'


path_analyzer = analysis.CustomAnalyzer('path',
                                        tokenizer='path_hierarchy',
                                        filter=['lowercase'])


lower_whitespace_analyzer = analysis.analyzer('lower_whitespace',
                                              tokenizer='whitespace',
                                              filter=['lowercase', 'stop'],
                                              char_filter=['html_strip'])


class DocumentDocType(ImprovedDocType):
    """
    The main documentation doc type to be used for searching.
    It stores a bit of meta data so we don't have to hit the db
    when rendering search results.

    The search view will be using the 'lang' and 'version' fields
    of the document's release to filter the search results, depending
    which was found in the URL.

    The breadcrumbs are shown under the search result title.
    """
    model = Document

    id = Long()
    title = Text(analyzer=lower_whitespace_analyzer, boost=1.2)
    path = Text(index='no', analyzer=path_analyzer)
    content = Text(analyzer=lower_whitespace_analyzer)
    content_raw = Text(index_options='offsets')
    release = Object(properties={
        'id': Long(),
        'version': Keyword(),
        'lang': Keyword(),
    })
    breadcrumbs = Nested(properties={
        'title': Keyword(),
        'path': Keyword(),
    })

    class Meta:
        index = 'docs'
        doc_type = 'document'

    @classmethod
    def alias_to_main_index(cls, index_name, using=None):
        """
        Alias `index_name` to 'docs' (`cls._doc_type.index`).
        """
        body = {'actions': [{'add': {'index': index_name, 'alias': cls._doc_type.index}}]}

        client = connections.get_connection(using or cls._doc_type.using)
        client.indices.refresh(index=index_name)
        try:
            old_index_name = list(client.indices.get_alias('docs').keys())[0]
        except elasticsearch.exceptions.NotFoundError:
            old_index_name = None
        else:
            body['actions'].append({'remove': {'index': old_index_name, 'alias': cls._doc_type.index}})

        client.indices.update_aliases(body=body)
        # Delete the old index that was aliased to 'docs'.
        if old_index_name:
            client.indices.delete(old_index_name)

    @classmethod
    def index_queryset(cls):
        qs = super().index_queryset()
        return (
            # don't index the module pages since source code is hard to
            # combine with full text search
            qs.exclude(path__startswith='_modules')
            # not the crazy big flattened index of the CBVs
              .exclude(path__startswith='ref/class-based-views/flattened-index')
              .select_related('release'))

    @classmethod
    def from_django(cls, obj):
        # turns HTML entities into unicode characters again and removes
        # all HTML tags, aka "plain text" versio of the document
        raw_body = strip_tags(unescape_entities(obj.body).replace(u'¶', ''))
        doc = cls(path=obj.path,
                  title=obj.title,
                  content=obj.body,
                  content_raw=raw_body,
                  meta={'id': obj.id})
        doc.release = {
            'id': obj.release.id,
            'lang': obj.release.lang,
            'version': obj.release.version,
        }
        breadcrumbs = []
        for breadcrumb in cls.model.objects.breadcrumbs(obj):
            breadcrumbs.append({
                'title': breadcrumb.title,
                'path': breadcrumb.path,
            })
        doc.breadcrumbs = breadcrumbs
        return doc

    def get_absolute_url(self):
        return document_url(self)
