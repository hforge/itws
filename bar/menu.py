# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2011 Nicolas Deram <nicolas@itaapy.com>
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
from itools.core import freeze, is_thingy, merge_dicts
from itools.datatypes import DateTime, String, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.autoform import timestamp_widget, title_widget
from ikaaro.buttons import Button
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.menu import Menu, MenuFile, Menu_View
from ikaaro.menu import MenuFolder, get_menu_namespace
from ikaaro.resource_views import DBResource_Edit
from ikaaro.table_views import AddRecordButton, Table_AddRecord
from ikaaro.views import CompositeForm

# Import from itws
from base import BoxAware
from base_views import Box_View
from itws.views import AdvanceGoToSpecificDocument, EditOnlyLanguageMenu
from itws.views import TableViewWithoutAddRecordButton



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



class MenuProxyBox_Edit(DBResource_Edit):

    title = MSG(u'Edit box title')
    schema = freeze({'title': Unicode(multilingual=True),
                     'timestamp': DateTime(readonly=True, ignore=True)})
    actions = [Button(access=True, css='button-ok', name='menu_edit',
                      title=MSG(u'Save'))]
    # Do not implement default action (compositeform)
    action = None

    widgets = freeze([timestamp_widget, title_widget])


    def get_value(self, resource, context, name, datatype):
        if name == 'title':
            return DBResource_Edit.get_value(self, resource.parent,
                                             context, name, datatype)
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)

    def get_namespace(self, resource, context):
        proxy = super(MenuProxyBox_Edit, self)
        namespace = proxy.get_namespace(resource, context)
        # Hook action, since autoform does not set 'value' to button if there
        # is only one button
        namespace['action'] = None
        namespace['actions'] = proxy._get_action_namespace(resource, context)

        return namespace


    def action_menu_edit(self, resource, context, form):
        # FIXME copy/paste from DBResource_Edit.action
        # because def action() could not be defined here (compositeform)

        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        # Get submit field names
        schema = self._get_schema(resource, context)
        fields, to_keep = self._get_query_fields(resource, context)

        # Save changes
        for key in fields | to_keep:
            datatype = schema[key]
            if getattr(datatype, 'readonly', False):
                continue
            if self.set_value(resource, context, key, form):
                return
        # Ok
        context.message = messages.MSG_CHANGES_SAVED


    def set_value(self, resource, context, name, form):
        """Return True if an error occurs otherwise False

           If an error occurs, the context.message must be an ERROR instance.
        """
        if name == 'title':
            value = form[name]
            menu = resource.parent
            if type(value) is dict:
                for language, data in value.iteritems():
                    menu.set_property(name, data, language=language)
            else:
                menu.set_property(name, value)
            return False

        return DBResource_Edit.set_value(self, resource, context, name, form)



class MenuSideBarTable_AddRecord(Table_AddRecord):

    title = MSG(u'Add entry')
    actions = [Button(access='is_allowed_to_edit',
                      name='add_record', title=MSG(u'Add'))]


    def get_actions(self, resource, context):
        return self.actions


    def _get_action_namespace(self, resource, context):
        # (1) Actions (submit buttons)
        actions = []
        for button in self.get_actions(resource, context):
            actions.append(button(resource=resource, context=context))
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



class MenuSideBarTable_View(TableViewWithoutAddRecordButton, Menu_View):

    # Hook actions, remove add_record shortcut
    table_actions = [ action for action in Menu_View.table_actions
                      if is_thingy(action, AddRecordButton) is False ]


    def get_table_columns(self, resource, context):
        base_columns = Menu_View.get_table_columns(self, resource, context)
        return [ column for column in base_columns if column[0] != 'child' ]



class MenuSideBarTable_CompositeView(CompositeForm):

    access = 'is_allowed_to_edit'
    subviews = [MenuProxyBox_Edit(),
                MenuSideBarTable_AddRecord(),
                MenuSideBarTable_View() ]


    def get_context_menus(self):
        return [ EditOnlyLanguageMenu(view=self) ]


    def _get_edit_view(self):
        # FIXME there is two edit view in this compositeform
        return self.subviews[0]


    # EditLanguageMenu API
    def _get_query_to_keep(self, resource, context):
        return self._get_edit_view()._get_query_to_keep(resource, context)


    def _get_query_fields(self, resource, context):
        return self._get_edit_view()._get_query_fields(resource, context)


    def _get_schema(self, resource, context):
        return freeze(self._get_edit_view()._get_schema(resource, context))


    def _get_widgets(self, resource, context):
        return self._get_edit_view()._get_widgets(resource, context)



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
    class_title = MSG(u'Side menu')
    class_description = MSG(u'Box to create a menu (1 level only)')
    class_icon16 = 'bar_items/icons/16x16/menu_side_bar.png'
    class_icon48 = 'bar_items/icons/48x48/menu_side_bar.png'
    class_views = ['view', 'menu', 'edit']
    class_menu = MenuSideBarTable

    class_schema = merge_dicts(MenuFolder.class_schema,
                               BoxAware.class_schema)

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


    def get_catalog_values(self):
        return merge_dicts(MenuFolder.get_catalog_values(self),
                           BoxAware.get_catalog_values(self))
