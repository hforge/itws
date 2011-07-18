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
from itools.datatypes import Boolean, String
from itools.web import get_context

# Import from ikaaro
from ikaaro.resource_ import DBResource

# Import from itws
from itws.enumerates import DynamicEnumerate


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




class Product(DBResource):

    class_schema = merge_dicts(DBResource.class_schema,
                    reference=String(source='metadata'),
                    is_buyable=Boolean(source='metadata',
                                   indexed=True, stored=True))

    def get_catalog_values(self):
        values = super(Product, self).get_catalog_values()
        values['is_buyable'] = True
        return values
