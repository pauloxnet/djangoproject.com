# Generated by Django 1.9.1 on 2016-01-21 07:14
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('releases', '0001_squashed_0004_make_release_date_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=500)),
                ('title', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentRelease',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lang', models.CharField(choices=settings.LANGUAGES, default='en', max_length=2)),
                ('is_default', models.BooleanField(default=False)),
                ('release', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='releases.Release', limit_choices_to={'status': 'f'})),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='documentrelease',
            unique_together=set([('lang', 'release')]),
        ),
        migrations.AddField(
            model_name='document',
            name='release',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='docs.DocumentRelease'),
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('release', 'path')]),
        ),
    ]
