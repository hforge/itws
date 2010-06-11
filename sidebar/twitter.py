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
from datetime import datetime
from traceback import format_exc
import re
import socket
import urllib2

# Import from itools
from itools import __version__ as itools_version
from itools.core import merge_dicts
from itools.datatypes import Integer, String, XMLContent, Boolean
from itools.gettext import MSG
from itools.log import log_error
from itools.rss import RSSFile
from itools.web import FormError
from itools.xml import XMLParser, XMLError

# Import from ikaaro
from ikaaro.forms import TextWidget, CheckBoxWidget
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import BarItem, register_box
from itws.repository_views import BarItem_View, BarItem_Edit
from itws.resources import ResourceWithCache



twitter_url = 'http://twitter.com/statuses/user_timeline/%s.rss'

def transform_links(tweet):
    tweet = tweet.split(':', 1)[1]
    tweet = re.sub(r'(\A|\s)@(\w+)',
                   r'\1@<a href="http://www.twitter.com/\2">\2</a>', tweet)
    tweet = re.sub(r'(\A|\s)#(\w+)',
               r'\1#<a href="http://search.twitter.com/search?q=%23\2">\2</a>',
               tweet)
    tweet = re.sub(r'(\A|\s)(http://(\w|\.|/|;|\?|=|%|&|-)+)',
                   r'\1<a href="\2"> \2</a>', tweet)
    tweet = re.sub('&', '&amp;', tweet)
    return XMLParser(tweet.encode('utf-8'))




class TwitterSideBar_Edit(BarItem_Edit):

    def _get_form(self, resource, context):
        form = BarItem_Edit._get_form(self, resource, context)
        # Check if the user_id exists
        user_id = form['user_id']
        uri = twitter_url % user_id

        # FIXME To improve
        # NOTE urllib2 only proposes GET/POST but not HEAD
        try:
            req = urllib2.Request(uri)
            req.add_header('User-Agent', 'itools/%s' % itools_version)
            response = urllib2.urlopen(req)
            data = response.read()
        except (socket.error, socket.gaierror, Exception,
                urllib2.HTTPError), e:
            raise FormError(invalid=['user_id'])

        return form


    def action(self, resource, context, form):
        BarItem_Edit.action(self, resource, context, form)
        if context.edit_conflict:
            return
        if form['force_update']:
            resource._update_data()



class TwitterSideBar_View(BarItem_View):

    template = '/ui/bar_items/twitter.xml'

    def get_namespace(self, resource, context):
        namespace = {'title': resource.get_title(),
                     'user_name': resource.get_property('user_name'),
                     'twitts': []}
        twitts, errors = resource.get_cached_data()
        ac = resource.get_access_control()
        is_allowed_to_edit = ac.is_allowed_to_edit(context.user, resource)
        namespace['twitts'] = twitts
        namespace['errors'] = is_allowed_to_edit and errors
        return namespace



class TwitterSideBar(BarItem, ResourceWithCache):

    class_id = 'sidebar-item-twitter'
    class_title = MSG(u'Twitter SideBar')
    class_description = MSG(u'Twitter sidebar feed')
    class_icon16 = 'bar_items/icons/16x16/twitter.png'
    class_icon48 = 'bar_items/icons/48x48/twitter.png'
    # Free twitter icon
    #http://www.webdesignerdepot.com/2009/07/50-free-and-exclusive-twitter-icons/

    # Item configuration
    box_schema = {'user_id': Integer(mandatory=True),
                  'user_name': String(mandatory=True),
                  'limit': Integer(mandatory=True, default=5, size=3),
                  'force_update': Boolean}


    box_widgets = [TextWidget('user_name',
                              title=MSG(u"Twitter account name")),
                   TextWidget('user_id', title=MSG(u"User Id")),
                   TextWidget('limit', title=MSG(u'Number of tweet')),
                   CheckBoxWidget('force_update',
                                  title=MSG(u'Force cache update')),
                  ]

    # Views
    view = TwitterSideBar_View()
    edit = TwitterSideBar_Edit()


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(BarItem.get_metadata_schema(),
                           cls.box_schema)


    def _update_data(self):
        user_id = self.get_property('user_id')
        limit = self.get_property('limit')
        uri = twitter_url % user_id
        data = None
        # errors
        errors = []
        errors_str = []

        # backup the default timeout
        default_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(3) # timeout in seconds

        # TODO Use itools.vfs instead of urllib2
        try:
            req = urllib2.Request(uri)
            req.add_header('User-Agent', 'itools/%s' % itools_version)
            response = urllib2.urlopen(req)
            data = response.read()
        except (socket.error, socket.gaierror, Exception,
                urllib2.HTTPError, urllib2.URLError), e:
            msg = '%s -- Network error: "%s"'
            msg = msg % (XMLContent.encode(str(uri)), e)
            msg = msg.encode('utf-8')
            errors.append(XMLParser(msg))
            errors_str.append(msg)

            summary = 'Error downloading feed\n'
            details = format_exc()
            log_error(summary + details)

        if data:
            # Parse
            feed = None
            try:
                feed = RSSFile(string=data)
            except Exception, e:
                msg = '%s <br />-- Error parsing: "%s"'
                msg = msg % (XMLContent.encode(str(uri)), e)
                msg = msg.encode('utf-8')
                errors.append(XMLParser(msg))
                errors_str.append(msg)
                summary = 'Error parsing feed\n'
                details = format_exc()
                log_error(summary + details)

            if feed:
                data = []
                for i, item in enumerate(feed.items):
                    if i == limit:
                        break
                    data.append(list(transform_links(item['description'])))

        # restore the default timeout
        socket.setdefaulttimeout(default_timeout)

        # errors to display
        list_errors = []
        for index, x in enumerate(errors):
            # FIXME if we simply append x (a generator)
            # this cause a segfault in the xml parser
            # Currently I don't know why
            # To avoid this critical error we transform the generator
            # into a list
            try:
                list_errors.append(list(x))
            except XMLError:
                # Default We show the string error
                list_errors.append(errors_str[index])
                continue
            #list_errors.append(x)

        # Save informations only if there is no errors
        metadata = self.metadata
        first_update = metadata.cache_mtime is None
        metadata.cache_mtime = datetime.now()
        if first_update or (metadata.cache_errors is not None \
                            and not list_errors):
            metadata.cache_data = data
            metadata.cache_errors = list_errors



register_resource_class(TwitterSideBar)
register_box(TwitterSideBar, allow_instanciation=True)
