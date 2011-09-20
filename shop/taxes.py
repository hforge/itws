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
from itools.datatypes import Decimal, Enumerate
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.buttons import RemoveButton
from ikaaro.folder import Folder
from ikaaro.resource_ import DBResource

# Import from itws
from itws.feed_views import FieldsTableFeed_View
from itws.views import FieldsAdvance_NewInstance, FieldsAutomaticEditView


class TaxesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        resources = [root.get_resource(brain.abspath)
                      for brain in root.search(format='tax').get_documents()]
        return [{'name': str(res.get_abspath()),
                 'value': res.get_property('tax_value')} for res in resources]


class Tax(DBResource):

    class_id = 'tax'
    class_title =MSG(u'Tax')
    class_views = ['edit']
    class_version = '20110916'
    class_schema = merge_dicts(
        DBResource.class_schema,
        tax_value=Decimal(source='metadata', title=MSG(u'Tax value')))

    # Views
    _fields = ['title', 'tax_value']
    edit = FieldsAutomaticEditView(edit_fields=_fields)
    new_instance = FieldsAdvance_NewInstance(fields=_fields,
                      access='is_admin')


class Taxes_View(FieldsTableFeed_View):

    access = 'is_admin'
    search_cls = Tax
    table_fields = ['checkbox', 'title', 'tax_value']
    table_actions = [RemoveButton]


class Taxes(Folder):

    class_id = 'taxes'
    class_title = MSG(u'Shop taxes')
    class_views = ['view']


    def init_resource(self, *args, **kw):
        Folder.init_resource(self, *args, **kw)
        # Init a default tax
        kw = {'title': {'en': u'French tax'},
              'tax_value': decimal('19.6')}
        self.make_resource('default', Tax, **kw)


    def get_document_types(self):
        return [Tax]

    # Views
    view = Taxes_View()
