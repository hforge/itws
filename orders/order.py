# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2011 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2011 Nicolas Deram <nicolas@itaapy.com>
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
from datetime import datetime
from decimal import Decimal as decimal

# Import from itools
from itools.core import freeze, merge_dicts
from itools.csv import Table as BaseTable
from itools.database import AndQuery, PhraseQuery
from itools.datatypes import Boolean, DateTime, Decimal
from itools.datatypes import Integer, String, Unicode, URI
from itools.gettext import MSG
from itools.pdf import stl_pmltopdf
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import PathSelectorWidget, TextWidget
from ikaaro.file import PDF
from ikaaro.folder import Folder
from ikaaro.table import Table
from ikaaro.utils import get_base_path_query
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.enumerates import Users_Enumerate
from itws.payments import format_price

# Import from payments
from order_views import Order_Manage, Order_AddPayment, Order_AddLine
from order_views import Order_NewInstance, Order_View
from utils import get_orders
from workflows import order_workflow


####################################
# An order contain lines
####################################

class Base_Order_Lines(BaseTable):

    record_properties = {
      'abspath': URI,
      'reference': String,
      'title': Unicode,
      'quantity': Integer,
      'price': Decimal(mandatory=True),
      }


class Order_Lines(Table):
    """Table with order lines.
       An order line must define:
       - abspath (of product)
       - reference (of product)
       - title (of product)
       - quantity
       - price (by unit)
    """
    class_id = 'orders-products'
    class_title = MSG(u'Products')
    class_handler = Base_Order_Lines

    class_views = ['view']

    form = [
        PathSelectorWidget('abspath', title=MSG(u'Abspath')),
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('quantity', title=MSG(u'Quantity')),
        TextWidget('price', title=MSG(u'Price'))]


####################################
# Order
####################################

class Order(WorkflowAware, Folder):
    """ Order on which we define a workflow.
        Folder with a table with order lines.
        Basic properties:
          - total_price
          - ctime
          - customer_id
          - is_order
    """
    class_id = 'order'
    class_title = MSG(u'Order')
    class_schema = freeze(merge_dicts(
        Folder.class_schema,
        WorkflowAware.class_schema,
        total_price=Decimal(source='metadata', title=MSG(u'Total price'),
            indexed=True, stored=True, default=decimal('0')),
        total_paid=Decimal(source='metadata', title=MSG(u'Total paid'),
            default=decimal('0')),
        ctime=DateTime(source='metadata',
            title=MSG(u'Creation date'), indexed=True, stored=True),
        customer_id=Users_Enumerate(source='metadata', indexed=True,
            stored=True, title=MSG(u'Customer')),
        bill=URI(source='metadata'),
        is_paid=Boolean(source='metadata', title=MSG(u'Is paid ?'),
            indexed=True, stored=True),
        is_order=Boolean(indexed=True, stored=True)))

    class_views = ['manage', 'add_line', 'add_payment', 'view']

    workflow = order_workflow


    def init_resource(self, *args, **kw):
        Folder.init_resource(self, *args, **kw)
        self.make_resource('lines', Order_Lines)
        # XXX ctime (Should be done in ikaaro)
        self.set_property('ctime', datetime.now())


    def get_catalog_values(self):
        values = super(Order, self).get_catalog_values()
        values['is_order'] = True
        return values

    ##################################################
    # Namespace
    ##################################################
    def get_namespace(self, context):
        # Build namespace
        creation_date = self.get_property('ctime')
        namespace = {
                'reference': self.name,
                'creation_date': context.format_date(creation_date)}
        for key in ['total_price', 'total_paid']:
            namespace[key] = format_price(self.get_property(key))
        # Customer
        customer_id = self.get_property('customer_id')
        user = context.root.get_user(customer_id)
        namespace['customer'] = {'link': context.get_link(user),
                                 'title': user.get_title()}
        return namespace


    def get_products_namespace(self, context):
        l = []
        products = self.get_resource('lines')
        get_value = products.handler.get_record_value
        for record in products.handler.get_records():
            kw = {'id': record.id}
            # Get base product namespace
            kw['reference'] = get_value(record, 'reference')
            kw['title'] = get_value(record, 'title')
            kw['price'] = get_value(record, 'price')
            kw['quantity'] = get_value(record, 'quantity')
            kw['total_price'] = kw['price'] * kw['quantity']
            # Get product link (if exist)
            abspath = get_value(record, 'abspath')
            product = context.root.get_resource(abspath, soft=True)
            if product:
                kw['link'] = context.get_link(product)
            # Add product to list of products
            l.append(kw)
        return l

    ##################################################
    # API
    ##################################################

    def get_total_price(self):
        return self.get_property('total_price')


    def add_lines(self, resources):
        """Add given order lines."""
        total_price = self.get_total_price()
        handler = self.get_resource('lines').handler
        for quantity, resource in resources:
            price = resource.get_price()
            total_price += price
            handler.add_record(
              {'abspath': str(resource.get_abspath()),
               'reference': resource.get_property('reference'),
               'title': resource.get_title(),
               'quantity': quantity,
               'price': price})
        self.set_property('total_price', total_price)


    def update_payment_state(self, context):
        """Update order payment state."""
        total_paid = decimal('0')
        for brain in self.get_payments(as_results=False):
            payment = context.root.get_resource(brain.abspath)
            if payment.get_property('is_paid') is False:
                continue
            total_paid += payment.get_property('amount')
        self.set_property('total_paid', total_paid)
        if total_paid < self.get_property('total_price'):
            self.set_workflow_state('partially_paid')
            self.set_property('is_paid', False)
        elif total_paid == self.get_property('total_price'):
            self.set_workflow_state('paid')
            self.set_property('is_paid', True)
        elif total_paid > self.get_property('total_price'):
            self.set_workflow_state('to-much-paid')
        # Generate bill
        # XXX Does we have to generate bill now ?
        self.generate_bill(context)


    def is_paid(self):
        return self.get_property('is_paid')


    def get_payments(self, as_results=False):
        """Get order payments as brains."""
        query = AndQuery(
            get_base_path_query(self.get_canonical_path()),
            PhraseQuery('is_payment', True))
        results = self.get_root().search(query)
        if as_results is True:
            return results
        return results.get_documents()


    def get_customer_email(self, context):
        customer_id = self.get_property('customer_id')
        user = context.root.get_user(customer_id)
        return user.get_property('email')


    def generate_bill(self, context):
        """Creates bill as a pdf."""
        # Get template
        document = self.get_resource('/ui/orders/bill.xml')
        # Build namespace
        orders = get_orders(self)
        namespace = self.get_namespace(context)
        namespace['logo'] = orders.get_pdf_logo_key(context)
        signature = orders.get_property('signature')
        signature = signature.encode('utf-8')
        namespace['pdf_signature'] = XMLParser(signature.replace('\n', '<br/>'))
        # Products
        namespace['products'] = self.get_products_namespace(context)
        # Build pdf
        pdf = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'},
                     'filename': 'bill.pdf'}
        self.del_resource('bill.pdf', soft=True)
        context.message = MSG(u'Bill has been generated')
        return self.make_resource('bill.pdf', PDF, body=pdf, **metadata)

    ##################################################
    # Views
    ##################################################
    view = Order_View()
    manage =  Order_Manage()
    add_line = Order_AddLine()
    add_payment = Order_AddPayment()
    new_instance = Order_NewInstance()
