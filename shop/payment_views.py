# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.stl import stl
from itools.web import STLView, get_context

# Import from ikaaro
from ikaaro.autoform import ReadOnlyWidget
from ikaaro.utils import make_stl_template

# Import from payments
from itws.views import FieldsAutomaticEditView


class Payment_Edit(FieldsAutomaticEditView):

    access = 'is_admin'
    title = MSG(u'Edit')

    base_edit_fields = ['amount', 'is_paid']
    introduction_template = '/ui/shop/payments/payment_introduction.xml'

    @property
    def edit_fields(self):
        resource = get_context().resource
        return self.base_edit_fields + resource.payment_fields


    def get_widget(self, name, datatype):
        if name == 'amount':
            return ReadOnlyWidget('amount', title=MSG(u"Amount"))
        proxy = super(Payment_Edit, self)
        return proxy.get_widget(name, datatype)


    def get_namespace(self, resource, context):
        namespace = FieldsAutomaticEditView.get_namespace(self, resource, context)
        namespace['before'] = self.get_introduction(resource, context)
        return namespace


    def get_introduction(self, resource, context):
        # Get payement way
        payment_way = resource.get_payment_way()
        if payment_way:
            payment_way = {'title': payment_way.get_title(),
                           'link': context.get_link(payment_way)}
        # Get order
        order = resource.get_order()
        if order:
            order = {'title': order.get_title(),
                     'link': context.get_link(order)}
        # Build namespace
        namespace = {'name': resource.name,
                     'order': order, 'payment_way': payment_way}
        template = resource.get_resource(self.introduction_template)
        return stl(template, namespace=namespace)


    def action(self, resource, context, form):
        # Update payment state
        resource.update_payment_state(context, paid=form['is_paid'])
        # Action
        proxy = super(Payment_Edit, self)
        return proxy.action(resource, context, form)



class Payment_End(STLView):

    access = 'is_allowed_to_view'
    template = '/ui/shop/payments/payment_end.xml'

    def get_namespace(self, resource, context):
        payment_way = resource.get_payment_way()
        return {'payment_end_msg': payment_way.get_property('payment_end_msg')}
