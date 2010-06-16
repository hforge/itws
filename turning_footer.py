# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2009 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 Romain Gauthier <romain@itaapy.com>
# Copyright (C) 2009-2010 Henry Obein <henry@itaapy.com>
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
from itools.core import merge_dicts
from itools.csv import Property
from itools.datatypes import Unicode, Boolean
from itools.gettext import MSG
from itools.stl import rewrite_uris
from itools.uri import get_reference, Path, Reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.forms import XHTMLBody, RTEWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTableFile, OrderedTable
from ikaaro.webpage import _get_links, _change_link

# Import from itws
from resources import OrderTableAware
from turning_footer_views import TurningFooterFile_EditRecord
from turning_footer_views import TurningFooterFile_View
from turning_footer_views import TurningFooterFolder_Edit
from turning_footer_views import TurningFooterFolder_View
from utils import get_path_and_view



class TurningFooterFile(OrderedTableFile):

    record_properties = {'data': Unicode(mandatory=True,
                                         # Multilingual
                                         multiple=True)}



class TurningFooterTable(OrderedTable):

    class_id = 'turning-footer-table'
    class_title = MSG(u'Turning footer')
    class_handler = TurningFooterFile
    class_views = ['view', 'add_record', 'configure']

    form = [RTEWidget('data', title=MSG(u"Body"))]

    # Views
    view = TurningFooterFile_View()
    edit = TurningFooterFile_EditRecord()


    def get_links(self):
        base = self.get_canonical_path()
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        handler = self.handler

        links = []
        for record in handler.get_records():
            for language in languages:
                data = handler.get_record_value(record, 'data',
                                                language=language)
                events = XHTMLBody.decode(data.encode('utf_8'))
                links.extend(_get_links(base, events))

        return links


    def update_links(self, source, target):
        # Caution multilingual property
        site_root = self.get_site_root()
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        handler = self.handler
        available_languages = site_root.get_property('website_languages')
        for record in handler.get_records():
            for language in available_languages:
                data = handler.get_record_value(record, 'data',
                                                language=language)
                events = XHTMLBody.decode(data.encode('utf_8'))
                events = _change_link(source, target, old_base, new_base,
                                      events)
                events = XHTMLBody.encode(events)
                events = Unicode.decode(events)
                property = Property(events, language=language)
                handler.update_record(record.id, **{'data': property})

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        def my_func(value):
            # Absolute URI or path
            uri = get_reference(value)
            if uri.scheme or uri.authority or uri.path.is_absolute():
                return value
            path = uri.path
            if not path or path.is_absolute() and path[0] == 'ui':
                return value

            # Strip the view
            path, view = get_path_and_view(path)

            # Resolve Path
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Get the 'new' absolute parth
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)

            path = str(target.get_pathto(new_abs_path)) + view
            value = Reference('', '', path, uri.query.copy(), uri.fragment)
            return str(value)

        handler = self.handler
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        for record in handler.get_records():
            for language in available_languages:
                data = handler.get_record_value(record, 'data',
                                                language=language)
                events = XHTMLBody.decode(data.encode('utf_8'))
                events = rewrite_uris(events, my_func)
                events = XHTMLBody.encode(events)
                events = Unicode.decode(events)
                property = Property(events, language=language)
                handler.update_record(record.id, **{'data': property})



class TurningFooterFolder(OrderTableAware, Folder):

    class_id = 'turning-footer-folder'
    class_version = '20100616'
    class_title = MSG(u'Turning Footer Folder')
    order_class = TurningFooterTable
    order_path = 'menu'
    __fixed_handlers__ = Folder.__fixed_handlers__ + [order_path]

    edit = TurningFooterFolder_Edit()
    view = TurningFooterFolder_View()


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        Folder._make_resource(cls, folder, name, **kw)
        OrderTableAware._make_resource(cls, folder, name, **kw)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           random=Boolean(default=True),
                           active=Boolean(default=True))


    def get_title(self, language=None, fallback=True):
        title = self.get_property('title', language=language)
        if title:
            return title
        if fallback:
            # Fallback to the resource's name
            return Folder.get_title(self, language)
        return u''


    def get_document_types(self):
        """Useful to add images or other types of file"""
        return [File]



###########################################################################
# Register
###########################################################################
register_resource_class(TurningFooterTable)
register_resource_class(TurningFooterFolder)
