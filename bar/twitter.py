# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2011 Nicolas Deram <nicolas@itaapy.com>
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
import httplib
import re
import socket
import urllib2

# Import from itools
from itools import __version__ as itools_version
from itools.core import freeze, merge_dicts
from itools.datatypes import Integer, String, XMLContent
from itools.gettext import MSG
from itools.log import log_warning
from itools.rss import RSSFile
from itools.xml import XMLParser, XMLError

# Import from itws
from base import Box
from base_views import Box_View
from itws.utils import ResourceWithCache



def http_head(hostname, path):
    try:
        conn = httplib.HTTPConnection(hostname)
        conn.request("HEAD", path)
        res = conn.getresponse()
        conn.close()
        return res.status == 200
    except (socket.error, socket.gaierror, Exception,
            httplib.HTTPException):
        return False
    return False


class TwitterID(Integer):

    @staticmethod
    def is_valid(value):
        hostname = "twitter.com"
        path = "/statuses/user_timeline/%s.rss" % value
        return http_head(hostname, path)



class IndenticaName(String):

    @staticmethod
    def is_valid(value):
        hostname = "identi.ca"
        path = "/%s" % value
        return http_head(hostname, path)



class TwitterSideBar_View(Box_View):

    template = '/ui/bar_items/twitter.xml'


    def _get_title_href(self, resource, context):
        user_name = resource.get_property('user_name')
        title_href = 'http://www.twitter.com/%s' % user_name
        return title_href


    def get_namespace(self, resource, context):
        namespace = {'title': resource.get_title(),
                     'title_href': self._get_title_href(resource, context),
                     'items': []}
        items, errors = resource.get_cached_data()
        ac = resource.get_access_control()
        is_allowed_to_edit = ac.is_allowed_to_edit(context.user, resource)
        namespace['items'] = items
        namespace['errors'] = is_allowed_to_edit and errors

        if is_allowed_to_edit is False and (items is None or len(items) == 0):
            self.set_view_is_empty(True)

        return namespace



class IdenticaSideBar_View(TwitterSideBar_View):

    def _get_title_href(self, resource, context):
        user_name = resource.get_property('user_name')
        title_href = 'http://identi.ca/%s' % user_name
        return title_href


class TwitterSideBar(Box, ResourceWithCache):

    class_id = 'box-twitter'
    class_title = MSG(u'Twitter')
    class_description = MSG(u'Twitter feed (micro-blogging service).')
    class_icon16 = 'bar_items/icons/16x16/twitter.png'
    class_icon48 = 'bar_items/icons/48x48/twitter.png'
    # Free twitter icon
    #http://www.webdesignerdepot.com/2009/07/50-free-and-exclusive-twitter-icons/
    class_schema = merge_dicts(Box.class_schema,
             user_id=TwitterID(source='metadata',
                               title=MSG(u'User Id')),
             user_name=String(source='metadata',
                              title=MSG(u"Twitter account name")),
             limit=Integer(source='metadata',
                           title=MSG(u"Number of tweets"), default=5))


    # Configuration
    allow_instanciation = True
    edit_fields = freeze(['user_id', 'user_name', 'limit'])

    # Views
    view = TwitterSideBar_View()


    def _get_account_uri(self):
        user_id = self.get_property('user_id')
        return 'http://twitter.com/statuses/user_timeline/%s.rss' % user_id


    def _transform_links(self, item):
        item = item.split(':', 1)[1]
        item = re.sub(r'(\A|\s)@(\w+)',
                      r'\1@<a href="http://www.twitter.com/\2">\2</a>', item)
        item = re.sub(r'(\A|\s)#(\w+)',
               r'\1#<a href="http://search.twitter.com/search?q=%23\2">\2</a>',
               item)
        item = re.sub(r'(\A|\s)(http://(\w|\.|/|;|\?|=|%|&|-)+)',
                      r'\1<a href="\2"> \2</a>', item)
        item = re.sub('&', '&amp;', item)
        return XMLParser(item.encode('utf-8'))


    def _get_data_from_item(self, item):
        return list(self._transform_links(item['description']))


    def _update_data(self):
        limit = self.get_property('limit')
        uri = self._get_account_uri()
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

            summary = 'sidebar/twitter, Error downloading feed\n'
            details = format_exc()
            log_warning(summary + details, domain='itws')

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
                summary = 'sidebar/twitter, Error parsing feed\n'
                details = format_exc()
                log_warning(summary + details, domain='itws')

            if feed:
                data = []
                i = 0
                for item in feed.items:
                    if i == limit:
                        break
                    try:
                        data.append(self._get_data_from_item(item))
                    except Exception, e:
                        msg = '%s <br />-- Error getting data from item: "%s"'
                        msg = msg % (XMLContent.encode(str(uri)), e)
                        msg = msg.encode('utf-8')
                        errors.append(XMLParser(msg))
                        errors_str.append(msg)
                        summary = 'sidebar/twitter, Error parsing feed\n'
                        details = format_exc()
                        log_warning(summary + details, domain='itws')
                        continue
                    else:
                        i += 1

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



class IdenticaSideBar(TwitterSideBar):

    class_id = 'box-identica'
    class_title = MSG(u'Identi.ca')
    class_description = MSG(u'Identi.ca feed (open micro-blogging service).')
    class_icon16 = 'bar_items/icons/16x16/identica.png'
    class_icon48 = 'bar_items/icons/48x48/identica.png'
    class_schema = merge_dicts(Box.class_schema,
             user_name=IndenticaName(source='metadata',
                                     title=MSG(u'Identi.ca account name')),
             limit=Integer(source='metadata', mandatory=True, default=5,
                           size=3, title=MSG(u'Number of messages')))

    # identica icons source: http://status.net/

    # Item configuration
    allow_instanciation = True

    edit_fields = freeze(['user_name', 'limit'])

    # Views
    view = IdenticaSideBar_View()


    def _get_account_uri(self):
        user_name = self.get_property('user_name')
        return 'http://identi.ca/%s/rss' % user_name


    def _transform_links(self, item):
        item = item.split(':', 1)[1]
        item = re.sub(r'(\A|\s)@(\w+)',
                      r'\1@<a href="http://identi.ca/\2">\2</a>', item)
        item = re.sub(r'(\A|\s)#([^ ]+)',
                      r'\1#<a href="http://identi.ca/tag/\2">\2</a>', item)
        item = re.sub(r'(\A|\s)(http://(\w|\.|/|;|\?|=|%|&|-)+)',
                      r'\1<a href="\2"> \2</a>', item)
        item = re.sub('&', '&amp;', item)
        return XMLParser(item.encode('utf-8'))


    def _get_data_from_item(self, item):
        return list(self._transform_links(item['title']))
