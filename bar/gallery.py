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
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget
from ikaaro.datatypes import Multilingual

# Import from itws
from itws.section_views.images import ImagesView_Configuration, ImagesView_View
from itws.bar.base import Box
from itws.bar.base_views import Box_View



class BoxGallery_View(ImagesView_View, Box_View):


    def _get_query_suffix(self):
        return Box_View._get_query_suffix(self)


    def _get_query_value(self, resource, context, name):
        if name in ('batch_size', 'reverse', 'sort_by'):
            conf = self._get_configuration_file(resource)
            return conf.get_property('view_%s' % name)
        return ImagesView_View._get_query_value(self, resource, context, name)


    def get_items(self, resource, context, *args):
        items = ImagesView_View.get_items(self, resource, context, *args)

        # FIXME BoxView API
        allowed_to_edit = self.is_admin(resource, context)
        if allowed_to_edit is False and len(items) == 0:
            self.set_view_is_empty(True)

        return items


    def _get_configuration_file(self, resource):
        return resource


    def _get_container(self, resource, context):
        # The container is the parent section
        return resource.parent


    def get_namespace(self, resource, context):
        namespace = ImagesView_View.get_namespace(self, resource, context)
        # Tweak some properties
        for key in ('title', 'display_thumb_title', 'display_title'):
            namespace[key] = resource.get_property(key)
        return namespace



class BoxGallery(ImagesView_Configuration, Box):

    class_id = 'box-gallery'
    class_title = MSG(u'Gallery')
    class_description = MSG(u'Display images or thumbnails as a gallery')
    class_icon16 = 'bar_items/icons/16x16/gallery.png'
    class_icon48 = 'bar_items/icons/48x48/gallery.png'

    is_side = False
    is_content = True

    class_schema = freeze(merge_dicts(
        ImagesView_Configuration.class_schema,
        display_title=Boolean(source='metadata', default=True)))

    # Configuration of automatic edit view
    display_title = True
    edit_schema = freeze(merge_dicts(
        ImagesView_Configuration.edit_schema,
        title=Multilingual,
        display_title=Boolean))
    edit_widgets  = freeze(
         [ CheckboxWidget('display_title',
                          title=MSG(u'Display title')) ]
         + ImagesView_Configuration.edit_widgets)


    view = BoxGallery_View()
