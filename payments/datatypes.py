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
from itools.datatypes import Boolean, Decimal

# Import from payments
from enumerates import Devises


class Price(Decimal):

    parameters_schema = {'with_tax': Boolean,
                         'devise': Devises,
                         'tax': Decimal}

    @classmethod
    def format(value, devise=u'€'):
        if value is None:
            return None
        if value._isinteger():
            value = str(int(value))
        else:
            price = '%.2f' % value
            if price.endswith('.00'):
                price = price.replace('.00', '')
        if devise is not None:
            price = u"{0} {1}".format(price, devise)
        return price

