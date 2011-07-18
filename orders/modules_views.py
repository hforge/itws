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
from itools.database import PhraseQuery
from itools.gettext import MSG

# Import from itws
from itws.feed_views import FieldsTableFeed_View


class OrderModule_ViewOrders(FieldsTableFeed_View):

    access = 'is_admin'
    title = MSG(u'Orders')

    batch_msg1 = MSG(u"There is 1 order")
    batch_msg2 = MSG(u"There are {n} orders")
    table_actions = []

    search_fields = ['name']
    table_fields = ['name', 'workflow_state', 'total_price']

    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'total_price':
            # TODO store in catalog
            return item_resource.get_property('total_price')
        proxy = super(OrderModule_ViewOrders, self)
        return proxy.get_item_value(resource, context, item, column)

    @property
    def search_cls(self):
        from order import Order
        return Order


    def get_items(self, resource, context, *args):
        query = PhraseQuery('is_order', True)
        return FieldsTableFeed_View.get_items(self, resource, context, query)
