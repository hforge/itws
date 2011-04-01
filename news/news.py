# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@itaapy.com>
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
from itools.core import freeze, get_abspath, merge_dicts
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.datatypes import Multilingual
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.autoform import TextWidget
from ikaaro.registry import register_document_type
from ikaaro.skins import register_skin

# Import from itws
from itws.bar import SideBarAware
from itws.control_panel import CPDBResource_CommitLog, CPDBResource_Links
from itws.control_panel import CPDBResource_Backlinks
from itws.control_panel import ITWS_ControlPanel
from itws.datatypes import PositiveIntegerNotNull
from itws.tags import register_tags_aware
from itws.views import AutomaticEditView
from itws.webpage import WebPage
from news_views import NewsFolder_View, NewsFolder_RSS
from news_views import NewsItem_AddImage, NewsFolder_BrowseContent
from news_views import NewsItem_Edit, NewsItem_View



###########################################################################
# Resources
###########################################################################
class NewsItem(WebPage):

    class_id = 'news'
    class_version = '20100811'
    class_title = MSG(u'News')
    class_description = MSG(u'News is a webpage with a small description '
                            u'used by the News Folder, News can be tagged')
    class_icon16 = 'news/icons/16x16/news_folder.png'
    class_icon48 = 'news/icons/48x48/news_folder.png'
    class_views = ['view', 'edit', 'control_panel']


    class_schema = merge_dicts(WebPage.class_schema,
             long_title=Multilingual(source='metadata'))


    def init_resource(self, **kw):
        # Initialize parent class
        super(NewsItem, self).init_resource(**kw)
        # Set pub_datetime
        dt = get_context().timestamp
        self.set_property('pub_datetime', dt)


    ##############
    # API
    ###############
    def get_long_title(self, language=None):
        """Return the long_title or the title"""
        long_title = self.get_property('long_title', language=language)
        if long_title:
            return long_title
        return self.get_title()


    def can_paste_into(self, target):
        return isinstance(target, NewsFolder)


    def update_20100811(self):
        """Set pub_datetime is not already set"""
        value = self.get_property('pub_datetime')
        if value:
            return
        # set pub_datetime
        mtime = self.get_property('mtime')
        self.set_property('pub_datetime', mtime)


    #####################
    # Views
    #####################
    edit = NewsItem_Edit()
    view = NewsItem_View()
    add_image = NewsItem_AddImage()



class NewsFolder(SideBarAware, Folder):

    class_id = 'news-folder'
    class_version = '20100621'
    class_title = MSG(u'News Folder')
    class_description = MSG(u'News Folder contains news ordered  '
                            u'by date of writing')
    class_icon16 = 'news/icons/16x16/news_folder.png'
    class_icon48 = 'news/icons/48x48/news_folder.png'
    class_views = ['view', 'edit', 'browse_content', 'control_panel']

    class_control_panel = ['backlinks', 'commit_log']

    class_schema = merge_dicts(
          SideBarAware.class_schema,
          Folder.class_schema,
          batch_size=PositiveIntegerNotNull(source='metadata', default=7))


    __fixed_handlers__ = (SideBarAware.__fixed_handlers__ +
                          Folder.__fixed_handlers__ + ['images'])

    # Configuration
    news_class = NewsItem

    # Configuration of automatic edit view
    edit_show_meta = True
    edit_schema =  freeze({'batch_size': PositiveIntegerNotNull})
    edit_widgets = freeze([
        TextWidget('batch_size', title=MSG(u'Batch size'), size=3)])


    def init_resource(self, **kw):
        Folder.init_resource(self, **kw)
        # Sidebar
        SideBarAware.init_resource(self, **kw)
        # Create images folder
        self.make_resource('images', Folder)


    def get_catalog_values(self):
        return merge_dicts(Folder.get_catalog_values(self),
                           SideBarAware.get_catalog_values(self))


    def get_document_types(self):
        return [self.news_class]

    ##########################
    # Views
    ##########################

    view = NewsFolder_View()
    edit = AutomaticEditView()
    browse_content = NewsFolder_BrowseContent(access='is_allowed_to_edit',
                                              title=MSG(u'Browse'))
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    rss = NewsFolder_RSS()
    control_panel = ITWS_ControlPanel()

    # Control panel
    commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')
    links = CPDBResource_Links()
    backlinks = CPDBResource_Backlinks()



# Register
register_document_type(NewsItem, NewsFolder.class_id)
register_tags_aware(NewsItem)

# Register skin
register_skin('news', get_abspath('../ui/news'))
