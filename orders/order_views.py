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
from itools.web import INFO, STLForm

# Import from ikaaro
from ikaaro.autoform import AutoForm, SelectWidget, TextWidget
from ikaaro.file import PDF
from ikaaro.views import CompositeForm
from ikaaro.workflow import get_workflow_preview

# Import from itws
from itws.payments import PaymentWays_Enumerate, get_payment_way, format_price
from itws.payments import PaymentWays_Widget
from itws.feed_views import TableFeed_View, FieldsTableFeed_View

# Import from orders
from product import Product_List
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
        ('amount', MSG(u'total_price')),
        ('is_payment_validated', MSG(u'Validated ?')),
        ('state', MSG(u'State'))])


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
        elif column  == 'is_payment_validated':
            return item_resource.is_payment_validated()
        elif column == 'state':
            return get_workflow_preview(item_resource, context)
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
        # Create payment and redirect to payment form
        payment_way = get_payment_way(resource, form['mode'])
        if not payment_way.is_enabled(context):
            raise ValueError
        total_price = form['amount']
        payment = resource.make_payment(payment_way, total_price)
        goto = '%s/;payment_form' % context.get_link(payment)
        return context.come_back(self.return_message, goto=goto)



class Order_Top(STLForm):
    """Display order main information with state and products."""
    access = 'is_admin'
    title = MSG(u'Manage order')
    template = '/ui/orders/order_manage.xml'


    def get_namespace(self, resource, context):
        customer_id = resource.get_property('customer_id')
        from itws.enumerates import Users_Enumerate
        from utils import get_orders
        orders = get_orders(resource)
        namespace = {}
        namespace['orders_link'] = context.get_link(orders)
        namespace['order'] = {'id': resource.name}
        namespace['customer'] = Users_Enumerate.get_value(customer_id)
        namespace['products'] = resource.get_products_namespace()
        namespace['transitions'] = SelectWidget('state',
            datatype=OrderStateEnumerate, value=None).render()
        return namespace


    def action_generate_bill(self, resource, context, form):
        return resource.generate_bill(context)


    action_change_order_state_schema = {'state': OrderStateEnumerate}
    def action_change_order_state(self, resource, context, form):
        resource.set_workflow_state(form['state'])



class Order_Manage(CompositeForm):
    """Display order main information with state and products
       and below a list of payments and bills.
    """
    access = 'is_admin'
    title = MSG(u'Manage order')

    subviews = [Order_Top(),
                Order_ViewPayments(),
                Order_ViewBills()]
