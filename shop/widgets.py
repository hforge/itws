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
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import Widget
from ikaaro.utils import make_stl_template

# Import from payments
from devises import Devises
from utils import get_payments, get_shop


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



class PaymentWays_Widget(Widget):
    title = MSG(u'Please choose a payment mode')

    template = make_stl_template("""
      <table cellpadding="5px" cellspacing="0">
        <tr stl:repeat="payment_way payment_ways">
          <td valign="top">
            <input type="radio" name="${name}"
              id="paymentway-${payment_way/name}"
              value="${payment_way/name}"/>
          </td>
          <td valign="top">
            ${payment_way/value}<br/><br/>
            <img stl:if="payment_way/logo"
              src="${payment_way/logo}/;download"/>
          </td>
          <td style="width:400px;vertical-align:top;">
            ${payment_way/description}
          </td>
        </tr>
      </table>""")


    def payment_ways(self):
        context = get_context()
        namespace = []
        payments = get_payments(context.resource)
        for brain in payments.get_payment_ways(enabled=True):
            payment_way = context.root.get_resource(brain.abspath)
            # XXX Does we have to set price in get_payment_way_description ?
            description = payment_way.get_payment_way_description(context, None)
            namespace.append({
                'name': payment_way.name,
                'value': payment_way.get_title(),
                'description': description,
                'logo':  payment_way.get_logo(context)})
        return namespace
