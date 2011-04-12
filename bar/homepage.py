# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
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
from itools.core import freeze
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent

# Import from itws
from bar_aware import ContentBarAware, SideBarAware
from repository import Repository



class WSDataFolder(Folder):

    class_id = 'neutral-ws-data'
    class_version = '20101012'
    class_title = MSG(u'Website data folder')
    class_views = ['browse_content', 'preview_content', 'commit_log']
    class_schema = Folder.class_schema

    # Hide in browse_content
    is_content = False

    __fixed_handlers__ = [SideBarAware.sidebar_name,
                          ContentBarAware.contentbar_name]

    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')


    def get_document_types(self):
        return [File, Folder]



class Website_BarAware(ContentBarAware, SideBarAware):
    """
    All websites that contains homePage_BarAware
    contains a folder 'ws-data' that allow to sort
    sidebar and contenbar of homepage
    """

    __fixed_handlers__ = (ContentBarAware.__fixed_handlers__ +
                          SideBarAware.__fixed_handlers__ +
                          ['ws-data', 'repository'])

    class_control_panel = []
    repository = 'ws-data'


    def init_resource(self, **kw):
        self.make_resource('ws-data', WSDataFolder)
        self.make_resource('repository', Repository)
        # Sidebar Aware
        SideBarAware.init_resource(self, **kw)
        # ContentBar Aware
        ContentBarAware.init_resource(self, **kw)


    # InternalResourcesAware, API
    def get_internal_use_resource_names(self):
        return freeze(SideBarAware.get_internal_use_resource_names(self) +
                      ContentBarAware.get_internal_use_resource_names(self) +
                      ['ws-data/', 'repository/'])
