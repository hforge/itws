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

# Import from itools
from itools.csv import Property
from itools.datatypes import String, Unicode, XMLContent
from itools.xml import XMLParser
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import ImageSelectorWidget, SelectWidget
from ikaaro.autoform import TextWidget, MultilineWidget, PathSelectorWidget
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.future.order import get_resource_preview
from ikaaro.menu import Target
from ikaaro.table import OrderedTableFile, OrderedTable
from ikaaro.table_views import OrderedTable_View
from ikaaro.views import CompositeForm

# Import from itws
from base import BoxAware
from base_views import Box_View
from itws.datatypes import ImagePathDataType
from itws.utils import get_path_and_view
from menu import MenuSideBarTable_AddRecord
from itws.views import AutomaticEditView, EditOnlyLanguageMenu



###########################################################################
# Views
###########################################################################
class DiaporamaTable_View(OrderedTable_View):

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
        return OrderedTable_View.get_item_value(self, resource, context, item, column)



class DiaporamaTable_CompositeView(CompositeForm):

    access = 'is_allowed_to_edit'
    title = DiaporamaTable_View.title
    subviews = [ # diaporama folder edition view
                 MenuSideBarTable_AddRecord(title=MSG(u'Add new image')),
                 DiaporamaTable_View() ]

    def get_context_menus(self):
        return [ EditOnlyLanguageMenu(view=self) ]


    def _get_query_to_keep(self, resource, context):
        """Return a list of dict {'name': name, 'value': value}"""
        return []


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

    styles = ['/ui/common/js/slider/style.css']
    scripts = ['/ui/common/js/slider/slider.js']

    def get_namespace(self, resource, context):
        width, height = 0, 0
        namespace = {'title': resource.get_title(),
                     'first_img': {'link': None}}
        banners = []
        table = resource.get_resource(resource.order_path)
        handler = table.handler
        get_value = handler.get_record_value
        for i, record in enumerate(handler.get_records_in_order()):
            # TODO Check ACL
            banner_ns = {}
            for key in ('title', 'description', 'target',):
                banner_ns[key] = get_value(record, key)
            # img path
            img_path = get_value(record, 'img_path')
            img_path_resource = table.get_resource(str(img_path), soft=True)
            img_path = None
            if img_path_resource:
                img_path = context.get_link(img_path_resource)
                img_path = '%s/;download' % img_path
                if i == 0:
                    width, height = img_path_resource.handler.get_size()
                    namespace['first_img']['path'] = img_path
                    for key in ('title', 'description', 'target',):
                        namespace['first_img'][key] = get_value(record, key)
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
                if i == 0:
                    namespace['first_img']['link'] = img_link
            banner_ns['img_link'] = img_link
            banners.append(banner_ns)
        namespace['banners'] = banners
        namespace['width'] = width
        namespace['height'] = height
        return namespace



###########################################################################
# Resources
###########################################################################
class DiaporamaTableFile(OrderedTableFile):

    record_properties = {
        'title': Unicode(multilingual=True),
        'description': Unicode(multilingual=True),
        'img_path': ImagePathDataType(multilingual=True, mandatory=True),
        'img_link': String, # XXX
        'target': Target(mandatory=True, default='_top')}



class DiaporamaTable(OrderedTable):

    class_id = 'diaporama-table'
    class_handler = DiaporamaTableFile
    class_views = ['view', 'configure', 'commit_log']
    view = DiaporamaTable_CompositeView()
    configure = GoToSpecificDocument(specific_document='..',
            specific_view='configure', title=MSG(u'Configure'))

    form = [ImageSelectorWidget('img_path', title=MSG(u'Image path')),
            PathSelectorWidget('img_link', title=MSG(u'Image link')),
            SelectWidget('target', title=MSG(u'Target')),
            TextWidget('title', title=MSG(u'Title (Link tip)')),
            MultilineWidget('description',
                            title=MSG(u'Description (Alternative text)'))]

    def get_links(self):
        base = self.get_canonical_path()
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        handler = self.handler
        links = set()

        get_value = handler.get_record_value
        for record in handler.get_records():
            for lang in available_languages:
                for key in ('img_path', 'img_link'):
                    path = get_value(record, key, lang)
                    if not path:
                        continue
                    ref = get_reference(path)
                    if not ref.scheme:
                        path, view = get_path_and_view(ref.path)
                        links.add(str(base.resolve2(path)))

        return links


    def update_links(self, source, target):
        # Caution multilingual property
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        handler = self.handler
        record_properties = handler.record_properties

        # TODO To improve
        get_value = handler.get_record_value
        for record in handler.get_records():
            for lang in available_languages:
                for key in ('img_path', 'img_link'):
                    path = get_value(record, key, lang)
                    if not path:
                        continue
                    ref = get_reference(path)
                    if ref.scheme:
                        continue
                    path, view = get_path_and_view(ref.path)
                    path = str(old_base.resolve2(path))
                    if path == source:
                        # Hit the old name
                        # Build the new reference with the right path
                        new_ref = deepcopy(ref)
                        new_ref.path = str(new_base.get_pathto(target)) + view
                        datatype = record_properties.get(key, String)
                        new_path = Property(datatype.decode(str(new_ref)),
                                            language=lang)
                        handler.update_record(record.id, **{key: new_path})

        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        target = self.get_canonical_path()

        handler = self.handler
        record_properties = handler.record_properties
        resources_old2new = get_context().database.resources_old2new
        # TODO To improve
        get_value = handler.get_record_value
        for record in handler.get_records():
            for lang in available_languages:
                for key in ('img_path', 'img_link'):
                    path = get_value(record, key, lang)
                    if not path:
                        continue
                    ref = get_reference(str(path))
                    if ref.scheme:
                        continue
                    path, view = get_path_and_view(ref.path)
                    # Calcul the old absolute path
                    old_abs_path = source.resolve2(path)
                    # Check if the target path has not been moved
                    new_abs_path = resources_old2new.get(old_abs_path,
                                                         old_abs_path)
                    # Build the new reference with the right path
                    # Absolute path allow to call get_pathto with the target
                    new_ref = deepcopy(ref)
                    new_ref.path = str(target.get_pathto(new_abs_path)) + view
                    # Update the record
                    datatype = record_properties.get(key, String)
                    new_path = Property(datatype.decode(str(new_ref)),
                                        language=lang)
                    handler.update_record(record.id, **{key: new_path})



class Diaporama(BoxAware, Folder):

    class_id = 'diaporama'
    class_version = '20100616'
    class_title = MSG(u'Diaporama')
    class_views = ['configure', 'edit', 'browse_content']
    class_description = MSG(u'Diaporama')

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['order-banners']

    # Configuration
    use_fancybox = False
    allow_instanciation = True
    is_content = True
    is_side = False

    order_path = 'order-banners'
    order_table = DiaporamaTable

    def init_resource(self, **kw):
        Folder.init_resource(self, **kw)
        self.make_resource(self.order_path, self.order_table)


    def get_document_types(self):
        return [Image]


    ##############
    # Views
    ##############
    view = Diaporama_View()
    edit = GoToSpecificDocument(specific_document='order-banners',
                                title=MSG(u'Edit'))
    configure = AutomaticEditView(title=MSG(u'Configure'))
