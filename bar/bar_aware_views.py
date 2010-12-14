# -*- coding: UTF-8 -*-
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


# Import from itools
from itools.core import freeze, merge_dicts
from itools.csv import Property
from itools.gettext import MSG
from itools.uri import get_reference

# Import from ikaaro
from ikaaro import messages
from ikaaro.autoform import RadioWidget
from ikaaro.registry import get_resource_class
from ikaaro.workflow import StaticStateEnumerate, WorkflowAware

# Import from itws
from datatypes import MyAuthorized_Classid, OrderBoxEnumerate
from itws.utils import state_widget
from itws.views import EasyNewInstance
from itws.widgets import ClassSelectorWidget



class EasyNewInstance_WithOrderer(EasyNewInstance):
    """
      NewInstance with:
        - Name is not need
        - Publication state is need
        - Has a selector of class id
        - Has a selector of position of resource in a given table
    """

    order_widget_title = MSG(u'Order box')

    def _get_container(self, resource, context):
        raise NotImplementedError


    def _get_order_table(self, resource, context):
        raise NotImplementedError


    def _get_box_goto(self, child, context):
        link_child = '%s/;edit' % context.get_link(child)
        goto = get_reference(link_child)
        # Is admin popup ?
        if ('is_admin_popup' in context.get_referrer() and
            getattr(child, 'use_fancybox', True) is True):
            goto.query['is_admin_popup'] = '1'
        else:
            goto = None
        return goto


    def get_schema(self, resource, context):
        return merge_dicts(EasyNewInstance.get_schema(self, resource, context),
                           class_id=MyAuthorized_Classid(view=self,
                               resource=resource, context=context,
                               mandatory=True),
                           order=OrderBoxEnumerate(default='order-bottom'),
                           state=StaticStateEnumerate(default='public'))


    def get_widgets(self, resource, context):
        return freeze(EasyNewInstance.get_widgets(self, resource, context) +
                      [ state_widget,
                       ClassSelectorWidget('class_id',
                           title=MSG(u'Resource type'), has_empty_option=False),
                       RadioWidget('order', title=self.order_widget_title,
                                  has_empty_option=False)])


    def get_value(self, resource, context, name, datatype):
        if name == 'cls_description':
            return u''
        elif name == 'class_id':
            value = context.query['type']
            return value or ''
        return EasyNewInstance.get_value(self, resource, context, name,
                                         datatype)


    def order_item(self, order, name, form, resource, context):
        order_table = self._get_order_table(resource, context)

        # Order child
        record = order_table.add_new_record({'name': name})
        if order == 'order-top':
            order_table.handler.order_top([record.id])
        else:
            order_table.handler.order_bottom([record.id])


    def action(self, resource, context, form):
        name = form['name']
        title = form['title']
        order = form['order']

        # Create the resource
        class_id = form['class_id']
        cls = get_resource_class(class_id)
        container = self._get_container(resource, context)
        child = container.make_resource(name, cls)

        # We order the resource in table if needed
        if order != 'do-not-order':
            self.order_item(order, name, form, resource, context)

        # The metadata
        metadata = child.metadata
        language = resource.get_edit_languages(context)[0]
        title = Property(title, lang=language)
        metadata.set_property('title', title)

        # Workflow
        if isinstance(child, WorkflowAware):
            child.set_property('state', form['state'])

        # Calcul Goto
        goto = self._get_box_goto(child, context)

        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class SideBarBox_NewInstance(EasyNewInstance_WithOrderer):


    def get_sidebaraware_resource(self, resource):
        from bar_aware import SideBarAware
        while not isinstance(resource, SideBarAware):
            resource = resource.parent
        return resource


    def _get_container(self, resource, context):
        site_root = resource.get_site_root()
        return site_root.get_repository()


    def _get_order_table(self, resource, context):
        sidebaraware_resource = self.get_sidebaraware_resource(resource)
        return sidebaraware_resource.get_order_table_sidebar()


    def get_aware_document_types(self, resource, context):
        site_root = resource.get_site_root()
        repository = site_root.get_repository()
        return repository._get_document_types(
                is_content=None, is_side=True,
                allow_instanciation=True)



class ContentBarBox_NewInstance(EasyNewInstance_WithOrderer):

    def get_contentbaraware_resource(self, resource):
        from bar_aware import ContentBarAware
        while not isinstance(resource, ContentBarAware):
            resource = resource.parent
        return resource


    def _get_container(self, resource, context):
        return resource.parent


    def _get_order_table(self, resource, context):
        contentbaraware_resource = self.get_contentbaraware_resource(resource)
        return contentbaraware_resource.get_order_table_contentbar()


    def get_aware_document_types(self, resource, context):
        site_root = resource.get_site_root()
        repository = site_root.get_repository()
        return repository._get_document_types(
                is_content=True, is_side=None,
                allow_instanciation=True)
