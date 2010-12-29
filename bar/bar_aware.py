# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import form itools
from itools.core import lazy
from itools.gettext import MSG
from itools.web import BaseView, get_context

# Import from itws
from repository import ContentbarBoxesOrderedTable
from repository import SidebarBoxesOrderedTable
from itws.section_views import get_section_view_from_registry
from itws.section_views import section_views_registry
from itws.views import AdvanceGoToSpecificDocument



################################################################################
# Resources
################################################################################
class SideBarAware(object):

    class_version = '20100621'
    class_views = ['order_sidebar']
    class_schema = {}

    sidebar_name = 'order-sidebar'
    repository = None

    __fixed_handlers__ = [sidebar_name]

    def init_resource(self, **kw):
        if self.repository:
            path = '%s/%s' % (self.repository, self.sidebar_name)
        else:
            path = self.sidebar_name
        self.make_resource(path, SidebarBoxesOrderedTable)


    @lazy
    def order_sidebar(self):
        if self.repository:
            specific_document = '%s/%s' % (self.repository, self.sidebar_name)
        else:
            specific_document = self.sidebar_name
        return AdvanceGoToSpecificDocument(
            access='is_allowed_to_edit',
            keep_query=True,
            specific_document=specific_document,
            title=MSG(u'Order Sidebar Boxes'))


    @lazy
    def new_sidebar_resource(self):
        if self.repository:
            specific_document = '%s/%s/;add_box' % (self.repository,
                                                    self.sidebar_name)
        else:
            specific_document = './%s/;add_box' % self.sidebar_name
        return AdvanceGoToSpecificDocument(
            access='is_allowed_to_edit',
            keep_query=True,
            specific_document=specific_document,
            title=MSG(u'Add sidebar box'))


    def get_content_folder(self):
        if self.repository:
            return self.get_resource(self.repository)
        return self


    def get_order_table_sidebar(self):
        content_folder = self.get_content_folder()
        return content_folder.get_resource(self.sidebar_name)



class ContentBarAware(object):

    class_version = '20100622'
    class_views = ['order_contentbar']

    contentbar_name = 'order-contentbar'
    repository = None

    __fixed_handlers__ = [contentbar_name]


    def init_resource(self, **kw):
        if self.repository:
            path = '%s/%s' % (self.repository, self.contentbar_name)
        else:
            path = self.contentbar_name
        self.make_resource(path, ContentbarBoxesOrderedTable)


    def get_content_folder(self):
        if self.repository:
            return self.get_resource(self.repository)
        return self


    def get_order_table_contentbar(self):
        content_folder = self.get_content_folder()
        return content_folder.get_resource(self.contentbar_name)


    @lazy
    def view(self):
        """ The main view is customizable
        """
        context = get_context()
        resource = context.resource
        if not isinstance(resource, ContentBarAware):
            return BaseView(title=MSG(u'View'),
                            access='is_allowed_to_view')
        # Get view
        view_name = resource.get_property('view')
        if section_views_registry.has_key(view_name):
            return get_section_view_from_registry(view_name)
        return None



    @lazy
    def configure_view(self):
        context = get_context()
        resource = context.resource
        if not isinstance(resource, ContentBarAware):
            return None
        if resource.get_resource('section_view', soft=True):
            return AdvanceGoToSpecificDocument(
                      access='is_allowed_to_edit',
                      title=MSG(u'Configure View'),
                      specific_document='./section_view',
                      keep_query=True)


    @lazy
    def order_contentbar(self):
        if self.repository:
            specific_document = '%s/%s' % (self.repository,
                                           self.contentbar_name)
        else:
            specific_document = self.contentbar_name
        return AdvanceGoToSpecificDocument(
            access='is_allowed_to_edit',
            keep_query=True,
            specific_document=specific_document,
            title=MSG(u'Order Central Part Boxes'))


    @lazy
    def new_contentbar_resource(self):
        if self.repository:
            specific_document = '%s/%s/;add_box' % (self.repository,
                                                    self.contentbar_name)
        else:
            specific_document ='./%s/;add_box' % self.contentbar_name
        return AdvanceGoToSpecificDocument(
            access='is_allowed_to_edit',
            keep_query=True,
            specific_document=specific_document,
            title=MSG(u'Order Central Part Boxes'))
