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

# Register payment modules
from buttons import NextButton
from enumerates import PaymentWays_Enumerate
from modules import PaymentModule
from utils import get_payment_way, format_price, get_payments
from widgets import PaymentWays_Widget

# Register payment ways
from check import Check
from paybox import Paybox


__all__ = [
        'Check',
        'PaymentModule',
        'Paybox',
        'PaymentWays_Enumerate',
        'PaymentWays_Widget']

register_skin('payments', get_abspath('ui'))

# Silent
get_payments
