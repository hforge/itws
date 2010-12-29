# -*- coding: UTF-8 -*-
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
from itools.core import thingy_lazy_property
from itools.gettext import get_domain, MSG
from itools.i18n import get_language_name
from itools.uri import decode_query

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.resource_ import DBResource
from ikaaro.skins_views import LocationTemplate as BaseLocationTemplate
from ikaaro.skins_views import LanguagesTemplate as BaseLanguagesTemplate
from ikaaro.utils import CMSTemplate, reduce_string
from ikaaro.workflow import WorkflowAware

# Import form itws
from utils import is_navigation_mode


class AdminBarTemplate(CMSTemplate):

    template = '/ui/common/admin_bar.xml'

    @thingy_lazy_property
    def workflow(self):
        resource = self.context.resource
        if isinstance(resource, WorkflowAware):
            return 'wf-%s' % resource.get_property('state')
        return None


    @thingy_lazy_property
    def tabs(self):
        context = self.context
        user = context.user
        if user is None:
            return []

        # Build tabs (Same that upper class)
        # Get resource & access control
        context = self.context
        here = context.resource
        here_link = context.get_link(here)

        # Tabs
        tabs = []
        for link, view in here.get_views():
            active = False

            # From method?param1=value1&param2=value2&...
            # we separate method and arguments, then we get a dict with
            # the arguments and the subview active state
            if '?' in link:
                name, args = link.split('?')
                args = decode_query(args)
            else:
                name, args = link, {}

            # Active
            if context.view == here.get_view(name, args):
                active = True

            # Add the menu
            tabs.append({
                'name': '%s/;%s' % (here_link, link),
                'icon': getattr(view, 'adminbar_icon', None),
                'label': view.get_title(context),
                'active': active,
                'rel': getattr(view, 'adminbar_rel', None),
                'class': active and 'active' or None})
        # New resources
        if isinstance(here, Folder) is True:
            active = context.view_name == 'new_resource'
            tabs.append({'name': './;new_resource',
                          'label': MSG(u'Add content'),
                          'icon': '/ui/icons/16x16/new.png',
                          'rel': None,
                          'class': active and 'active' or None})
        return tabs


    @thingy_lazy_property
    def edition_tabs(self):
        views = []
        context = self.context
        navigation_mode = is_navigation_mode(context)
        # edit mode
        views.append({'name': '/;fo_switch_mode?mode=0',
                      'label': MSG(u'On'),
                      'class': 'active' if not navigation_mode else None})
        views.append({'name': '/;fo_switch_mode?mode=1',
                      'label': MSG(u'Off'),
                      'class': 'active' if navigation_mode else None})
        return views



    @thingy_lazy_property
    def backoffice_tabs(self):
        context = self.context
        tabs = []
        active = context.view_name == 'control_panel'
        tabs.append({'name': '/;control_panel',
                     'label': MSG(u'Control panel'),
                     'icon': '/ui/icons/16x16/external.png',
                     'class': active and 'active' or None})
        active = context.view_name == 'new_resource'
        tabs.append({'name': '/;new_resource',
                     'label': MSG(u'Create a new resource'),
                     'icon': '/ui/icons/16x16/new.png',
                     'class': active and 'active' or None})
        return tabs


class LocationTemplate(BaseLocationTemplate):

    template = '/ui/common/location.xml'

    # Configuration
    bc_prefix = None
    bc_separator = '>'
    tabs_separator = '|'
    # breadcrumbs configuration
    excluded = []
    skip_breadcrumb_in_homepage = False
    # tabs comfiguration
    tabs_hidden_roles = None
    tabs_hide_if_only_one_item = True
    display = True


    def get_breadcrumb_short_name(self, resource):
        if isinstance(resource, DBResource):
            if resource.has_property('breadcrumb_title'):
                return resource.get_property('breadcrumb_title')
            return reduce_string(resource.get_title(), 15, 30)
        return ''


    @thingy_lazy_property
    def breadcrumb(self):
        context = self.context
        here = context.resource
        site_root = context.site_root
        if self.skip_breadcrumb_in_homepage:
            if type(here) == type(site_root):
                return []

        excluded = self.excluded

        # Initialize the breadcrumb with the root resource
        path = '/'
        title = site_root.get_title()
        breadcrumb = [{
            'class': 'first',
            'url': path,
            'name': title,
            'short_name': self.get_breadcrumb_short_name(site_root),
            }]

        # Complete the breadcrumb
        resource = site_root
        for name in context.uri.path:
            path = path + ('%s/' % name)
            resource = resource.get_resource(name, soft=True)
            if path in excluded:
                continue
            if resource is None:
                break
            # FIXME Check ACL
            url = path
            title = resource.get_title()
            short_name = self.get_breadcrumb_short_name(resource)
            # Append
            breadcrumb.append({
                'class': '',
                'url': url,
                'name': title,
                'short_name': short_name,
            })

        breadcrumb[-1]['class'] += ' last'

        # Hide breadcrumb if there is only one item
        if len(breadcrumb) == 1:
            return []

        return breadcrumb


    @thingy_lazy_property
    def tabs(self):
        context = self.context
        user = context.user
        if user is None:
            return []
        excluded_roles = self.tabs_hidden_roles
        if excluded_roles:
            user_name = user.name
            site_root = context.site_root
            for role in excluded_roles:
                if site_root.has_user_role(user_name, role):
                    return []

        # Build tabs (Same that upper class)
        # Get resource & access control
        context = self.context
        here = context.resource
        here_link = context.get_link(here)

        # Tabs
        tabs = []
        for link, view in here.get_views():
            active = False
            # ACL
            if view.access != 'is_allowed_to_view':
                continue

            # From method?param1=value1&param2=value2&...
            # we separate method and arguments, then we get a dict with
            # the arguments and the subview active state
            if '?' in link:
                name, args = link.split('?')
                args = decode_query(args)
            else:
                name, args = link, {}

            # Active
            if context.view == here.get_view(name, args):
                active = True

            # Add the menu
            tabs.append({
                'name': '%s/;%s' % (here_link, link),
                'label': view.get_title(context),
                'active': active,
                'class': active and 'active' or None})
        # Do not show if only one item
        if self.tabs_hide_if_only_one_item and len(tabs) == 1:
            return []
        return tabs



class LanguagesTemplate(BaseLanguagesTemplate):
    """
    """

    template = '/ui/common/languages.xml'

    # Configuration
    show_language_title = False

    @thingy_lazy_property
    def languages(self):
        context = self.context
        # Website languages
        ws_languages = context.site_root.get_property('website_languages')
        if len(ws_languages) == 1:
            return []

        # Select language
        accept = context.accept_language
        current_language = accept.select_language(ws_languages)
        # Sort the available languages
        ws_languages = list(ws_languages)
        ws_languages.sort()

        languages = []
        ws_languages_len = len(ws_languages)
        gettext = get_domain('itools').gettext
        for index, language in enumerate(ws_languages):
            href = context.uri.replace(language=language)
            selected = (language == current_language)
            css_class = 'selected' if selected else ''
            if index == 0:
                css_class = '%s first' % css_class
            if index == (ws_languages_len - 1):
                css_class = '%s last' % css_class
            value = get_language_name(language)
            languages.append({
                'name': language,
                'value': gettext(value, language),
                'href': href,
                'selected': selected,
                'class': css_class})
        return languages
