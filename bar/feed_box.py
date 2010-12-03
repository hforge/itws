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
from itools.datatypes import String
# Import from ikaaro
from ikaaro.autoform import CheckboxWidget, SelectWidget, TextWidget

# Import from itws
from base import Box
from base_views import Box_View
from itws.datatypes import PositiveInteger
# XXX API public
from itws.tags import TagsList
from itws.tags.datatypes import TagsAwareClassEnumerate
from itws.feed_views import Feed_View
from itws.tags.utils import get_tagaware_items
from itws.widgets import DualSelectWidget




from itws.feed_views import Details_View
from itws.feed_views import FeedViews_Enumerate
class BoxFeed_View(Box_View, Details_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')

    view_name = 'feed-box'
    more_title = None

    # Configuration
    batch_template = None

#    def get_template_viewbox(self, resource, context):
#        # XXX To fix
#        # XXX move on same folder
#        template = resource.get_property('view')
#        if template == '1':
#            return '/ui/feed_views/NewsItem_preview.xml'
#        elif template == '2':
#            return '/ui/news/SectionNews_view.xml'
#        elif template == '3':
#            return '/ui/news/Tag_item_viewbox.xml'
#        return '/ui/common/Tag_item_viewbox.xml'


    def get_items(self, resource, context, *args):
        count = resource.get_property('count')
        tags = resource.get_property('tags')
        feed_class_id = resource.get_property('feed_class_id')
        return get_tagaware_items(context, formats=feed_class_id,
                  number=count, tags=tags, brain_and_docs=True)



    def sort_and_batch(self, resource, context, items):
        return items




class BoxFeed(Box):

    class_id = 'box-feed'
    class_title = MSG(u'Box to feed items')
    class_version = '20101119'
    class_icon16 = 'bar_items/icons/16x16/box_section_news.png'
    class_description = MSG(u'Display the last N items (Webpage/News) filtered by tags')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    class_schema = merge_dicts(Box.class_schema,
                               feed_class_id=TagsAwareClassEnumerate(source='metadata', multiple=True),
                               feed_source=String(source='metadata', multiple=True),
                               view=FeedViews_Enumerate(source='metadata'),
                               count=PositiveInteger(source='metadata', default=3),
                               tags=TagsList(source='metadata', multiple=True,
                                             default=[]))

    # Configuration
    allow_instanciation = True
    is_side = True
    is_content = True

    # Automatic Edit View
    edit_schema = {'feed_class_id': TagsAwareClassEnumerate(multiple=True),
                   'view': FeedViews_Enumerate,
                   'count': PositiveInteger(default=3),
                   'tags': TagsList(multiple=True)}


    edit_widgets = [CheckboxWidget('feed_class_id', title=MSG(u'Feed Source'),
                       has_empty_option=True),
        SelectWidget('view', title=MSG(u'Feed template')),
        TextWidget('count',
                   title=MSG(u'Number of items to show (0 = All)'), size=3),
        DualSelectWidget('tags', title=MSG(u'Show only items with this TAGS'),
                         is_inline=True, has_empty_option=False)]


    # Views
    view = BoxFeed_View()
