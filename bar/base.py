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
from itools.core import merge_dicts
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import File

# Import from itws
from base_views import Box_Preview
from itws.views import AutomaticEditView , EasyNewInstance


class BoxAware(object):

    edit = AutomaticEditView()
    new_instance = EasyNewInstance()
    preview = order_preview = Box_Preview()

    edit_schema = {}
    edit_widgets = []

    is_side = True
    is_content = False
    allow_instanciation = True



class Box(BoxAware, File):

    class_version = '20100622'
    class_title = MSG(u'Box')
    class_description = MSG(u'Sidebar box')
    edit_schema = {}
    class_schema = merge_dicts(File.class_schema,
                               edit_schema)

    download = None
    externaledit = None

    is_side = True
    is_content = False
    allow_instanciation = True
