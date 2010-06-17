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
from itools.datatypes import DateTime, Unicode

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import Button
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import title_widget, timestamp_widget
from ikaaro.future.menu import Menu, Menu_View
from ikaaro.future.menu import MenuFolder, get_menu_namespace
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_Edit, EditLanguageMenu
from ikaaro.table import Table_AddRecord
from ikaaro.table_views import OrderedTable_View
from ikaaro.views import CompositeForm

# Import from itws
from itws.repository import register_box, BoxAware
from itws.repository_views import Box_View
from itws.views import AdvanceGoToSpecificDocument



class MenuSideBar_View(Box_View):

    template = '/ui/bar_items/menu.xml'

    def get_namespace(self, resource, context):
        depth = 1
        show_first_child = False
        flat = None
        src = '%s/menu' % resource.get_abspath()
        menu = get_menu_namespace(context, depth, show_first_child, flat=flat,
                                  src=src)
        if len(menu['items']) == 0:
            self.set_view_is_empty(True)
        return {'title': resource.get_title(),
                'menu': menu}



class MenuProxyBox_Edit(DBResource_Edit):

    schema = {'title': Unicode(multilingual=True),
              'timestamp': DateTime(readonly=True, ignore=True)}

    widgets = [timestamp_widget,
               title_widget]

    def get_value(self, resource, context, name, datatype):
        if name == 'title':
            language = resource.get_content_language(context)
            return resource.parent.get_property(name, language=language)
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)


    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        # Save changes
        title = form['title']
        language = resource.get_content_language(context)
        # Set title to menufolder
        resource.parent.set_property('title', title, language=language)
        # Ok
        context.message = messages.MSG_CHANGES_SAVED



class MenuSideBarTable_AddRecord(Table_AddRecord):

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

    access = 'is_allowed_to_edit'
    subviews = [ MenuProxyBox_Edit(), # menu folder edition view
                 MenuSideBarTable_AddRecord(),
                 MenuSideBarTable_View() ]
    context_menus = [EditLanguageMenu()]



class MenuSideBarTable(Menu):

    class_id = 'box-menu-table'
    view = MenuSideBarTable_CompositeView(title=Menu_View.title)



class MenuSideBar(BoxAware, MenuFolder):

    class_id = 'box-menu'
    class_version = '20100616'
    class_title = MSG(u'Side Menu')
    class_description = MSG(u'Box to create a sidebar menu (1 level only)')
    class_views = ['view', 'menu', 'edit']
    class_menu = MenuSideBarTable

    view = MenuSideBar_View()
    menu = GoToSpecificDocument(specific_document='menu',
                                title=MSG(u'Edit menu'))
    edit = AdvanceGoToSpecificDocument(
            specific_document='menu', specific_method='edit',
            title=MenuFolder.edit.title, keep_query=True)
    
    use_fancybox = False

    def update_20100616(self):
        for resource in self.search_resources(cls=Menu):
            metadata = resource.metadata
            metadata.set_changed()
            metadata.format = MenuSideBarTable.class_id
            metadata.version = MenuSideBarTable.class_version
            metadata.set_changed()



register_resource_class(MenuSideBar)
register_resource_class(MenuSideBarTable)
register_box(MenuSideBar, allow_instanciation=True)
