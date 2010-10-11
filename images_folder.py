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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from itws
from itws.images_folder_views import ImagesFolder_ManageView



class ImagesFolder(Folder):

    class_id = 'images-folder'
    class_title = MSG(u'Images folder')
    class_views = ['manage_view', 'backlinks', 'commit_log']

    manage_view = ImagesFolder_ManageView()


    def get_document_types(self):
        return [ File, type(self) ]



# Register
register_resource_class(ImagesFolder)
