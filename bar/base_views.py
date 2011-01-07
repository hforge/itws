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

# Import from standard library
from copy import copy
from warnings import warn

# Import from itools
from itools.core import lazy
from itools.gettext import MSG
from itools.stl import set_prefix
from itools.web import get_context, STLView

# Import from ikaaro
from ikaaro.views import CompositeView

# Import from itws
from itws.utils import get_admin_bar



class Box_View(STLView):

    styles = []
    scripts = []

    def get_view_is_empty(self):
        return getattr(self, '_view_is_empty', False)


    def set_view_is_empty(self, value):
        setattr(self, '_view_is_empty', value)


    def is_admin(self, resource, context):
        ac = resource.get_access_control()
        return ac.is_allowed_to_edit(context.user, resource)


    def get_styles(self, context):
        return self.styles


    def get_scripts(self, context):
        return self.scripts



class Bar_View(CompositeView):

    template = '/ui/common/Bar_view.xml'
    id = None
    order_name = None
    order_method = None
    order_label = None
    admin_bar_prefix_name = None
    boxes_css_class = None
    container_cls = None

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        buttons = []
        section_path = context.get_link(resource)
        # Order table empty ?
        order_path = self.get_order_path(resource)
        order_table = resource.get_resource(order_path)
        if len(list(order_table.handler.get_record_ids())):
            buttons.append(
                    {'path': '%s/;%s' % (section_path, self.order_method),
                     'icon': '/ui/common/icons/16x16/sort.png',
                     'rel': 'fancybox',
                     'label': self.order_label,
                     'target': None})

        return buttons


    def get_order_path(self, resource):
        if resource.repository is None:
            return self.order_name
        return '%s/%s' % (resource.repository, self.order_name)


    def is_empty(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if allowed:
            return False
        for item in self.subviews:
            return False
        return True


    def _get_repository(self, resource, context):
        return resource.get_site_root().get_repository()


    def _get_item_id(self, item, context):
        item_id = '%s-%s' % (item.class_id, item.name)
        item_id = item_id.replace('.', '-dot-')
        return item_id


    def get_bar_aware(self, resource, context):
        _bar_aware = resource
        while isinstance(_bar_aware, self.container_cls) is False:
            if _bar_aware.parent is None:
                break
            _bar_aware = _bar_aware.parent
        context._bar_aware = _bar_aware
        return _bar_aware


    @lazy
    def subviews(self):
        all_items = []
        context = get_context()
        resource = context.resource
        bar_aware_resource = self.get_bar_aware(resource, context)
        order_path = self.get_order_path(bar_aware_resource)
        order = bar_aware_resource.get_resource(order_path)
        orderfile = order.handler
        user = context.user
        repository = self._get_repository(bar_aware_resource, context)
        order = orderfile.get_records_in_order()

        for record in order:
            name = orderfile.get_record_value(record, 'name')
            item = repository.get_resource(name)
            if item is None:
                path = item.get_abspath()
                warn('%s > bar item not found: %s' % (path, name))
                continue
            ac = item.get_access_control()
            if ac.is_allowed_to_view(user, item) is False:
                continue
            view = copy(item.view)
            view.item = item
            all_items.append(view)
        return all_items


    def get_namespace(self, resource, context):
        here = context.resource
        # Build namespace
        namespace = {'id': self.id}

        # Manage buttons
        manage_buttons = self.get_manage_buttons(resource, context)
        allowed_to_edit = len(manage_buttons) > 0
        namespace['admin_bar'] = get_admin_bar(resource, manage_buttons)

        # Bar items
        views = []
        for view in self.subviews:
            item = view.item
            if view.get_view_is_empty():
                continue
            stream = view.GET(item, context)
            prefix = here.get_pathto(item)
            stream = set_prefix(stream, '%s/' % prefix)
            views.append(
              {'id': self._get_item_id(item, context),
               'css_class': self.boxes_css_class,
               'format': item.class_id,
               'admin_bar': get_admin_bar(item),
               'content': stream})

        namespace['views'] = views
        # Do not display the box if there is no items
        display = True
        if allowed_to_edit is False and len(views) == 0:
            display = False
        namespace['display'] = display
        # Del context._bar_aware
        del context._bar_aware

        return namespace



class SideBar_View(Bar_View):

    id = 'sidebar-items'
    order_name = 'order-sidebar'
    order_method = 'order_sidebar'
    order_label = MSG(u'Order sidebar boxes')
    admin_bar_prefix_name = 'sidebar-box'
    boxes_css_class = 'sidebar-box'


    @property
    def container_cls(self):
        from bar_aware import SideBarAware
        return SideBarAware


    def get_manage_buttons(self, resource, context):
        from bar_aware import SideBarAware
        from itws.ws_neutral import NeutralWS
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        if isinstance(context.resource, (NeutralWS, SideBarAware)):
            buttons = Bar_View.get_manage_buttons(self, resource, context)
            section_path = context.get_link(resource)
            buttons.append({'path': '%s/;new_sidebar_resource' % section_path,
                            'icon': '/ui/common/icons/16x16/new.png',
                            'label': MSG(u'Add a sidebar box'),
                            'rel': 'fancybox',
                            'target': None})
        else:
            section_path = context.get_link(resource)
            buttons = [{'path': section_path,
                        'icon': '/ui/icons/16x16/search.png',
                        'label': MSG(u'Go there to edit sidebar'),
                        'rel': None,
                        'target': None}]
        return buttons
