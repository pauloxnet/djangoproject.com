# Generated by Django 1.11.7 on 2017-11-07 15:13
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0002_extend_lang_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='document',
            name='search',
            field=django.contrib.postgres.search.SearchVectorField(editable=False, null=True),
        ),
        migrations.AddIndex(
            model_name='document',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search'], name='docs_docume_search_5dc895_gin'),
        ),
        TrigramExtension(),
    ]
