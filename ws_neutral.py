# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2011 Taverne Sylvain <sylvain@itaapy.com>
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
import sys

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
from ikaaro.control_panel import ControlPanel
from ikaaro.datatypes import Multilingual
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.registry import register_document_type
from ikaaro.user import User
from ikaaro.website import WebSite

# Special case for the Wiki
try:
    from wiki import WikiFolder
except ImportError:
    WikiFolder = None

# Import from itws
from OPML import RssFeeds
from about import AboutITWS
from bar import HTMLContent, Website_BarAware, Section
from control_panel import CPEdit404, CPEditRobotsTXT, CPFOSwitchMode
from control_panel import CPEditTags, CPDBResource_CommitLog
from control_panel import ITWS_ControlPanel
from feed_views import Search_View
from section_views import SectionViews_Enumerate
from news import NewsFolder
from notfoundpage import NotFoundPage_View
from robots_txt import RobotsTxt
from sitemap import SiteMap
from tags import TagsAware, TagsFolder
from theme import Theme
from views import Website_NewResource
from webpage import WebPage
from ws_neutral_views import NeutralWS_Edit, NeutralWS_RSS



############################################################
# Neutral Web Site
############################################################

class NeutralWS(Website_BarAware, WebSite):
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
    """

    class_id = 'neutral'
    class_version = '20101015'
    class_title = MSG(u'ITWS Web Site')
    class_description = MSG(u'Create a new ITWS Web Site')
    class_icon16 = 'common/icons/16x16/itws-website.png'
    class_icon48 = 'common/icons/48x48/itws-website.png'
    class_views = ['view', 'edit', 'configure_view', 'control_panel']
    class_schema = merge_dicts(WebSite.class_schema,
            Website_BarAware.class_schema,
            breadcrumb_title=Multilingual(source='metadata'),
            view=SectionViews_Enumerate(source='metadata',
                                        default='composite-view'))

    class_control_panel = (WebSite.class_control_panel +
                          Website_BarAware.class_control_panel +
                          ['edit_tags', 'edit_footer', 'edit_turning_footer',
                           'edit_404', 'edit_robots_txt', 'commit_log'])

    __fixed_handlers__ = (WebSite.__fixed_handlers__ +
                          Website_BarAware.__fixed_handlers__ +
                          ['about-itws', 'sitemap.xml', 'robots.txt',
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
        # Init bars
        Website_BarAware.init_resource(self, **kw)
        # Add a sitemap
        self.make_resource('sitemap.xml', self.sitemap_class)
        # Create Robots.txt
        self.make_resource('robots.txt', RobotsTxt)
        # Add an image folder
        self.make_resource('images', Folder)
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


    def get_catalog_values(self):
        return merge_dicts(WebSite.get_catalog_values(self),
                           Website_BarAware.get_catalog_values(self))


    @property
    def class_skin(self):
        return self.get_resource('theme').get_property('class_skin')


    def get_skin(self, context):
        # TODO It's an interesting mechanism (add in ikaaro)
        if (context.get_query_value('is_admin_popup', type=Boolean) is True
              or getattr(context.view, 'is_popup', False)):
            return self.get_resource('/ui/admin-popup/')
        return WebSite.get_skin(self, context)


    def before_traverse(self, context, min=Decimal('0.000001'),
                        zero=Decimal('0.0')):
        proxy = super(NeutralWS, self)
        proxy.before_traverse(context, min, zero)
        # URI language ie en.mywebsite.com, fr.mywebsite.com
        if context.uri:
            uri_lang = context.uri.authority.split('.')[0]
            available_languages = self.get_property('website_languages')
            if uri_lang in available_languages:
                # URI language (1.5)
                accept = context.accept_language
                accept.set(uri_lang, 1.5)


    # InternalResourcesAware API
    def get_internal_use_resource_names(self):
        return freeze(Website_BarAware.get_internal_use_resource_names(self) +
                      ['robots.txt', 'sitemap.xml', 'theme/', 'tags/',
                       'repository/'])


    def get_document_types(self):
        types = WebSite.get_document_types(self)
        # News Folder can only be instanciated once
        if self.newsfolder_class:
            if self.get_news_folder(get_context()) is None:
                types.append(self.newsfolder_class)

        return types + [Section, RssFeeds]


    def get_repository(self, soft=False):
        # Backward compatibility
        repository = self.get_resource('right-depot', soft=True)
        if repository:
            return repository
        return self.get_resource('repository', soft=soft)


    def get_news_folder(self, context):
        # News folder MUST be in root '/foo'
        abspath = self.get_canonical_path()
        query = [PhraseQuery('parent_path', str(abspath)),
                 PhraseQuery('format', self.newsfolder_class.class_id)]
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
        proxy = super(NeutralWS, self)
        # XXX Temporary hack for Wiki
        if WikiFolder and isinstance(resource, WikiFolder):
            frontpage = resource.get_resource('FrontPage')
            return proxy.is_allowed_to_view(user, frontpage)
        # XXX Temporary hack for Tracker
        tracker_mod = sys.modules.get('ikaaro.tracker')
        if tracker_mod:
            # Tracker module has been loaded
            tracker_cls = tracker_mod.Tracker
            if isinstance(resource, (tracker_cls, tracker_cls.issue_class)):
                # Tracker/Issue are visible if the user can edit them
                return proxy.is_allowed_to_edit(user, resource)
        return proxy.is_allowed_to_view(user, resource)


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
    website_new_resource = Website_NewResource()

    # Control panel
    control_panel = ITWS_ControlPanel(title=ControlPanel.title)

    edit_tags = CPEditTags()
    edit_404 = CPEdit404()
    edit_robots_txt = CPEditRobotsTXT()
    fo_switch_mode = CPFOSwitchMode()


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
        # Fix submenu, delete them and tweak child property
        parent = self.get_resource('theme/menu')
        menu = parent.get_resource('menu')
        if parent.allow_submenu is False:
            # delete all submenus
            for name in parent._get_names():
                if name.startswith('menu-'):
                    parent.del_resource(name, ref_action='force')
        # Fix child property
        handler = menu.handler
        for record in handler.get_records():
            if parent.allow_submenu is False:
                handler.update_record(record.id, **{'child': ''})
            else:
                # check if child exists
                child = handler.get_record_value(record, 'child')
                if child and menu.get_resource(child, soft=True) is None:
                    handler.update_record(record.id, **{'child': ''})

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


    def update_20101013(self):
        """Transform images folder into normal Folder"""
        from ikaaro.folder import Folder
        from obsolete import ImagesFolder

        for resource in self.traverse_resources():
            if isinstance(resource, ImagesFolder):
                metadata = resource.metadata
                metadata.set_changed()
                metadata.format = Folder.class_id
                metadata.version= Folder.class_version


    def update_20101014(self):
        """Fix security policy"""
        value = self.get_security_policy()
        if value == 'community':
            value = 'extranet'
        self.set_property('website_is_open', value)


    def update_20101015(self):
        """Fix TagsAware pub_datetime
        Add tzinfo"""
        from pytz import timezone
        from itools.core import utc

        # Current server timezone
        paris = timezone('Europe/Paris')

        database = get_context().database
        for resource in self.traverse_resources():
            if isinstance(resource, TagsAware):
                pub_datetime = resource.get_property('pub_datetime')
                if pub_datetime is None:
                    continue
                # localize date
                local_datetime = paris.localize(pub_datetime)
                utc_datetime = local_datetime - local_datetime.utcoffset()
                utc_datetime = utc_datetime.replace(tzinfo=utc)
                # Call metadata.set_property directly to avoid
                # comparison error 'TypeError'
                # -> can't compare offset-naive and offset-aware datetimes
                database.change_resource(resource)
                resource.metadata.set_property('pub_datetime', utc_datetime)



############################################################
# Register
############################################################
register_document_type(NeutralWS, 'iKaaro')
