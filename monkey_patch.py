# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Henry Obein <henry@itaapy.com>
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
from ikaaro.cc import SubscribeForm
from ikaaro.file import File, Image
from ikaaro.file_views import File_ExternalEdit_View
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.menu import Menu_View
from ikaaro.registry import resources_registry
from ikaaro.resource_views import DBResource_Edit
from ikaaro.revisions_views import DBResource_CommitLog, DBResource_Changes
from ikaaro.root import Root
from ikaaro.text import CSS
from ikaaro.tracker import Tracker
from ikaaro.views_new import NewInstance

# Import from itws
from feed_views import Browse_Navigator, Browse_Navigator_Rename
from itws.control_panel import CPDBResource_Backlinks, CPDBResource_CommitLog
from itws.control_panel import CPExternalEdit, CPDBResource_Links
from itws.control_panel import ITWS_ControlPanel
from popup import ITWS_DBResource_AddImage, ITWS_DBResource_AddLink
from popup import ITWS_DBResource_AddMedia
from views import Folder_NewResource
from ws_neutral import NeutralWS



# Monkey patchs
# Hide sidebar on some views
# ikaaro views
NewInstance.display_sidebar = False
Folder_NewResource.display_sidebar = False
Folder_BrowseContent.display_sidebar = False
DBResource_Edit.display_sidebar = False
File_ExternalEdit_View.display_sidebar = False
SubscribeForm.display_sidebar = False
DBResource_CommitLog.display_sidebar = False
DBResource_Changes.display_sidebar = False
Menu_View.display_sidebar = False
# itws views
NeutralWS.about.display_sidebar = False
NeutralWS.credits.display_sidebar = False
NeutralWS.license.display_sidebar = False
# Hide sidebar on some resources
Tracker.display_sidebar = False
Tracker.issue_class.display_sidebar = False

# NEW RESOURCE
# Keep Root.new_resource intact
Root.new_resource = Folder.new_resource.__class__()
Folder.new_resource = Folder_NewResource()
# NEW INSTANCE
# Note: This monkey patch does not affect Blog, Tracker, Event, File
NewInstance.goto_view = 'edit'

# Add ITWS_ControlPanel for Folder resources
Folder.class_views = ['view', 'browse_content', 'edit', 'control_panel']
Folder.control_panel = ITWS_ControlPanel()
Folder.class_control_panel = ['links', 'backlinks', 'commit_log',
                              'preview_content']
Folder.preview_content.description = MSG(u'Display images as thumbnail')
Folder.preview_content.itws_icon = 'preview-content.png'
Folder.links = CPDBResource_Links()
Folder.backlinks = CPDBResource_Backlinks()
Folder.commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')

# Add ITWS_ControlPanel for Images resources
Image.class_views = ['view', 'download', 'edit', 'externaledit',
                     'control_panel']
Image.control_panel = ITWS_ControlPanel()
Image.class_control_panel = ['externaledit', 'links',
                             'backlinks', 'commit_log']
Image.externaledit = CPExternalEdit()
Image.links = CPDBResource_Links()
Image.backlinks = CPDBResource_Backlinks()
Image.commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')

# Add ITWS_ControlPanel for File resources
File.class_views = ['view', 'edit', 'externaledit', 'control_panel']
File.control_panel = ITWS_ControlPanel()
File.class_control_panel = ['links', 'backlinks', 'commit_log']
File.links = CPDBResource_Links()
File.backlinks = CPDBResource_Backlinks()
File.commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')

# Hide in browse_content
CSS.is_content = False


# Add navigator to all resources
for cls in resources_registry.values():
    if issubclass(cls, Folder):
        cls.manage_content = Browse_Navigator()
        cls.manage_content_rename = Browse_Navigator_Rename()
    cls.add_image = ITWS_DBResource_AddImage()
    cls.add_link = ITWS_DBResource_AddLink()
    cls.add_media = ITWS_DBResource_AddMedia()

