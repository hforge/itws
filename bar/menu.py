# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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
from itools.datatypes import String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import Button
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.menu import Menu, MenuFile, Menu_View
from ikaaro.menu import MenuFolder, get_menu_namespace
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import EditLanguageMenu
from ikaaro.table import Table_AddRecord
from ikaaro.table_views import OrderedTable_View
from ikaaro.views import CompositeForm

# Import from itws
from base import BoxAware
from base_views import Box_View
from itws.views import AdvanceGoToSpecificDocument



##############################################################################
# VIEWS
##############################################################################

class MenuSideBar_View(Box_View):

    template = '/ui/bar_items/menu.xml'

    def get_namespace(self, resource, context):
        depth = 1
        show_first_child = False
        flat = None
        src = '%s/menu' % resource.get_abspath()
        menu = get_menu_namespace(context, depth, show_first_child, flat=flat,
                                  src=src)
        if len(menu['items']) == 0 and not self.is_admin(resource, context):
            self.set_view_is_empty(True)
        return {'title': resource.get_title(),
                'menu': menu}



class MenuSideBarTable_AddRecord(Table_AddRecord):

    title = MSG(u'Add entry')
    template = '/ui/common/improve_auto_form.xml'
    actions = [Button(access='is_allowed_to_edit',
                      name='add_record', title=MSG(u'Add'))]

    def get_actions(self, resource, context):
        return self.actions


    def _get_action_namespace(self, resource, context):
        # (1) Actions (submit buttons)
        actions = []
        for button in self.get_actions(resource, context):
            if button.confirm:
                confirm = button.confirm.gettext().encode('utf_8')
                onclick = 'return confirm("%s");' % confirm
            else:
                onclick = None
            actions.append(
                {'value': button.name,
                 'title': button.title,
                 'class': button.css,
                 'onclick': onclick})

        return actions


    def get_namespace(self, resource, context):
        namespace = Table_AddRecord.get_namespace(self, resource, context)
        # actions namespace
        namespace['actions'] = self._get_action_namespace(resource, context)
        return namespace


    def action_add_record(self, resource, context, form):
        return Table_AddRecord.action(self, resource, context, form)


    def action_on_success(self, resource, context):
        context.message = messages.MSG_CHANGES_SAVED



class MenuSideBarTable_View(Menu_View):

    table_actions = OrderedTable_View.table_actions

    def get_table_columns(self, resource, context):
        base_columns = Menu_View.get_table_columns(self, resource, context)
        return [ column for column in base_columns if column[0] != 'child' ]



class MenuSideBarTable_CompositeView(CompositeForm):

    # XXX Migration
    # How to edit menu sidebar title ?

    access = 'is_allowed_to_edit'
    subviews = [MenuSideBarTable_AddRecord(),
                MenuSideBarTable_View() ]
    context_menus = [EditLanguageMenu()]

    def get_namespace(self, resource, context):
        # XXX Force GET to avoid problem in STLForm.get_namespace
        # side effect unknown
        real_method = context.method
        context.method = 'GET'
        views = [ view.GET(resource, context) for view in self.subviews ]
        context.method = real_method
        return {'views': views}



##############################################################################
# RESOURCES
##############################################################################

class MenuSideBarTableFile(MenuFile):

    record_properties = merge_dicts(MenuFile.record_properties,
                                    path=String(mandatory=True))



class MenuSideBarTable(Menu):

    class_id = 'box-menu-table'
    class_handler = MenuSideBarTableFile

    view = MenuSideBarTable_CompositeView(title=Menu_View.title)



class MenuSideBar(BoxAware, MenuFolder):

    class_id = 'box-menu'
    class_version = '20100616'
    class_title = MSG(u'Side Menu')
    class_description = MSG(u'Box to create a sidebar menu (1 level only)')
    class_views = ['view', 'menu', 'edit']
    class_menu = MenuSideBarTable

    # Configuration
    use_fancybox = False
    allow_instanciation = True

    # Views
    view = MenuSideBar_View()
    menu = GoToSpecificDocument(specific_document='menu',
                                title=MSG(u'Edit menu'))
    edit = AdvanceGoToSpecificDocument(
            specific_document='menu', specific_method='edit',
            title=MenuFolder.edit.title, keep_query=True)




register_resource_class(MenuSideBar)
register_resource_class(MenuSideBarTable)
