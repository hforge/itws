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

# Import from standard library

# Import from itools
from itools.core import merge_dicts
from itools.database import AndQuery, PhraseQuery
from itools.datatypes import Integer
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.utils import get_base_path_query

# Import from payments
from payments_views import PaymentModule_View, PaymentModule_DoPayment
from payments_views import PaymentModule_ViewPayments
from payment_way import payment_ways_registry
from utils import get_payment_way, get_shop


class PaymentModule(Folder):

    class_id = 'payments'
    class_title = MSG(u'Payment Module')
    class_views = ['view_payments', 'view', 'do_payment']

    class_schema = merge_dicts(Folder.class_schema,
        incremental_reference=Integer(source='metadata',
            title=MSG(u'Index'), default=0))

    is_content = False

    # Views
    view = PaymentModule_View()
    view_payments = PaymentModule_ViewPayments()
    do_payment = PaymentModule_DoPayment()


    def get_document_types(self):
        return payment_ways_registry.values()


    def init_resource(self, **kw):
        super(PaymentModule, self).init_resource(**kw)
        # Init payment ways
        for name, cls in payment_ways_registry.items():
            self.make_resource(name, cls)


    ######################
    # Public API
    ######################
    def make_reference(self):
        reference = self.get_property('incremental_reference') + 1
        self.set_property('incremental_reference', reference)
        return str(reference)


    def make_payment(self, resource, mode, amount, customer,
                      devise=None, order=None):
        # Auto incremental name for payments
        name = self.make_reference()
        payment_way = get_payment_way(self, mode)
        order_abspath = str(order.get_abspath()) if order else None
        # Devise
        if devise is None:
            shop = get_shop(resource)
            devise = shop.get_property('devise')
        # Payment configuration
        kw = {'amount': amount,
              'customer_id': customer.name,
              'devise': devise,
              'order_abspath': order_abspath}
        # Create order
        cls = payment_way.payment_class
        return resource.make_resource(name, cls, **kw)


    # XXX See if we can remove it
    def get_payment_ways(self, enabled=None, as_results=False):
        query = AndQuery(
            get_base_path_query(self.get_canonical_path()),
            PhraseQuery('is_payment_way', True))
        if enabled is not None:
            query.append(PhraseQuery('enabled', enabled))
        results = self.get_root().search(query)
        if as_results is True:
            return results
        return results.get_documents()
