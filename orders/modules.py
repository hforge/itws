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
from itools.database import PhraseQuery
from itools.datatypes import Integer, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import MultilineWidget
from ikaaro.folder import Folder

# Import from itws
from itws.datatypes import ImagePathDataType
from itws.views import FieldsAutomaticEditView

# Import from orders
from order import Order
from modules_views import OrderModule_ViewOrders, OrderModule_ExportOrders
from modules_views import OrderModule_ViewProducts


class OrderModule(Folder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_description = MSG(u'Order module')
    class_views = ['view', 'products', 'configure', 'export']
    class_schema = merge_dicts(Folder.class_schema,
        incremental_reference=Integer(source='metadata',
            title=MSG(u'Index'), default=0),
        # Configuration
        logo=ImagePathDataType(source='metadata', title=MSG(u'PDF Logo')),
        signature=Unicode(source='metadata', title=MSG(u'PDF Signature'),
                          widget=MultilineWidget))
    is_content = False

    order_class = Order

    def get_document_types(self):
        return [self.order_class]


    def get_orders(self, as_results=False):
        query = PhraseQuery('is_order', True)
        results = self.get_root().search(query)
        if as_results is True:
            return results
        return results.get_documents()


    def get_pdf_logo_key(self, context):
        logo = self.get_property('logo')
        resource_logo = self.get_resource(logo, soft=True) if logo else None
        if resource_logo is not None:
            key = resource_logo.handler.key
            return context.database.fs.get_absolute_path(key)
        return None


    def make_reference(self):
        reference = self.get_property('incremental_reference') + 1
        self.set_property('incremental_reference', reference)
        return str(reference)

    ###################################
    # Public API
    ###################################

    def make_order(self, resource, customer, lines, cls=Order):
        # Auto incremental name for orders
        name = self.make_reference()
        # Create Order resource
        order = resource.make_resource(name, cls, customer_id=customer.name)
        # Add products to order
        order.add_lines(lines)
        return order


    ###################################
    # Views
    ###################################
    view = OrderModule_ViewOrders()
    export = OrderModule_ExportOrders()
    products = OrderModule_ViewProducts()
    configure = FieldsAutomaticEditView(title=MSG(u'Configure Order module'),
                    edit_fields=['logo', 'signature'])
