# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_auto_20140926_2347'),
        ('cmsplugin_sections', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SectionsMenuPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('plugin', models.ForeignKey(related_name='container_reference', editable=False, to='cms.CMSPlugin', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.RemoveField(
            model_name='sectioncontainerpluginmodel',
            name='subordinate_page',
        ),
        migrations.AddField(
            model_name='sectioncontainerpluginmodel',
            name='menu',
            field=models.BooleanField(default=True, help_text='The menu can be rendered separately in another plugin. Useful for placement in another placeholder.', verbose_name='include menu?'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sectioncontainerpluginmodel',
            name='section_links',
            field=models.BooleanField(default=True, help_text='Provides convenient linking between sections by adding links to next and previous sections in each.', verbose_name='include section links?'),
            preserve_default=True,
        ),
    ]
