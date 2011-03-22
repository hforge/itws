# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.datatypes import Boolean, String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget, PathSelectorWidget, RadioWidget
from ikaaro.autoform import TextWidget
from ikaaro.file import File
from ikaaro.menu import Target

# Import from itws
from itws.views import AutomaticEditView , EasyNewInstance



title_link_schema = freeze({
    'title_link': String(source='metadata'),
    'title_link_target': Target(source='metadata', default='_top')})
title_link_widgets = freeze([
    PathSelectorWidget('title_link', title=MSG(u'Title link')),
    RadioWidget('title_link_target', title=MSG(u'Title link target'),
                has_empty_option=False, oneline=True)])

display_title_widget = CheckboxWidget('display_title',
        title=MSG(u'Display title'))


class BoxAware(object):

    class_schema = freeze({
        'box_aware': Boolean(indexed=True),
        'specific_css': String(source='metadata')})

    edit = AutomaticEditView()
    new_instance = EasyNewInstance()

    edit_schema = freeze({'specific_css': String(hidden_by_default=True)})
    edit_widgets = freeze([TextWidget('specific_css',
                                      title=MSG(u'Specific CSS'))])

    is_sidebox = True
    is_contentbox = False
    allow_instanciation = True
    # Hide in browse_content
    is_content = False


    def get_catalog_values(self):
        return {'box_aware': True}


    def get_specific_css(self):
        return self.get_property('specific_css')



class Box(BoxAware, File):

    class_version = '20100622'
    class_title = MSG(u'Box')
    class_description = MSG(u'Sidebar box')
    class_icon16 = 'bar_items/icons/16x16/box.png'
    class_icon48 = 'bar_items/icons/48x48/box.png'
    # Configuration of automatic edit view
    class_schema = freeze(merge_dicts(
        File.class_schema, BoxAware.class_schema))

    download = None
    externaledit = None

    is_sidebox = True
    is_contentbox = False
    allow_instanciation = True


    def get_catalog_values(self):
        return merge_dicts(File.get_catalog_values(self),
                           BoxAware.get_catalog_values(self))

