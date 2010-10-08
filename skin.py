# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Taverne Sylvain <sylvain@itaapy.com>
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
from itools.core import get_abspath
from itools.database.ro import ROGitDatabase
from itools.datatypes import Unicode
from itools.gettext import get_domain, MSG
from itools.i18n import get_language_name
from itools.stl import stl, set_prefix
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import HTMLBody, stl_namespaces
from ikaaro.menu import get_menu_namespace
from ikaaro.resource_ import DBResource
from ikaaro.skins import Skin, register_skin
from ikaaro.skins_views import LocationTemplate, LanguagesTemplate
from ikaaro.tracker import Tracker, Issue
from ikaaro.utils import reduce_string
from ikaaro.website import WebSite

# Special case for the Wiki
try:
    from ikaaro.wiki import WikiFolder
except ImportError:
    WikiFolder = None


# Import from itws
from bar import ContentBarAware, SideBarAware, SideBar_View
from news import NewsFolder, NewsItem
from repository import Repository, SidebarBoxesOrderedTable
from utils import get_admin_bar, is_navigation_mode



def get_breadcrumb_short_name(resource):
    if isinstance(resource, DBResource):
        if resource.has_property('breadcrumb_title'):
            return resource.get_property('breadcrumb_title')
        return reduce_string(resource.get_title(), 15, 30)
    return ''


class LocationTemplateWithoutTab(LocationTemplate):

    template = '/ui/common/location.xml'
    bc_prefix = None
    bc_separator = '>'
    tabs_separator = '|'
    # breadcrumbs configuration
    excluded = []
    skip_breadcrumb_in_homepage = False
    # tabs comfiguration
    tabs_hidden_roles = None
    tabs_hide_if_only_one_item = True
    display = True # XXX When do not display ?

    def get_breadcrumb(self, context):
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
            'short_name': get_breadcrumb_short_name(site_root),
            }]

        # Complete the breadcrumb
        resource = site_root
        user = context.user
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
            short_name = get_breadcrumb_short_name(resource)
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


    def get_tabs(self, context):
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

        tabs = LocationTemplate.get_tabs(self, context)
        if self.tabs_hide_if_only_one_item and len(tabs) == 1:
            return []
        return tabs




class CommonLanguagesTemplate(LanguagesTemplate):

    template = '/ui/common/languages.xml'

    show_language_title = False

    def get_namespace(self):
        context = self.context
        # Website languages
        ws_languages = context.site_root.get_property('website_languages')
        if len(ws_languages) == 1:
            return {'languages': []}

        here = context.resource
        ac = here.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, here)

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

        return {'languages': languages,
                'show_language_title': self.show_language_title}



class FoBoFooterAwareSkin(Skin):

    nav_data = {'template': None, 'depth': 1, 'show_first_child': False}
    add_common_nav_css = True
    footer_data = {
        'template': '/ui/common/template_footer.xml', 'depth': 1,
        'src': 'footer', 'show_first_child': False, 'separator': '|' }

    location_template = LocationTemplateWithoutTab
    languages_template = CommonLanguagesTemplate

    template_title_root = MSG(u"{root_title}")
    template_title_base = MSG(u"{root_title} - {here_title}")

    def get_template_title(self, context):
        """Return the title to give to the template document.
        """
        here = context.resource
        root = here.get_site_root()
        root_title = root.get_title()

        # Choose the template
        if root is here:
            template = self.template_title_root
            here_title = None
        else:
            template = self.template_title_base
            # FIXME Check ACL
            here_title = here.get_title()

        # The view
        view_title = context.view.get_title(context)
        if type(view_title) is MSG:
            view_title = view_title.gettext()

        # Ok
        return template.gettext(root_title=root_title, here_title=here_title,
                                view_title=view_title)


    def get_styles(self, context):
        styles = Skin.get_styles(self, context)
        # insert common style after bo.css
        styles.insert(1, '/ui/common/style.css')
        if self.add_common_nav_css:
            styles.append('/ui/common/menu.css')
        styles.append('/ui/common/js/jquery.multiselect2side/css/jquery.multiselect2side.css')
        # Add a specific style
        styles.append('/style/;download')
        return styles


    def get_scripts(self, context):
        scripts = Skin.get_scripts(self, context)
        scripts.append('/ui/common/js/javascript.js')
        scripts.append('/ui/common/js/jquery.multiselect2side/js/jquery.multiselect2side.js')
        return scripts


    def _build_nav_namespace(self, context, data):
        depth = data['depth']
        sfc = data['show_first_child']
        src = data.get('src', None)
        flat = data.get('flat', None)

        # Get the menu namespace
        ns = get_menu_namespace(context, depth, sfc, flat=flat, src=src)
        # HOOK the namespace
        for item in ns.get('items', []):
            if item['class'] == 'in-path':
                item['in-path'] = True
            else:
                item['in-path'] = False

        return ns


    def build_nav_namespace(self, context):
        data = self.nav_data
        data['src'] = 'theme/menu'
        ns = self._build_nav_namespace(context, data)

        # HACK menu if needed
        # Add edit entry
        if is_navigation_mode(context) is False:
            src = data.get('src', 'theme/menu') # FIXME
            menu = context.site_root.get_resource(src, soft=True)
            if menu:
                ac = menu.get_access_control()
                if ac.is_allowed_to_edit(context.user, menu):
                    fake_ns = {'active': False,
                               'class': None,
                               'description': None,
                               'id': 'menu_edit_menu', # FIXME
                               'in_path': False,
                               'items': [],
                               'path': context.get_link(menu),
                               'real_path': menu.get_abspath(),
                               'target': '_top',
                               'title': u'+'}
                    ns['items'].append(fake_ns)

        return ns


    def build_footer_namespace(self, context):
        data = self.footer_data
        ns = self._build_nav_namespace(context, data)

        here = context.resource
        footer = context.site_root.get_resource('%s/menu' % data['src'])
        handler = footer.handler
        records = list(handler.get_records_in_order())
        get_value = handler.get_record_value
        prefix = here.get_pathto(footer)
        # HOOK the namespace
        for index, item in enumerate(ns.get('items', [])):
            record = records[index]
            title = get_value(record, 'title')
            path = get_value(record, 'path')
            html_content = get_value(record, 'html_content')
            item['html'] = None
            if not path and not title and html_content:
                html = HTMLBody.decode(Unicode.encode(html_content))
                html = set_prefix(html, prefix)
                item['html'] = html
        ns['separator'] = data.get('separator', '|')

        # admin bar
        ns['admin_bar'] = get_admin_bar(footer.parent) # menu folder

        return ns


    def build_namespace(self, context):
        namespace = Skin.build_namespace(self, context)

        # Nav
        # If there is no template specify we simply return the namespace
        nav = self.build_nav_namespace(context)
        namespace['nav'] = nav
        namespace['nav_length'] = len(nav['items'])
        nav_template = self.nav_data['template']
        if nav_template is not None:
            nav_template = self.get_resource(nav_template)
            namespace['nav'] = stl(nav_template, {'items': nav['items']})

        # Footer
        footer_template = self.footer_data['template']
        if footer_template is not None:
            ns_footer = self.build_footer_namespace(context)
            footer = None
            if len(ns_footer['items']):
                footer_template = self.get_resource(footer_template)
                footer = stl(footer_template, ns_footer)
            namespace['footer'] = footer

        # Hide context menus if no user authenticated
        if context.user is None:
            namespace['context_menus'] = []

        # Allow to hide the menu if there is only one item
        namespace['display_menu'] = (namespace['nav_length'] > 1)

        return namespace



############################################################
# Skin
############################################################
class NeutralSkin(FoBoFooterAwareSkin):

    nav_data = {'template': '/ui/neutral/template_nav.xml',
                'depth': 1, 'show_first_child': False}

    fo_edit_template = list(XMLParser(
    """
    <div class="fo-edit">
      <a stl:if="not edit_mode" href="/;fo_switch_mode?mode=1"
         title="${edition_title}">${edition_title}</a>
      <a stl:if="edit_mode" href="/;fo_switch_mode?mode=0"
         title="${navigation_title">${navigation_title}</a>
    </div>
    """, stl_namespaces))

    not_allowed_view_name_for_sidebar_view = ['not_found', 'about',
                                              'credits', 'license']

    not_allowed_cls_for_sidebar_view = [Tracker, Tracker.issue_class]
    # XXX Migration
    #                                        SlideShow, Slide, RssFeeds]
    manage_buttons = []


    def get_not_allowed_cls_for_sidebar_view(self):
        types = self.not_allowed_cls_for_sidebar_view[:] # copy
        if WikiFolder:
            types.append(WikiFolder)
        return types


    def get_backoffice_class(self, context):
        # backoffice class
        here = context.resource
        bo_class = None
        current_view = context.view_name
        if current_view in ('edit', 'browse_content', 'preview_content',
                            'login', 'new_resource', 'backlinks', 'edit_state'):
            bo_class = 'backoffice'
        elif isinstance(here, (Tracker, Issue)):
            # XXX Migration add import for ===>, CSS, MenuFolder, Menu)):
            bo_class = 'backoffice'
        elif isinstance(here, WebSite):
            ac = here.get_access_control()
            if ac.is_allowed_to_edit(context.user, here):
                bo_class = 'backoffice'
        elif here.name in ('order-slides',):
            bo_class = 'backoffice'

        return bo_class


    def get_rss_feeds(self, context, site_root):
        rss = []
        site_root_abspath = site_root.get_abspath()
        # Global RSS
        ws_title = site_root.get_title()
        rss_title = MSG(u'{ws_title} -- RSS Feeds').gettext(ws_title=ws_title)
        rss.append({'path': '/;rss', 'title': rss_title})

        # News RSS
        news_folder = site_root.get_news_folder(context)
        if news_folder:
            title = news_folder.get_title()
            rss_title = MSG(u'{ws_title} {title} -- RSS Feeds')
            rss_title = rss_title.gettext(title=title, ws_title=ws_title)
            rss.append({'path': '%s/;rss' % context.get_link(news_folder),
                        'title': rss_title})

        return rss


    def get_sidebar_resource(self, context):
        here = context.resource
        site_root = context.site_root
        sidebar_resource = site_root
        if isinstance(here, SideBarAware):
            sidebar_resource = here
        elif isinstance(here, SidebarBoxesOrderedTable):
            parent = here.parent
            if isinstance(parent, site_root.wsdatafolder_class):
                # Special case for ws-data folder
                sidebar_resource = site_root
            else:
                sidebar_resource = parent
        elif isinstance(here, NewsItem) or\
                isinstance(here.parent, site_root.section_class):
            sidebar_resource = here.parent
        return sidebar_resource


    def build_namespace(self, context):
        namespace = FoBoFooterAwareSkin.build_namespace(self, context)

        here = context.resource
        site_root = context.site_root

        # banner namespace
        banner_ns = {}
        banner_ns['title'] = site_root.get_property('banner_title')
        banner_ns['description'] = site_root.get_property('description')
        banner_path = None
        path = site_root.get_property('banner_path')
        if path:
            banner = site_root.get_resource(path, soft=True)
            if banner:
                ac = banner.get_access_control()
                if ac.is_allowed_to_view(context.user, banner):
                    banner_path = context.get_link(banner)
        banner_ns['path'] = banner_path
        namespace['banner'] = banner_ns

        # site search
        text = context.get_form_value('site_search_text', type=Unicode)
        namespace['text'] = text.strip()

        # Specific class based on the current resource format
        class_id = getattr(here, 'class_id', None)
        if class_id:
            class_id = class_id.replace('/', '-slash-')
            view_name = context.view_name or here.get_default_view_name()
            page_css_class = '%s-%s' % (class_id, view_name)
            page_css_class = page_css_class.replace('_', '-')
            namespace['page_css_class'] = page_css_class.lower()
            # resources classes
            resource_classes = []
            r = here
            while not isinstance(r, type(site_root)):
                resource_classes.append(r)
                r = r.parent
            resource_classes = [ r.name for r in reversed(resource_classes) ]
            namespace['resource_class'] = ' '.join(resource_classes)
        else:
            namespace['page_css_class'] = None
            namespace['resource_class'] = None

        # Add custom data inside the template
        custom_data = site_root.get_property('custom_data') or ''
        namespace['custom_data'] = XMLParser(custom_data)

        # RSS Feeds title
        namespace['rss_feeds'] = self.get_rss_feeds(context, site_root)

        # favicon
        favicon = site_root.get_property('favicon')
        namespace['favicon'] = False
        if favicon:
            favicon_resource = site_root.get_resource(favicon, soft=True)
            if favicon_resource:
                ac = favicon_resource.get_access_control()
                if ac.is_allowed_to_view(context.user, favicon_resource):
                    mimetype = favicon_resource.handler.get_mimetype()
                    favicon_href = '%s/;download' % resolve_uri('/', favicon)
                    namespace['favicon_href'] = favicon_href
                    namespace['favicon_type'] = mimetype
                    namespace['favicon'] = True

        if namespace['favicon'] is False:
            # ikaaro add a default favicon
            if 'image' in namespace['favicon_type']:
                namespace['favicon'] = True

        # Turning footer
        turning_footer = site_root.get_resource('turning-footer', soft=True)
        if turning_footer:
            view = turning_footer.view
            namespace['turning_footer'] = view.GET(turning_footer, context)
        else:
            namespace['turning_footer'] = None

        # manage buttons
        manage_buttons = []
        if context.user:
            manage_buttons = self.manage_buttons
        namespace['manage_buttons'] = manage_buttons

        # backoffice class
        namespace['bo_class'] = self.get_backoffice_class(context)

        # Readonly
        body_css = None
        if type(context.database) is ROGitDatabase:
            body_css = 'read-only'
        namespace['body_css'] = body_css

        # Sidebar
        nacfsv = self.get_not_allowed_cls_for_sidebar_view()
        sidebar = None
        not_allowed = isinstance(here, tuple(nacfsv))
        navnfsv = self.not_allowed_view_name_for_sidebar_view
        if context.view_name not in navnfsv and not not_allowed:
            sidebar_resource = self.get_sidebar_resource(context)

            if sidebar_resource:
                order_name = sidebar_resource.sidebar_name
                sidebar_view = SideBar_View(order_name=order_name)
                if not sidebar_view.is_empty(sidebar_resource, context):
                    # Heuristic, do not compute sidebar view
                    # if there is no items
                    sidebar = sidebar_view.GET(sidebar_resource, context)

        namespace['sidebar_view'] = sidebar
        namespace['sidebar'] = sidebar or namespace['context_menus']

        # FO edit/no edit
        ac = here.get_access_control()
        events = None
        if ac.is_allowed_to_edit(context.user, here):
            edit_mode = is_navigation_mode(context) is False
            events = stl(events=self.fo_edit_template,
                         namespace={
                             'edit_mode': edit_mode,
                             'edition_title': MSG(u'Go to editing mode'),
                             'navigation_title': MSG(u'Back to navigation')})
        namespace['fo_edit_toolbar'] = events

        # languages
        ws_languages = site_root.get_property('website_languages')
        accept = context.accept_language
        namespace['lang'] = accept.select_language(ws_languages)

        # Manage view acl
        view = site_root.get_view('manage_view')
        manage_view_allowed = ac.is_access_allowed(context.user, site_root,
                                                   view)
        namespace['manage_view_allowed'] = manage_view_allowed

        return namespace


    def get_styles(self, context):
        styles = FoBoFooterAwareSkin.get_styles(self, context)
        if styles.count('/ui/aruni/aruni.css'):
            styles.remove('/ui/aruni/aruni.css')
        # In edition mode we add fancybox css
        edit_mode = is_navigation_mode(context) is False
        if edit_mode is True:
            styles.append('/ui/common/js/fancybox/jquery.fancybox-1.3.1.css')
        return styles


    def get_scripts(self, context):
        scripts = FoBoFooterAwareSkin.get_scripts(self, context)
        # In edition mode we add fancybox script
        edit_mode = is_navigation_mode(context) is False
        if edit_mode is True:
            scripts.append('/ui/common/js/fancybox/jquery.fancybox-1.3.1.pack.js')
        return scripts



class NeutralSkin2(NeutralSkin):

    add_common_nav_css = False
    manage_buttons = [
        {'path': '/menu/menu', 'label': MSG(u'Order menu')},
        {'path': '/;new_resource?type=section',
         'label': MSG(u'Add a section')},
        {'path': '/;edit_languages', 'label': MSG(u'Edit languages')}]



class K2Skin(NeutralSkin2):

    # FIXME
    fo_edit_template = list(XMLParser(
    """
    <td class="fo-edit">
      <a stl:if="not edit_mode" href="/;fo_switch_mode?mode=1"
         title="${edition_title}">${edition_title}</a>
      <a stl:if="edit_mode" href="/;fo_switch_mode?mode=0"
         title="${navigation_title}">${navigation_title}</a>
    </td>
    """, stl_namespaces))



class AdminPopupSkin(Skin):

    def get_styles(self, context):
        styles = Skin.get_styles(self, context)
        styles.append('/ui/common/js/jquery.multiselect2side/css/jquery.multiselect2side.css')
        return styles


    def get_scripts(self, context):
        scripts = Skin.get_scripts(self, context)
        scripts.append('/ui/common/js/jquery.multiselect2side/js/jquery.multiselect2side.js')
        return scripts


    def build_namespace(self, context):
        namespace = Skin.build_namespace(self, context)
        # Get some values
        resource = context.resource
        # Title & description of popup
        namespace['title'] = resource.class_title
        namespace['description'] = resource.class_description
        namespace['context_menus'] = list(self._get_context_menus(context))
        return namespace


# Register common skin
path = get_abspath('ui/common')
register_skin('common', path)

###################
# Register skins
###################

# neutral
path = get_abspath('ui/neutral')
skin = NeutralSkin(path)
register_skin('neutral', skin)
# neutral 2
path = get_abspath('ui/neutral2')
skin = NeutralSkin2(path)
register_skin('neutral2', skin)
# k2
path = get_abspath('ui/k2')
skin = K2Skin(path)
register_skin('k2', skin)
# Admin popup
path = get_abspath('ui/admin-popup')
skin = AdminPopupSkin(path)
register_skin('admin-popup', skin)


# CSS skeleton
css_skeleton = """/* CSS */
#header {
/* background: #a11; */

/* Image source: http://www.flickr.com/photos/joebeone/2240389708/ */
/* Image license: http://creativecommons.org/licenses/by/2.0/deed.en */
background: url("../images/background-ties/;download") no-repeat scroll 0 0 transparent;
}

#header .login,
#header .header-toolbar {
background: #822;
}

#header .title a {
color: #822;
}

#nav ul li a {
background: #822;
}

#nav ul li.in-path a {
background: #ecc;
}
"""

