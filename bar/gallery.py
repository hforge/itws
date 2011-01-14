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

# Import from itws
from itws.section_views.images import ImagesView_Configuration, ImagesView_View
from itws.bar.base import Box
from itws.bar.base_views import Box_View



class BoxGallery_View(ImagesView_View, Box_View):

    def _get_configuration_file(self, resource):
        return resource


    def _get_container(self, resource, context):
        # The container is the parent section
        return resource.parent



class BoxGallery(ImagesView_Configuration, Box):

    class_id = 'box-gallery'
    class_title = MSG(u'Gallery')
    class_description = MSG(u'Display images or content')

    is_side = False
    is_content = True

    view = BoxGallery_View()
