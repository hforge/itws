# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from standard library
import re

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Integer, String
from itools.fs import vfs
from itools.gettext import MSG
from itools.rss import RSSFile
from itools.xml import XMLParser, XMLError

# Import from ikaaro
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import BarItem, register_bar_item
from itws.repository_views import BarItem_View



twitter_url = 'http://twitter.com/statuses/user_timeline/%s.rss'

def transform_links(tweet):
    tweet = tweet.split(':', 1)[1]
    tweet = re.sub(r'(\A|\s)@(\w+)',
                   r'\1@<a href="http://www.twitter.com/\2">\2</a>', tweet)
    tweet = re.sub(r'(\A|\s)#(\w+)',
               r'\1#<a href="http://search.twitter.com/search?q=%23\2">\2</a>',
               tweet)
    tweet = re.sub(r'(\A|\s)(http://(\w|\.|/|\?|=|%|&|-)+)',
                   r'\1<a href="\2"> \2</a>', tweet)
    tweet = re.sub('&', '&amp;', tweet)
    return XMLParser(tweet.encode('utf-8'))


class TwitterSideBar_View(BarItem_View):

    template = '/ui/bar_items/twitter.xml'

    def get_namespace(self, resource, context):
        namespace = {'title': resource.get_title(),
                     'user_name': resource.get_property('user_name'),
                     'twitts': []}
        user_id = resource.get_property('user_id')
        limit = resource.get_property('limit')
        try:
            f = vfs.open(twitter_url % user_id)
        except Exception:
            return namespace
        try:
            feed = RSSFile(string=f.read())
        except XMLError:
            return namespace
        for i, item in enumerate(feed.items):
            if i == limit:
                break
            data = transform_links(item['description'])
            namespace['twitts'].append(data)
        return namespace



class TwitterSideBar(BarItem):

    class_id = 'sidebar-item-twitter'
    class_title = MSG(u'Twitter SideBar')
    class_description = MSG(u'Twitter sidebar feed')
    class_icon16 = 'bar_items/icons/16x16/twitter.png'
    class_icon48 = 'bar_items/icons/48x48/twitter.png'
    # Free twitter icon
    #http://www.webdesignerdepot.com/2009/07/50-free-and-exclusive-twitter-icons/

    # Item configuration
    item_schema = {'user_id': Integer(mandatory=True),
                   'user_name': String(mandatory=True),
                   'limit': Integer(mandatory=True, default=5)}


    item_widgets = [TextWidget('user_name', title=MSG(u"Twitter account name")),
                    TextWidget('user_id', title=MSG(u"User Id")),
                    TextWidget('limit', title=MSG(u'Number of tweet'))]

    # Views
    view = TwitterSideBar_View()


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(BarItem.get_metadata_schema(),
                           cls.item_schema)



register_resource_class(TwitterSideBar)
register_bar_item(TwitterSideBar, allow_instanciation=True)
