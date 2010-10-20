# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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
from itools.datatypes import String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.datatypes import Multilingual
from ikaaro.autoform import SelectWidget, HTMLBody
from ikaaro.autoform import TextWidget, PathSelectorWidget
from ikaaro.menu import MenuFolder, Menu, MenuFile, Target
from ikaaro.registry import register_resource_class

# Import from itws
from widgets import XMLTitleWidget


class FooterMenuFile(MenuFile):

    record_properties = {
        'title': Multilingual,
        'html_content': HTMLBody(multilingual=True,
                            parameters_schema={'lang': String}),
        'path': String,
        'target': Target(mandatory=True, default='_top')}



class FooterMenu(Menu):

    class_id = 'footer-menu'
    class_title = MSG(u'Footer Menu')
    class_handler = FooterMenuFile

    form = [TextWidget('title', title=MSG(u'Title')),
            XMLTitleWidget('html_content', title=MSG(u'HTML Content')),
            PathSelectorWidget('path', title=MSG(u'Path')),
            SelectWidget('target', title=MSG(u'Target'))]


    def _is_allowed_to_access(self, context, uri):
        # Check if uri == '' to avoid reference with a path = '.'
        if uri == '':
            # Allow empty link for the Footer
            return True
        return Menu._is_allowed_to_access(self, context, uri)


    # XXX Migration
    # Why does there's no get_links / update_links mechanism
    # fo html_content ?



class FooterFolder(MenuFolder):

    class_id = 'footer-folder'
    class_title = MSG(u'Footer Folder')
    class_menu = FooterMenu

    use_fancybox = False


    def get_admin_edit_link(self, context):
        return context.get_link(self.get_resource('menu'))




register_resource_class(FooterFolder)
register_resource_class(FooterMenu)
