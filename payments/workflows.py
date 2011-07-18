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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.workflow import Workflow


class PaymentStateEnumerate(Enumerate):
    options = [
        {'name': '', 'value': MSG(u"Unknow")},
        {'name': 'open', 'value': MSG(u'Waiting validation')},
        {'name': 'validated', 'value': MSG(u'Payment validated')},
        {'name': 'bank_refused', 'value': MSG(u'Payment refused by the bank')},
        {'name': 'invalid_amount', 'value': MSG(u'Invalid amount')},
        {'name': 'payment_error', 'value': MSG(u'Payment error')},
        {'name': 'canceled', 'value': MSG(u'Canceled')}]


payment_workflow = Workflow()
add_state = payment_workflow.add_state
for option in PaymentStateEnumerate.options:
    add_state(option['name'], title=option['value'])
payment_workflow.set_initstate('open')
