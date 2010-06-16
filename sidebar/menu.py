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
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import title_widget, timestamp_widget
from ikaaro.future.menu import Menu, Menu_View
from ikaaro.future.menu import MenuFolder, get_menu_namespace
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_Edit, EditLanguageMenu
from ikaaro.views import CompositeForm

# Import from itws
from itws.repository import register_box, BoxAware
from itws.repository_views import Box_View
from itws.repository_views import Box_Edit



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



class MenuSideBarTable_View(CompositeForm):

    access = 'is_allowed_to_edit'
    subviews = [ MenuProxyBox_Edit(), # menu folder edition view
                 Menu_View() ]
    context_menus = [EditLanguageMenu()]



class MenuSideBarTable(Menu):

    class_id = 'box-menu-table'
    view = MenuSideBarTable_View(title=Menu_View.title)



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
    edit = GoToSpecificDocument(specific_document='menu',
                                specific_method='edit',
                                title=MenuFolder.edit.title)


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
