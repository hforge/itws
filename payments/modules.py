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
from itools.database import AndQuery, PhraseQuery
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.utils import get_base_path_query

# Import from payments
from modules_views import PaymentModule_View, PaymentModule_DoPayment
from modules_views import PaymentModule_ViewPayments
from payment_way import payment_ways_registry


class PaymentModule(Folder):
    class_id = 'payments'
    class_title = MSG(u'Payment Module')
    class_views = ['view', 'view_payments', 'do_payment']


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