# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import from the Standard Library
from copy import deepcopy

# Import from itools
from itools.core import get_abspath, merge_dicts
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.uri import encode_query, get_reference, Path
from itools.web import get_context
from itools.xapian import PhraseQuery, AndQuery, OrQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_PreviewContent, GoToSpecificDocument
from ikaaro.forms import stl_namespaces, TextWidget, Widget
from ikaaro.registry import register_document_type
from ikaaro.registry import register_resource_class
from ikaaro.skins import register_skin

# Import from itws
from bar import SideBarAware
from datatypes import PositiveIntegerNotNull
from news_views import NewsFolder_View, NewsFolder_RSS
from news_views import NewsItem_AddImage, NewsFolder_BrowseContent
from news_views import NewsItem_Edit, NewsItem_View, NewsItem_Viewbox
from news_views import NewsFolder_ManageView
from repository import Repository
from resources import ManageViewAware
from tags import TagsAware
from utils import get_path_and_view
from views import AutomaticEditView
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
    class_version = '20100810'
    class_title = MSG(u'News')
    class_description = MSG(u'News is a webpage with a small description '
                            u'used by the News Folder, News can be tagged')
    class_icon16 = 'news/icons/16x16/news_folder.png'
    class_icon48 = 'news/icons/48x48/news_folder.png'
    class_views = ['view', 'edit', 'manage_view', 'edit_state',
                   'backlinks', 'commit_log']


    viewbox = NewsItem_Viewbox()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(WebPage.get_metadata_schema(),
                           long_title=Unicode,
                           thumbnail=String(default='') # Multilingual
                          )


    def get_long_title(self, language=None):
        """Return the long_title or the title"""
        long_title = self.get_property('long_title', language=language)
        if long_title:
            return long_title
        return self.get_title()


    def can_paste_into(self, target):
        return isinstance(target, NewsFolder)


    ##########################################################################
    # TagsAware API
    ##########################################################################
    def get_preview_thumbnail(self):
        path = self.get_property('thumbnail')
        if not path:
            return None
        ref = get_reference(path)
        if ref.scheme:
            return None
        return self.get_resource(path, soft=True)


    def get_news_tags_namespace(self, context):
        tags_folder = self.get_site_root().get_resource('tags')
        news_folder_link = context.get_link(self.parent)
        # query
        base_query = deepcopy(context.uri.query)

        tags = []
        for tag_name in self.get_property('tags'):
            tag = tags_folder.get_resource(tag_name)
            base_query['tag'] = tag_name
            query = encode_query(base_query)
            href = '%s?%s' % (news_folder_link, query)
            tags.append({'title': tag.get_title(), 'href': href})
        return tags


    ##########################################################################
    # Links API
    ##########################################################################
    def get_links(self):
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
        available_languages = site_root.get_property('website_languages')

        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        for lang in available_languages:
            path = self.get_property('thumbnail', language=lang)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            path, view = get_path_and_view(ref.path)
            path = str(old_base.resolve2(path))
            if path == source:
                # Hit the old name
                # Build the new reference with the right path
                new_ref = deepcopy(ref)
                new_ref.path = str(new_base.get_pathto(target)) + view
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


    edit = NewsItem_Edit()
    view = NewsItem_View()
    add_image = NewsItem_AddImage()
    manage_view = GoToSpecificDocument(specific_document='..',
            specific_view='manage_view', title=NewsFolder_ManageView.title)



class NewsFolder(ManageViewAware, SideBarAware, Folder):

    class_id = 'news-folder'
    class_version = '20100621'
    class_title = MSG(u'News Folder')
    class_description = MSG(u'News Folder contains news ordered  '
                            u'by date of writing')
    class_icon16 = 'news/icons/16x16/news_folder.png'
    class_icon48 = 'news/icons/48x48/news_folder.png'
    class_views = (['view', 'manage_view',
                    'edit', 'backlinks', 'commit_log'])
    __fixed_handlers__ = (SideBarAware.__fixed_handlers__ +
                          Folder.__fixed_handlers__ + ['images'])
    news_class = NewsItem

    # Configuration of automatic edit view
    edit_show_meta = True
    edit_schema =  {'batch_size': PositiveIntegerNotNull}
    edit_widgets = [TextWidget('batch_size', title=MSG(u'Batch size'), size=3)]

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
        query = [ PhraseQuery('parent_path', str(abspath)),
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

        # size
        size = 0
        if number:
            size = number

        root = context.root
        results = root.search(AndQuery(*query))
        documents = results.get_documents(sort_by='pub_datetime',
                                          reverse=True, size=size)
        if brain_only:
            return documents

        return [ root.get_resource(doc.abspath)
                 for doc in documents ]


    view = NewsFolder_View()
    edit = AutomaticEditView()
    manage_view = NewsFolder_ManageView()
    browse_content = NewsFolder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    rss = NewsFolder_RSS()


# Register
register_resource_class(NewsItem)
register_resource_class(NewsFolder)
register_document_type(NewsItem, TagsAware.class_id)

# Register skin
path = get_abspath('ui/news')
register_skin('news', path)
