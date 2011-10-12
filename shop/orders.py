# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.database import AndQuery, PhraseQuery
from itools.datatypes import Boolean, DateTime, Decimal
from itools.datatypes import Integer, String, Unicode, URI
from itools.gettext import MSG
from itools.pdf import stl_pmltopdf
from itools.xml import XMLParser
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import MultilineWidget
from ikaaro.folder import Folder
from ikaaro.file import PDF
from ikaaro.resource_ import DBResource
from ikaaro.utils import get_base_path_query
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.datatypes import ImagePathDataType
from itws.enumerates import Users_Enumerate
from itws.views import FieldsAutomaticEditView

# Import from orders
from devises import Devises
from order_views import Order_Manage, Order_AddPayment, Order_AddLine
from order_views import Order_NewInstance, Order_View
from order_views import OrderModule_ViewOrders, OrderModule_ExportOrders
from utils import get_orders, get_shop, get_arrondi, format_price
from workflows import order_workflow


#############################################
# Mails to inform customer
#############################################
mail_confirmation_creation_title = MSG(u'Order confirmation')

mail_confirmation_creation_body = MSG(u"""Hi,
Your order number #{order_name} has been recorded.
You can found details on our website:\n
  {order_uri}\n
""")

mail_confirmation_payment_title = MSG(u'Payment validated on your order '
                                      u'#{order_name}')
mail_confirmation_payment_body = MSG(u"""Hi,
Payment has been validated on your order #{order_name}
You can found details here:\n
  {order_uri}\n
  """)

#############################################
# Mails to inform webmaster
##############################################

mail_notification_title = MSG(u'Notification: New order #{order_name} in your '
                              u'shop')

mail_notification_body = MSG(u"""Hi,
A new order has been done in your shop.
You can found details here:\n
  {order_uri}\n
  """)

mail_notification_payment_title = MSG(u'Notification: Payment validated on '
                                      u'order #{order_name}')
mail_notification_payment_body = MSG(u"""Hi,
Payment has been validated on order #{order_name}
You can found details here:\n
  {order_uri}\n
  """)

####################################
# An order contain order products
####################################

class Order_Product(DBResource):

    class_id = 'order-product'
    class_title = MSG(u'Order product')
    class_version = '20110919'
    class_icon16 = 'icons/16x16/folder.png'
    class_icon48 = 'icons/16x16/folder.png'

    class_schema = merge_dicts(DBResource.class_schema,
          abspath=URI(source='metadata', title=MSG(u'Original product')),
          reference=String(source='metadata', title=MSG(u'Product reference')),
          title=Unicode(source='metadata', title=MSG(u'Product title')),
          quantity=Integer(source='metadata', title=MSG(u'Quantity')),
          pre_tax_price=Decimal(source='metadata',
              title=MSG(u'Pre tax Price')),
          tax=Decimal(source='metadata', title=MSG(u'Tax')))


####################################
# Order
####################################

class Order(WorkflowAware, Folder):
    """ Order on which we define a workflow.
        Order contains 1 to n Order_Product
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
        name=String(stored=True, indexed=True, title=MSG(u'Reference')),
        total_price=Decimal(source='metadata', title=MSG(u'Total price'),
            indexed=True, stored=True, default=decimal('0')),
        total_paid=Decimal(source='metadata', title=MSG(u'Total paid'),
            default=decimal('0')),
        devise=Devises(source='metadata', title=MSG(u'Currency'),
            default='978'),
        ctime=DateTime(source='metadata',
            title=MSG(u'Creation date'), indexed=True, stored=True),
        customer_id=Users_Enumerate(source='metadata', indexed=True,
            stored=True, title=MSG(u'Customer')),
        bill=URI(source='metadata', title=MSG(u'Bill')),
        is_paid=Boolean(source='metadata', title=MSG(u'Is paid ?'),
            indexed=True, stored=True),
        is_order=Boolean(indexed=True, stored=True)))

    class_views = ['manage', 'add_line', 'add_payment', 'view']

    workflow = order_workflow


    def init_resource(self, *args, **kw):
        Folder.init_resource(self, *args, **kw)
        # XXX ctime (Should be done in ikaaro)
        self.set_property('ctime', datetime.now())
        # Currency
        shop = get_shop(self)
        devise = shop.get_property('devise')
        self.set_property('devise', devise)
        # Workflow
        self.onenter_open()


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
        return {
            'reference': self.name,
            'customer': self.get_customer_namespace(context),
            'creation_date': context.format_date(creation_date),
            'total_price': self.format_price(self.get_property('total_price')),
            'total_paid': self.format_price(self.get_property('total_paid'))}


    def get_customer_namespace(self, context):
        customer_id = self.get_property('customer_id')
        user = context.root.get_user(customer_id)
        return {'name': user.name,
                'link': context.get_link(user),
                'title': user.get_title(),
                'firstname': user.get_property('firstname'),
                'lastname': user.get_property('lastname'),
                'email': user.get_property('email')}


    def get_products_namespace(self, context):
        query = AndQuery(
            get_base_path_query(self.get_canonical_path()),
            PhraseQuery('format', 'order-product'))
        l = []
        for brain in context.root.search(query).get_documents():
            resource = context.root.get_resource(brain.abspath)
            # Get base product namespace
            kw = {}
            for key in ['reference', 'title', 'tax', 'quantity']:
                kw[key] = resource.get_property(key)
            kw['pre_tax_price'] = resource.get_property('pre_tax_price')
            tax = kw['tax'] / decimal(100) + 1
            kw['price_with_tax'] = get_arrondi(kw['pre_tax_price'] * tax)
            total_price = kw['price_with_tax'] * kw['quantity']
            kw['pre_tax_price'] = self.format_price(kw['pre_tax_price'])
            kw['total_price'] = self.format_price(total_price)
            kw['price_with_tax'] = self.format_price(kw['price_with_tax'])
            # Get product link (if exist)
            abspath = resource.get_property('abspath')
            product = context.root.get_resource(abspath, soft=True)
            if product:
                # Add link only if edit allowed
                link = None
                ac = resource.get_access_control()
                if ac.is_allowed_to_edit(context.user, product):
                    link = context.get_link(product)
                kw['link'] = link
            # Add product to list of products
            l.append(kw)
        return l

    ##################################################
    # Workflow
    ##################################################
    def onenter_open(self):
        context = get_context()
        shop = get_shop(self)
        root = context.root
        site_root = context.site_root
        # Build email informations
        uri = context.uri.resolve('/%s' % site_root.get_pathto(self))
        kw = {'order_name': self.name,
              'order_uri': uri}
        # Send confirmation to customer
        customer_id = self.get_property('customer_id')
        user = root.get_user(customer_id)
        to_addr = user.get_property('email')
        subject = mail_confirmation_creation_title.gettext(**kw)
        body = mail_confirmation_creation_body.gettext(**kw)
        root.send_email(to_addr, subject, text=body)
        # Send confirmation to the shop
        subject = mail_notification_title.gettext(**kw)
        body = mail_notification_body.gettext(**kw)
        for to_addr in shop.get_notification_mails():
            root.send_email(to_addr, subject, text=body)


    def onenter_paid(self):
        context = get_context()
        root = context.root
        shop = get_shop(self)
        site_root = context.site_root
        uri = context.uri.resolve('/%s' % site_root.get_pathto(self))
        kw = {'order_name': self.name,
              'order_uri': uri}
        # Send confirmation to customer
        customer_id = self.get_property('customer_id')
        user = root.get_user(customer_id)
        to_addr = user.get_property('email')
        subject = mail_confirmation_payment_title.gettext(**kw)
        body = mail_confirmation_payment_body.gettext(**kw)
        root.send_email(to_addr, subject, text=body)
        # We send email to inform shop administrator
        subject = mail_notification_payment_title.gettext(**kw)
        text = mail_notification_payment_body.gettext(**kw)
        for to_addr in shop.get_notification_mails():
            root.send_email(to_addr, subject, text=text)


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
            self.set_workflow_state('partially-paid')
            self.set_property('is_paid', False)
        elif total_paid == self.get_property('total_price'):
            self.generate_bill(context)
            self.set_workflow_state('paid')
            self.set_property('is_paid', True)
            self.onenter_paid()
        elif total_paid > self.get_property('total_price'):
            self.set_workflow_state('to-much-paid')



    ##################################################
    # API
    ##################################################
    def format_price(self, price):
        devise = self.get_property('devise')
        symbol = Devises.symbols[devise]
        return format_price(price, symbol)


    def get_total_price(self):
        return self.get_property('total_price')


    def add_lines(self, resources):
        """Add given order lines."""
        total_price = self.get_total_price()
        for quantity, resource in resources:
            price = resource.get_price_with_tax()
            total_price += price * quantity
            reference = resource.get_property('reference')
            order_product = self.get_resource(reference, soft=True)
            if order_product is None:
                kw = {'abspath': str(resource.get_abspath()),
                      'reference': reference,
                      'title': resource.get_title(),
                      'quantity': quantity,
                      'tax': resource.get_tax_value(),
                      'pre_tax_price': resource.get_price_without_tax()}
                self.make_resource(reference, Order_Product, **kw)
            else:
                old_quantity = order_product.get_property('quantity')
                order_product.set_property('quantity', old_quantity + quantity)
        self.set_property('total_price', total_price)


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


    def generate_bill(self, context):
        """Creates bill as a pdf."""
        # Get template
        document = self.get_resource('/ui/shop/orders/bill.xml')
        # Build namespace
        orders = get_orders(self)
        namespace = self.get_namespace(context)
        namespace['logo'] = orders.get_pdf_logo_key(context)
        signature = orders.get_property('signature')
        signature = signature.encode('utf-8')
        namespace['pdf_signature'] = XMLParser(signature.replace('\n', '<br/>'))
        # Products
        namespace['products'] = self.get_products_namespace(context)
        # Customer
        namespace['customer'] = self.get_customer_namespace(context)
        # Build pdf
        try:
            pdf = stl_pmltopdf(document, namespace=namespace)
        except Exception:
            return None
        metadata =  {'title': {'en': u'Bill'},
                     'filename': 'bill.pdf'}
        self.del_resource('bill', soft=True)
        return self.make_resource('bill', PDF, body=pdf, **metadata)

    ##################################################
    # Views
    ##################################################
    view = Order_View()
    manage =  Order_Manage()
    add_line = Order_AddLine()
    add_payment = Order_AddPayment()
    new_instance = Order_NewInstance()


####################################
# Orders
####################################

class Orders(Folder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_description = MSG(u'Order module')
    class_views = ['view', 'products', 'configure', 'export']
    class_schema = merge_dicts(Folder.class_schema,
        incremental_reference=Integer(source='metadata',
            title=MSG(u'Index'), default=0),
        # Configuration
        logo=ImagePathDataType(source='metadata', title=MSG(u'PDF Logo')),
        signature=Unicode(source='metadata', title=MSG(u'PDF Signature'),
                          widget=MultilineWidget))
    is_content = False

    order_class = Order

    def get_document_types(self):
        return [self.order_class]


    def get_orders(self, as_results=False):
        query = PhraseQuery('is_order', True)
        results = self.get_root().search(query)
        if as_results is True:
            return results
        return results.get_documents()


    def get_pdf_logo_key(self, context):
        logo = self.get_property('logo')
        resource_logo = self.get_resource(logo, soft=True) if logo else None
        if resource_logo is not None:
            key = resource_logo.handler.key
            return context.database.fs.get_absolute_path(key)
        return None


    def make_reference(self):
        reference = self.get_property('incremental_reference') + 1
        self.set_property('incremental_reference', reference)
        return str(reference)

    ###################################
    # Public API
    ###################################

    def make_order(self, resource, customer, lines, cls=Order):
        # Auto incremental name for orders
        name = self.make_reference()
        # Create Order resource
        order = resource.make_resource(name, cls, customer_id=customer.name)
        # Add products to order
        order.add_lines(lines)
        return order


    ###################################
    # Views
    ###################################
    view = OrderModule_ViewOrders()
    export = OrderModule_ExportOrders()
    configure = FieldsAutomaticEditView(title=MSG(u'Configure Order module'),
                    edit_fields=['logo', 'signature'])
