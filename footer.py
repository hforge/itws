# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
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

# Import from itools
from itools.core import freeze, merge_dicts
from itools.csv import Property
from itools.datatypes import Boolean, String
from itools.gettext import MSG
from itools.stl import rewrite_uris
from itools.uri import get_reference, Path, Reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import SelectWidget, XHTMLBody, RadioWidget
from ikaaro.autoform import TextWidget, PathSelectorWidget
from ikaaro.datatypes import Multilingual
from ikaaro.menu import MenuFolder, Menu, MenuFile, Target
from ikaaro.webpage import _get_links, _change_link
from ikaaro.file_views import File_Edit

# Import from itws
from widgets import XMLTitleWidget
from utils import get_path_and_view



class Footer_Edit(File_Edit):

    widgets = freeze(File_Edit.widgets
                     + [RadioWidget('sanitize', title=MSG(u'Sanitize HTML')) ])

    def _get_schema(self, resource, context):
        proxy = super(Footer_Edit, self)
        return freeze(merge_dicts(proxy._get_schema(resource, context),
                                  sanitize=Boolean))


class FooterMenuFile(MenuFile):

    record_properties = {
        'title': Multilingual,
        'html_content': XHTMLBody(multilingual=True,
                            parameters_schema={'lang': String}),
        'path': String,
        'target': Target(mandatory=True, default='_top')}



class FooterMenu(Menu):

    class_id = 'footer-menu'
    class_version = '20090123'
    class_title = MSG(u'Footer menu')
    class_handler = FooterMenuFile

    class_schema = freeze(merge_dicts(
        Menu.class_schema,
        sanitize=Boolean(source='metadata', default=True)))

    form = [TextWidget('title', title=MSG(u'Title')),
            XMLTitleWidget('html_content', title=MSG(u'HTML Content')),
            PathSelectorWidget('path', title=MSG(u'Path')),
            SelectWidget('target', title=MSG(u'Target'))]

    edit = Footer_Edit()


    def get_schema(self):
        record_properties = self.handler.record_properties
        # Hook html_content datatype
        datatype = record_properties.get('html_content', None)
        if datatype:
            sanitize = self.get_property('sanitize')
            return merge_dicts(record_properties,
                               html_content=datatype(sanitize_html=sanitize))
        return record_properties


    def _is_allowed_to_access(self, context, uri):
        # Check if uri == '' to avoid reference with a path = '.'
        if uri == '':
            # Allow empty link for the Footer
            return True
        return Menu._is_allowed_to_access(self, context, uri)


    ###########################
    ## Links API
    ###########################

    def get_links(self):
        base = self.get_canonical_path()
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        links = Menu.get_links(self)
        handler = self.handler
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            for language in available_languages:
                html_content = get_value(record, 'html_content',
                                         language=language)
                if html_content is None:
                    continue
                links.update(_get_links(base, html_content))

        return links


    def update_links(self,  source, target):
        base = self.get_canonical_path()
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)
        handler = self.handler
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            properties = []
            for language in available_languages:
                html_content = get_value(record, 'html_content',
                                         language=language)
                if html_content is None:
                    continue
                events = _change_link(source, target, old_base, new_base,
                                      html_content)
                events = list(events)
                properties.append(Property(events, language=language))
            self.update_record(record.id, **{'html_content': properties})
        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        target = self.get_canonical_path()
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
            properties = []
            for language in available_languages:
                html_content = get_value(record, 'html_content',
                                         language=language)
                if html_content is None:
                    continue
                events = rewrite_uris(html_content, my_func)
                events = list(events)
                properties.append(Property(events, language=language))
            self.update_record(record.id, **{'html_content': properties})


    def update_20090123(self):
        """html_content Unicode -> XHTMLBody"""
        from itools.core import merge_dicts
        from itools.html import HTMLParser
        from ikaaro.autoform import XHTMLBody

        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        class FakeHandler(FooterMenuFile):
            record_properties = merge_dicts(FooterMenuFile.record_properties,
                    html_content=String(multilingual=True))

        handler = self.handler
        try:
            handler.record_properties = FakeHandler.record_properties
        except IOError:
            # metadata handler exists but not the data one
            return

        old_handler = FakeHandler()
        old_handler.load_state_from_string(self.handler.to_str())
        for record_id in old_handler.get_record_ids():
            old_record = old_handler.get_record(record_id)
            old_get_value = old_handler.get_record_value
            for lang in available_languages:
                html_content = old_get_value(old_record, 'html_content', lang)
                if html_content is None:
                    continue
                # string -> events
                events = HTMLParser(html_content)
                p_value = Property(XHTMLBody.encode(events), language=lang)
                old_handler.update_record(record_id,
                                          **{'html_content': p_value})

        handler.load_state_from_string(old_handler.to_str())
        handler.set_changed()



class FooterFolder(MenuFolder):

    class_id = 'footer-folder'
    class_title = MSG(u'Footer folder')
    class_menu = FooterMenu

    use_fancybox = False


    def get_admin_edit_link(self, context):
        return context.get_link(self.get_resource('menu'))
