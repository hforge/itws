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

# Import from itools
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from itws
from repository import BoxSectionChildrenToc, BoxNewsSiblingsToc
from repository import BoxSectionNews, BoxTags
from repository import ContentBoxSectionChildrenToc, SidebarBoxesOrderedTable
from repository import ContentbarBoxesOrderedTable
from repository import register_box, Box
from repository_views import Box_View
from sidebar import TwitterSideBar, MenuSideBar
from webpage import WebPage


################################################################################
# Update changement fonctionnement section and ws-data
################################################################################
class BoxSectionWebpages(Box):

    class_id = 'contentbar-box-articles'
    view = Box_View()

    def get_admin_edit_link(self, context):
        return './order-section'



class BoxWebsiteWebpages(BoxSectionWebpages):

    class_id = 'ws-neutral-box-articles'
    class_title = MSG(u"Website's Webpages")
    class_description = MSG(u'Display the ordered webpages of the homepage')
    view = Box_View()

    def get_admin_edit_link(self, context):
        return '/ws-data/order-resources'



register_resource_class(BoxSectionWebpages)
register_resource_class(BoxWebsiteWebpages)

register_box(BoxSectionWebpages, allow_instanciation=False,
             is_content=True, is_side=False)
register_box(BoxWebsiteWebpages, allow_instanciation=False,
             is_content=True, is_side=False)


################################################################################

# ws_neutral.NeutralWS.update_20100429
# Remove Obsolete article class
class Article(WebPage):
    class_id = 'article'
    class_version = '20100107'

class WSArticle(Article):
    class_id = 'ws-neutral-article'

class SidebarItem(WebPage):
    class_id = 'sidebar-item'
    class_title = MSG(u'HTML Content (obsolete)')
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
    class_title = MSG(u'Old box (obsolete)')
    view = SidebarItem_SectionSiblingsToc()

# update 20100611
class BarItem_Section_News(BoxSectionNews):
    class_id = 'sidebar-item-section-news'
    class_title = MSG(
        u'%s (obsolete)' % BoxSectionNews.class_title.gettext())
class SidebarItem_Tags(BoxTags):
    class_id = 'sidebar-item-tags'
    class_title = MSG(
        u'%s (obsolete)' % BoxTags.class_title.gettext())
class SidebarItem_SectionChildrenToc(BoxSectionChildrenToc):
    class_id = 'sidebar-item-section-children-toc'
    class_title = MSG(
        u'%s (obsolete)' % BoxSectionChildrenToc.class_title.gettext())
class SidebarItem_NewsSiblingsToc(BoxNewsSiblingsToc):
    class_id = 'sidebar-item-news-siblings-toc'
    class_title = MSG(
        u'%s (obsolete)' % BoxNewsSiblingsToc.class_title.gettext())
class ContentBarItem_Articles(BoxSectionWebpages):
    class_id = 'contentbar-item-articles'
    class_title = MSG(
        u'%s (obsolete)' % BoxSectionWebpages.class_title.gettext())
class ContentBarItem_WebsiteArticles(BoxWebsiteWebpages):
    class_id = 'ws-neutral-item-articles'
    class_title = MSG(
        u'%s (obsolete)' % BoxWebsiteWebpages.class_title.gettext())
class ContentBarItem_SectionChildrenToc(ContentBoxSectionChildrenToc):
    class_id = 'contentbar-item-children-toc'
    class_title = MSG(
        u'%s (obsolete)' % ContentBoxSectionChildrenToc.class_title.gettext())
class SidebarItemsOrderedTable(SidebarBoxesOrderedTable):
    class_id = 'sidebar-items-ordered-table'
    class_title = MSG(
        u'%s (obsolete)' % SidebarBoxesOrderedTable.class_title.gettext())
class ContentbarItemsOrderedTable(ContentbarBoxesOrderedTable):
    class_id = 'contentbar-items-ordered-table'
    class_title = MSG(
        u'%s (obsolete)' % ContentbarBoxesOrderedTable.class_title.gettext())
class OldTwitterSideBar(TwitterSideBar):
    class_id = 'sidebar-item-twitter'
    class_title = MSG(
        u'%s (obsolete)' % TwitterSideBar.class_title.gettext())
class OldMenuSideBar(MenuSideBar):
    class_id = 'sidebar-item-menu'
    class_title = MSG(
        u'%s (obsolete)' % MenuSideBar.class_title.gettext())

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
register_box(ContentBarItem_Articles, is_side=False, is_content=True)
register_box(ContentBarItem_WebsiteArticles, is_side=False, is_content=True)
register_box(ContentBarItem_SectionChildrenToc, is_side=False, is_content=True)
register_box(SidebarItemsOrderedTable)
register_box(ContentbarItemsOrderedTable, is_side=False, is_content=True)
register_box(OldTwitterSideBar)
register_box(OldMenuSideBar)



