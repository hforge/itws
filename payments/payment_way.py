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
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean, String, Integer

# Import from ikaaro
from ikaaro.autoform import XHTMLBody
from ikaaro.folder import Folder

# Import from payments
from payment import Payment
from payment_way_views import PaymentWay_Configure

# Import from itws
from itws.datatypes import ImagePathDataType


####################################
# Register payments
####################################

payment_ways_registry = {}
def register_payment_way(payment_way):
    payment_ways_registry[payment_way.class_id] = payment_way



class PaymentWay(Folder):
    class_id = 'payment_way'
    class_schema = freeze(merge_dicts(
        Folder.class_schema,
        data=XHTMLBody(source='metadata', multilingual=True,
            parameters_schema={'lang': String}),
        enabled=Boolean(source='metadata', default=True, indexed=True,
            stored=True),
        logo=ImagePathDataType(source='metadata', multilingual=True,
            parameters_schema={'lang': String}, stored=True),
        increment=Integer(source='metadata', default=0),
        is_payment_way=Boolean(indexed=True)))
    class_views = ['configure']

    logo = None
    payment_class = Payment

    # Views
    configure = PaymentWay_Configure()


    def init_resource(self, **kw):
        # Autofill resource
        kw['title'] = {'en': self.class_title.gettext()}
        kw['description'] = {'en': self.class_description.gettext()}
        super(PaymentWay, self).init_resource(**kw)


    def get_catalog_values(self):
        values = super(PaymentWay, self).get_catalog_values()
        values['logo'] = self.get_property('logo')
        values['is_payment_way'] = True
        return values


    ###################################################
    # Public API
    ###################################################

    def get_logo(self, context):
        # XXX We can set a default logo
        logo = self.get_property('logo')
        if logo is None:
            return None
        logo = self.get_resource(logo, soft=True)
        if logo is None:
            return None
        return context.get_link(logo)


    def get_payment_way_description(self, context, total_amount):
        """Overridable: for example to add available points...
        """
        return self.get_property('data')


    def is_enabled(self, context):
        """Overridable: A payment way can be disabled according to
        context."""
        return self.get_property('enabled')
