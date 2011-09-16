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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder

# Import from itws
from orders import Orders
from taxes import Taxes

class Shop(Folder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = ['browse_content']
    __fixed_handlers__ = Folder.__fixed_handlers__ + ['orders', 'taxes']

    def init_resource(self, *args, **kw):
        Folder.init_resource(self, *args, **kw)
        self.make_resource('orders', Orders)
        self.make_resource('taxes', Taxes)

    # Views
    #view = Shop_View()
