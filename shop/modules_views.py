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
from itools.web import ERROR
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import AutoForm, SelectWidget
from ikaaro.utils import CMSTemplate

# Importfrom itws
from utils import join_pdfs
from itws.feed_views import FieldsTableFeed_View


class OrderState_Template(CMSTemplate):

    template = '/ui/shop/order_state.xml'

    title = None
    link = None
    color = None


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
        list_pdf = []
        for order in resource.get_resources():
            pdf = resource.get_resource('./%s/bill' % order.name, soft=True)
            if pdf is None:
                continue
            path = context.database.fs.get_absolute_path(pdf.handler.key)
            list_pdf.append(path)
        # Join pdf
        pdf = join_pdfs(list_pdf)
        if pdf is None:
            context.message = ERROR(u"Error: Can't merge PDF")
            return
        context.set_content_type('application/pdf')
        context.set_content_disposition('attachment; filename="Orders.pdf"')
        return pdf



class OrderModule_ViewOrders(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'Orders')

    sort_by = 'ctime'
    reverse = True
    batch_msg1 = MSG(u"There is 1 order")
    batch_msg2 = MSG(u"There are {n} orders")
    table_actions = []

    styles = ['/ui/shop/style.css']

    search_on_current_folder = False
    search_on_current_folder_recursive = True

    search_fields = ['name', 'customer_id']
    table_fields = ['checkbox', 'name', 'customer_id', 'workflow_state',
                    'total_price', 'total_paid', 'ctime', 'bill']

    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column in ('total_price', 'total_paid'):
            value = item_resource.get_property(column)
            return item_resource.format_price(value)
        elif column == 'name':
            return OrderState_Template(title=brain.name,
                link=context.get_link(item_resource), color='#BF0000')
        elif column == 'workflow_state':
            return OrderState_Template(title=item_resource.get_statename(),
                link=context.get_link(item_resource), color='#BF0000')
        elif column == 'bill':
            bill = item_resource.get_resource('bill', soft=True)
            if bill is None:
                return None
            return XMLParser("""
                    <a href="%s/;download">
                      <img src="/ui/icons/16x16/pdf.png"/>
                    </a>""" % context.get_link(bill))
        proxy = super(OrderModule_ViewOrders, self)
        return proxy.get_item_value(resource, context, item, column)


    @property
    def search_cls(self):
        from order import Order
        return Order


    def get_items(self, resource, context, *args):
        query = PhraseQuery('is_order', True)
        return FieldsTableFeed_View.get_items(self, resource, context, query)
