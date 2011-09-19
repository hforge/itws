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

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean, DateTime, Decimal, String, URI
from itools.datatypes import Enumerate
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.registry import resources_registry
from ikaaro.resource_ import DBResource

# Import from payments
from payment_views import Payment_Edit, Payment_End
from utils import format_price
from itws.enumerates import Users_Enumerate


class Payments_Enumerate(Enumerate):

    def get_options(cls):
        return [{'name': x.class_id, 'value': x.class_title} for x
            in resources_registry.values() if issubclass(x, Payment)]


class Payment(DBResource):

    class_id = 'payment'
    class_title = MSG(u'A payment')
    class_icon16 = 'icons/16x16/file.png'
    class_icon48 = 'icons/48x48/file.png'
    class_version = '20110725'

    payment_class = None
    payment_schema = {}

    class_schema = freeze(merge_dicts(
        DBResource.class_schema,
        payment_schema,
        name=String(stored=True, indexed=True, title=MSG(u'Reference')),
        mtime=DateTime(source='metadata', indexed=True, stored=True,
            title=MSG(u'Dernière modification')),
        amount=Decimal(source='metadata', title=MSG(u'Amount'),
            indexed=True, stored=True),
        customer_id=Users_Enumerate(source='metadata', title=MSG(u'Customer id')),
        is_paid=Boolean(source='metadata', title=MSG(u'Is paid ?'),
            indexed=True, stored=True),
        order_abspath=URI(source='metadata', title=MSG(u'Order')),
        payment_class_id=Payments_Enumerate(indexed=True, title=MSG(u'Payment')),
        is_payment=Boolean(indexed=True)))
    class_views = ['edit', 'payment_form']


    mail_subject_template = MSG(u"Payment validated")

    mail_body_template = MSG(u"Hi, your payment has been validated.\n\n"
                             u"------------------------\n"
                             u"Id payment: {name}\n"
                             u"Payment Way: {payment_way}\n"
                             u"Amount: {amount}\n"
                             u"------------------------\n"
                             u"\n\n")


    def get_catalog_values(self):
        values = super(Payment, self).get_catalog_values()
        values['is_payment'] = True
        values['customer_id'] = self.get_property('customer_id')
        values['payment_class_id'] = self.class_id
        return values


    ###################################################
    # API
    ###################################################
    def get_payment_way(self):
        root = self.get_root()
        search = root.search(format=self.payment_way_class_id)
        brain = search.get_documents()[0]
        return root.get_resource(brain.abspath, soft=True)


    def update_payment_state(self, context, paid):
        # Set payment as paid or not
        self.set_property('is_paid', paid)
        if paid:
            # Get customer email
            customer = context.root.get_user(self.get_property('customer_id'))
            customer_email = customer.get_property('email')
            # Sent an email to inform user that payment has been done
            subject = self.mail_subject_template.gettext()
            text = self.mail_body_template.gettext(
                  name=self.name,
                  payment_way=self.get_payment_way().get_title(),
                  amount=format_price(self.get_property('amount')))
            context.root.send_email(customer_email, subject, text=text)
        # Inform order that a new payment as been done
        order_abspath = self.get_property('order_abspath')
        if order_abspath:
            order = self.get_resource(order_abspath)
            order.update_payment_state(context)


    def is_payment_validated(self):
        return self.get_property('is_paid') == True


    def get_advanced_state(self):
        datatype = self.class_schema.get('advanced_state')
        if datatype:
            advanced_state = self.get_property('advanced_state')
            return datatype.get_value(advanced_state).gettext()
        return None


    def get_order(self):
        order_abspath = self.get_property('order_abspath')
        if not order_abspath:
            return None
        return self.get_resource(order_abspath)

    ###################################################
    # Views
    ###################################################
    edit = Payment_Edit()
    payment_form = GoToSpecificDocument(title=MSG(u'Pay'),
                      specific_document='.', specific_view='end')
    end = Payment_End()
