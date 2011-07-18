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
from itools.core import freeze
from itools.datatypes import String, Integer, Unicode
from itools.gettext import MSG
from itools.web import STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import AutoForm, ReadOnlyWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.workflow import state_widget, get_workflow_preview

# Import from payments
from utils import format_price
from workflows import PaymentStateEnumerate


class Payment_Edit(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')
    schema = freeze({
        'id_payment': Integer,
        'payment_way': String,
        'amount': Unicode,
        'state': PaymentStateEnumerate,
        'advanced_state': Unicode})
    widgets = freeze([
        ReadOnlyWidget('id_payment', title=MSG(u"Payment ID")),
        ReadOnlyWidget('payment_way', title=MSG(u"Payment Way")),
        ReadOnlyWidget('amount', title=MSG(u"Amount")),
        state_widget,
        ReadOnlyWidget('advanced_state', title=MSG(u"Details"))])


    def get_value(self, resource, context, name, datatype):
        if name == 'payment_way':
            payment_way = resource.get_payment_way()
            payment_way_title = payment_way.get_title().encode('utf-8')
            payment_way_link = context.get_link(payment_way)
            return XMLParser('<a href="%s">%s</a>' % (payment_way_link,
                                                      payment_way_title))
        elif name == 'amount':
            return u'%s' % resource.get_property('amount')
        elif name == 'id_payment':
            return resource.name
        elif name == 'advanced_state':
            return resource.get_advanced_state()
        return resource.get_property(name)


    def action(self, resource, context, form):
        workflow_state = form['state']
        if workflow_state == 'validated':
            resource.set_payment_as_validated(resource, context)
        else:
            resource.set_workflow_state(workflow_state)
        context.message = MSG_CHANGES_SAVED



class Payment_End(STLView):

    access = 'is_authenticated'
    template = '/ui/payments/payment_end.xml'

    def get_namespace(self, resource, context):
        return {
            'payment_way': resource.get_payment_way().get_title(),
            'amount': format_price(resource.get_property('amount'), unit=u"€"),
            'state': get_workflow_preview(resource, context)}
