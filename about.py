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
from itools.core import get_abspath, merge_dicts
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.skins import register_skin, Skin
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.registry import register_resource_class



class About_View(STLView):

    access = True
    title = MSG(u'About')
    template='/ui/about/view.xml'



class About(Folder):

    class_id = 'about'
    class_title = MSG(u'About')
    class_views = ['view', 'edit', 'browse_content']

    view = About_View()
    browse_content = Folder_BrowseContent(access='is_admin')


    def _get_catalog_values(self):
        return merge_dicts(Folder._get_catalog_values(self),
                           workflow_state='public')



register_resource_class(About)
# Register skin
path = get_abspath('ui/about')
skin = Skin(path)
register_skin('about', skin)
