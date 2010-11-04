# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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


# Import from itools
from itools.csv import Property
from itools.datatypes import String
from itools.gettext import MSG
from itools.stl import rewrite_uris
from itools.uri import get_reference, Path, Reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import SelectWidget, XHTMLBody
from ikaaro.autoform import TextWidget, PathSelectorWidget
from ikaaro.datatypes import Multilingual
from ikaaro.menu import MenuFolder, Menu, MenuFile, Target
from ikaaro.webpage import _get_links, _change_link

# Import from itws
from widgets import XMLTitleWidget
from utils import get_path_and_view


class FooterMenuFile(MenuFile):

    record_properties = {
        'title': Multilingual,
        'html_content': XHTMLBody(multilingual=True,
                            parameters_schema={'lang': String}),
        'path': String,
        'target': Target(mandatory=True, default='_top')}



class FooterMenu(Menu):

    class_id = 'footer-menu'
    class_title = MSG(u'Footer Menu')
    class_handler = FooterMenuFile

    form = [TextWidget('title', title=MSG(u'Title')),
            XMLTitleWidget('html_content', title=MSG(u'HTML Content')),
            PathSelectorWidget('path', title=MSG(u'Path')),
            SelectWidget('target', title=MSG(u'Target'))]


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
        site_root_abspath = site_root.get_abspath()
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
                links.extend(_get_links(base, html_content))

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
            for language in available_languages:
                html_content = get_value(record, 'html_content',
                                         language=language)
                if html_content is None:
                    continue
                events = _change_link(source, target, old_base, new_base,
                                      html_content)
                events = list(events)
                p_events = Property(events, language=language)
                # TODO Update all language in one time
                self.update_record(record.id, **{'html_content': p_events})
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
            for language in available_languages:
                html_content = get_value(record, 'html_content',
                                         language=language)
                if html_content is None:
                    continue
                events = rewrite_uris(html_content, my_func)
                events = list(events)
                p_events = Property(events, language=language)
                # TODO Update all language in one time
                self.update_record(record.id, **{'html_content': p_events})



class FooterFolder(MenuFolder):

    class_id = 'footer-folder'
    class_title = MSG(u'Footer Folder')
    class_menu = FooterMenu

    use_fancybox = False


    def get_admin_edit_link(self, context):
        return context.get_link(self.get_resource('menu'))
