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

# Import from standard library

# Import from itools
from itools.core import freeze
from itools.datatypes import Decimal, Integer
from itools.gettext import MSG
from itools.web import INFO, STLForm, STLView

# Import from ikaaro
from ikaaro.autoform import AutoForm, SelectWidget, TextWidget
from ikaaro.file import PDF
from ikaaro.views import CompositeForm, CompositeView

# Import from itws
from itws.payments import PaymentWays_Enumerate, format_price
from itws.payments import PaymentWays_Widget, get_payments
from itws.views import FieldsAdvance_NewInstance
from itws.feed_views import TableFeed_View, FieldsTableFeed_View

# Import from orders
from product import Product_List
from utils import get_orders
from workflows import OrderStateEnumerate


class Order_AddLine(AutoForm):

    access = 'is_admin'
    title = MSG(u'Add a line')
    schema = {'product': Product_List,
              'quantity': Integer}
    widgets = [SelectWidget('product', title=MSG(u'Line')),
               TextWidget('quantity', title=MSG(u'Quantity'))]

    def action(self, resource, context, form):
        r = resource.get_resource(form['product'])
        resource.add_lines([(form['quantity'], r)])
        message = INFO(u'This product has been added to your order')
        return context.come_back(message, goto='./;manage')



class Order_ViewBills(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'List bills')

    table_actions = []
    show_resource_title = False
    query_suffix = 'order-bill'

    batch_msg1 = MSG(u"There is 1 bill.")
    batch_msg2 = MSG(u"There are {n} bills.")

    table_fields = ['name', 'title']

    search_class_id = 'application/pdf'
    search_cls = PDF


class Order_ViewPayments(TableFeed_View):

    access = 'is_admin'
    title = MSG(u'List Payments')

    show_resource_title = False
    query_suffix = 'payments'
    table_actions = []

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are {n} payments.")

    table_columns = freeze([
        ('reference', MSG(u'Reference')),
        ('payment_way', MSG(u'Payment Way')),
        ('amount', MSG(u'Amount')),
        ('advanced_state', MSG(u'Advanced state')),
        ('is_payment_validated', MSG(u'Validated ?'))])


    def get_items(self, resource, context):
        return resource.get_payments(as_results=True)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'reference':
            return (brain.name, brain.name)
        elif column == 'payment_way':
            return item_resource.get_payment_way().get_title()
        elif column == 'amount':
            return format_price(item_resource.get_property('amount'))
        elif column == 'advanced_state':
            return item_resource.get_advanced_state()
        elif column  == 'is_payment_validated':
            return item_resource.is_payment_validated()
        raise NotImplementedError



class Order_AddPayment(AutoForm):

    access = 'is_admin'
    title = MSG(u'Add a payment')
    return_message = INFO(u"Please follow the payment procedure below.")

    schema = freeze({
        'amount': Decimal,
        'mode': PaymentWays_Enumerate})
    widgets = freeze([
        TextWidget('amount', title=MSG(u'Amount')),
        PaymentWays_Widget('mode', title=MSG(u"Payment Way"))])


    def action(self, resource, context, form):
        payments_module = get_payments(resource)
        payment = payments_module.make_payment(
                      resource, form['mode'], form['amount'],
                      context.user, order=resource)
        goto = '%s/;payment_form' % context.get_link(payment)
        return context.come_back(self.return_message, goto=goto)



class Order_AdminTop(STLForm):
    """Display order main information with state and products."""
    access = 'is_admin'
    title = MSG(u'Manage order')
    template = '/ui/orders/order_manage.xml'


    def get_namespace(self, resource, context):
        orders = get_orders(resource)
        total_price = resource.get_property('total_price')
        namespace = resource.get_namespace(context)
        namespace['orders_link'] = context.get_link(orders)
        namespace['order'] = {'id': resource.name}
        namespace['total_price'] = format_price(total_price)
        namespace['products'] = resource.get_products_namespace(context)
        namespace['state'] = SelectWidget('state', has_empty_option=False,
            datatype=OrderStateEnumerate, value=resource.get_statename()).render()
        return namespace


    action_change_order_state_schema = {'state': OrderStateEnumerate}
    def action_change_order_state(self, resource, context, form):
        resource.set_workflow_state(form['state'])


class Order_Top(STLView):

    access = 'is_allowed_to_view'
    template = '/ui/orders/order_top.xml'

    def get_namespace(self, resource, context):
        bill = resource.get_resource('bill', soft=True)
        return {'name': resource.name,
                'bill': context.get_link(bill) if bill else None,
                'is_paid': resource.get_property('is_paid')}



class Order_ViewProducts(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View products')
    template = '/ui/orders/order_view_products.xml'

    def get_namespace(self, resource, context):
        namespace = {}
        namespace['products'] = resource.get_products_namespace(context)
        namespace['total_price'] = resource.get_property('total_price')
        return namespace


class Order_View(CompositeView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')

    subviews = [Order_Top(),
                Order_ViewProducts()]



class Order_Manage(CompositeForm):
    """Display order main information with state and products
       and below a list of payments and bills.
    """
    access = 'is_admin'
    title = MSG(u'Manage order')

    subviews = [Order_AdminTop(),
                Order_ViewProducts(),
                Order_ViewPayments(),
                Order_ViewBills()]


class Order_NewInstance(FieldsAdvance_NewInstance):

    access = 'is_admin'
    title = MSG(u'Create a new order')
    fields = ['customer_id']

    def _get_form(self, resource, context):
        # Skip checking name as we use make_reference
        return super(AutoForm, self)._get_form(resource, context)


    def action(self, resource, context, form):
        orders_module = resource
        order = orders_module.make_order(resource, context.user, lines=[])
        goto = context.get_link(order)
        message = MSG(u'Order has been created')
        return context.come_back(message, goto=goto)
