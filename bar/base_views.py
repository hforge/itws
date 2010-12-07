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
from warnings import warn

# Import from itools
from itools.gettext import MSG
from itools.stl import set_prefix
from itools.web import STLView

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
    views = []

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        buttons = []
        section_path = context.get_link(resource)
        # Order table empty ?
        order_table = resource.get_resource(self.order_name)
        if len(list(order_table.handler.get_record_ids())):
            buttons.append(
                    {'path': '%s/;%s' % (section_path, self.order_method),
                     'icon': '/ui/common/icons/16x16/sort.png',
                     'rel': 'fancybox',
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


    def _get_item_id(self, item, context):
        return '%s-%s' % (item.class_id, item.name)


    def _get_items(self, resource, context, check_acl=True):
        order = resource.get_resource(self.order_name, soft=True)
        if order:
            orderfile = order.handler
            user = context.user
            repository = self._get_repository(resource, context)
            order = orderfile.get_records_in_order()

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

        # FIXME Add the BarAware resource to the context
        # It is used by section TOC views
        _bar_aware = resource
        while isinstance(_bar_aware, self.container_cls) is False:
            if _bar_aware.parent is None:
                break
            _bar_aware = _bar_aware.parent
        context._bar_aware = _bar_aware

        for item in self._get_items(resource, context, check_acl=True):
            view = item.view
            self.views.append(view)
            view.set_view_is_empty(False)
            stream = view.GET(item, context)
            if view.get_view_is_empty() or stream is None:
                continue
            prefix = here.get_pathto(item)
            stream = set_prefix(stream, '%s/' % prefix)
            item_id = self._get_item_id(item, context)
            # replace '.' by -dot- because '.' is interpreted as a class in CSS
            item_id = item_id.replace('.', '-dot-')
            namespace = {
                'id': item_id,
                'format': item.class_id,
                'admin_bar': get_admin_bar(item),
                'content': stream,
                'css_class': self.boxes_css_class}
            render_view = self.box_view(namespace=namespace)
            items.append(render_view.GET(resource, context))

        # FIXME Remove the section from the context for section TOC views
        del context._bar_aware

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


    def get_styles(self, context):
        styles = []
        for view in self.views:
            styles.extend(view.get_styles(context))
        return styles


    def get_scripts(self, context):
        scripts = []
        for view in self.views:
            scripts.extend(view.get_scripts(context))
        return scripts



class SideBar_View(Bar_View):

    id = 'sidebar-items'
    order_name = 'order-sidebar'
    order_method = 'order_sidebar'
    order_label = MSG(u'Order Sidebar Boxes')
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
                            'label': MSG(u'Add Sidebar Box'),
                            'rel': 'fancybox',
                            'target': None})
        else:
            # XXX What text and what icon ?
            section_path = context.get_link(resource)
            buttons = [{'path': section_path,
                        'icon': '/ui/icons/16x16/search.png',
                        'label': MSG(u'Go there to edit sidebar'),
                        'rel': None,
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
        from bar_aware import ContentBarAware
        return ContentBarAware


    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        buttons = Bar_View.get_manage_buttons(self, resource, context)
        section_path = context.get_link(resource)
        buttons.append({'path': '%s/;new_contentbar_resource' % section_path,
                        'icon': '/ui/common/icons/16x16/new.png',
                        'rel': 'fancybox',
                        'label': MSG(u'Add Central Part Box'),
                        'target': None})

        return buttons


    def _get_repository(self, resource, context):
        return resource.get_site_root().get_repository()


    def _get_item_id(self, item, context):
        return '%s-%s-%s' % (item.class_id, context._bar_aware.name, item.name)



