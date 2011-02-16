# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008, 2011 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009 Romain Gauthier <romain@itaapy.com>
# Copyright (C) 2009-2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import from the Standard Library
from copy import deepcopy
from datetime import datetime, timedelta
from operator import itemgetter
from traceback import format_exc
import re
import socket
import urllib2

# Import from itools
from itools import __version__ as itools_version
from itools.core import freeze, get_abspath, merge_dicts
from itools.csv import CSVFile
from itools.datatypes import Boolean, Integer, URI, Unicode, String, HTTPDate
from itools.datatypes import Decimal, XMLContent
from itools.gettext import MSG
from itools.html import HTMLParser, sanitize_stream
from itools.i18n.locale_ import format_date
from itools.log import log_warning
from itools.rss import RSSFile
from itools.stl import stl, set_prefix
from itools.uri import get_reference
from itools.web import BaseView, INFO, ERROR, STLView
from itools.xml import XMLParser, stream_to_str, XMLError

# Import from ikaaro
from ikaaro.buttons import BrowseButton
from ikaaro.autoform import RadioWidget, TextWidget
from ikaaro.skins import register_skin
from ikaaro.text import CSV
from ikaaro.text_views import CSV_View as BaseCSV_View, CSV_EditRow, CSV_AddRow
from ikaaro.views_new import NewInstance

# Import from itws
from itws.views import AutomaticEditView



rss_default_pub_date = datetime(1970, 1, 1)

######################################################################
# Views
######################################################################
class ActivateButton(BrowseButton):

    access = 'is_allowed_to_edit'
    name = 'activate'
    title = MSG(u'Activate')



class DeactivateButton(BrowseButton):

    access = 'is_allowed_to_edit'
    name = 'deactivate'
    title = MSG(u'Deactivate')



class RssFeeds_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    icon = 'view.png'
    template = '/ui/rssfeeds/RssFeeds_view.xml'
    styles = ['/ui/rssfeeds/style.css']
    query_schema = {'feed': String(default='all')}


    def get_namespace(self, resource, context):
        accept = context.accept_language
        ac = resource.get_access_control()
        is_allowed_to_edit = ac.is_allowed_to_edit(context.user, resource)
        articles, errors = resource.get_articles()
        see_errors = is_allowed_to_edit and errors

        # Filter
        feed_filter = context.get_query_value('feed')
        feeds_cache = resource.get_summary()
        if feeds_cache is None:
            # XXX Sometime there is a bug with the cache
            resource.update_rss()
            feeds_cache = resource.get_summary()

        if feed_filter != 'all' and feed_filter in feeds_cache:
            feed = feeds_cache[feed_filter]
            if not feed['articles']:
                # If there is no articles inside the feed,
                # we fallback to all articles
                context.message = ERROR(u'There is no items for this feed.')
                feed_filter = 'all'
            else:
                articles = [ article for article in feed['articles'] ]
        else:
            feed_filter = 'all'

        # sort by publication date
        articles.sort(key=lambda x: x['pubDate'], reverse=True)
        for article in articles:
            article['formated_pubDate'] = format_date(article['pubDate'],
                                                      accept)
        # Filter
        feeds = []
        total_nb_articles = 0
        for uri, data in feeds_cache.iteritems():
            nb_articles = data['nb_articles']
            if nb_articles:
                title = data['title']
                if len(title) > 45:
                    title = u'%s…' % title[:45]
                title = title.encode('utf-8')
                feeds.append({'title': title, 'uri': uri,
                              'nb_articles': data['nb_articles'],
                              'selected': feed_filter == uri})
                total_nb_articles += nb_articles

        # sort by title
        nb_articles_format = '%{0}d'.format(len(str(total_nb_articles)))
        feeds.sort(key=lambda x: x['title'])
        feeds.insert(0, {'uri': 'all',
                         'title': MSG(u'All feeds').gettext('utf-8'),
                         'nb_articles': total_nb_articles,
                         'selected': feed_filter == 'all'})
        # Update all the entries
        for feed in feeds:
            nb = feed['nb_articles']
            nb = nb_articles_format % feed['nb_articles']
            feed['nb_articles'] = nb

        ns = {'articles': articles,
              'errors': errors,
              'see_errors': see_errors,
              'feeds': feeds}

        return ns



class FeedRSS_OPML(BaseView):

    access = 'is_allowed_to_view'
    title = MSG(u"OPML version")


    def get_mtime(self, resource):
        return resource.handler.last_download_time


    def GET(self, resource, context):
        # Content-Type
        context.set_content_type('text/opml')
        context.set_content_disposition('attachment', 'rss-agregator.opml')
        stream = resource.to_opml_stream(context)
        return stream_to_str(stream)



class CSV_View(BaseCSV_View):

    def sort_and_batch(self, resource, context, items):
        # Sort
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        if sort_by:
            sort_by = resource.handler.columns.index(sort_by)
            items.sort(key=itemgetter(sort_by), reverse=reverse)

        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    table_actions = (BaseCSV_View.table_actions +
                     [ ActivateButton, DeactivateButton ])


    def _action_activate_deactivate(self, resource, context, form, active):
        ids = form['ids']
        handler = resource.handler
        for id in ids:
            handler.update_row(id, **{'active': active})


    def action_activate(self, resource, context, form):
        self._action_activate_deactivate(resource, context, form, True)

        # Ok
        context.message = INFO(u'Feeds activated.')


    def action_deactivate(self, resource, context, form):
        self._action_activate_deactivate(resource, context, form, False)

        context.database.change_resource(resource)
        # Ok
        context.message = INFO(u'Feeds deactivated.')



class RssFeeds_Configure(AutomaticEditView):

    def get_value(self, resource, context, name, datatype):
        if name == 'update_now':
            return False
        return AutomaticEditView.get_value(self, resource, context, name,
                                           datatype)


    def set_value(self, resource, context, name, form):
        if name == 'update_now':
            resource.update_rss()
            return
        return AutomaticEditView.set_value(self, resource, context, name, form)



######################################################################
# Handler / resource
######################################################################
class RssFeedsFile(CSVFile):

    schema = {'uri': URI(mandatory=True, default=''),
              'keywords': Unicode(),
              'active': Boolean(default=False)}

    columns = ['uri', 'keywords', 'active']

    # Cache API
    last_download_time = None
    last_articles = None
    feeds_summary = None
    errors = None



class RssFeeds(CSV):

    class_id = 'rssfeeds'
    class_version = '20100618'
    class_title = MSG(u'RSS Feeds')
    class_description = MSG(u'RSS feeds allow to aggregate external feeds, '
                            u'filtering content by keywords')
    class_icon16 = 'rssfeeds/icons/16x16/rss_feeds.png'
    class_icon48 = 'rssfeeds/icons/48x48/rss_feeds.png'
    class_views = ['view', 'edit', 'add_row', 'configure']
    class_handler = RssFeedsFile
    class_schema = merge_dicts(CSV.class_schema,
                               TTL=Integer(source='metadata', default=15),
                               timeout=Decimal(source='metadata', default=1.0))

    # Views
    new_instance = NewInstance()
    view = RssFeeds_View()
    edit = CSV_View(title=MSG(u'RSS List'))
    edit_row = CSV_EditRow(title=MSG(u'Edit RSS'))
    add_row = CSV_AddRow(title=MSG(u'Add RSS'))
    configure = RssFeeds_Configure(title=MSG(u'Configure'))
    export_to_opml = FeedRSS_OPML()

    # Configuration of automatic edit view
    edit_show_meta = True
    edit_schema = freeze({
        'TTL': Integer(mandatory=True),
        'update_now': Boolean(ignore=True),
        'timeout': Decimal(mandatory=True)})
    edit_widgets = freeze([
        TextWidget('TTL', title=MSG(u"RSS TTL in minutes.")),
        TextWidget('timeout', title=MSG(u"Timeout in seconds")),
        RadioWidget('update_now', title=MSG(u"Update RSS now"))])


    def get_columns(self):
        return [('uri', MSG(u'URL')),
                ('keywords', MSG(u'Keywords (Separated by comma)')),
                ('active', MSG(u'Active'))]


    def update_rss(self):
        handler = self.handler
        errors = []
        errors_str = []
        articles = []
        feeds_summary = {}
        # backup the default timeout
        default_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.get_property('timeout'))

        # Download the feeds
        for uri, keywords, active in handler.get_rows():
            if active is False:
                continue
            keywords = [x.strip().lower() for x in keywords.split(',')]

            # TODO Use itools.vfs instead of urllib2
            try:
                req = urllib2.Request(uri)
                req.add_header('User-Agent', 'itools/%s' % itools_version)
                response = urllib2.urlopen(req)
                data = response.read()
            except (socket.error, socket.gaierror, Exception,
                    urllib2.HTTPError), e:
                msg = '%s <br />-- Network error: "%s"'
                msg = msg % (XMLContent.encode(str(uri)), e)
                msg = msg.encode('utf-8')
                errors.append(XMLParser(msg))
                errors_str.append(msg)

                summary = ('rssfeeds, Error downloading feed\n'
                           'uri: %s\n\n' % str(uri))
                details = format_exc()
                log_warning(summary + details, domain='itws')
                continue

            # Parse
            try:
                feed = RSSFile(string=data)
            except Exception, e:
                msg = '%s <br />-- Error parsing: "%s"'
                msg = msg % (XMLContent.encode(str(uri)), e)
                msg = msg.encode('utf-8')
                errors.append(XMLParser(msg))
                errors_str.append(msg)
                summary = ('rssfeeds, Error parsing feed\n'
                           'uri: %s\n\n' % str(uri))
                details = format_exc()
                log_warning(summary + details, domain='itws')
                continue

            # Check
            feed_articles = []
            for item in feed.items:
                # Check if description is available
                if item.get('description') is None:
                    # Invalid item (not well formed)
                    continue
                item['pubDate_valid'] = True
                if not item.has_key('pubDate'):
                    item['pubDate'] = rss_default_pub_date
                    item['pubDate_valid'] = False
                item['channel'] = feed.channel
                # Add the Article if correspond to keywords
                for keyword in keywords:
                    if (re.search(keyword, item['title'].lower()) or
                        re.search(keyword, item['description'].lower())):
                        feed_articles.append(item)
                        break

            # Check if the articles are well formed
            for article in feed_articles:
                article['valid'] = True
                description = article['description'].encode('utf-8')
                try:
                    description = HTMLParser(description)
                    article['description'] = sanitize_stream(description)
                except (XMLError, UnicodeDecodeError), e:
                    article['valid'] = False
                    msg = '%s <br />-- Error on article: "%s"<br />-- "%s"'
                    msg = msg % (XMLContent.encode(str(uri)), e,
                                 article['title'])
                    msg = msg.encode('utf-8')
                    errors.append(XMLParser(msg))
                    errors_str.append(msg)
                    summary = ('rssfeeds, Error sanitizing feed\n'
                               'uri: %s\n\n' % str(uri))
                    details = format_exc()
                    log_warning(summary + details, domain='itws')

            # Skip invalid articles
            feed_articles = [ article for article in feed_articles
                              if article['valid'] ]
            articles.extend(feed_articles)
            # Generate the feed summary

            try:
                feeds_summary[uri] = {'title': feed.channel['title'],
                                      'nb_articles': len(feed_articles),
                                      'articles': feed_articles}
            except KeyError:
                # Channel is not well formed -> no attribute title
                continue

            # Add the anchors
            uri_ref = get_reference(uri)
            for number, article in enumerate(articles):
                # Set prefix with url for article content
                description = set_prefix(article['description'],
                        prefix='.', uri=uri_ref)
                # Transform generator into list
                article['description'] = list(description)
                # Anchor
                article['anchor'] = 'anchor%d' % number
                article['reverse_anchor'] = 'reverse_anchor%d' % number

        # restore the default timeout
        socket.setdefaulttimeout(default_timeout)

        # Save informations
        handler.last_download_time = datetime.now()
        handler.last_articles = articles
        list_errors = []
        for index, x in enumerate(errors):
            # FIXME (old comment 2010-12-27,
            # the problem did not occurred since)
            # if we simply append x (a generator) this cause a segfault in the
            # xml parser
            list_errors.append(x)

        handler.errors = list_errors
        handler.feeds_summary = feeds_summary


    def get_articles(self):
        # Download or send the cache ??
        handler = self.handler
        now = datetime.now()
        last_download_time = handler.last_download_time
        update_feeds_delta = timedelta(minutes=self.get_property('TTL'))
        if (last_download_time is None or
            now - last_download_time > update_feeds_delta):
            self.update_rss()
        return handler.last_articles, handler.errors


    def get_summary(self):
        # Download or send the cache ??
        handler = self.handler
        now = datetime.now()
        last_download_time = handler.last_download_time
        update_feeds_delta = timedelta(minutes=self.get_property('TTL'))
        if (last_download_time is None or
            now - last_download_time > update_feeds_delta):
            self.update_rss()

        return handler.feeds_summary


    def to_opml_stream(self, context):
        namespace = {}
        namespace['title'] = self.get_property('title')
        namespace['mtime'] = HTTPDate.encode(self.get_mtime())
        revisions = self.get_revisions(context)
        name = email = None
        if revisions:
            root = context.root
            username = revisions[0]['username']
            user = root.get_user(username)
            if user:
                name = user.get_title()
                email = user.get_property('email')

        owner = {'name': name, 'email': email}
        namespace['owner'] = owner

        # Feeds
        articles, errors = self.get_articles()
        feeds_cache = deepcopy(self.handler.feeds_summary)
        feeds = []
        for uri, data in feeds_cache.iteritems():
            feeds.append({'title': data['title'],
                          'nb_articles': data['nb_articles'],
                          'uri': uri,
                          'type': 'rss' # FIXME hardcoded
                          })
        namespace['feeds'] = feeds
        handler = self.get_resource('/ui/rssfeeds/RssFeeds_export_to_opml.xml')
        return stl(handler, namespace=namespace)



# Register skin
path = get_abspath('../ui/rssfeeds')
register_skin('rssfeeds', path)
