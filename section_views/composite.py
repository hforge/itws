# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.gettext import MSG

# Import from itws
from itws.bar.base_views import Bar_View


class Section_Composite_View(Bar_View):

    title = MSG(u'View')
    access = 'is_allowed_to_view'

    view_name = 'composite-view'
    view_title = MSG(u'Composite view')
    view_configuration_cls = None

    order_name = 'order-contentbar'
    repository = '.'

    id = 'contentbar-items'
    order_name = 'order-contentbar'
    order_method = 'order_contentbar'
    order_label = MSG(u'Order Central Part Boxes')
    admin_bar_prefix_name = 'contentbar-box'
    boxes_css_class = 'contentbar-box'


    @property
    def container_cls(self):
        from itws.bar.bar_aware import ContentBarAware
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


    def _get_item_id(self, item, context):
        return '%s-%s-%s' % (item.class_id, context._bar_aware.name, item.name)


    def _get_repository(self, resource, context):
        if resource.repository:
            return resource.get_resource(resource.repository)
        return resource
