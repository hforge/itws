# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2009 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009 Romain Gauthier <romain@itaapy.com>
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
from decimal import Decimal

# Import from itools
from itools.core import get_abspath
from itools.csv import Property
from itools.datatypes import Unicode, String
from itools.fs import FileName
from itools.gettext import MSG
from itools.stl import stl
from itools.uri import get_reference, resolve_uri, Path
from itools.web import get_context
from itools.xapian import AndQuery, PhraseQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.database import ReadOnlyDatabase
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import stl_namespaces
from ikaaro.future.menu import MenuFolder, Menu
from ikaaro.future.order import ResourcesOrderedContainer, ResourcesOrderedTable
from ikaaro.registry import register_resource_class, register_document_type
from ikaaro.resource_views import DBResource_Backlinks
from ikaaro.skins import register_skin
from ikaaro.text import CSS
from ikaaro.tracker import Tracker, Issue
from ikaaro.website import WebSite as BaseWebSite
from ikaaro.wiki import WikiFolder, WikiPage
from ikaaro.workflow import WorkflowAware

# Import from itws
from addresses import AddressesFolder
from bar import ContentBarAware, SideBarAware, SideBar_View
from common import FoBoFooterAwareSkin
from datatypes import MultilingualString, NeutralClassSkin
from news import NewsFolder, NewsItem
from repository import Repository, SidebarItemsOrderedTable
from resources import Image, RobotsTxt
from rssfeeds import RssFeeds
from section import Section
from sitemap import SiteMap
from slides import SlideShow, Slide
from tags import TagsFolder
from tracker import ITWSTracker
from turning_footer import TurningFooterFolder
from utils import get_path_and_view, is_navigation_mode
from views import SmartOrderedTable_View
from webpage import WebPage
from website import WebSite
from ws_neutral_views import NeutralWS_ArticleNewInstance
from ws_neutral_views import NeutralWS_FOSwitchMode
from ws_neutral_views import NeutralWS_ManageView, WSDataFolder_ManageView
from ws_neutral_views import NeutralWS_View, NeutralWS_Edit
from ws_neutral_views import NotFoundPage, NeutralWS_RSS



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
         title="Go to edition mode">Go to edition mode</a>
      <a stl:if="edit_mode" href="/;fo_switch_mode?mode=0"
         title="Back to navigation">Back to navigation</a>
    </div>
    """, stl_namespaces))

    not_allowed_view_name_for_sidebar_view = ['not_found', 'about',
                                              'credits', 'license']
    not_allowed_cls_for_sidebar_view = [ITWSTracker, ITWSTracker.issue_class,
                                        WikiFolder, WikiPage, SlideShow, Slide,
                                        RssFeeds, AddressesFolder]
    manage_buttons = []

    def get_backoffice_class(self, context):
        # backoffice class
        here = context.resource
        bo_class = None
        current_view = context.view_name
        if current_view in ('edit', 'browse_content', 'preview_content',
                            'login', 'new_resource', 'backlinks', 'edit_state'):
            bo_class = 'backoffice'
        elif isinstance(here, (Tracker, Issue, CSS, MenuFolder, Menu)):
            bo_class = 'backoffice'
        elif isinstance(here, BaseWebSite):
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
        rss_title = MSG(u'{title} -- RSS Feeds').gettext(title=ws_title)
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
        site_root = here.get_site_root()
        sidebar_resource = site_root
        if isinstance(here, SideBarAware):
            sidebar_resource = here
        elif isinstance(here, SidebarItemsOrderedTable):
            sidebar_resource = here.parent
        elif isinstance(here, NewsItem) or\
                isinstance(here.parent, site_root.section_class):
            sidebar_resource = here.parent
        return sidebar_resource


    def build_namespace(self, context):
        namespace = FoBoFooterAwareSkin.build_namespace(self, context)

        here = context.resource
        site_root = here.get_site_root()

        # banner namespace
        banner_ns = {}
        banner_ns['title'] = site_root.get_property('banner_title')
        banner_ns['description'] = site_root.get_property('description')
        banner_path = site_root.get_property('banner_path')
        if banner_path:
            banner = site_root.get_resource(banner_path, soft=True)
            if banner:
                banner_path = context.get_link(banner)
            else:
                banner_path = None
        banner_ns['path'] = banner_path
        namespace['banner'] = banner_ns

        # site search
        text = context.get_form_value('site_search_text', type=Unicode)
        namespace['text'] = text.strip()

        # page id css
        class_id = getattr(here, 'class_id', None)
        if class_id:
            view_name = context.view_name or here.get_default_view_name()
            page_css_class = '%s-%s' % (class_id, view_name)
            page_css_class = page_css_class.replace('_', '-')
            namespace['page_css_class'] = page_css_class.lower()
        else:
            namespace['page_css_class'] = None

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
        if type(context.database) is ReadOnlyDatabase:
            body_css = 'read-only'
        namespace['body_css'] = body_css

        # Sidebar
        sidebar = None
        not_allowed = isinstance(here,
                                 tuple(self.not_allowed_cls_for_sidebar_view))
        navnfsv = self.not_allowed_view_name_for_sidebar_view
        if context.view_name not in navnfsv and not not_allowed:
            sidebar_resource = self.get_sidebar_resource(context)

            # When request path is /ui/xxx -> 404
            # site_root is the root resource, and it is not SidebarAware
            if sidebar_resource and isinstance(sidebar_resource, SideBarAware):
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
                         namespace={'edit_mode': edit_mode})
        namespace['fo_edit_toolbar'] = events

        return namespace


    def get_styles(self, context):
        styles = FoBoFooterAwareSkin.get_styles(self, context)
        if styles.count('/ui/aruni/aruni.css'):
            styles.remove('/ui/aruni/aruni.css')

        return styles



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
         title="Go to edition mode">Go to edition mode</a>
      <a stl:if="edit_mode" href="/;fo_switch_mode?mode=0"
         title="Back to navigation">Back to navigation</a>
    </td>
    """, stl_namespaces))



############################################################
# Web Site
############################################################
class WSDataFolder(Folder):

    class_id = 'neutral-ws-data'
    class_version = '20100519'
    class_title = MSG(u'Website data folder')
    __fixed_handlers__ = [SideBarAware.sidebar_name,
                          ContentBarAware.contentbar_name,
                          'order-resources' # FIXME
                         ]
    class_views = ['manage_view', 'backlinks', 'commit_log']

    order_contentbar = ContentBarAware.order_contentbar
    order_sidebar = SideBarAware.order_sidebar

    # Views
    manage_view = WSDataFolder_ManageView()
    order_articles = GoToSpecificDocument(specific_document='order-resources',
                                          title=MSG(u'Order the webpages'),
                                          access='is_allowed_to_edit')
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    backlinks = DBResource_Backlinks(access='is_allowed_to_edit')

    def get_editorial_documents_types(self):
        return [ self.parent.get_article_class() ]


    def get_document_types(self):
        return [ self.parent.get_article_class(), File ]


    def get_ordered_names(self, context=None):
        # proxy
        return self.parent.get_ordered_names(context)


    def update_20100519(self):
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        titles = []
        for language in languages:
            title = self.get_property('title', language)
            if title:
                titles.append(title)

        if not titles:
            self.set_property('title', MSG(u'Configure Homepage').gettext(),
                              languages[0])



class WSOrderedTable(ResourcesOrderedTable):

    class_id = 'neutral-ws-ordered-table'
    order_root_path = '..' # Parent ws-data folder

    view = SmartOrderedTable_View()
    # Order view title & description configuration
    ordered_view_title = MSG(u'Order Home "WebPages slot"')
    ordered_view_title_description = MSG(
            u'The HomePage has a "WebPages Slot", you can add several '
            u'WebPages to it and order them.')
    unordered_view_title = MSG(u'Available Webpages')
    unordered_view_title_description = MSG(
            u'These Webpages are available, '
            u'you can make them visible in the Home "WebPages slot" '
            u'by adding them to the ordered list.')

    def get_orderable_classes(self):
        return [ self.parent.parent.get_article_class() ]



class NeutralWS(SideBarAware, ContentBarAware, ResourcesOrderedContainer,
                WebSite):

    class_id = 'neutral'
    class_version = '20100531'
    class_title = MSG(u'neutral website')
    class_views = ['view', 'manage_view', 'edit_ws_data', 'browse_content',
                   'commit_log']

    sidebar_name = 'ws-data/%s' % SideBarAware.sidebar_name
    contentbar_name = 'ws-data/%s' % ContentBarAware.contentbar_name
    # Order Articles
    order_path = 'ws-data/order-resources'
    order_class = WSOrderedTable

    __fixed_handlers__ = (WebSite.__fixed_handlers__
                          + ['style', 'menu',
                             'footer', 'sitemap.xml', 'robots.txt',
                             'repository', 'images', 'turning-footer',
                             'tags', 'ws-data'])
    menus = ('menu',)
    footers = ('footer',)
    sitemap_class = SiteMap
    section_class = Section
    newsfolder_class = NewsFolder
    wsdatafolder_class = WSDataFolder

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        website_class = cls
        context = get_context()
        root = context.root
        # XXX How to choose language
        # TODO allow to choose language at website creation
        default_language = 'en'
        # Parent
        WebSite._make_resource(cls, folder, name, **kw)
        website = root.get_resource(name)
        # Add repository
        Repository._make_resource(Repository, folder,
                                  '%s/%s' % (name, 'repository'))
        # WSDataFolder
        cls2 = website_class.wsdatafolder_class
        cls2._make_resource(cls2, folder, '%s/ws-data' % name,
                title={default_language: MSG(u'Configure Homepage').gettext()})
        # Make the table for ResourcesOrderedContainer
        order_class = cls.order_class
        order_class._make_resource(order_class, folder,
                                   '%s/%s' % (name, cls.order_path))
        # SideBarAware
        SideBarAware._make_resource(cls, folder, name, **kw)
        # ContentBarAware
        ContentBarAware._make_resource(cls, folder, name, **kw)
        contentbar_table = root.get_resource(
                '%s/%s' % (name, cls.contentbar_name))
        item_name = Repository.website_articles_view_name
        contentbar_table.add_new_record({'name': item_name})
        # index
        section_class = cls.section_class
        section_class._make_resource(section_class, folder, '%s/index' % name,
                                     title={'en': u'Index'})
        # Add a sitemap
        cls = website_class.sitemap_class
        cls._make_resource(cls, folder, '%s/sitemap.xml' % name)
        # Add Robots.txt
        RobotsTxt._make_resource(RobotsTxt, folder, '%s/robots.txt' % name)
        # Add an image folder
        Folder._make_resource(Folder, folder, '%s/%s' % (name, 'images'))
        # Add the banner
        banner_resource = root.get_resource('/ui/neutral/banner.png')
        banner_data = banner_resource.to_str()
        cls = Image
        filename = name2 = 'banner.png'
        name2, extension, language = FileName.decode(name2)
        metadata = {'format': 'image/png', 'filename': filename,
                'extension': extension, 'state': 'public',
                'body': banner_data}
        cls._make_resource(cls, folder, '%s/images/%s' % (name, name2),
                **metadata)
        # Set a default banner
        if 'banner_title' not in kw:
            vhosts = website.get_property('vhosts')
            if vhosts:
                banner_title = vhosts[0]
            else:
                banner_title = website.get_title()
            website.set_property('banner_title', banner_title,
                                 language=default_language)
        # Turning footer
        cls = TurningFooterFolder
        cls._make_resource(cls, folder, '%s/turning-footer' % name)
        # Tags
        cls = TagsFolder
        cls._make_resource(cls, folder, '%s/tags' % name)
        # Init Website menu with 2 items
        for menu_name in website_class.menus:
            menu = root.get_resource('%s/%s/menu' % (name, menu_name))
            title = Property(MSG(u'Homepage').gettext(),
                             language=default_language)
            menu.add_new_record({'title': title, 'path': '/'})
            title = Property(MSG(u'Contact').gettext(),
                             language=default_language)
            menu.add_new_record({'title': title, 'path': '/;contact'})
        # Init Website footer with 2 items
        for footer_name in website_class.footers:
            menu = root.get_resource('%s/%s/menu' % (name, footer_name))
            title = Property(MSG(u'About').gettext(),
                             language=default_language)
            menu.add_new_record({'title': title, 'path': '/;about'})
            title = Property(MSG(u'Contact us').gettext(),
                             language=default_language)
            menu.add_new_record({'title': title, 'path': '/;contact'})


    @classmethod
    def get_orderable_classes(cls):
        return (cls, Section)


    @classmethod
    def get_metadata_schema(cls):
        schema = WebSite.get_metadata_schema()
        schema['breadcrumb_title'] = Unicode
        schema['banner_title'] = Unicode(default='')
        schema['banner_path'] = MultilingualString(default='')
        schema['class_skin'] = NeutralClassSkin(default='ui/k2')
        schema['date_of_writing_format'] = String(default='')

        return schema


    def get_class_skin(self):
        return self.get_property('class_skin')

    class_skin = property(get_class_skin, None, None, '')


    def get_editorial_documents_types(self):
        # FIXME Should be merge with get_document_types
        types = [SlideShow, AddressesFolder, WebPage]
        if self.section_class:
            types.append(self.section_class)
        if self.newsfolder_class:
            types.append(self.newsfolder_class)
        return types


    def get_document_types(self):
        types = []
        for _type in WebSite.get_document_types(self):
            if _type is Tracker:
                types.append(ITWSTracker)
            else:
                types.append(_type)
        # News Folder can only be instanciated once
        if self.newsfolder_class:
            if self.get_news_folder(get_context()) is None:
                types.append(self.newsfolder_class)

        return types + [Section, SlideShow, RssFeeds, AddressesFolder]


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
        query = [PhraseQuery('parent_path', str(abspath)),
                 PhraseQuery('format', self.newsfolder_class.class_id)]
        query = AndQuery(*query)
        # Search
        results = context.root.search(query, sort_by='name')
        if len(results):
            database = context.database
            doc = results.get_documents()[0]
            path = doc.abspath
            if type(context.database) is not ReadOnlyDatabase:
                path = database.resources_old2new.get(path, path)
            return self.get_resource(path)
        return None


    def format_date(self, value, language=None):
        if not value:
            return value
        if language is None:
            language = self.get_content_language(get_context())
        format = self.get_property('date_of_writing_format', language=language)
        if format:
            return value.strftime(format)
        return value


    def get_article_class(self):
        # ContentBarItem_Articles_View API
        return WebPage


    def get_links(self):
        links = WebSite.get_links(self)

        base = self.get_abspath()
        available_languages = self.get_property('website_languages')

        for lang in available_languages:
            path = self.get_property('banner_path', language=lang)
            if not path:
                continue
            ref = get_reference(path)
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                links.append(str(base.resolve2(path)))

        return links


    def update_links(self, source, target):
        WebSite.update_links(self, source, target)
        # Caution multilingual banner_path
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        available_languages = self.get_property('website_languages')
        for lang in available_languages:
            path = self.get_property('banner_path', language=lang)
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
                self.set_property('banner_path', str(new_ref), language=lang)

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        WebSite.update_relative_links(self, source)
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new
        # Caution multilingual banner_path
        available_languages = self.get_property('website_languages')
        for lang in available_languages:
            path = self.get_property('banner_path', language=lang)
            if path:
                ref = get_reference(str(path))
                if not ref.scheme:
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
                    # Update the title link
                    self.set_property('banner_path', str(new_ref),
                                      language=lang)


    ############################################################################
    # ACL
    ############################################################################
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


    def update_20100429(self):
        webpage_cls = self.get_article_class()
        print
        for resource in self.traverse_resources():
            metadata = resource.metadata
            if metadata.format in ('article', 'ws-neutral-article'):
                print u'Fix %s' % resource.get_abspath()
                metadata.set_changed()
                metadata.format = webpage_cls.class_id
                metadata.version = webpage_cls.class_version


    def update_20100503(self):
        self.del_property('rss_feeds_items_format')
        self.del_property('rss_feeds_max_items_number')


    def update_20100518(self):
        # XXX
        metadata = self.metadata
        properties = metadata.properties
        if 'class_skin' in properties is False:
            # Set old default value
            self.set_property('class_skin', '/ui/neutral')


    def update_20100531(self):
        WebSite.update_20100524(self)


    # User Interface
    edit_ws_data = GoToSpecificDocument(
            specific_document='ws-data', title=MSG(u'Manage home page content'),
            access='is_allowed_to_edit')
    edit_menu = GoToSpecificDocument(
            specific_document='menu/menu',
            title=MSG(u'Menu'), access='is_allowed_to_edit')
    edit_turning_footer = GoToSpecificDocument(
            specific_document='turning-footer',
            title=MSG(u'Turning Footer'), access='is_allowed_to_edit')
    edit_footer = GoToSpecificDocument(
            specific_document='footer/menu',
            title=MSG(u'Footer'), access='is_allowed_to_edit')
    view = NeutralWS_View()
    manage_view = NeutralWS_ManageView()
    # Helper
    add_new_article = NeutralWS_ArticleNewInstance()
    fo_switch_mode = NeutralWS_FOSwitchMode()
    # Order
    order_items = GoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document='ws-data/order-resources',
        title=MSG(u'Order webpages'))
    order_contentbar = GoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=contentbar_name,
        title=MSG(u'Order the "central part" items'))
    order_sidebar = GoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=sidebar_name,
        title=MSG(u'Order the sidebar items'))
    # Compatibility
    rss = last_news_rss = NeutralWS_RSS()
    edit_tags = GoToSpecificDocument(specific_document='tags',
                                     specific_view='browse_content',
                                     access='is_allowed_to_edit',
                                     title=MSG(u'Edit tags'))
    edit = NeutralWS_Edit()
    not_found = NotFoundPage()



############################################################
# Register
############################################################
register_resource_class(Image)
register_resource_class(NeutralWS)
register_resource_class(WSDataFolder)
register_resource_class(WSOrderedTable)
register_document_type(NeutralWS, BaseWebSite.class_id)

# Skin
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
