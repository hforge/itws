# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 Romain Gauthier <romain@itaapy.com>
# Copyright (C) 2009-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Nicolas Deram <nicolas@itaapy.com>
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

# Import from standard library
from random import choice

# Import from itools
from itools.core import freeze, merge_dicts
from itools.csv import Property
from itools.datatypes import Boolean, String
from itools.gettext import MSG
from itools.stl import rewrite_uris, set_prefix
from itools.uri import get_reference, Path, Reference
from itools.web import get_context, STLView

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.autoform import CheckboxWidget, XHTMLBody, RTEWidget
from ikaaro.table import OrderedTableFile, OrderedTable
from ikaaro.webpage import _get_links, _change_link

# Import from itws
from utils import get_admin_bar, get_path_and_view
from views import AutomaticEditView



class TurningFooterFolder_View(STLView):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    template = '/ui/common/TurningFooterFolder_view.xml'


    def get_namespace(self, resource, context):
        # title
        title = resource.get_title(fallback=False)
        menu = resource.get_resource(resource.order_path)
        handler = menu.handler

        is_active = resource.get_property('active')
        ids = list(handler.get_record_ids_in_order())
        if not ids or not is_active:
            return {'content': None,
                    'title': title,
                    'display': False,
                    'admin_bar': None}

        if resource.get_property('random'):
            id = choice(ids)
        else:
            id = ids[0]

        record = handler.get_record(id)
        data = handler.get_record_value(record, 'data')
        here = context.resource
        content = set_prefix(data, prefix='%s/' % here.get_pathto(menu))
        # admin bar
        admin_bar = get_admin_bar(resource)

        return {'content': content,
                'title': title,
                'display': True,
                'admin_bar': admin_bar}



class TurningFooterFile(OrderedTableFile):

    record_properties = {'data': XHTMLBody(mandatory=True,
                                           multilingual=True,
                                           parameters_schema={'lang': String})}



class TurningFooterTable(OrderedTable):

    class_id = 'turning-footer-table'
    class_title = MSG(u'Turning footer')
    class_handler = TurningFooterFile
    class_views = ['view', 'add_record', 'configure']

    form = [RTEWidget('data', title=MSG(u"Body"))]

    # Views
    configure = GoToSpecificDocument(specific_document='..',
            specific_view='configure', title=MSG(u'Configure'))

    # Hide sidebar
    display_sidebar = False

    ##########################
    # Links API
    ##########################
    def get_links(self):
        links = super(TurningFooterTable, self).get_links()
        base = self.get_canonical_path()
        # languages
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        # Append links contained in data
        handler = self.handler
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            for language in available_languages:
                data = get_value(record, 'data', language=language)
                if data is None:
                    continue
                links.update(_get_links(base, data))

        return links


    def update_links(self, source, target):
        super(TurningFooterTable, self).update_links(source, target)

        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        # languages
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        # Append links contained in data
        handler = self.handler
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            for language in available_languages:
                data = get_value(record, 'data', language=language)
                if data is None:
                    continue
                events = _change_link(source, target, old_base, new_base,
                                      data)
                events = list(events)
                p_events = Property(events, language=language)
                # TODO Update all language in one time
                self.update_record(record.id, **{'data': p_events})
        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        super(TurningFooterTable, self).update_relative_links(source)

        target = self.get_canonical_path()
        # languages
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
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
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            for language in available_languages:
                data = get_value(record, 'data', language=language)
                if data is None:
                    continue
                events = rewrite_uris(data, my_func)
                events = list(events)
                p_events = Property(events, language=language)
                # TODO Update all language in one time
                self.update_record(record.id, **{'data': p_events})



class TurningFooterFolder(Folder):

    class_id = 'turning-footer-folder'
    class_version = '20100616'
    class_title = MSG(u'Turning footer folder')
    class_views = ['configure', 'edit', 'browse_content',
                   'backlinks', 'commit_log']


    class_schema = merge_dicts(Folder.class_schema,
                           random=Boolean(source='metadata', default=True),
                           active=Boolean(source='metadata', default=True))

    order_class = TurningFooterTable
    order_path = 'menu'
    use_fancybox = False

    # Hide in browse_content
    is_content = False


    __fixed_handlers__ = Folder.__fixed_handlers__ + [order_path]

    # AutomaticEditView configuration
    edit_schema = freeze({'random': Boolean, 'active': Boolean})

    edit_widgets = freeze([
               CheckboxWidget('random', title=MSG(u'Random selection')),
               CheckboxWidget('active', title=MSG(u'Is active'))])


    def init_resource(self, **kw):
        Folder.init_resource(self, **kw)
        self.make_resource(self.order_path, self.order_class)


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


    #############################
    # Views
    #############################
    view = TurningFooterFolder_View()
    edit = GoToSpecificDocument(specific_document='menu',
                                title=MSG(u'Edit'))
    configure = AutomaticEditView(title=MSG(u'Configure'),
                                  edit_schema=edit_schema,
                                  edit_widgets=edit_widgets)
