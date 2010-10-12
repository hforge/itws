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
from itools.csv import Table as TableFile, Property
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import ImageSelectorWidget, SelectWidget
from ikaaro.autoform import TextWidget, MultilineWidget, PathSelectorWidget
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.menu import Target
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from itws
from base import BoxAware
from diaporama_views import DiaporamaTable_CompositeView
from diaporama_views import Diaporama_View
from itws.utils import get_path_and_view



###########################################################################
# Resources
###########################################################################
class DiaporamaImagePathDatatype(Unicode):

    @staticmethod
    def is_valid(value):
        here = get_context().resource
        try:
            ref = get_reference(str(value)) # multilingual -> unicode, multiple
            if not ref.scheme:
                resource = here.get_resource(ref.path, soft=True)
                if resource and isinstance(resource, Image):
                    return True
        except Exception, e:
            return False
        return False



class DiaporamaTableFile(TableFile):

    record_properties = {
        'title': Unicode(multiple=True),
        'description': Unicode(multiple=True),
        'img_path': DiaporamaImagePathDatatype(multiple=True, mandatory=True), # multilingual
        'img_link': String,
        'target': Target(mandatory=True, default='_top')}



class DiaporamaTable(Table):

    class_id = 'diaporama-table'
    class_handler = DiaporamaTableFile
    class_views = ['view', 'commit_log']
    view = DiaporamaTable_CompositeView()

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
        record_properties = handler.record_properties
        links = []

        get_value = handler.get_record_value
        for record in handler.get_records():
            for lang in available_languages:
                for key in ('img_path', 'img_link'):
                    path = get_value(record, key, lang)
                    if not path:
                        continue
                    ref = get_reference(str(path)) # Unicode -> str
                    if not ref.scheme:
                        path, view = get_path_and_view(ref.path)
                        links.append(str(base.resolve2(path)))

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
                    ref = get_reference(str(path)) # Unicode -> str
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

        get_context().server.change_resource(self)


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
    class_views = ['view', 'edit', 'browse_content', 'preview_content',
                   'backlinks', 'commit_log']
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
        self.make_resource(self.order_path, self.order_class)


    def get_document_types(self):
        return [Image]


    def get_title(self, language=None, fallback=True):
        title = self.get_property('title', language=language)
        if title:
            return title
        if fallback:
            # Fallback to the resource's name
            return Folder.get_title(self, language)
        return u''

    ##############
    # Views
    ##############
    view = Diaporama_View()
    edit = GoToSpecificDocument(specific_document='order-banners',
                                title=MSG(u'Edit'))




register_resource_class(Diaporama)
register_resource_class(DiaporamaTable)
