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
from repository import ContentbarBoxesOrderedTable
from repository import SidebarBoxesOrderedTable
from utils import get_admin_bar
from views import BarAwareBoxAwareNewInstance



################################################################################
# Views
################################################################################
class BarBox_View(STLView):

    template = '/ui/common/BarBox_view.xml'
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
    boxes_css_class = None
    box_view = BarBox_View
    container_cls = None

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
                        'icon': '/ui/common/icons/16x16/sort.png',
                        'label': self.order_label,
                        'target': None})

        return buttons


    def is_empty(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if allowed:
            return False
        for item in self._get_items(resource, context):
            return False
        return True


    def _get_repository(self, resource, context):
        return resource.get_site_root().get_repository()


    def _get_items(self, resource, context, check_acl=True):
        order = resource.get_resource(self.order_name, soft=True)
        if order:
            orderfile = order.handler
            user = context.user
            repository = self._get_repository(resource, context)
            order = orderfile.get_records_in_order()
            items = []

            for record in order:
                name = orderfile.get_record_value(record, 'name')
                item = repository.get_resource(name, soft=True)
                if item is None:
                    path = resource.get_abspath()
                    warn('%s > bar item not found: %s' % (path, name))
                    continue
                if check_acl:
                    ac = item.get_access_control()
                    if ac.is_allowed_to_view(user, item) is False:
                        continue

                yield item


    def get_items(self, resource, context):
        here = context.resource
        items = []

        # FIXME Add the section to the context for section TOC views
        _section = resource
        while isinstance(_section, self.container_cls) is False:
            _section = _section.parent
        context._section = _section
        context._bar_aware = _section

        for item in self._get_items(resource, context, check_acl=True):
            view = item.view
            view.set_view_is_empty(False)
            stream = view.GET(item, context)
            if view.get_view_is_empty() or stream is None:
                continue
            prefix = here.get_pathto(item)
            stream = set_prefix(stream, '%s/' % prefix)
            item_id = '%s-%s' % (item.class_id, item.name.replace('.', '-dot-'))
            namespace = {
                'id': item_id,
                'format': item.class_id,
                'admin_bar': get_admin_bar(item),
                'content': stream,
                'css_class': self.boxes_css_class}
            render_view = self.box_view(namespace=namespace)
            items.append(render_view.GET(resource, context))

        # FIXME Remove the section from the context for section TOC views
        del context._section

        return items


    def get_namespace(self, resource, context):
        namespace = {'id': self.id}

        # Manage buttons
        manage_buttons = self.get_manage_buttons(resource, context)
        allowed_to_edit = len(manage_buttons) > 0
        namespace['admin_bar'] = get_admin_bar(resource, manage_buttons)

        # Bar items
        items = self.get_items(resource, context)
        namespace['items'] = items

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
    order_label = MSG(u'Order Sidebar Boxes')
    admin_bar_prefix_name = 'sidebar-box'
    boxes_css_class = 'sidebar-box'


    @property
    def container_cls(self):
        return SideBarAware


    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        site_root = resource.get_site_root()
        if isinstance(context.resource, SideBarAware):
            buttons = Bar_View.get_manage_buttons(self, resource, context)
            section_path = context.get_link(resource)
            buttons.append({'path': '%s/;new_sidebar_resource' % section_path,
                            'icon': '/ui/common/icons/16x16/new.png',
                            'label': MSG(u'Add Sidebar Box'),
                            'target': None})
        else:
            # XXX What text and what icon ?
            section_path = context.get_link(resource)
            buttons = [{'path': section_path,
                        'icon': '/ui/icons/16x16/search.png',
                        'label': MSG(u'Go there to edit sidebar'),
                        'target': None}]
        return buttons



class ContentBar_View(Bar_View):

    id = 'contentbar-items'
    order_name = 'order-contentbar'
    order_method = 'order_contentbar'
    order_label = MSG(u'Order Central Part Boxes')
    admin_bar_prefix_name = 'contentbar-box'
    boxes_css_class = 'contentbar-box'


    @property
    def container_cls(self):
        return ContentBarAware


    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        site_root = resource.get_site_root()
        buttons = Bar_View.get_manage_buttons(self, resource, context)
        section_path = context.get_link(resource)
        buttons.append({'path': '%s/;new_contentbar_resource' % section_path,
                        'icon': '/ui/common/icons/16x16/new.png',
                        'label': MSG(u'Add Central Part Box'),
                        'target': None})

        return buttons


    def _get_repository(self, resource, context):
        return resource.get_site_root().get_repository()




################################################################################
# Resources
################################################################################
class SideBarAware(object):

    class_version = '20100621'
    class_views = ['order_sidebar']
    sidebar_name = 'order-sidebar'
    __fixed_handlers__ = [sidebar_name]

    order_sidebar = GoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=sidebar_name,
        title=MSG(u'Order Sidebar Boxes'))
    new_sidebar_resource = BarAwareBoxAwareNewInstance(
            title=MSG(u'Add Sidebar Box'), is_side=True)

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        cls2 = SidebarBoxesOrderedTable
        cls2._make_resource(cls2, folder,
                            '%s/%s' % (name, cls.sidebar_name))


    def update_20100621(self):
        # Fix class_id
        table = self.get_resource(self.sidebar_name)
        metadata = table.metadata
        metadata.set_changed()
        metadata.format = 'sidebar-boxes-ordered-table'



class ContentBarAware(object):

    class_version = '20100622'
    class_views = ['order_contentbar']
    contentbar_name = 'order-contentbar'
    __fixed_handlers__ = [contentbar_name]

    order_contentbar = GoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=contentbar_name,
        title=MSG(u'Order Central Part Boxes'))
    new_contentbar_resource = BarAwareBoxAwareNewInstance(
            title=MSG(u'Add Central Part Box'), is_content=True)

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        cls2 = ContentbarBoxesOrderedTable
        cls2._make_resource(cls2, folder,
                            '%s/%s' % (name, cls.contentbar_name))


    def update_20100622(self):
        # Fix class_id
        table = self.get_resource(self.contentbar_name)
        metadata = table.metadata
        metadata.set_changed()
        metadata.format = 'contentbar-boxes-ordered-table'
