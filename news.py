# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
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

# Import from the Standard Library
from copy import deepcopy

# Import from itools
from itools.core import get_abspath, merge_dicts
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import get_context
from itools.xapian import PhraseQuery, AndQuery, OrQuery, StartQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.forms import stl_namespaces, XHTMLBody, Widget
from ikaaro.registry import register_document_type
from ikaaro.registry import register_resource_class, register_field
from ikaaro.skins import register_skin
from ikaaro.utils import reduce_string

# Import from itws
from bar import SideBarAware
from datatypes import PositiveIntegerNotNull
from news_views import NewsFolder_View, NewsFolder_Edit, NewsFolder_RSS
from news_views import NewsItem_AddImage, NewsFolder_BrowseContent
from news_views import NewsItem_Edit, NewsItem_View
from repository import Repository
from tags import TagsAware
from utils import is_empty, get_path_and_view
from webpage import WebPage



class InfoWidget(Widget):

    template = list(XMLParser(
        """${value}""", stl_namespaces))


    def get_namespace(self, datatype, value):
        return {'value': value}



###########################################################################
# Resources
###########################################################################
class NewsItem(WebPage):

    class_id = 'news'
    class_version = '20100129'
    class_title = MSG(u'News')
    class_icon16 = 'news/icons/16x16/news_folder.png'
    class_icon48 = 'news/icons/48x48/news_folder.png'
    class_views = ['view', 'edit', 'edit_state']


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(WebPage.get_metadata_schema(),
                           long_title=XHTMLBody,
                           thumbnail=String(default='') # Multilingual
                          )


    def _get_catalog_values(self):
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        date_of_writing = self.get_property('date_of_writing')
        available_languages = self.get_available_languages(languages)
        preview_content = self.get_preview_content()
        return merge_dicts(WebPage._get_catalog_values(self),
                           available_languages=available_languages,
                           preview_content=preview_content)


    def get_links(self):
        # FIXME We should add long_title content
        links = WebPage.get_links(self)

        base = self.get_canonical_path()
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        for language in available_languages:
            path = self.get_property('thumbnail')
            if not path:
                continue
            ref = get_reference(path)
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                links.append(str(base.resolve2(path)))

        return links


    def update_links(self, source, target):
        WebPage.update_links(self, source, target)

        site_root = self.get_site_root()
        base = self.get_canonical_path()
        available_languages = site_root.get_property('website_languages')

        for lang in available_languages:
            path = self.get_property('thumbnail', language=lang)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            path, view = get_path_and_view(ref.path)
            path = str(base.resolve2(path))
            if path == source:
                # Hit the old name
                # Build the new reference with the right path
                new_ref = deepcopy(ref)
                new_ref.path = str(base.get_pathto(target)) + view
                self.set_property('thumbnail', str(new_ref), language=lang)

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        WebPage.update_relative_links(self, source)

        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        for lang in available_languages:
            path = self.get_property('thumbnail', language=lang)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            path, view = get_path_and_view(ref.path)
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)
            # Build the new reference with the right path
            # Absolute path allow to call get_pathto with the target
            new_ref = deepcopy(ref)
            new_ref.path = str(target.get_pathto(new_abs_path)) + view
            self.set_property('thumbnail', str(new_ref), language=lang)


    def get_preview_content(self):
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        preview_content = {}
        for language in languages:
            handler = self.get_html_document(language)
            text = handler.to_text()
            data = reduce_string(text, 10000, 255)
            preview_content[language] = data
        return preview_content


    def get_long_title(self, language=None):
        """Return the long_title or the title"""
        long_title = self.get_property('long_title', language=language)
        if long_title is not None:
            long_title = list(long_title)
            if is_empty(long_title) is False:
                return long_title
        return self.get_title()


    def can_paste_into(self, target):
        return isinstance(target, NewsFolder)


    def get_available_languages(self, languages):
        """Available languages for the current news"""
        if self.has_date_of_writing() is False:
            return []
        available_langs = []
        for language in languages:
            handler = self.get_handler(language)
            if handler.is_empty() is False:
                available_langs.append(language)
        return available_langs


    edit = NewsItem_Edit()
    view = NewsItem_View()
    tag_view = NewsItem_View(sidebar=False, id=None, title_link=True)
    add_image = NewsItem_AddImage()



class NewsFolder(SideBarAware, Folder):

    class_id = 'news-folder'
    class_version = '20100403'
    class_title = MSG(u'News Folder')
    class_icon16 = 'news/icons/16x16/news_folder.png'
    class_icon48 = 'news/icons/48x48/news_folder.png'
    class_views = (['view', 'browse_content', 'edit']
                   + SideBarAware.class_views)
    __fixed_handlers__ = (SideBarAware.__fixed_handlers__ +
                          Folder.__fixed_handlers__ + ['images'])
    news_class = NewsItem

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        root = get_context().root
        Folder._make_resource(cls, folder, name, **kw)
        Folder._make_resource(Folder, folder, '%s/images' % name)
        SideBarAware._make_resource(SideBarAware, folder, name, **kw)
        # Add siblings item
        siblings_item_name = Repository.news_siblings_view_name
        table_name = cls.sidebar_name
        table = root.get_resource('%s/%s/%s' % (folder.key, name, table_name))
        table.add_new_record({'name': siblings_item_name})


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema['batch_size'] = PositiveIntegerNotNull(default=7)
        return schema


    def get_document_types(self):
        return [self.news_class, File]


    def get_news_query_terms(self, state=None, tags=[]):
        abspath = self.get_canonical_path()
        abspath = '%s/' % abspath
        query = [ StartQuery('abspath', abspath),
                  PhraseQuery('format', self.news_class.class_id) ]
        if state:
            query.append(PhraseQuery('workflow_state', state))
        if tags:
            tags_query = [ PhraseQuery('tags', tag) for tag in tags ]
            if len(tags_query):
                tags_query = OrQuery(*tags_query)
            query.append(tags_query)
        return query


    def get_news(self, context, state='public', language=None, number=None,
                 tags=[], brain_only=False):
        query = self.get_news_query_terms(state, tags)
        if language is None:
            language = self.get_content_language(context)
        query.append(PhraseQuery('available_languages', [language]))

        # size
        size = 0
        if number:
            size = number

        root = context.root
        results = root.search(AndQuery(*query))
        documents = results.get_documents(sort_by='date_of_writing',
                                          reverse=True, size=size)
        if brain_only:
            return documents

        return [ root.get_resource(doc.abspath)
                 for doc in documents ]


    def get_available_languages(self, languages):
        """Available languages for the current news"""
        root = get_context().root
        query_terms = self.get_news_query_terms(state='public')
        results = root.search(AndQuery(*query_terms))

        available_languages = []
        for language in languages:
            sub_results = results.search(
                    PhraseQuery('available_languages', [language]))
            if len(sub_results):
                available_languages.append(language)

        return available_languages


    view = NewsFolder_View()
    edit = NewsFolder_Edit()
    browse_content = NewsFolder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    rss = NewsFolder_RSS()


# Register
register_resource_class(NewsItem)
register_resource_class(NewsFolder)
register_document_type(NewsItem, TagsAware.class_id)

register_field('available_languages', String(is_stored=True, is_indexed=True,
                                             multiple=True))
register_field('preview_content', Unicode(is_stored=True, is_indexed=True))

# Register skin
path = get_abspath('ui/news')
register_skin('news', path)
