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
from itools.core import thingy_lazy_property
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import Widget

# Import from itws
from devises import Devises
from utils import get_shop


class PriceWidget(Widget):

    def get_template(self):
        context = get_context()
        template = '/ui/shop/price_widget.xml'
        return context.root.get_resource(template)


    @thingy_lazy_property
    def devise(self):
        here = get_context().resource
        shop = get_shop(here)
        devise = shop.get_property('devise')
        return Devises.symbols[devise]
