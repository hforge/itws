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
from itools.core import get_abspath, merge_dicts
from itools.database.ro import ROGitDatabase
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.stl import stl, set_prefix
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.menu import MenuFolder, Menu, get_menu_namespace
from ikaaro.skins import Skin as BaseSkin, register_skin
from ikaaro.text import CSS
from ikaaro.tracker import Tracker
from ikaaro.tracker.issue import Issue
from ikaaro.website import WebSite
from ikaaro.website_views import ContactForm

# Special case for the Wiki
try:
    from ikaaro.wiki import WikiFolder
    wiki_is_install = True
except ImportError:
    wiki_is_install = False


# Import from itws
from bar import SideBarAware, SideBar_View
from webpage_views import WebPage_View
from news import NewsItem
from news.news_views import NewsFolder_View, NewsItem_View
from OPML import RssFeeds
from skin_views import LocationTemplate, LanguagesTemplate
from tags.tags_views import TagsFolder_TagCloud
from utils import get_admin_bar, is_navigation_mode
from feed_views import Feed_View



############################################################
# Skin
###########################################################
class Skin(BaseSkin):

    title = MSG(u'ITWS skin')

    nav_data = {'template': '/ui/neutral/template_nav.xml',
                'depth': 1,
                'flat': None,
                'src': 'theme/menu',
                'show_first_child': False}

    add_common_nav_css = False

    footer_data = {
        'template': '/ui/common/template_footer.xml', 'depth': 1,
        'flat': None,
        'src': 'theme/footer', 'show_first_child': False, 'separator': '|' }

    location_template = LocationTemplate
    languages_template = LanguagesTemplate

    template_title_root = MSG(u"{root_title}")
    template_title_base = MSG(u"{root_title} - {here_title}")


    not_allowed_view_name_for_sidebar_view = ['not_found', 'about',
                                              'credits', 'license']

    not_allowed_cls_for_sidebar_view = [Tracker, Tracker.issue_class, RssFeeds]
    allowed_views_for_sidebar_view = (Feed_View,
        NewsFolder_View, NewsItem_View, WebPage_View, ContactForm,
        TagsFolder_TagCloud)

    def get_not_allowed_cls_for_sidebar_view(self):
        types = self.not_allowed_cls_for_sidebar_view[:] # copy
        if wiki_is_install:
            types.append(WikiFolder)
        return types


    def get_backoffice_class(self, context):
        # backoffice class
        here = context.resource
        bo_class = None
        current_view = context.view_name
        if current_view in ('edit', 'browse_content', 'preview_content',
                            'login', 'new_resource', 'backlinks',
                            'edit_state'):
            bo_class = 'backoffice'
        elif isinstance(here, (Tracker, Issue, CSS, MenuFolder, Menu)):
            bo_class = 'backoffice'
        elif isinstance(here, WebSite):
            ac = here.get_access_control()
            if ac.is_allowed_to_edit(context.user, here):
                bo_class = 'backoffice'

        return bo_class


    def get_rss_feeds(self, context, site_root):
        rss = []
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


    def get_sidebar_resource(self, context):
        here = context.resource
        site_root = context.site_root
        sidebar_resource = site_root
        if isinstance(here, SideBarAware):
            sidebar_resource = here
        elif isinstance(here, NewsItem) or\
                isinstance(here.parent, site_root.section_class):
            sidebar_resource = here.parent
        return sidebar_resource


    def build_nav_namespace(self, context):
        data = self.nav_data
        menu = context.site_root.get_resource(data['src'])
        ns = get_menu_namespace(context,
            data['depth'], data['show_first_child'],
            flat=data['flat'], menu=menu)
        if is_navigation_mode(context) is True:
            return ns
        # Add [+] item in menu (To edit)
        ac = menu.get_access_control()
        if ac.is_allowed_to_edit(context.user, menu):
            ns['items'].append(
                {'active': False,
                 'class': None,
                 'description': None,
                 'id': 'menu_edit_menu', # FIXME
                 'in_path': False,
                 'items': [],
                 'path': context.get_link(menu),
                 'real_path': menu.get_abspath(),
                 'target': '_top',
                 'title': u'+'})
        return ns


    def build_footer_namespace(self, context):
        data = self.footer_data
        ns = get_menu_namespace(context,
            data['depth'], data['show_first_child'],
            flat=data['flat'], src=data['src'])

        here = context.resource
        # Manipulate directly the table handler
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
                html = set_prefix(html_content, '%s/' % prefix)
                item['html'] = html
        ns['separator'] = data.get('separator', '|')

        # admin bar
        ns['admin_bar'] = get_admin_bar(footer.parent) # menu folder

        return ns


    def build_namespace(self, context):
        namespace = BaseSkin.build_namespace(self, context)

        here = context.resource
        site_root = context.site_root
        theme = site_root.get_resource('theme')

        # banner namespace
        banner_ns = {}
        banner_ns['title'] = theme.get_property('banner_title')
        banner_ns['description'] = site_root.get_property('description')
        banner_path = None
        path = theme.get_property('banner_path')
        if path:
            banner = theme.get_resource(path, soft=True)
            if banner:
                ac = banner.get_access_control()
                if ac.is_allowed_to_view(context.user, banner):
                    banner_path = context.get_link(banner)
        banner_ns['path'] = banner_path
        namespace['banner'] = banner_ns

        # Site search
        text = context.get_form_value('search_text', type=Unicode)
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
        custom_data = theme.get_property('custom_data') or ''
        namespace['custom_data'] = XMLParser(custom_data)

        # RSS Feeds title
        namespace['rss_feeds'] = self.get_rss_feeds(context, site_root)

        # Turning footer
        turning_footer = site_root.get_resource('theme/turning-footer',
                                                soft=True)
        if turning_footer:
            view = turning_footer.view
            namespace['turning_footer'] = view.GET(turning_footer, context)
        else:
            namespace['turning_footer'] = None

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
        is_authorized_view = isinstance(context.view,
                                        self.allowed_views_for_sidebar_view)
        if (context.view_name not in navnfsv and
            not not_allowed and is_authorized_view):
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

        # Language
        ws_languages = site_root.get_property('website_languages')
        accept = context.accept_language
        namespace['lang'] = accept.select_language(ws_languages)

        # Manage view acl
        view = site_root.get_view('manage_view')
        manage_view_allowed = ac.is_access_allowed(context.user, site_root,
                                                   view)
        namespace['manage_view_allowed'] = manage_view_allowed

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
        namespace['footer'] = None
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


    def get_styles(self, context):
        styles = BaseSkin.get_styles(self, context)
        if styles.count('/ui/aruni/aruni.css'):
            styles.remove('/ui/aruni/aruni.css')
        # insert common style after bo.css
        styles.insert(1, '/ui/common/style.css')
        if self.add_common_nav_css:
            styles.append('/ui/common/menu.css')
        styles.append('/ui/common/js/jquery.multiselect2side/style.css')
        # In edition mode we add fancybox css
        edit_mode = is_navigation_mode(context) is False
        if edit_mode is True:
            styles.append('/ui/common/js/fancybox/jquery.fancybox-1.3.1.css')
        return styles


    def get_scripts(self, context):
        scripts = BaseSkin.get_scripts(self, context)
        # In edition mode we add fancybox script
        edit_mode = is_navigation_mode(context) is False
        if edit_mode is True:
            scripts.append('/ui/common/js/fancybox/jquery.fancybox-1.3.1.pack.js')
        scripts.append('/ui/common/js/javascript.js')
        scripts.append('/ui/common/js/jquery.multiselect2side/javascript.js')
        return scripts



class NeutralSkin(Skin):

    title = MSG(u'Neutral Skin 1')

    add_common_nav_css = True



class AdminPopupSkin(BaseSkin):

    def get_styles(self, context):
        styles = BaseSkin.get_styles(self, context)
        styles.append('/ui/common/js/jquery.multiselect2side/style.css')
        styles.remove('/theme/style/;download')
        return styles


    def get_scripts(self, context):
        scripts = BaseSkin.get_scripts(self, context)
        scripts.append('/ui/common/js/jquery.multiselect2side/javascript.js')
        return scripts


    def build_namespace(self, context):
        return merge_dicts(BaseSkin.build_namespace(self, context),
                  title=context.view.get_title(context),
                  description=context.resource.class_description,
                  context_menus=list(self._get_context_menus(context)))



###################
# Register skins
###################

# Internal
register_skin('common', get_abspath('ui/common'))
register_skin('admin-popup', AdminPopupSkin(get_abspath('ui/admin-popup')))

# New skins
register_skin('k2', Skin(get_abspath('ui/k2')))

# Old skins
register_skin('neutral', NeutralSkin(get_abspath('ui/neutral')))
