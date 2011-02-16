# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Henry Obein <henry@itaapy.com>
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
from itools.datatypes import Enumerate
from itools.gettext import MSG



class OrderBoxEnumerate(Enumerate):

    options = [{'name': 'do-not-order',
                'value': MSG(u"Do not order (won't be displayed)")},
               {'name': 'order-top', 'value': MSG(u'Order top')},
               {'name': 'order-bottom', 'value': MSG(u'Order bottom')}]



class MyAuthorized_Classid(Enumerate):

    site_root = None

    @classmethod
    def get_options(cls):
        options = []
        view = cls.view
        for cls in view.get_aware_document_types(cls.resource, cls.context):
            options.append({'name': cls.class_id,
                            'value': cls.class_title})
        return options
