# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.core import freeze
from itools.database import PhraseQuery
from itools.datatypes import Decimal
from itools.gettext import MSG
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import AutoForm, TextWidget

# Import from payments
from buttons import NextButton
from enumerates import PaymentWays_Enumerate
from payment import Payment
from payment_way import PaymentWay
from widgets import PaymentWays_Widget
from itws.feed_views import FieldsTableFeed_View


class PaymentModule_View(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'Payment modes')

    batch_msg1 = MSG(u"There is 1 payment mode.")
    batch_msg2 = MSG(u"There are {n} payments mode.")

    table_fields = ['logo', 'name', 'title', 'description', 'enabled']
    table_actions = []

    search_cls = PaymentWay


    def get_items(self, resource, context):
        return resource.get_payment_ways(as_results=True)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'logo':
            logo = item_resource.get_property('logo')
            if logo:
                logo = item_resource.get_resource(logo)
                link = context.get_link(logo)
                logo = '<img src="{0}/;download"/>'.format(link)
            else:
                logo = '-'
            return (XMLParser(logo), brain.name)
        proxy = super(PaymentModule_View, self)
        return proxy.get_item_value(resource, context, item, column)


class PaymentModule_ViewPayments(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'Payments')

    sort_by = 'mtime'
    reverse = True
    batch_msg1 = MSG(u"There is 1 payment")
    batch_msg2 = MSG(u"There are {n} payments")
    table_actions = []
    search_template = None
    search_cls = Payment

    table_fields = ['name', 'amount', 'is_paid', 'order_abspath', 'mtime']

    def get_items(self, resource, context):
        query = PhraseQuery('is_payment', True)
        return resource.get_root().search(query)



class PaymentModule_DoPayment(AutoForm):

    access = 'is_admin'
    title = MSG(u"Do a payment")
    actions = [NextButton]
    return_message = None

    schema = freeze({
        'amount': Decimal,
        'mode': PaymentWays_Enumerate(default='paybox')})

    widgets = freeze([
        TextWidget('amount', title=MSG(u"Amount")),
        PaymentWays_Widget('mode', title=MSG(u"Payment Mode"))])


    def action(self, resource, context, form):
        payment = resource.make_payment(resource, form['mode'],
            form['amount'], context.user)
        goto = '%s/;payment_form' % context.get_link(payment)
        return context.come_back(self.return_message, goto=goto)
