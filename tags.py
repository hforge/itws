# -*- coding: UTF-8 -*-
# Copyright (C) 2008, 2010 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from standard Library

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Tokens, Boolean
from itools.datatypes import String, Date
from itools.gettext import MSG
from itools.uri import Path, encode_query
from itools.web import get_context
from itools.xapian import AndQuery, PhraseQuery, StartQuery, OrQuery

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.registry import register_field, register_resource_class
from ikaaro.resource_views import DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog

# Import from itws
from resources import MultilingualCatalogTitleAware, ManageViewAware
from tags_views import Tag_View, Tag_RSS, TagsFolder_TagCloud, TagItem_View
from tags_views import TagsFolder_BrowseContent, Tags_ManageView
from views import EasyNewInstance
from views import AutomaticEditView


class Tag(File, MultilingualCatalogTitleAware):

    class_id = 'tag'
    class_version = '20100618'
    class_title = MSG(u'Tag')
    class_views = ['view', 'edit', 'commit_log', 'backlinks']

    backlinks = DBResource_Backlinks(access='is_allowed_to_edit')
    edit = AutomaticEditView()
    edit_state = None
    externaledit = None
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    new_instance = EasyNewInstance()
    view = Tag_View()
    rss = Tag_RSS()

    # Configuration of automatic edit view
    edit_show_meta = True
    edit_schema = {}
    edit_widgets = []

    def _get_catalog_values(self):
        return merge_dicts(File._get_catalog_values(self),
                MultilingualCatalogTitleAware._get_catalog_values(self))


    def get_title(self, language=None, fallback=True):
        title = self.get_property('title', language=language)
        if title:
            return title
        # Fallback to the resource's name
        if fallback:
            return unicode(self.name)


    def can_paste_into(self, target):
        return isinstance(target, TagsFolder)


    def update_20100618(self):
        if self.get_property('state'):
            # state was set
            return
        if self.get_workflow_state() == 'private':
            # state was default public
            self.set_property('state', 'public')



class TagsFolder(ManageViewAware, Folder):

    class_id = 'tags-folder'
    class_title = MSG(u'Tags')
    class_views = ['tag_cloud', 'manage_view']
    class_version = '20100118'

    tag_class = Tag

    tag_cloud = TagsFolder_TagCloud()
    browse_content = TagsFolder_BrowseContent()
    manage_view = Tags_ManageView()

    # Tags to create when creating the tags folder
    default_tags = [('odf', u'ODF'), ('python', u'Python'),
                    ('cms', u'CMS'), ('git', u'GIT')]


    @staticmethod
    def _make_resource(cls, folder, name, language=None, **kw):
        Folder._make_resource(cls, folder, name, **kw)
        if language is None:
            site_root = get_context().resource.get_site_root()
            language = site_root.get_property('website_languages')[0]
        # Create default tags
        for tag in cls.default_tags:
            tag_name, title = tag
            Tag._make_resource(Tag, folder, '%s/%s' % (name, tag_name),
                               title={language: title})


    def get_document_types(self):
        return [ Tag ]


    def get_tags_query_terms(self, state=None, tags=[], formats=[]):
        site_root = self.get_site_root()
        abspath = '%s/' % site_root.get_canonical_path()
        query = [ StartQuery('abspath', abspath),
                  PhraseQuery('is_tagsaware', True) ]

        if state:
            query.append(PhraseQuery('workflow_state', state))
        if tags:
            tags_query = [ PhraseQuery('tags', tag) for tag in tags ]
            if len(tags_query) > 1:
                tags_query = OrQuery(*tags_query)
            else:
                tags_query = tags_query[0]
            query.append(tags_query)
        if formats:
            tags_format = [ PhraseQuery('format', f) for f in formats ]
            if len(tags_format):
                tags_format = OrQuery(*tags_format)
            query.append(tags_format)
        return query


    def is_empty(self, context):
        all_tags_aware_query = self.get_tags_query_terms(state='public')
        all_tags_aware_query = AndQuery(*all_tags_aware_query)

        # tags
        tag_brains = self.get_tag_brains(context)

        # all tags
        all_tags_aware_results = context.root.search(all_tags_aware_query)
        query = [  PhraseQuery('tags', brain.name)
                   for brain in tag_brains ]
        results = all_tags_aware_results.search(OrQuery(*query))

        return len(results) == 0


    def get_tag_brains(self, context, sort_by='name', size=0, state='public'):
        # tags
        abspath = self.get_canonical_path()
        tags_query = AndQuery(PhraseQuery('parent_path', str(abspath)),
                              PhraseQuery('format', Tag.class_id),
                              PhraseQuery('workflow_state', state))
        tags_results = context.root.search(tags_query)
        documents = tags_results.get_documents(sort_by=sort_by, size=size)
        return [ x for x in documents ]



class TagsAware(object):

    # Only useful for the registry
    class_id = 'tags-aware'
    tag_view = TagItem_View()

    @classmethod
    def get_metadata_schema(cls):
        # FIXME Replace Tokens by TagsList
        return {'tags': Tokens(), 'date_of_writing': Date}


    def _get_catalog_values(self):
        indexes = {}
        indexes['tags'] = self.get_property('tags')
        indexes['date_of_writing'] = self.get_property('date_of_writing')
        indexes['is_tagsaware'] = True
        return indexes


    def get_tags_namespace(self, context):
        tags_folder = self.get_site_root().get_resource('tags')
        query = encode_query({'format': self.class_id})
        tags = []
        for tag_name in self.get_property('tags'):
            tag = tags_folder.get_resource(tag_name)
            tags.append({'title': tag.get_title(),
                'href': '%s?%s' % (context.get_link(tag), query)})
        return tags


    def get_date_of_writing(self):
        return self.get_property('date_of_writing')


    def get_date_of_writing_formatted(self, language=None):
        site_root = self.get_site_root()
        value = self.get_date_of_writing()
        return site_root.format_date(value, language)


    def has_date_of_writing(self):
        date_of_writing = self.get_date_of_writing()
        return date_of_writing is not None


    def get_links(self):
        site_root = self.get_site_root()
        tags_base = site_root.get_abspath().resolve2('tags')
        links = [ str(tags_base.resolve2(tag))
                  for tag in self.get_property('tags') ]
        return links


    def update_links(self, source, target):
        source = Path(source)
        site_root = self.get_site_root()
        tags_base = site_root.get_abspath().resolve2('tags')
        if tags_base.get_prefix(source) == tags_base:
            tags = list(self.get_property('tags'))
            source_name = source.get_name()
            target_name = Path(target).get_name()
            for tag in tags:
                if tag == source_name:
                    # Hit
                    index = tags.index(source_name)
                    tags[index] = target_name
                    self.set_property('tags', tags)
        get_context().database.change_resource(self)



register_resource_class(TagsFolder)
register_resource_class(Tag)

register_field('is_tagsaware', Boolean(is_indexed=True))
register_field('tags', String(is_stored=True, is_indexed=True, multiple=True))
register_field('date_of_writing', Date(is_stored=True, is_indexed=True))
