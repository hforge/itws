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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder

# Import from itws
from bar_aware import ContentBarAware, SideBarAware
from repository import Repository



class WSDataFolder(Folder):

    class_id = 'neutral-ws-data'
    class_version = '20101012'
    class_title = MSG(u'Website data folder')
    class_views = ['commit_log']
    class_schema = Folder.class_schema


    __fixed_handlers__ = [SideBarAware.sidebar_name,
                          ContentBarAware.contentbar_name]

    def get_document_types(self):
        return [File, Folder]



class Website_BarAware(ContentBarAware, SideBarAware):
    """
    All websites that contains homePage_BarAware
    contains a folder 'ws-data' that allow to sort
    sidebar and contenbar of homepage
    """

    __fixed_handlers__ = ['ws-data', 'repository']
    class_control_panel = []
    repository = 'ws-data'


    def init_resource(self, **kw):
        self.make_resource('ws-data', WSDataFolder)
        self.make_resource('repository', Repository)
        # Sidebar Aware
        SideBarAware.init_resource(self, **kw)
        # ContentBar Aware
        ContentBarAware.init_resource(self, **kw)
