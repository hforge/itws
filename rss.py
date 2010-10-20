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

# Import from itools
from itools.core import freeze
from itools.database import AndQuery, RangeQuery, NotQuery, PhraseQuery, OrQuery
from itools.gettext import MSG
from itools.html import stream_to_str_as_xhtml
from itools.rss import RSSFile
from itools.web import BaseView, get_context

# Import from ikaaro
from ikaaro.utils import get_base_path_query
from ikaaro.webpage import WebPage

# Import from itws
from utils import set_prefix_with_hostname


class BaseRSS(BaseView):

    access = True
    allowed_formats = freeze([])
    excluded_formats = freeze([])
    excluded_paths = freeze([])
    excluded_container_paths = freeze([])
    max_items_number = 20


    def get_base_query(self, resource, context):
        # Filter by website
        abspath = resource.get_site_root().get_canonical_path()
        query = [ get_base_path_query(str(abspath)) ]
        # Filter by pub_datetime
        today = datetime.now()
        min_date = datetime(1900, 1, 1)
        query.append(RangeQuery('pub_datetime', min_date, today))
        # Do not show image
        query.append(PhraseQuery('is_image', False))
        return query


    def get_allowed_formats(self, resource, context):
        return self.allowed_formats


    def get_excluded_formats(self, resource, context):
        return self.excluded_formats


    def get_excluded_paths(self, resource, context):
        return self.excluded_paths


    def get_excluded_container_paths(self, resource, context):
        return self.excluded_container_paths


    def get_max_items_number(self, resource, context):
        return self.max_items_number


    def get_if_modified_since_query(self, resource, context,
                                    if_modified_since):
        if not if_modified_since:
            return []
        return AndQuery(RangeQuery('pub_datetime', if_modified_since, None),
                        NotQuery(PhraseQuery('pub_datetime',
                                             if_modified_since)))


    def get_items(self, resource, context, if_modified_since=None):
        # Base query (workflow aware, image, state ...)
        query = self.get_base_query(resource, context)

        # Allowed formats
        formats = self.get_allowed_formats(resource, context)
        if formats:
            if len(formats) > 1:
                query2 = OrQuery(*[ PhraseQuery('format', format)
                                    for format in formats ])
            else:
                query2 = PhraseQuery('format', formats[0])
            query.append(query2)

        # Excluded formats
        excluded_formats = self.get_excluded_formats(resource, context)
        if excluded_formats:
            if len(excluded_formats) > 1:
                query2 = OrQuery(*[ PhraseQuery('format', format)
                                    for format in excluded_formats ])
            else:
                query2 = PhraseQuery('format', excluded_formats[0])
            query.append(NotQuery(query2))

        # Excluded paths
        excluded_paths = self.get_excluded_paths(resource, context)
        if excluded_paths:
            if len(excluded_paths) > 1:
                query2 = OrQuery(*[ PhraseQuery('abspath', str(path))
                                    for path in excluded_paths ])
            else:
                query2 = PhraseQuery('abspath', str(excluded_paths[0]))
            query.append(NotQuery(query2))

        # Excluded container paths
        excluded_cpaths = self.get_excluded_container_paths(resource, context)
        if excluded_cpaths:
            if len(excluded_cpaths) > 1:
                query2 = OrQuery(*[ get_base_path_query(str(path))
                                    for path in excluded_cpaths ])
            else:
                query2 = get_base_path_query(str(excluded_cpaths[0]))
            query.append(NotQuery(query2))

        # An If-Modified-Since ?
        query2 = self.get_if_modified_since_query(resource, context,
                                                  if_modified_since)
        if query2:
            query.append(query2)

        query = AndQuery(*query)
        return resource.get_root().search(query)


    def _sort_and_batch(self, resource, context, results):
        size = self.get_max_items_number(resource, context)
        items = results.get_documents(sort_by='pub_datetime',
                                      reverse=True, size=size)
        return items


    def sort_and_batch(self, resource, context, results):
        items = self._sort_and_batch(resource, context, results)

        # Access Control (FIXME this should be done before batch)
        user = context.user
        root = context.root
        allowed_items = []
        for item in items:
            abspath = item.abspath
            resource = root.get_resource(abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        return allowed_items


    def get_mtime(self, resource):
        context = get_context()
        items = self.get_items(resource, context)
        items = self.sort_and_batch(resource, context, items)
        # FIXME If there is no modifications ?
        if not items:
            return
        last_brain = items[0][0]
        dow = last_brain.pub_datetime
        # date -> datetime
        return datetime(dow.year, dow.month, dow.day)


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column in ('link', 'guid'):
            value = context.uri.resolve(context.get_link(item_resource))
            return str(value)
        elif column == 'pubDate':
            return brain.pub_datetime
        elif column == 'title':
            return item_resource.get_title()
        elif column == 'description':
            if issubclass(item_resource.__class__, WebPage):
                data = item_resource.get_html_data()
                if data is None:
                    # Skip empty content
                    return ''
                # Set the prefix
                prefix = site_root.get_pathto(item_resource)
                data = set_prefix_with_hostname(data, '%s/' % prefix,
                                                uri=context.uri)
                data = stream_to_str_as_xhtml(data)
                return data.decode('utf-8')
            else:
                return item_resource.get_property('description')


    def GET(self, resource, context):
        language = context.get_query_value('language')
        if language is None:
            # Get Language
            site_root = context.site_root
            ws_languages = site_root.get_property('website_languages')
            accept = context.accept_language
            language = accept.select_language(ws_languages)
        if_modified_since = context.get_header('if-modified-since')
        items = self.get_items(resource, context, if_modified_since)
        items = self.sort_and_batch(resource, context, items)

        # Construction of the RSS flux
        feed = RSSFile()

        site_root = resource.get_site_root()
        host = context.uri.authority
        # The channel
        channel = feed.channel
        channel['title'] = site_root.get_property('title')
        channel['link'] = 'http://%s/?language=%s' % (host, language)
        channel['description'] = MSG(u'Last News').gettext()
        channel['language'] = language

        # The new items
        feed_items = feed.items
        for item in items:
            ns = {}
            for key in ('link', 'guid', 'title', 'pubDate', 'description'):
                ns[key] = self.get_item_value(resource, context, item, key,
                                              site_root)
            feed_items.append(ns)

        # Filename and Content-Type
        context.set_content_disposition('inline', "last_news.rss")
        context.set_content_type('application/rss+xml')
        return feed.to_str()
