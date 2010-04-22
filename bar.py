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

# Import from the Standard Library
from warnings import warn

# Import form itools
from itools.gettext import MSG
from itools.stl import set_prefix
from itools.web import STLView

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument

# Import from itws
from repository import ContentbarItemsOrderedTable
from repository import SidebarItemsOrderedTable
from utils import get_admin_bar
from views import STLBoxView



################################################################################
# Views
################################################################################
class Bar_Item_View(STLBoxView):

    template = '/ui/common/Bar_Item_view.xml'
    # Namespace should be set at the view instanciation
    namespace = {}

    def get_namespace(self, resource, context):
        return self.namespace



class Bar_View(STLView):

    template = '/ui/common/Bar_view.xml'
    id = None
    order_name = None
    order_method = None
    order_label = None
    admin_bar_prefix_name = None
    items_css_class = None
    item_view = Bar_Item_View

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        buttons = []
        site_root = resource.get_site_root()
        repository = site_root.get_repository()
        section_path = context.get_link(resource)
        path = context.get_link(repository)
        buttons.append({'path': '%s/;%s' % (section_path, self.order_method),
                        'icon': '/ui/common/icons/48x48/sort.png',
                        'label': self.order_label,
                        'target': None})

        return buttons


    def is_empty(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if allowed:
            return False
        return len(self._get_items(resource, context)) == 0


    def _get_items(self, resource, context, check_acl=True):
        order = resource.get_resource(self.order_name, soft=True)
        if order is None:
            return []

        orderfile = order.handler
        user = context.user
        repository = resource.get_site_root().get_repository()
        order = orderfile.get_records_in_order()
        items = []

        for record in order:
            name = orderfile.get_record_value(record, 'name')
            item = repository.get_resource(name, soft=True)
            if item is None:
                path = resource.get_abspath()
                warn(u'%s > bar item not found: %s' % (path, name))
                continue
            if check_acl:
                ac = item.get_access_control()
                if ac.is_allowed_to_view(user, item) is False:
                    continue

            items.append(item)
        return items


    def get_items(self, resource, context):
        here = context.resource
        items = []

        # FIXME Add the section to the context for section TOC views
        context._section = resource

        for item in self._get_items(resource, context, check_acl=True):
            view = item.view
            view.set_view_is_empty(False)
            stream = view.GET(item, context)
            if view.get_view_is_empty() or stream is None:
                continue
            prefix = here.get_pathto(item)
            stream = set_prefix(stream, '%s/' % prefix)
            buttons = item.view.get_manage_buttons(item, context)

            # FIXME if the item name contains '.', the item id is
            # interpreted as #id.class by jquery
            item_id = '%s-%s-%s' % (self.admin_bar_prefix_name,
                                    item.class_id, item.name)
            admin_bar = get_admin_bar(buttons, item_id, item.class_title)
            namespace = {}
            namespace['id'] = item_id
            namespace['format'] = item.class_id
            namespace['admin_bar'] = admin_bar
            namespace['content'] = stream
            namespace['css_class'] = self.items_css_class
            render_view = self.item_view(namespace=namespace)
            items.append(render_view.GET(resource, context))

        # FIXME Remove the section from the context for section TOC views
        del context._section

        return items


    def get_namespace(self, resource, context):
        namespace = {'id': self.id}

        # Manage buttons
        manage_buttons = self.get_manage_buttons(resource, context)
        allowed_to_edit = len(manage_buttons) > 0
        # XXX 'article-items'
        namespace['admin_bar'] = get_admin_bar(manage_buttons,
                self.admin_bar_prefix_name, icon=True)

        # Bar items
        items = self.get_items(resource, context)
        namespace['items'] = items
        namespace['items_css_class'] = self.items_css_class

        # Do not display the box if there is no items
        display = True
        if allowed_to_edit is False and len(items) == 0:
            display = False
        namespace['display'] = display

        return namespace



class SideBar_View(Bar_View):

    id = 'sidebar-items'
    order_name = 'order-sidebar'
    order_method = 'order_sidebar'
    order_label = MSG(u'Add/Order sidebar items')
    admin_bar_prefix_name = 'sidebar-item'
    items_css_class = 'sidebar-item'

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        site_root = resource.get_site_root()
        buttons = Bar_View.get_manage_buttons(self, resource, context)
        section_path = context.get_link(resource)
        repository = site_root.get_repository()
        path = context.get_link(repository)
        buttons.append({'path': '%s/;new_sidebar_resource' % path,
                        'icon': '/ui/common/icons/48x48/new.png',
                        'label': MSG(u'Create a new sidebar item'),
                        'target': '_blank'})

        return buttons



class ContentBar_View(Bar_View):

    id = 'contentbar-items'
    order_name = 'order-contentbar'
    order_method = 'order_contentbar'
    order_label = MSG(u'Add/Order contentbar items')
    admin_bar_prefix_name = 'contentbar-item'
    items_css_class = 'contentbar-item'

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        site_root = resource.get_site_root()
        buttons = Bar_View.get_manage_buttons(self, resource, context)
        section_path = context.get_link(resource)
        repository = site_root.get_repository()
        path = context.get_link(repository)
        buttons.append({'path': '%s/;new_contentbar_resource' % path,
                        'icon': '/ui/common/icons/48x48/new.png',
                        'label': MSG(u'Create a new contentbar item'),
                        'target': '_blank'})

        return buttons



################################################################################
# Resources
################################################################################
class SideBarAware(object):

    class_views = ['order_sidebar']
    sidebar_name = 'order-sidebar'
    __fixed_handlers__ = [sidebar_name]

    order_sidebar = GoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=sidebar_name,
        title=MSG(u'Order the sidebar items'))

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        cls2 = SidebarItemsOrderedTable
        cls2._make_resource(cls2, folder,
                            '%s/%s' % (name, cls.sidebar_name))



class ContentBarAware(object):

    class_views = ['order_contentbar']
    contentbar_name = 'order-contentbar'
    __fixed_handlers__ = [contentbar_name]

    order_contentbar = GoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=contentbar_name,
        title=MSG(u'Order the contentbar items'))

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        cls2 = ContentbarItemsOrderedTable
        cls2._make_resource(cls2, folder,
                            '%s/%s' % (name, cls.contentbar_name))
