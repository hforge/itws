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
from itools.core import merge_dicts
from itools.gettext import MSG
from itools.uri import encode_query
from itools.web import BaseView

# Import from ikaaro
from ikaaro.autoform import TextWidget
from ikaaro.resource_views import DBResource_Edit
from ikaaro.webpage import WebPage_View

# Import from itws
from base import Box
from base_views import Box_View, Box_Preview
#from toc import ContentBoxSectionNews_View
from itws.datatypes import PositiveInteger
from itws.tags import TagsList
from itws.utils import to_box
from itws.widgets import DualSelectWidget


class BoxNewsSiblingsToc_Preview(Box_Preview):

    def get_details(self, resource, context):
        return [u'Useful in a news folder, show a Table of Content '
                u'with all news.']

class BoxSectionNews_Preview(Box_Preview):

    def get_details(self, resource, context):
        details = []
        for key in ('count', 'tags'):
            value = resource.get_property(key)
            details.append(u'%s: %s' % (key, value))
        return details





class SidebarBox_Preview(BaseView):
    title = MSG(u'Preview')

    def GET(self, resource, context):
        return to_box(resource, WebPage_View().GET(resource, context))


class BoxSectionNews_View(Box_View):

    access = 'is_allowed_to_edit'
    template = '/ui/bar_items/SectionNews_view.xml'
    title = MSG(u'View')

    # Configuration
    more_title = MSG(u'Show all')
    thumb_width = thumb_height = 96

    def _get_news_item_view(self):
        from itws.news.news_views import NewsItem_Preview
        return NewsItem_Preview()


    def _get_news_folder(self, resource, context):
        site_root = resource.get_site_root()
        news_folder = site_root.get_news_folder(context)
        return news_folder


    def _get_items(self, resource, context, news_folder):
        count = resource.get_property('count')
        tags = resource.get_property('tags')
        return news_folder.get_news(context, number=count, tags=tags)


    def _get_items_ns(self, resource, context, render=True):
        news_folder = self._get_news_folder(resource, context)
        items = self._get_items(resource, context, news_folder)

        view = self._get_news_item_view()
        ns_items = []
        for item in items:
            if render:
                ns_items.append(view.GET(item, context))
            else:
                ns_items.append(view.get_namespace(item, context))

        return ns_items


    def get_namespace(self, resource, context):
        namespace = {}

        # News title and items
        news_folder = self._get_news_folder(resource, context)
        # no news folder
        title = resource.get_property('title')
        items = []
        items_number = 0
        if news_folder:
            news_count = resource.get_property('count')
            # if news_count == 0, do not display all news
            if news_count:
                items = self._get_items_ns(resource, context, render=False)
                items_number = len(items)
                if items:
                    # Add 'first' and 'last' css classes
                    for i in xrange(items_number):
                        items[i]['css'] = ''
                    items[0]['css'] += ' first'
                    items[-1]['css'] += ' last'

        if items_number == 0 and self.is_admin(resource, context) is False:
            # Hide the box if there is no news and
            # if the user cannot edit the box
            self.set_view_is_empty(True)

        site_root = resource.get_site_root()
        namespace['newsfolder'] = news_folder
        newfolder_cls_title = site_root.newsfolder_class.class_title
        namespace['newsfolder_cls_title'] = newfolder_cls_title
        namespace['title'] = title
        namespace['items'] = items
        namespace['display'] = items_number != 0
        # more link
        more_link = None
        if news_folder:
            more_title = self.more_title.gettext().encode('utf-8')
            tags = resource.get_property('tags')
            link = context.get_link(news_folder)
            if tags:
                # FIXME Do not add tags to query if all tags are selected
                query =  {'tag': tags}
                link = '%s?%s' % (link, encode_query(query))
            more_link = {'href': link, 'title': more_title}
        namespace['more'] = more_link
        # Thumbnail configuration
        namespace['thumb_width'] = self.thumb_width
        namespace['thumb_height'] = self.thumb_height

        return namespace


class BoxSectionNews_Edit(DBResource_Edit):

    def _get_news_folder(self, resource, context):
        site_root = resource.get_site_root()
        news_folder = site_root.get_news_folder(context)
        return news_folder


    def _get_schema(self, resource, context):
        schema = merge_dicts(
            DBResource_Edit._get_schema(self, resource, context),
            count=PositiveInteger(default=3))
        # News folder
        newsfolder = self._get_news_folder(resource, context)
        if newsfolder:
            # Count is already defined in resource.edit_schema
            # Do not add it but override 'tags' definition
            site_root = resource.get_site_root()
            # tags
            tags = site_root.get_resource('tags')
            sub_schema = {}
            if len(tags.get_tag_brains(context)):
                tags = TagsList(news_folder=newsfolder, multiple=True,
                                site_root=site_root)
                sub_schema['tags'] = tags

            return merge_dicts(schema, sub_schema)
        return schema


    def get_widgets(self, resource, context):
        # base widgets
        widgets = DBResource_Edit.get_widgets(self, resource, context)[:]

        # News folder
        newsfolder = self._get_news_folder(resource, context)
        if newsfolder:
            widgets.append(TextWidget('count', title=MSG(u'News to show'),
                                      size=3))
            # tags
            tags = resource.get_site_root().get_resource('tags')
            if len(tags.get_tag_brains(context)):
                widget = DualSelectWidget('tags', title=MSG(u'News TAGS'),
                        is_inline=True, has_empty_option=False)
                widgets.append(widget)

        return widgets


class BoxSectionNews(Box):

    class_id = 'box-section-news'
    class_title = MSG(u'Last News Box (Sidebar)')
    class_icon16 = 'bar_items/icons/16x16/box_section_news.png'
    class_description = MSG(u'Display the last N news filtered by tags')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    class_schema = merge_dicts(Box.class_schema,
                               count=PositiveInteger(source='metadata', default=3),
                               tags=TagsList(source='metadata'))

    # Configuration
    allow_instanciation = True
    is_side = True
    is_content = False

    # Views
    preview = order_preview = BoxSectionNews_Preview()
    view = BoxSectionNews_View()
    edit = BoxSectionNews_Edit()



class ContentBoxSectionNews(BoxSectionNews):

    class_id = 'contentbar-box-section-news'
    class_title = MSG(u'Last News Box (Contentbar)')

    allow_instanciation = True
    is_content = True
    is_side = False

    # XXX migration
    #view = ContentBoxSectionNews_View()



