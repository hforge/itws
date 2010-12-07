# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009 Romain Gauthier <romain@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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
from decimal import Decimal

# Import from itools
from itools.core import freeze, get_abspath, merge_dicts
from itools.csv import Property
from itools.database.ro import ROGitDatabase
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.html import XHTMLFile
from itools.web import get_context
from itools.database import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.datatypes import Multilingual
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.registry import register_document_type
from ikaaro.user import User
from ikaaro.utils import get_base_path_query
from ikaaro.website import WebSite
from ikaaro.workflow import WorkflowAware

# Import from itws
from OPML import RssFeeds
from about import AboutITWS
from bar import HTMLContent, Website_BarAware, HomePage_BarAware, Section
from control_panel import CPEdit404, CPEditRobotsTXT, CPFOSwitchMode
from control_panel import CPEditTags, CPDBResource_CommitLog
from control_panel import ITWS_ControlPanel, CP_AdvanceNewResource
from feed_views import Search_View
from images_folder import ImagesFolder
from news import NewsFolder
from notfoundpage import NotFoundPage_View
from robots_txt import RobotsTxt
from sitemap import SiteMap
from tags import TagsAware, TagsFolder
from theme import Theme
from webpage import WebPage
from ws_neutral_views import NeutralWS_Edit, NeutralWS_RSS



############################################################
# Neutral Web Site
############################################################

class NeutralWS(Website_BarAware, HomePage_BarAware, WebSite):
    """
    A neutral website is a website...
    [1] Which allow to:
       - Configure breadcrumb base title
    [2] Which contains:
       - A sitemap.xml
       - An about itws webpage
       - A footer
       - A news folder
       - A turning footer
       - A tags folder
       - A robots.txt
       - A 404 webpage
       - A folder with images
    [3] Which is Website_BarAware (Contains a repository of boxes)
    [4] With homepage that show 2 bars (HomePage_BarAware)
    """

    class_id = 'neutral'
    class_version = '20101012'
    class_title = MSG(u'ITWS website')
    class_views = ['view', 'edit', 'manage_content',
                   'add_content', 'control_panel']
    class_schema = merge_dicts(WebSite.class_schema,
                              breadcrumb_title=Multilingual(source='metadata'))


    class_control_panel = (WebSite.class_control_panel +
                          Website_BarAware.class_control_panel +
                          HomePage_BarAware.class_control_panel +
                          ['edit_tags', 'edit_footer', 'edit_turning_footer',
                           'edit_404', 'edit_robots_txt', 'commit_log',
                           'advance_new_resource', 'fo_switch_mode'])

    __fixed_handlers__ = (WebSite.__fixed_handlers__ +
                          Website_BarAware.__fixed_handlers__ +
                          HomePage_BarAware.__fixed_handlers__ +
                          ['about-itws', 'news', 'sitemap.xml', 'robots.txt',
                           'images', 'tags'])

    # Configuration
    class_theme = Theme
    first_contenbar = 'data/welcome_on_itws.xhtml'
    first_sidebar = 'data/first_sidebar.xhtml'

    # Classes
    newsfolder_class = NewsFolder
    section_class = Section
    sitemap_class = SiteMap
    tagsfolder_class = TagsFolder

    def init_resource(self, **kw):
        kw['website_is_open'] = 'extranet'
        # TODO allow to choose language at website creation
        default_language = 'en'
        # Initialize ikaaro website (Parent class)
        WebSite.init_resource(self, **kw)
        # The website is BarAware
        Website_BarAware.init_resource(self, **kw)
        # The homepage is BarAware
        HomePage_BarAware.init_resource(self, **kw)
        # Add a sitemap
        self.make_resource('sitemap.xml', self.sitemap_class)
        # Create Robots.txt
        self.make_resource('robots.txt', RobotsTxt)
        # Add an image folder
        self.make_resource('images', ImagesFolder)
        # Tags
        self.make_resource('tags', self.tagsfolder_class,
                           language=default_language)
        # Add default news folder
        self.make_resource('news', self.newsfolder_class)
        # About
        self.make_resource('about-itws', AboutITWS,
                       title={default_language: MSG(u'About ITWS').gettext()})

        # Add link to news in menu
        theme = self.get_resource('theme')
        menu = theme.get_resource('menu/menu')
        menu.add_new_record({'path': '/news/',
                             'title': Property(MSG(u'News').gettext(),
                                               language='en')})
        # Create a 'Welcome' html-content item in ws-data
        # Order this item in the contentbar
        path = get_abspath(self.first_contenbar)
        handler = ro_database.get_handler('%s.%s' % (path, default_language),
                                          XHTMLFile)
        ws_data = self.get_resource('ws-data')
        ws_data.make_resource('welcome', HTMLContent,
                  title={default_language: MSG(u'Welcome').gettext()},
                  state='public',
                  display_title=True,
                  body=handler.to_str(),
                  language=default_language)
        table = ws_data.get_resource('order-contentbar')
        table.add_new_record({'name': 'welcome'})

        # Create a 'Welcome' html-content item in repository
        # Order this item in the sidebar
        path = get_abspath(self.first_sidebar)
        handler = ro_database.get_handler('%s.%s' % (path, default_language),
                                          XHTMLFile)
        repository = self.get_resource('repository')
        repository.make_resource('first-sidebar', HTMLContent,
                  title={default_language: MSG(u'My first sidebar').gettext()},
                  state='public',
                  display_title=True,
                  body=handler.to_str(),
                  language=default_language)
        table = ws_data.get_resource('order-sidebar')
        table.add_new_record({'name': 'first-sidebar'})


    @classmethod
    def get_orderable_classes(cls):
        return (cls, Section)


    @property
    def class_skin(self):
        return self.get_resource('theme').get_property('class_skin')


    def get_skin(self, context):
        if context.get_query_value('is_admin_popup', type=Boolean) is True:
            return self.get_resource('/ui/admin-popup/')
        return WebSite.get_skin(self, context)


    def get_internal_use_resource_names(self):
        return freeze(['repository', 'robots.txt', 'sitemap.xml',
                       'theme', 'tags', 'turning-footer', 'ws-data'])


    def get_document_types(self):
        types = WebSite.get_document_types(self)
        # News Folder can only be instanciated once
        if self.newsfolder_class:
            if self.get_news_folder(get_context()) is None:
                types.append(self.newsfolder_class)

        return types + [Section, RssFeeds]


    def before_traverse(self, context, min=Decimal('0.000001'),
                        zero=Decimal('0.0')):
        # The default language
        accept = context.accept_language
        default = self.get_default_language()
        if accept.get(default, zero) < min:
            accept.set(default, min)
        # The Query
        language = context.get_form_value('language')
        if language is not None:
            context.set_cookie('language', language)
        # Language negotiation
        user = context.user
        language = context.get_cookie('language')
        if language is not None:
            accept.set(language, 3.0)
        if user:
            language = user.get_property('user_language')
            accept.set(language, 2.0)


    def get_repository(self, soft=False):
        # Backward compatibility
        repository = self.get_resource('right-depot', soft=True)
        if repository:
            return repository
        return self.get_resource('repository', soft=soft)


    def get_news_folder(self, context):
        # News folder MUST be in root '/xxx'
        abspath = self.get_canonical_path()
        query = [get_base_path_query(str(abspath)),
                  PhraseQuery('format', self.newsfolder_class.class_id)]
        #query = get_base_path_query(str(abspath))
        # Search
        results = context.root.search(AndQuery(*query), sort_by='name')
        if len(results):
            database = context.database
            doc = results.get_documents()[0]
            path = doc.abspath
            if type(context.database) is not ROGitDatabase:
                path = database.resources_old2new.get(path, path)
            return self.get_resource(path)
        return None


    def get_article_class(self):
        # ContentBarItem_Articles_View API
        return WebPage


    ###########################################################################
    # ACL
    ###########################################################################
    def is_allowed_to_view(self, user, resource):
        # Get the variables to resolve the formula
        # Intranet or Extranet
        is_open = self.get_property('website_is_open')
        # User not authenticated or intranet mode
        if is_open is False or user is None:
            # Default ACL
            return WebSite.is_allowed_to_view(self, user, resource)

        # The role of the user
        if self.is_admin(user, resource):
            role = 'admins'
        else:
            role = self.get_user_role(user.name)

        # The state of the resource
        if isinstance(resource, WorkflowAware):
            state = resource.workflow_state
        else:
            state = 'public'

        if role == 'guests':
            # Special case for the guests
            return state == 'public'
        elif state == 'public':
            return True
        return role is not None


    #######################################################################
    # Views
    #######################################################################

    # Base views
    edit = NeutralWS_Edit()
    not_found = NotFoundPage_View()
    rss = last_news_rss = NeutralWS_RSS()
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')
    site_search = Search_View()

    # Control panel
    control_panel = ITWS_ControlPanel()

    edit_tags = CPEditTags()
    edit_404 = CPEdit404()
    edit_robots_txt = CPEditRobotsTXT()
    fo_switch_mode = CPFOSwitchMode()
    advance_new_resource = CP_AdvanceNewResource()


    ###########################################
    # Upgrade to 0.62
    ###########################################
    def update_20100701(self):
        # Fix website vhosts
        WebSite.update_20100430(self)


    def update_20100702(self):
        # Add theme
        theme = self.get_resource('theme', soft=True)
        class_theme = self.class_theme
        if theme and isinstance(theme, class_theme) is False:
            raise RuntimeError, 'A resource named theme already exists'

        # Create theme
        theme = self.make_resource('theme', class_theme,
                                   title={'en': u'Theme'})


    # Move old root data inside the theme folder
    def update_20100703(self):
        # Del default menu, footer, turning-footer and css
        theme = self.get_resource('theme')
        theme.del_resource('menu', ref_action='force')
        theme.del_resource('footer', ref_action='force')
        theme.del_resource('turning-footer', ref_action='force')
        theme.del_resource('style', ref_action='force')

        languages = self.get_property('website_languages')
        # Move 404 page
        source = self.get_resource('404', soft=True)
        if source:
            target = self.get_resource('theme/404')
            for language in languages:
                handler_source = source.get_handler(language)
                handler_target = target.get_handler(language)
                handler_target.load_state_from_string(handler_source.to_str())
                handler_target.set_changed()
            target._on_move_resource(str(source.get_abspath()))
        # delete old 404
        self.del_resource('404', ref_action='force')


    def update_20100704(self):
        """Move menu, style inside the theme folder"""
        self.move_resource('menu', 'theme/menu')
        self.move_resource('footer', 'theme/footer')
        self.move_resource('turning-footer', 'theme/turning-footer')
        self.move_resource('style', 'theme/style')


    def update_20100705(self):
        website_languages = self.get_property('website_languages')

        # Logo
        theme = self.get_resource('theme')
        theme.set_property('logo', None)

        # Favicon
        favicon = self.get_resource(self.get_property('favicon'), soft=True)
        self.del_property('favicon')
        if favicon:
            theme.set_property('favicon', theme.get_pathto(favicon))

        # Banner path
        for language in website_languages:
            banner_path = self.get_property('banner_path', language=language)
            if banner_path is None:
                continue
            banner = self.get_resource(banner_path, soft=True)
            if banner:
                theme.set_property('banner_path', theme.get_pathto(banner),
                                   language=language)

        # Other
        schema = theme.class_schema
        for key in ['custom_data', 'class_skin', 'banner_title']:
            datatype = schema[key]
            # Multilingual property or not
            if getattr(datatype, 'multilingual', False):
                languages = website_languages
            else:
                languages = [None]
            # Move property
            for language in languages:
                value = self.get_property(key, language=language)
                if value:
                    theme.set_property(key, value, language=language)
            # Delete old property
            self.del_property(key)


    def update_20100706(self):
        """Fix user property"""
        users = self.get_resource('users')

        class_schema_keys = User.class_schema.keys()
        set_class_schema_keys = set(class_schema_keys)
        for user in users.search_resources(cls=User):
            property_keys = user.metadata.properties.keys()
            diff = set(property_keys).difference(set_class_schema_keys)
            for key in diff:
                user.del_property(key)


    def update_20100708(self):
        """Fix TagsAware tags property"""

        for resource in self.traverse_resources():
            if isinstance(resource, TagsAware):
                old_value = resource.get_property('tags')
                if not old_value: # empty list
                    continue
                new_value = old_value[0].split(' ')
                resource.set_property('tags', new_value)


############################################################
# Register
############################################################
register_document_type(NeutralWS, WebSite.class_id)
