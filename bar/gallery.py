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

    show_first_batch = False
    show_second_batch = False


    def get_query_schema(self):
        # Do not defined query
        return Box_View.get_query_schema(self)


    def get_items(self, resource, context, *args):
        items = ImagesView_View.get_items(self, resource, context, *args)

        # FIXME BoxView API
        allowed_to_edit = self.is_admin(resource, context)
        if allowed_to_edit is False and len(items) == 0:
            self.set_view_is_empty(True)

        return items


    def sort_and_batch(self, resource, context, results):
        user = context.user
        root = context.root
        conf = self._get_configuration_file(resource)

        start = 0
        sort_by = conf.get_property('view_sort_by')
        size = conf.get_property('view_batch_size')
        reverse = conf.get_property('view_reverse')

        if sort_by is None:
            get_key = None
        else:
            get_key = getattr(self, 'get_key_sorted_by_' + sort_by, None)
        if get_key:
            # Custom but slower sort algorithm
            items = results.get_documents()
            items.sort(key=get_key(), reverse=reverse)
            if size:
                items = items[start:start+size]
            elif start:
                items = items[start:]
        else:
            # Faster Xapian sort algorithm
            items = results.get_documents(sort_by=sort_by, reverse=reverse,
                                          start=start, size=size)

        # Access Control (FIXME this should be done before batch)
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        return allowed_items


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
    class_description = MSG(u'Display images or content')
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
                          title=MSG(u'Display title on section view')) ]
         + ImagesView_Configuration.edit_widgets)


    view = BoxGallery_View()
