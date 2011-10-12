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
from itools.database import PhraseQuery
from itools.datatypes import Decimal, Enumerate, Integer
from itools.gettext import MSG
from itools.web import INFO, ERROR, STLForm, STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import AutoForm, SelectWidget, TextWidget
from ikaaro.file import PDF
from ikaaro.utils import CMSTemplate
from ikaaro.views import CompositeForm, CompositeView

# Import from itws
from itws.views import FieldsAdvance_NewInstance
from itws.feed_views import TableFeed_View, FieldsTableFeed_View
from itws.utils import bool_to_img

# Import from shop
from devises import Devises
from payments_views import PaymentWays_Enumerate
from product import Product_List
from utils import join_pdfs, get_orders, get_payments
from widgets import PaymentWays_Widget
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
    title = MSG(u'Bills')

    table_actions = []
    show_resource_title = False
    query_suffix = 'order-bill'

    batch_msg1 = MSG(u"There is 1 bill.")
    batch_msg2 = MSG(u"There are {n} bills.")

    table_fields = ['name', 'title']

    search_class_id = 'application/pdf'
    search_cls = PDF



class Order_ViewPayments(TableFeed_View):

    access = 'is_allowed_to_view'
    title = MSG(u'Payments')

    show_resource_title = False
    query_suffix = 'payments'
    table_actions = []

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are {n} payments.")

    admin_view = False
    table_columns = freeze([
        ('reference', MSG(u'Reference')),
        ('payment_way', MSG(u'Payment Way')),
        ('amount', MSG(u'Amount')),
        ('is_payment_validated', MSG(u'Validated ?'))])

    def get_table_columns(self, resource, context):
        if self.admin_view is False:
            return self.table_columns
        return self.table_columns + [
            ('advanced_state', MSG(u'Advanced state'))]


    def get_items(self, resource, context):
        return resource.get_payments(as_results=True)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'reference':
            if self.admin_view is False:
                return brain.name
            return (brain.name, brain.name)
        elif column == 'payment_way':
            return item_resource.get_payment_way().get_title()
        elif column == 'amount':
            devise = item_resource.get_property('devise')
            symbol = Devises.symbols[devise]
            amount = item_resource.get_property('amount')
            return u'%s %s' % (amount, symbol)
        elif column == 'advanced_state':
            return item_resource.get_advanced_state()
        elif column  == 'is_payment_validated':
            value = item_resource.is_payment_validated()
            if value:
                return bool_to_img(value)
            return u'Régler', '%s/;payment_form' % brain.name
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
        devise = resource.get_property('devise')
        payment = payments_module.make_payment(
                      resource, form['mode'], form['amount'],
                      context.user, devise, order=resource)
        goto = '%s/;payment_form' % context.get_link(payment)
        return context.come_back(self.return_message, goto=goto)



class Order_AdminTop(STLForm):
    """Display order main information with state and products."""
    access = 'is_admin'
    title = MSG(u'Manage order')
    template = '/ui/shop/orders/order_manage.xml'


    def get_namespace(self, resource, context):
        orders = get_orders(resource)
        namespace = resource.get_namespace(context)
        namespace['orders_link'] = context.get_link(orders)
        namespace['order'] = {'id': resource.name}
        #namespace['state'] = SelectWidget('state', has_empty_option=False,
        #    datatype=OrderStateEnumerate, value=resource.get_statename()).render()
        return namespace


    #action_change_order_state_schema = {'state': OrderStateEnumerate}
    #def action_change_order_state(self, resource, context, form):
    #    resource.generate_bill(context)
    #    resource.set_workflow_state(form['state'])


class Order_Top(STLView):

    access = 'is_allowed_to_view'
    template = '/ui/shop/orders/order_top.xml'

    def get_namespace(self, resource, context):
        bill = resource.get_bill()
        return {'name': resource.name,
                'bill': context.get_link(bill) if bill else None,
                'is_paid': resource.get_property('is_paid')}



class Order_ViewProducts(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'Products')
    template = '/ui/shop/orders/order_view_products.xml'

    def get_namespace(self, resource, context):
        namespace = {}
        namespace['products'] = resource.get_products_namespace(context)
        total = resource.get_property('total_price')
        namespace['total_price'] = resource.format_price(total)
        return namespace



class Order_View(CompositeView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')

    subviews = [Order_Top(),
                Order_ViewProducts(),
                Order_ViewPayments(admin_view=False)]



class Order_Manage(CompositeForm):
    """Display order main information with state and products
       and below a list of payments and bills.
    """
    access = 'is_admin'
    title = MSG(u'Manage order')

    subviews = [Order_AdminTop(),
                Order_ViewProducts(),
                Order_ViewPayments(admin_view=True),
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


class OrderState_Template(CMSTemplate):

    template = '/ui/shop/orders/order_state.xml'

    title = None
    link = None
    color = None


class ExportFormats(Enumerate):

    # TODO We have to be able to export in CSV format
    options = [#{'name': 'csv', 'value': MSG(u'CSV')},
               {'name': 'pdf', 'value': MSG(u'PDF')}]


class OrderModule_ExportOrders(AutoForm):

    access = 'is_admin'
    title = MSG(u'Export Orders')

    schema = {'format': ExportFormats()}
    widgets = [SelectWidget('format', title=MSG(u'Format'),
                            has_empty_option=False)]

    def action(self, resource, context, form):
        list_pdf = []
        for order in resource.get_resources():
            pdf = resource.get_resource('./%s/bill' % order.name, soft=True)
            if pdf is None:
                continue
            path = context.database.fs.get_absolute_path(pdf.handler.key)
            list_pdf.append(path)
        # Join pdf
        pdf = join_pdfs(list_pdf)
        if pdf is None:
            context.message = ERROR(u"Error: Can't merge PDF")
            return
        context.set_content_type('application/pdf')
        context.set_content_disposition('attachment; filename="Orders.pdf"')
        return pdf



class OrderModule_ViewOrders(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'Orders')

    sort_by = 'ctime'
    reverse = True
    batch_msg1 = MSG(u"There is 1 order")
    batch_msg2 = MSG(u"There are {n} orders")
    table_actions = []

    styles = ['/ui/shop/style.css']

    search_on_current_folder = False
    search_on_current_folder_recursive = True

    search_fields = ['name', 'customer_id']
    table_fields = ['checkbox', 'name', 'customer_id', 'workflow_state',
                    'total_price', 'total_paid', 'ctime', 'bill']

    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column in ('total_price', 'total_paid'):
            value = item_resource.get_property(column)
            return item_resource.format_price(value)
        elif column == 'name':
            return OrderState_Template(title=brain.name,
                link=context.get_link(item_resource), color='#BF0000')
        elif column == 'workflow_state':
            return OrderState_Template(title=item_resource.get_statename(),
                link=context.get_link(item_resource), color='#BF0000')
        elif column == 'bill':
            bill = item_resource.get_bill()
            if bill is None:
                return None
            return XMLParser("""
                    <a href="%s/;download">
                      <img src="/ui/icons/16x16/pdf.png"/>
                    </a>""" % context.get_link(bill))
        proxy = super(OrderModule_ViewOrders, self)
        return proxy.get_item_value(resource, context, item, column)


    @property
    def search_cls(self):
        from orders import Order
        return Order


    def get_items(self, resource, context, *args):
        query = PhraseQuery('is_order', True)
        return FieldsTableFeed_View.get_items(self, resource, context, query)
