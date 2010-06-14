# -*- coding: UTF-8 -*-
# Copyright (C) 2007, 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
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

# ws_neutral.NeutralWS.update_20100429
# Remove Obsolete article class
from itools.web import STLView
from ikaaro.registry import register_resource_class
from webpage import WebPage
from repository import register_box, Box
from repository import BoxSectionNews, BoxTags
from repository import BoxSectionChildrenToc, BoxNewsSiblingsToc
from repository import BoxSectionWebpages, BoxWebsiteWebpages
from repository import ContentBoxSectionChildrenToc, SidebarBoxesOrderedTable
from repository import ContentbarBoxesOrderedTable
from sidebar import TwitterSideBar, MenuSideBar

class Article(WebPage):
    class_id = 'article'
    class_version = '20100107'

class WSArticle(Article):
    class_id = 'ws-neutral-article'

class SidebarItem(WebPage):
    class_id = 'sidebar-item'
    class_version = '20091127'

class SidebarItem_SectionSiblingsToc(STLView):

    def GET(self, resource, context):
        return None

    def set_view_is_empty(self, bool):
        return

    def get_view_is_empty(self):
        return True

class SidebarItem_SectionSiblingsToc(Box):
    class_id = 'sidebar-item-section-siblings-toc'
    view = SidebarItem_SectionSiblingsToc()

# update 20100611
class BarItem_Section_News(BoxSectionNews):
    class_id = 'sidebar-item-section-news'
class SidebarItem_Tags(BoxTags):
    class_id = 'sidebar-item-tags'
class SidebarItem_SectionChildrenToc(BoxSectionChildrenToc):
    class_id = 'sidebar-item-section-children-toc'
class SidebarItem_NewsSiblingsToc(BoxNewsSiblingsToc):
    class_id = 'sidebar-item-news-siblings-toc'
class ContentBarItem_Articles(BoxSectionWebpages):
    class_id = 'contentbar-item-articles'
class ContentBarItem_WebsiteArticles(BoxWebsiteWebpages):
    class_id = 'ws-neutral-item-articles'
class ContentBarItem_SectionChildrenToc(ContentBoxSectionChildrenToc):
    class_id = 'contentbar-item-children-toc'
class SidebarItemsOrderedTable(SidebarBoxesOrderedTable):
    class_id = 'sidebar-items-ordered-table'
class ContentbarItemsOrderedTable(ContentbarBoxesOrderedTable):
    class_id = 'contentbar-items-ordered-table'
class OldTwitterSideBar(TwitterSideBar):
    class_id = 'sidebar-item-twitter'
class OldMenuSideBar(MenuSideBar):
    class_id = 'sidebar-item-menu'

register_resource_class(Article)
register_resource_class(SidebarItem)
register_resource_class(SidebarItem_SectionSiblingsToc)
register_resource_class(WSArticle)
# update 20100611
register_resource_class(BarItem_Section_News)
register_resource_class(SidebarItem_Tags)
register_resource_class(SidebarItem_SectionChildrenToc)
register_resource_class(SidebarItem_NewsSiblingsToc)
register_resource_class(ContentBarItem_Articles)
register_resource_class(ContentBarItem_WebsiteArticles)
register_resource_class(ContentBarItem_SectionChildrenToc)
register_resource_class(SidebarItemsOrderedTable)
register_resource_class(ContentbarItemsOrderedTable)
register_resource_class(OldTwitterSideBar)
register_resource_class(OldMenuSideBar)

register_box(SidebarItem, allow_instanciation=True, is_content=True)
register_box(SidebarItem_SectionSiblingsToc, allow_instanciation=False)
# update 20100611
register_box(BarItem_Section_News)
register_box(SidebarItem_Tags)
register_box(SidebarItem_SectionChildrenToc)
register_box(SidebarItem_NewsSiblingsToc)
register_box(ContentBarItem_Articles)
register_box(ContentBarItem_WebsiteArticles)
register_box(ContentBarItem_SectionChildrenToc)
register_box(SidebarItemsOrderedTable)
register_box(ContentbarItemsOrderedTable)
register_box(OldTwitterSideBar)
register_box(OldMenuSideBar)
