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
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.autoform import MultilineWidget
from ikaaro.folder import Folder

# Import from itws
from itws.views import FieldsAutomaticEditView

# Import from shop
from devises import Devises
from orders import Orders
from payments import PaymentModule
from product import Products
from taxes import Taxes


class Shop_View(STLView):

    access = 'is_admin'
    title = MSG(u'View')
    template = '/ui/shop/view.xml'


class Shop(Folder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = ['view', 'edit']
    class_schema = merge_dicts(
        Folder.class_schema,
        notification_mails=Unicode(source='metadata',
            widget=MultilineWidget, title=MSG(u'Notification mails')),
        devise=Devises(source='metadata', title=MSG(u'Shop currencies'),
                       mandatory=True, default='978'))
    __fixed_handlers__ = Folder.__fixed_handlers__ + [
        'orders', 'payments', 'products', 'taxes']

    def init_resource(self, *args, **kw):
        Folder.init_resource(self, *args, **kw)
        self.make_resource('orders', Orders,
            title={'en': u'Orders'})
        self.make_resource('payments', PaymentModule,
            title={'en': u'Payments'})
        self.make_resource('products', Products,
            title={'en': u'Products'})
        self.make_resource('taxes', Taxes,
            title={'en': u'Taxes'})

    ###############################################
    # API
    ###############################################
    def get_notification_mails(self):
        return self.get_property('notification_mails').split()

    # Views
    view = Shop_View()
    edit = FieldsAutomaticEditView(edit_fields=['devise', 'notification_mails'])
