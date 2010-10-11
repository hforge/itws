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
from itools.gettext import MSG

# Import from itws
from repository import ContentbarBoxesOrderedTable
from repository import SidebarBoxesOrderedTable
from itws.views import AdvanceGoToSpecificDocument



################################################################################
# Resources
################################################################################
class SideBarAware(object):

    class_version = '20100621'
    class_views = ['order_sidebar']
    class_schema = {}

    sidebar_name = 'order-sidebar'
    __fixed_handlers__ = [sidebar_name]

    order_sidebar = AdvanceGoToSpecificDocument(
        access='is_allowed_to_edit',
        keep_query=True,
        specific_document=sidebar_name,
        title=MSG(u'Order Sidebar Boxes'))

    new_sidebar_resource = AdvanceGoToSpecificDocument(
        access='is_allowed_to_edit',
        keep_query=True,
        specific_document='%s/;add_box' % sidebar_name,
        title=MSG(u'Order Sidebar Boxes'))

    # Sidebar items
    # (name, cls, ordered)
    sidebar_items = []


    def init_resource(self, **kw):
        self.make_resource(self.sidebar_name, SidebarBoxesOrderedTable)

        # XXX Migration TODO
        ## Preorder specific sidebar items
        #root = get_context().root
        #table_name = cls.sidebar_name
        #table = root.get_resource('%s/%s/%s' % (folder.key, name, table_name))
        ## FIXME state should be customizable
        #state = 'public'

        #for item in cls.sidebar_items:
        #    name2, cls2, ordered = item
        #    cls2._make_resource(cls2, folder, '%s/%s' % (name, name2),
        #                        state=state)
        #    if ordered:
        #        table.add_new_record({'name': name2})



class ContentBarAware(object):

    class_version = '20100622'
    class_views = ['order_contentbar']
    contentbar_name = 'order-contentbar'
    __fixed_handlers__ = [contentbar_name]

    order_contentbar = AdvanceGoToSpecificDocument(
        access='is_allowed_to_edit',
        keep_query=True,
        specific_document=contentbar_name,
        title=MSG(u'Order Central Part Boxes'))
    new_contentbar_resource = AdvanceGoToSpecificDocument(
        access='is_allowed_to_edit',
        keep_query=True,
        specific_document='%s/;add_box' % contentbar_name,
        title=MSG(u'Order Central Part Boxes'))

    # Contentbar items
    # (name, cls, ordered)
    contentbar_items = []

    def init_resource(self, **kw):
        self.make_resource(self.contentbar_name, ContentbarBoxesOrderedTable)

        ## Preorder specific contentbar items
        #root = get_context().root
        #table_name = cls.contentbar_name
        #table = root.get_resource('%s/%s/%s' % (folder.key, name, table_name))
        ## FIXME state should be customizable
        #state = 'public'

        #for item in cls.contentbar_items:
        #    name2, cls2, ordered = item
        #    cls2._make_resource(cls2, folder, '%s/%s' % (name, name2),
        #                        state=state)
        #    if ordered:
        #        table.add_new_record({'name': name2})
