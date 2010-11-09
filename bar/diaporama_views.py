# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2010 Henry Obein <henry@itaapy.com>
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

# Import from the Standard Library
from copy import deepcopy
from random import choice

# Import from itools
from itools.datatypes import XMLContent
from itools.gettext import MSG
from itools.uri import get_reference
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.future.order import get_resource_preview
from ikaaro.table_views import Table_View
from ikaaro.views import CompositeForm

# Import from itws
from base_views import Box_View
from menu import MenuSideBarTable_AddRecord



###########################################################################
# Views
###########################################################################
class DiaporamaTable_View(Table_View):

    def get_item_value(self, resource, context, item, column):
        if column == 'img_path':
            img_path = resource.handler.get_record_value(item, column)
            # NOTE img_path is unicode multiple -> multilingual
            image = resource.get_resource(str(img_path), soft=True)
            if not image:
                return None
            return get_resource_preview(image, 128, 64, 0, context)
        elif column == 'img_link':
            img_link = resource.handler.get_record_value(item, column)
            reference = get_reference(img_link)
            if reference.scheme:
                # Encode the reference '&' to avoid XMLError
                reference = XMLContent.encode(str(reference))
                return XMLParser('<a href="%s">%s</a>' % (reference, reference))
            # Split path/view
            reference_path = str(reference.path)
            view = None
            if reference_path.count(';'):
                reference_path, view = reference_path.split('/;' ,1)
            item_resource = resource.get_resource(reference_path, soft=True)
            if not item_resource:
                # Not found, just return the reference
                # Encode the reference '&' to avoid XMLError
                return XMLContent.encode(str(reference))
            # Build the new reference with the right path
            reference2 = deepcopy(reference)
            reference2.path = context.get_link(item_resource)
            if view:
                # Append the view
                reference2.path = '%s/;%s' % (reference2.path, view)
            # Encode the reference '&' to avoid XMLError
            # Reference : the reference used for the a content
            reference = XMLContent.encode(str(reference))
            # Reference2 : the reference used for href attribute
            reference2 = XMLContent.encode(str(reference2))
            return XMLParser('<a href="%s">%s</a>' % (reference2, reference))
        return Table_View.get_item_value(self, resource, context, item, column)



class DiaporamaTable_CompositeView(CompositeForm):

    # XXX Migration
    # How to edit title of Diaporama ?

    access = 'is_allowed_to_edit'
    title = DiaporamaTable_View.title
    subviews = [ # diaporama folder edition view
                 MenuSideBarTable_AddRecord(title=MSG(u'Add new image')),
                 DiaporamaTable_View() ]

    def get_namespace(self, resource, context):
        # XXX Force GET to avoid problem in STLForm.get_namespace
        # side effect unknown
        real_method = context.method
        context.method = 'GET'
        views = [ view.GET(resource, context) for view in self.subviews ]
        context.method = real_method
        return {'views': views}



class Diaporama_View(Box_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    template = '/ui/bar_items/Diaporama_view.xml'

    def get_namespace(self, resource, context):
        namespace = {}
        table = resource.get_resource(resource.order_path)
        handler = table.handler

        # title
        title = resource.get_title(fallback=False)
        ids = list(handler.get_record_ids())
        if not ids:
            return {'banner': {},
                    'title': title}

        record = handler.get_record(choice(ids))
        get_value = handler.get_record_value

        # TODO Check ACL
        banner_ns = {}
        banner_ns['title'] = get_value(record, 'title')
        banner_ns['description'] = get_value(record, 'description')
        banner_ns['target'] = get_value(record, 'target')
        # img path
        img_path = get_value(record, 'img_path')
        img_path_resource = table.get_resource(str(img_path), soft=True)
        img_path = None
        if img_path_resource:
            img_path = context.get_link(img_path_resource)
            img_path = '%s/;download' % img_path
        banner_ns['img_path'] = img_path
        # img link
        img_link = get_value(record, 'img_link')
        if img_link:
            reference = get_reference(img_link)
            if reference.scheme:
                img_link = reference
            else:
                item_link_resource = resource.get_resource(reference.path,
                                                           soft=True)
                if not item_link_resource:
                    img_link = reference
                else:
                    img_link = context.get_link(item_link_resource)
        banner_ns['img_link'] = img_link

        return {'banner': banner_ns,
                'title': title}
