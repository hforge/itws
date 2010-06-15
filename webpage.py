# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import String, Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.registry import register_resource_class, register_document_type
from ikaaro.webpage import WebPage as BaseWebPage

# Import from itws
from tags import TagsAware
from webpage_views import WebPage_Edit, WebPage_View



class WebPage(BaseWebPage, TagsAware):
    # Override the ikaaro webpage to allow to add iframe

    edit = WebPage_Edit()
    view = WebPage_View()

    @classmethod
    def get_metadata_schema(cls):
        schema = merge_dicts(BaseWebPage.get_metadata_schema(),
                             TagsAware.get_metadata_schema(),
                             display_title=Boolean,
                             state=String(default='public'))
        return schema


    def _get_catalog_values(self):
        return merge_dicts(BaseWebPage._get_catalog_values(self),
                           TagsAware._get_catalog_values(self))


    def get_class_views(self):
        # Add helper for manage view
        views = BaseWebPage.class_views
        parent = self.parent
        site_root = self.get_site_root()
        section_cls = site_root.section_class
        wsdata_cls = site_root.wsdatafolder_class
        if isinstance(parent, (section_cls, wsdata_cls)):
            new_views = list(views)
            new_views.insert(2, 'manage_view')
            return new_views
        return views

    class_views = property(get_class_views, None, None, '')


    def get_view(self, name, query=None):
        # Add helper for manage view
        view = BaseWebPage.get_view(self, name, query)
        if view:
            return view
        if name == 'manage_view':
            parent = self.parent
            site_root = self.get_site_root()
            section_cls = site_root.section_class
            wsdata_cls = site_root.wsdatafolder_class
            if isinstance(parent, (section_cls, wsdata_cls)):
                return GoToSpecificDocument(specific_document='..',
                        specific_view='manage_view',
                        title=MSG(u'Manage parent section'))
        return None


    def get_available_languages(self, languages):
        available_langs = []
        for language in languages:
            handler = self.get_handler(language)
            if handler.is_empty() is False:
                available_langs.append(language)
        return available_langs


    def get_links(self):
        links = BaseWebPage.get_links(self)
        links.extend(TagsAware.get_links(self))
        return links


    def update_links(self, source, target):
        BaseWebPage.update_links(self, source, target)
        TagsAware.update_links(self, source, target)


    def update_relative_links(self, source):
        BaseWebPage.update_relative_links(self, source)
        # Not need for TagsAware



register_resource_class(WebPage)
register_resource_class(WebPage, format='application/xhtml+xml')
register_document_type(WebPage, TagsAware.class_id)
