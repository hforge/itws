# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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
from ikaaro.file_views import File_NewInstance
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.messages import MSG_NEW_RESOURCE
from ikaaro.registry import register_resource_class
from ikaaro.views import CompositeForm


class ImagesFolder_FileNewInstance(File_NewInstance):

    def action(self, resource, context, form):
        File_NewInstance.action(self, resource, context, form)
        return context.come_back(MSG_NEW_RESOURCE)



class ImagesFolder_ManageView(CompositeForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage view')
    subviews = [ ImagesFolder_FileNewInstance(),
                 Folder_PreviewContent() ]
    context_menus = Folder_PreviewContent.context_menus
    styles = ['/ui/gallery/style.css']


    def _get_form(self, resource, context):
        for view in self.subviews:
            method = getattr(view, context.form_action, None)
            if method is not None:
                form_method = getattr(view, '_get_form')
                return form_method(resource, context)
        return None



class ImagesFolder(Folder):

    class_id = 'images-folder'
    class_title = MSG(u'Images folder')
    class_views = ['manage_view', 'backlinks', 'commit_log']

    manage_view = ImagesFolder_ManageView()


    def get_document_types(self):
        return [ File, type(self) ]



# Register
register_resource_class(ImagesFolder)
