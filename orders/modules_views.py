# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Enumerate
from itools.database import PhraseQuery
from itools.gettext import MSG
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import AutoForm, SelectWidget

# Import from itws
from utils import join_pdfs
from itws.feed_views import FieldsTableFeed_View


class ExportFormats(Enumerate):

    # TODO We have to be able to export in CSV format
    options = [#{'name': 'csv', 'value': MSG(u'CSV')},
               {'name': 'pdf', 'value': MSG(u'PDF')}]


class OrderModule_ExportOrders(AutoForm):

    access = 'is_admin'
    title = MSG(u'Export Orders')

    schema = {'format': ExportFormats()}
    widgets = [SelectWidget('format', title=MSG(u'Format'),
                            has_empty_option=False)]

    def action(self, resource, context, form):
        context.set_content_type('application/pdf')
        context.set_content_disposition('attachment; filename="Orders.pdf"')
        list_pdf = []
        for order in resource.get_resources():
            pdf = resource.get_resource('./%s/bill.pdf' % order.name, soft=True)
            if pdf is None:
                continue
            path = context.database.fs.get_absolute_path(pdf.handler.key)
            list_pdf.append(path)
        # Join pdf
        pdf = join_pdfs(list_pdf)
        return pdf



class OrderModule_ViewOrders(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'Orders')

    batch_msg1 = MSG(u"There is 1 order")
    batch_msg2 = MSG(u"There are {n} orders")
    table_actions = []

    search_fields = ['name', 'customer_id']
    table_fields = ['checkbox', 'name', 'customer_id', 'workflow_state',
                    'total_price', 'ctime', 'pdf']

    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'total_price':
            # TODO store in catalog
            order_price = item_resource.get_property('total_price')
            from decimal import Decimal as decimal
            order_price = decimal('20')
            return order_price
        elif column == 'pdf':
            return XMLParser("""
                    <a href="./%s/bill.pdf/;download">
                      <img src="/ui/icons/16x16/pdf.png"/>
                    </a>""" % brain.name)
        proxy = super(OrderModule_ViewOrders, self)
        return proxy.get_item_value(resource, context, item, column)


    @property
    def search_cls(self):
        from order import Order
        return Order


    def get_items(self, resource, context, *args):
        query = PhraseQuery('is_order', True)
        return FieldsTableFeed_View.get_items(self, resource, context, query)



class OrderModule_ViewProducts(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'List buyable products')

    search_fields = []
    table_actions = []
    table_fields = ['reference', 'title']

    @property
    def search_cls(self):
        from product import Product
        return Product


    def get_items(self, resource, context, *args):
        return context.root.search(is_buyable=True)
