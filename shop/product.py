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
from itools.core import merge_dicts
from itools.database import PhraseQuery
from itools.datatypes import Boolean, String
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.buttons import RemoveButton, RenameButton, CopyButton, PasteButton
from ikaaro.buttons import PublishButton, RetireButton
from ikaaro.resource_ import DBResource
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.enumerates import DynamicEnumerate
from itws.feed_views import FieldsTableFeed_View


class Product_List(DynamicEnumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        resources = [root.get_resource(brain.abspath)
                      for brain in root.search(is_buyable=True).get_documents()]
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
            return item_resource.get_price()
        proxy = super(Products_View, self)
        return proxy.get_item_value(resource, context, item, column)



class Product(DBResource, WorkflowAware):

    class_schema = merge_dicts(DBResource.class_schema,
                    WorkflowAware.class_schema,
                    reference=String(source='metadata', indexed=True),
                    is_buyable=Boolean(source='metadata',
                                   indexed=True, stored=True))

    def get_catalog_values(self):
        values = super(Product, self).get_catalog_values()
        values['reference'] = self.get_property('reference')
        values['is_buyable'] = True
        return values


    def get_price(self):
        raise NotImplementedError



class Products(DBResource):

    class_id = 'products'
    class_title = MSG(u'Your shop products')
    class_description = MSG(u'Buyable products on shop')
    class_version = '20110916'
    class_icon16 = 'icons/16x16/text.png'
    class_views = ['view']

    view = Products_View()

    def get_document_types(self):
        return []
