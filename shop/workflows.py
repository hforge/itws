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


class OrderStateEnumerate(Enumerate):

    options = [
        {'name': 'open', 'value': MSG(u'Waiting payment'), 'color': '#BF0000'},
        {'name': 'partially-paid', 'value': MSG(u'Partially paid'), 'color': '#75906E'},
        {'name': 'to-much-paid', 'value': MSG(u'To much Paid'), 'color': '#75906F'},
        {'name': 'paid', 'value': MSG(u'Paid'), 'color': '#FFAB00'},
        {'name': 'canceled', 'value': MSG(u'Canceled'), 'color': '#FF1F00'},
        {'name': 'closed', 'value': MSG(u'Closed'), 'color': '#000000'}]


order_workflow = Workflow()
add_state = order_workflow.add_state
for option in OrderStateEnumerate.options:
    add_state(option['name'],  title=option['value'])
order_workflow.set_initstate('open')
