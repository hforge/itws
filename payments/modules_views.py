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
from ikaaro.views import BrowseForm

# Import from payments
from buttons import NextButton
from enumerates import PaymentWays_Enumerate
from payment import Payment
from widgets import PaymentWays_Widget
from itws.feed_views import FieldsTableFeed_View


class PaymentModule_View(BrowseForm):
    access = 'is_admin'
    title = MSG(u'Payment modes')

    batch_msg1 = MSG(u"There is 1 payment mode.")
    batch_msg2 = MSG(u"There are {n} payments mode.")

    table_columns = freeze([
        ('logo', MSG(u'Logo')),
        ('title', MSG(u'Title')),
        ('description', MSG(u'Description')),
        ('enabled', MSG(u'Enabled ?'))])


    def get_items(self, resource, context):
        return resource.get_payment_ways(as_results=True)


    def sort_and_batch(self, resource, context, results):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return results.get_documents(start=start, size=size)


    def get_item_value(self, resource, context, brain, column):
        if column == 'logo':
            logo = '<img src="{0}"/>'.format(brain.logo)
            return (XMLParser(logo), brain.name)
        elif column == 'title':
            return (brain.title, brain.name)
        elif column == 'description':
            # TODO store in catalog
            item_resource = resource.get_resource(brain.name)
            return item_resource.get_property('description')
        elif column == 'enabled':
            return MSG(u"Yes") if brain.enabled else MSG(u"No")
        raise NotImplementedError


class PaymentModule_ViewPayments(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'Payments')

    batch_msg1 = MSG(u"There is 1 payment")
    batch_msg2 = MSG(u"There are {n} payments")
    table_actions = []
    search_template = None
    search_cls = Payment

    table_fields = ['name', 'workflow_state', 'amount']

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
