# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.core import freeze, merge_dicts
from itools.datatypes import Enumerate, Integer, Unicode
from itools.gettext import MSG

# Import from ikaaro

# Import from payments
from payment import Payment
from payment_way import PaymentWay, register_payment_way


class CheckStatus(Enumerate):

    default = 'waiting'

    options = [
      {'name': 'waiting', 'value': MSG(u'Waiting for payment')},
      {'name': 'refused', 'value': MSG(u'Check refused by the bank')},
      {'name': 'invalid', 'value': MSG(u'Invalid amount')},
      {'name': 'success', 'value': MSG(u'Payment successful')},
      ]


class CheckPayment(Payment):

    class_id = 'check-payment'
    class_title = MSG(u'Check Payment')

    payment_way_class_id = 'check'

    payment_schema = freeze(merge_dicts(
        Payment.payment_schema,
        check_number=Integer(source='metadata', title=MSG(u'Check number')),
        bank=Unicode(source='metadata', title=MSG(u'Bank')),
        account_holder=Unicode(source='metadata', title=MSG(u'Account holder')),
        advanced_state=CheckStatus(source='metadata',
            title=MSG(u'Advanced State'))))

    class_schema = freeze(merge_dicts(
        Payment.class_schema,
        payment_schema))



class Check(PaymentWay):

    class_id = 'check'
    class_title = MSG(u'Check')
    class_description = MSG(u'Payment by check')

    # Views
    class_views = ['configure']

    logo = '/ui/payments/paybox/images/logo.png'
    payment_class = CheckPayment



register_payment_way(Check)
