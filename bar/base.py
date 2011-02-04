# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
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
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import File

# Import from itws
from itws.views import AutomaticEditView , EasyNewInstance



class BoxAware(object):

    edit = AutomaticEditView()
    new_instance = EasyNewInstance()

    edit_schema = freeze({})
    edit_widgets = freeze([])

    is_side = True
    is_content = False
    allow_instanciation = True

    class_schema = freeze({
        'box_aware': Boolean(indexed=True)})


    def get_catalog_values(self):
        return {'box_aware': True}



class Box(BoxAware, File):

    class_version = '20100622'
    class_title = MSG(u'Box')
    class_description = MSG(u'Sidebar box')
    class_icon16 = 'bar_items/icons/16x16/box.png'
    class_icon48 = 'bar_items/icons/48x48/box.png'
    # Configuration of automatic edit view
    edit_schema = freeze({})
    class_schema = freeze(merge_dicts(
        File.class_schema, BoxAware.class_schema, edit_schema))

    download = None
    externaledit = None

    is_side = True
    is_content = False
    allow_instanciation = True


    def get_catalog_values(self):
        return merge_dicts(File.get_catalog_values(self),
                           BoxAware.get_catalog_values(self))

