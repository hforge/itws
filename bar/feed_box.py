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
from itools.core import freeze, merge_dicts
from itools.gettext import MSG
from itools.database import OrQuery, PhraseQuery
from itools.datatypes import Enumerate, String

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget, SelectWidget, TextWidget

# Import from itws
from base import Box
from base_views import Box_View
from itws.datatypes import PositiveInteger
from itws.tags import TagsList, TagsAwareClassEnumerate
from itws.widgets import DualSelectWidget

# XXX We have to refactor BoxFeed_View
from itws.feed_views import Details_View


class BoxFeed_Enumerate(Enumerate):

    options = [
      {'name': '/ui/feed_views/Tag_item_viewbox.xml', 'value': MSG(u'V3')},
#      {'name': '/ui/news/SectionNews_view.xml', 'value': MSG(u'V2')},
      {'name': '/ui/feed_views/NewsItem_preview.xml', 'value': MSG(u'V1')}]


class BoxFeed_View(Box_View, Details_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    template = '/ui/bar_items/BoxFeed_view.xml'

    view_name = 'feed-box'

    # Configuration
    batch_template = None

    search_on_current_folder = False
    search_on_current_folder_recursive = False

    specific_id_wrapper = False


    def get_query_schema(self):
        return {}


    @property
    def table_template(self):
        view_resource = self.view_resource
        return view_resource.get_property('view')


    def get_items(self, resource, context, *args):
        args = list(args)
        tags = resource.get_property('tags')
        if tags:
            args.append(OrQuery(*[PhraseQuery('tags', x) for x in tags]))
        formats = resource.get_property('feed_class_id')
        if formats:
            args.append(OrQuery(*[PhraseQuery('format', x) for x in formats]))
        return Details_View.get_items(self, resource, context, *args)


    def sort_and_batch(self, resource, context, results):
        root = context.root
        user = context.user
        items = results.get_documents(sort_by='pub_datetime',
                                      reverse=True,
                                      start=0,
                                      size=resource.get_property('count'))
        # Access Control (FIXME this should be done before batch)
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))
        return allowed_items



class BoxFeed(Box):

    class_id = 'box-feed'
    class_title = MSG(u'Box to feed items')
    class_version = '20101228'
    class_icon16 = 'bar_items/icons/16x16/box_section_news.png'
    class_description = MSG(u'Display the last N items (Webpage/News) filtered by tags')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    class_schema = merge_dicts(Box.class_schema,
                               feed_class_id=TagsAwareClassEnumerate(source='metadata', multiple=True),
                               feed_source=String(source='metadata', multiple=True),
                               view=BoxFeed_Enumerate(source='metadata'),
                               count=PositiveInteger(source='metadata', default=3),
                               tags=TagsList(source='metadata', multiple=True,
                                             default=[]))

    # Configuration
    allow_instanciation = True
    is_side = True
    is_content = True

    # Automatic Edit View
    edit_schema = freeze(
            {'feed_class_id': TagsAwareClassEnumerate(multiple=True),
             'view': BoxFeed_Enumerate,
             'count': PositiveInteger(default=3),
             'tags': TagsList(multiple=True)})


    edit_widgets = freeze([
        CheckboxWidget('feed_class_id', title=MSG(u'Feed Source'),
                       has_empty_option=True),
        SelectWidget('view', title=MSG(u'Feed template'),
                     has_empty_option=False),
        TextWidget('count',
                   title=MSG(u'Number of items to show (0 = All)'), size=3),
        DualSelectWidget('tags', title=MSG(u'Show only items with this TAGS'),
                         is_inline=True, has_empty_option=False)])


    # Views
    view = BoxFeed_View()


    def update_20101228(self):
        # XXX Update for developers
        self.set_property('view', '/ui/feed_views/Tag_item_viewbox.xml')
