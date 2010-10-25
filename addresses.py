# -*- coding: UTF-8 -*-
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2009-2010 Taverne Sylvain <sylvain@itaapy.com>
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
from itools.core import get_abspath, merge_dicts
from itools.datatypes import Unicode, Integer, Decimal
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.registry import register_resource_class
from ikaaro.skins import register_skin
from ikaaro.webpage import WebPage

# Import from itws
from addresses_views import AddressItem_Edit
from addresses_views import Addresses_View
from addresses_views import OpenLayerRender



class AddressItem(WebPage):

    class_id = 'address'
    class_version = '20100408'
    class_title = MSG(u'Address')
    class_description = MSG(u'Address')
    class_icon16 = 'addresses/icons/16x16/addresses.png'
    class_icon48 = 'addresses/icons/48x48/addresses.png'
    class_views = ['edit', 'back', 'edit_state']

    # Schema
    class_schema = merge_dicts(WebPage.class_schema,
          # Metadata
          address=Unicode(source='metadata'),
          latitude=Decimal(source='metadata', default=Decimal.encode('48.8566')),
          longitude=Decimal(source='metadata', default=Decimal.encode('2.3509')),
          width=Integer(source='metadata', default=400),
          height=Integer(source='metadata', default=5),
          zoom=Integer(source='metadata', default=5),
          render=OpenLayerRender(source='metadata', default='osm'))


    # Views
    edit = AddressItem_Edit()
    back = GoToSpecificDocument(specific_document='../',
                                title=MSG(u'Back to Addresses Folder'))



class AddressesFolder(Folder):

    class_id = 'addresses-folder'
    class_title = MSG(u'Addresses Folder')
    class_description = MSG(u'Create OpenStreetMap or Google Maps '
                            u'from addresses')
    class_icon16 = 'addresses/icons/16x16/addresses.png'
    class_icon48 = 'addresses/icons/48x48/addresses.png'
    class_views = ['view', 'configure']
    class_version = '20090810'

    # Views
    view = Addresses_View()

    def get_document_types(self):
        return [AddressItem]



register_resource_class(AddressItem)
register_resource_class(AddressesFolder)
# Register skin
path = get_abspath('ui/addresses')
register_skin('addresses', path)
