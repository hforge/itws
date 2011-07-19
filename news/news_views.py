# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.core import freeze, merge_dicts, thingy_property
from itools.datatypes import String, Boolean
from itools.gettext import MSG
from itools.web import get_context, STLView
from itools.database import PhraseQuery, RangeQuery

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.popup import DBResource_AddImage
from ikaaro.utils import get_base_path_query

# Import from itws
from itws.feed_views import Details_View, Feed_View
from itws.rss import BaseRSS
from itws.webpage_views import WebPage_Edit



class NewsItem_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    icon = 'view.png'
    template = '/ui/news/NewsItem_view.xml'
    styles = ['/ui/news/style.css']

    # customization (obsolete)
    id = 'news'
    title_link = None


    def get_namespace(self, resource, context):
        dow = resource.get_pub_datetime_formatted()
        # title
        title = resource.get_long_title()
        # content
        content = resource.get_html_data()
        # Allowed to edit
        ac = resource.get_access_control()
        if ac.is_allowed_to_edit(context.user, resource):
            edit = True
        else:
            edit = False

        namespace = {'id': self.id, 'pub_datetime': dow}
        namespace['title'] = title
        namespace['content'] = content
        namespace['is_allowed_to_edit'] = edit
        title_link = None
        if self.title_link:
            title_link = context.get_link(resource)
        namespace['title_link'] = title_link

        return namespace



class NewsItem_AddImage(DBResource_AddImage):

    def get_start(self, resource):
        return resource.get_resource('../images')



class NewsItem_Edit(WebPage_Edit):

    edit_fields = freeze(['title', 'display_title', 'long_title',
                          'data', 'tags', 'thumbnail', 'pub_datetime'])


class NewsFolder_View(Details_View):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    styles = ['/ui/news/style.css']

    view_name = 'news-folder-view'
    view_title = MSG(u'News folder view')

    search_template = None
    sort_by = 'pub_datetime'
    reverse = True

    # Display sidebar
    display_sidebar = True


    @thingy_property
    def batch_size(self):
        here = get_context().resource
        return here.get_property('batch_size')


    def get_items(self, resource, context, *args):
        args = [PhraseQuery('format', 'news')]
        return Feed_View.get_items(self, resource, context, *args)


    def _get_namespace(self, brain, resource, context, column, current_path):
        if column == 'title':
            # Return title or long_title
            title = resource.get_property('title')
            if title:
                return title
            # long title
            long_title = resource.get_property('long_title')
            if long_title:
                return long_title
            # Fallback
            return resource.get_title()
        return Feed_View._get_namespace(self, brain, resource, context, column,
                                        current_path)



class NewsFolder_RSS(BaseRSS):

    def get_base_query(self, resource, context):
        today = datetime.now()
        min_date = datetime(1900, 1, 1)
        # Filter by news folder
        abspath = resource.get_canonical_path()
        return [ get_base_path_query(str(abspath)),
                 PhraseQuery('workflow_state', 'public'),
                 RangeQuery('pub_datetime', min_date, today)]


    def get_allowed_formats(self, resource, context):
        return [resource.news_class.class_id]



############################################################
# Manage view
############################################################
class NewsFolder_BrowseContent(Folder_BrowseContent):

    access = 'is_allowed_to_edit'

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               sort_by=String(default='pub_datetime'),
                               reverse=Boolean(default=True))

    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('abspath', MSG(u'Path')),
        ('title', MSG(u'Title')),
        ('pub_datetime', MSG(u'Date of writing')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('format', MSG(u'Type')),
        ('workflow_state', MSG(u'State'))]


    def get_items(self, resource, context, *args):
        proxy = super(NewsFolder_BrowseContent, self)
        results = proxy.get_items(resource, context, *args)
        # Return only direct children
        abspath = str(resource.get_canonical_path())
        query = get_base_path_query(abspath, depth=1)
        return results.search(query)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'pub_datetime':
            if brain.is_tagsaware is False:
                return None
            return context.format_datetime(brain.pub_datetime)
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)
