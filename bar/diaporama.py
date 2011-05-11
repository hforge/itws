# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Armel FORTUN <armel@maar.fr>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.core import freeze, is_thingy, merge_dicts
from itools.csv import Property
from itools.datatypes import Boolean, URI, String, Unicode, XMLContent
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.uri.generic import EmptyReference
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import ImageSelectorWidget, RadioWidget
from ikaaro.autoform import TextWidget, PathSelectorWidget
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.future.order import get_resource_preview
from ikaaro.menu import Target
from ikaaro.table import OrderedTableFile, OrderedTable
from ikaaro.table_views import OrderedTable_View, AddRecordButton
from ikaaro.views import CompositeForm

# Import from itws
from base import display_title_widget, BoxAware
from base_views import Box_View
from itws.datatypes import ImagePathDataType
from itws.utils import get_path_and_view
from itws.views import AutomaticEditView, EditOnlyLanguageMenu
from itws.views import TableViewWithoutAddRecordButton
from menu import MenuSideBarTable_AddRecord



###########################################################################
# Views
###########################################################################
class DiaporamaTable_AddRecord(MenuSideBarTable_AddRecord):
    """Redirect to current view after adding new record"""

    title = MSG(u'Add new image')

    def action_on_success(self, resource, context):
        message = context.message
        if type(message) is list:
            message = message[0]
        goto = context.get_link(context.resource)
        return context.come_back(message, goto=goto)



class DiaporamaTable_View(TableViewWithoutAddRecordButton, OrderedTable_View):

    search_template = None
    # Hook actions, remove add_record shortcut
    table_actions = [ action for action in OrderedTable_View.table_actions
                      if is_thingy(action, AddRecordButton) is False ]


    def get_item_value(self, resource, context, item, column):
        if column == 'img_path':
            img_path = resource.handler.get_record_value(item, column)
            image = resource.get_resource(str(img_path), soft=True)
            if not image:
                return None
            return get_resource_preview(image, 128, 64, 0, context)
        elif column == 'img_link':
            img_link = resource.handler.get_record_value(item, column)
            reference = get_reference(img_link)
            if isinstance(reference, EmptyReference):
                return None
            if reference.scheme:
                # Encode the reference '&' to avoid XMLError
                ref = XMLContent.encode(str(reference))
                return XMLParser('<a href="{ref}">{ref}</a>'.format(ref=ref))
            # Split path/view
            reference_path, view = get_path_and_view(reference.path)
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
        return OrderedTable_View.get_item_value(self, resource, context, item,
                                                column)



class DiaporamaTable_CompositeView(CompositeForm):

    access = 'is_allowed_to_edit'
    title = DiaporamaTable_View.title
    subviews = [ # diaporama folder edition view
                 DiaporamaTable_AddRecord(),
                 DiaporamaTable_View() ]


    def get_context_menus(self):
        return [ EditOnlyLanguageMenu(view=self) ]


    def _get_edit_view(self):
        return self.subviews[0]


    # EditLanguageMenu API
    def _get_query_to_keep(self, resource, context):
        return self._get_edit_view()._get_query_to_keep(resource, context)


    def _get_query_fields(self, resource, context):
        return self._get_edit_view()._get_query_fields(resource, context)


    def _get_schema(self, resource, context):
        return freeze(self._get_edit_view()._get_schema(resource, context))


    def _get_widgets(self, resource, context):
        return self._get_edit_view()._get_widgets(resource, context)



class Diaporama_View(Box_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    template = '/ui/bar_items/Diaporama_view.xml'

    styles = ['/ui/common/js/slider/style.css']
    scripts = ['/ui/common/js/slider/slider.js']


    def get_namespace(self, resource, context):
        width, height = 0, 0
        title = resource.get_property('display_title')
        if title:
            title = resource.get_title()
        namespace = {'title': title}
        user = context.user
        banners = []
        # Use to compute first image namespace
        first_banner_resource = None
        table = resource.get_resource(resource.order_path)
        handler = table.handler
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            banner_ns = {}
            for key in ('title', 'description', 'target',):
                banner_ns[key] = get_value(record, key)
            # img path
            img_path = get_value(record, 'img_path')
            img_path_resource = table.get_resource(str(img_path), soft=True)
            if img_path_resource is None:
                # Skip broken image
                continue
            # ACL
            ac = img_path_resource.get_access_control()
            if ac.is_allowed_to_view(user, img_path_resource) is False:
                continue
            if first_banner_resource is None:
                first_banner_resource = img_path_resource
            img_path = '%s/;download' % context.get_link(img_path_resource)
            banner_ns['img_path'] = img_path
            # img link
            img_link = get_value(record, 'img_link')
            if img_link:
                reference = get_reference(img_link)
                if reference.scheme:
                    img_link = reference
                else:
                    item_link_resource = table.get_resource(reference.path,
                                                            soft=True)
                    if not item_link_resource:
                        img_link = reference
                    else:
                        img_link = context.get_link(item_link_resource)
            else:
                img_link = None
            banner_ns['img_link'] = img_link
            banners.append(banner_ns)

        # Compute first_img namespace
        first_img = {}
        if first_banner_resource:
            first_img = banners[0]
            width, height = first_banner_resource.handler.get_size()
        namespace['first_img'] = first_img
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
        'img_link': URI,
        'target': Target(mandatory=True, default='_top')}



class DiaporamaTable(OrderedTable):

    class_id = 'diaporama-table'
    class_handler = DiaporamaTableFile
    class_views = ['view', 'configure', 'commit_log']
    view = DiaporamaTable_CompositeView()
    configure = GoToSpecificDocument(specific_document='..',
            specific_view='configure', title=MSG(u'Configure'))

    # Hide in browse_content
    is_content = False

    form = [ImageSelectorWidget('img_path', title=MSG(u'Image Path')),
            PathSelectorWidget('img_link', title=MSG(u'Image Link')),
            RadioWidget('target', title=MSG(u'Link Target'),
                has_empty_option=False, oneline=True),
            TextWidget('title', title=MSG(u'Caption Title')),
            TextWidget('description', title=MSG(u'Caption Content'))]


    def get_links(self):
        base = self.get_canonical_path()
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        handler = self.handler
        links = super(DiaporamaTable, self).get_links()

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
        super(DiaporamaTable, self).update_links(source, target)

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
        super(DiaporamaTable, self).update_relative_links(source)

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
    class_title = MSG(u'Slideshow')
    class_views = ['configure', 'edit', 'browse_content']
    class_description = MSG(u'Slideshow of a set of images')
    class_icon16 = 'bar_items/icons/16x16/slideshow.png'
    class_icon48 = 'bar_items/icons/48x48/slideshow.png'

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['order-banners']

    class_schema = merge_dicts(Folder.class_schema,
                               BoxAware.class_schema,
                               display_title=Boolean(source='metadata',
                                                     default=True))

    # Configuration
    use_fancybox = False
    allow_instanciation = True
    is_contentbox = True
    is_sidebox = False

    edit_schema = freeze({'display_title': Boolean})
    edit_widgets = freeze([display_title_widget])

    order_path = 'order-banners'
    order_table = DiaporamaTable


    def init_resource(self, **kw):
        Folder.init_resource(self, **kw)
        self.make_resource(self.order_path, self.order_table)


    def get_document_types(self):
        # FIXME The side effect is that new_resource allow to add Image
        # only inside Diaporama folder without using the Diaporama view.
        return [Image]


    def get_catalog_values(self):
        return merge_dicts(Folder.get_catalog_values(self),
                           BoxAware.get_catalog_values(self))


    ##############
    # Views
    ##############
    view = Diaporama_View()
    edit = GoToSpecificDocument(specific_document='order-banners',
                                title=MSG(u'Edit'))
    configure = AutomaticEditView(title=MSG(u'Configure'))
