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
from itools.datatypes import Boolean, Decimal
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.resource_ import DBResource
from ikaaro.workflow import WorkflowAware, get_workflow_preview

# Import from payments
from payment_views import Payment_Edit, Payment_End
from utils import format_price
from workflows import payment_workflow

class Payment(WorkflowAware, DBResource):

    class_id = 'payment'
    class_icon16 = 'icons/16x16/file.png'
    class_icon48 = 'icons/48x48/file.png'

    payment_class = None
    payment_schema = {}

    class_schema = freeze(merge_dicts(
        DBResource.class_schema,
        WorkflowAware.class_schema,
        payment_schema,
        amount=Decimal(source='metadata', title=MSG(u'Amount'),
            indexed=True, stored=True),
        is_payment=Boolean(indexed=True)))
    class_views = ['edit', 'payment_form']

    workflow = payment_workflow

    # Views
    edit = Payment_Edit()
    payment_form = GoToSpecificDocument(title=MSG(u'Pay'),
                      specific_document='.', specific_view='end')
    end = Payment_End()


    def get_catalog_values(self):
        values = super(Payment, self).get_catalog_values()
        values['is_payment'] = True
        return values


    ##################################################
    # Namespace
    ##################################################
    def get_namespace(self, context):
        order = self.parent
        namespace = {
                'id': self.name,
                'complete_id': '%s-%s' % (order.name, self.name),
                'payment_mode': self.payment_mode} # TODO
        # Base namespace (from subclasses)
        get_property = self.get_property
        for key in self.payment_schema:
            namespace[key] = get_property(key)
        # State
        namespace['state'] = get_workflow_preview(self, context)
        # Format amount
        namespace['amount'] = format_price(namespace['amount'], unit=u"€")
        # Customer
        customer_id = order.get_property('customer_id') or '0'
        customer = context.root.get_user(customer_id)
        namespace['customer'] = {
            'id': customer_id,
            'title': customer.get_title(),
            'email': customer.get_property('email')}
        # Advanced state (from subclasses)
        namespace['advanced_state'] = None
        # Timestamp
        namespace['ts'] = context.format_datetime(get_property('mtime'))
        return namespace


    ###################################################
    # API
    ###################################################
    def get_payment_way(self):
        root = self.get_root()
        search = root.search(format=self.payment_way_class_id)
        brain = search.get_documents()[0]
        return root.get_resource(brain.abspath, soft=True)


    def is_payment_validated(self):
        return self.get_workflow_state() == 'validated'


    def get_advanced_state(self):
        datatype = self.class_schema.get('advanced_state')
        if datatype:
            advanced_state = self.get_property('advanced_state')
            return datatype.get_value(advanced_state).gettext()
        return None
