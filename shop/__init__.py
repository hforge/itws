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

# Import from itools
from itools.core import get_abspath

# Import from ikaaro
from ikaaro.skins import register_skin

# Import from orders
from buttons import NextButton
from check import Check
from orders import Orders, Order
from order_views import Order_NewInstance
from paybox import Paybox
from payments import PaymentModule
from payments_views import PaymentWays_Enumerate
from product import Product, Product_List
from shop import Shop
from utils import get_orders, get_payments, get_payment_way
from taxes import Taxes
from widgets import PaymentWays_Widget, PriceWidget


__all__ = ['Orders']

register_skin('shop', get_abspath('ui'))

# Silent pyflakes
PriceWidget, Shop, Order, Product, Taxes, get_orders
