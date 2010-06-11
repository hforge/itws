# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.future.menu import MenuFolder, get_menu_namespace
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import register_box
from itws.repository_views import BarItem_View, BarItem_Edit
from itws.views import EasyNewInstance



class MenuSideBar_View(BarItem_View):

    template = '/ui/bar_items/menu.xml'

    def get_namespace(self, resource, context):
        depth = 1
        show_first_child = False
        flat = None
        src = '%s/menu' % resource.get_abspath()
        menu = get_menu_namespace(context, depth, show_first_child, flat=flat,
                                  src=src)
        return {'title': resource.get_title(),
                'menu': menu}



class MenuSideBar(MenuFolder):

    class_id = 'sidebar-item-menu'
    class_title = MSG(u'Side Menu')
    class_description = MSG(u'Box to create a sidebar menu')
    class_views = ['view', 'menu', 'edit']

    box_schema = {}
    box_widgets = []

    new_instance = EasyNewInstance()
    view = MenuSideBar_View()
    menu = GoToSpecificDocument(specific_document='menu',
                                title=MSG(u'Edit menu'))
    edit = BarItem_Edit()



register_resource_class(MenuSideBar)
register_box(MenuSideBar, allow_instanciation=True)
