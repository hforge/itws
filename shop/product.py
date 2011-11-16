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

# Import from standard library
from decimal import Decimal as decimal

# Import from itools
from itools.core import merge_dicts
from itools.database import PhraseQuery
from itools.datatypes import Boolean, Decimal, String
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.buttons import RemoveButton, RenameButton, CopyButton, PasteButton
from ikaaro.buttons import PublishButton, RetireButton
from ikaaro.folder import Folder
from ikaaro.resource_ import DBResource
from ikaaro.workflow import WorkflowAware

# Import from itws
from taxes import TaxesEnumerate
from utils import get_arrondi, format_price
from widgets import PriceWidget
from itws.enumerates import DynamicEnumerate
from itws.feed_views import FieldsTableFeed_View
from itws.views import FieldsAutomaticEditView, FieldsAdvance_NewInstance


class Product_List(DynamicEnumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        resources = [root.get_resource(brain.abspath)
                     for brain in root.search(is_buyable=True,
                      workflow_state='public').get_documents(sort_by='name')]
        return [{'name': str(res.get_abspath()),
                 'value': res.get_title()}
                   for res in resources]

    @classmethod
    def get_resource(cls, name):
        context = get_context()
        return context.site_root.get_resource(name)



class Products_View(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'List buyable products')

    search_fields = ['reference', 'title']
    table_actions = [CopyButton, PasteButton, RenameButton,
             RemoveButton, PublishButton, RetireButton]
    table_columns = [('checkbox', None),
                     ('reference', MSG(u'Reference')),
                     ('title', MSG(u'Title')),
                     ('price', MSG(u'Price (With taxes)')),
                     ('workflow_state', MSG(u'State'))]

    search_on_current_folder = False
    search_on_current_folder_recursive = True

    def get_table_columns(self, resource, context):
        return self.table_columns


    @property
    def search_cls(self):
        from product import Product
        return Product


    def get_items(self, resource, context, *args):
        args = list(args)
        args.append(PhraseQuery('is_buyable', True))
        proxy = super(Products_View, self)
        return proxy.get_items(resource, context, *args)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'reference':
            return item_resource.get_property('reference')
        elif column == 'title':
            return item_resource.get_title(), context.get_link(item_resource)
        elif column == 'price':
            return item_resource.get_price_with_tax(with_devise=True)
        proxy = super(Products_View, self)
        return proxy.get_item_value(resource, context, item, column)



class Product(Folder, WorkflowAware):

    class_id = 'product'
    class_schema = merge_dicts(Folder.class_schema,
        WorkflowAware.class_schema,
        reference=String(source='metadata', indexed=True, stored=True,
            title=MSG(u'Reference')),
        tax=TaxesEnumerate(source='metadata', title=MSG(u'Tax'),
            has_empty_option=False, css='tax-widget'),
        pre_tax_price=Decimal(source='metadata', title=MSG(u'Price'),
            widget=PriceWidget),
        is_buyable=Boolean(source='metadata', title=MSG(u'Buyable?'),
            indexed=True, stored=True))

    def get_catalog_values(self):
        values = super(Product, self).get_catalog_values()
        values['reference'] = self.get_property('reference')
        values['is_buyable'] = True
        return values

    #########################
    # API
    #########################

    def get_price_without_tax(self, with_devise=False):
        price = get_arrondi(self.get_property('pre_tax_price'))
        if with_devise is False:
            return price
        return format_price(price)


    def get_price_with_tax(self, with_devise=False):
        price = self.get_property('pre_tax_price')
        tax = self.get_tax_value() / decimal(100) + 1
        price = get_arrondi(price * tax)
        if with_devise is False:
            return price
        return format_price(price)


    def get_tax_value(self):
        tax = self.get_property('tax')
        if tax is None:
            return decimal(1)
        tax = self.get_resource(tax)
        return tax.get_property('tax_value')


    # Views
    _fields = ['title', 'reference', 'description', 'tax', 'pre_tax_price']
    edit = FieldsAutomaticEditView(edit_fields=_fields)
    new_instance = FieldsAdvance_NewInstance(fields=_fields, access='is_admin')



class Products(DBResource):

    class_id = 'products'
    class_title = MSG(u'Your shop products')
    class_description = MSG(u'Buyable products on shop')
    class_version = '20110916'
    class_icon16 = 'icons/16x16/text.png'
    class_views = ['view']


    def get_document_types(self):
        return []


    # Views
    view = Products_View()
