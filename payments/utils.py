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


def get_payments(resource):
    return resource.get_site_root().get_resource('payments')


def get_payment_way(resource, mode):
    payment_ways = get_payments(resource)
    return payment_ways.get_resource(mode)


def format_price(price, unit=None):
    if price is None:
        return None
    if price._isinteger():
        price = str(int(price))
    else:
        price = '%.2f' % price
        if price.endswith('.00'):
            price = price.replace('.00', '')
    if unit is not None:
        price = u"{0} {1}".format(price, unit)
    return price
