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
from copy import deepcopy

# Import from itools
from itools.web import get_context
from itools.datatypes import Enumerate
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import SelectWidget
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent

# Import from itws
from base import Feed_View


class CategoriesSortEnumerate(Enumerate):

    values = [('title', '0', MSG(u'Title: A to Z')),
              ('title', '1', MSG(u'Title: Z to A')),
              ('mtime', '1', MSG(u'Mtime: Younger before')),
              ('mtime', '0', MSG(u'Mtime: Older before')),
              ('workflow_state', '1', MSG(u'State: Public before')),
              ('workflow_state', '0', MSG(u'State: Private before'))]

    @classmethod
    def get_options(cls):
        context = get_context()
        options = []
        for sort_by, reverse, value in cls.values:
            uri = deepcopy(context.uri)
            uri.query['sort_by'] = sort_by
            uri.query['reverse'] = reverse
            options.append(
                {'name': str(uri),
                 'value': value})
        return options


class Browse_Navigator(Feed_View):

    access = 'is_allowed_to_edit'
    search_template = None
    batch_size = 25
    sort_by = 'mtime'
    is_popup = True

    template = '/ui/feed_views/base_feed_view_div.xml'
    search_template = '/ui/folder/browse_search.xml'
    content_template = '/ui/feed_views/browse_navigator.xml'

    search_on_current_folder = True
    ignore_internal_resources = True
    show_title = False

    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('title', MSG(u'Title')),
        ('format', MSG(u'Type')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('workflow_state', MSG(u'State'))]


    def get_content_namespace(self, resource, context, items):
        # Get namespace
        namespace = Folder_BrowseContent.get_table_namespace(self,
                        resource, context, items)
        # Sort by
        widget = SelectWidget('sort_by',
                              datatype=CategoriesSortEnumerate(),
                              value=str(context.uri),
                              has_empty_option=False)
        namespace['sort_by'] = widget.render()
        # The breadcrumb
        breadcrumb = []
        node = resource
        while node != context.root:
            if node.has_property('breadcrumb_title'):
                title = node.get_property('breadcrumb_title')
            else:
                title = node.get_title()
            link = context.get_link(node)
            breadcrumb.insert(0, {'name': node.name,
                                  'title': title,
                                  'url':  link})
            node = node.parent
        namespace['breadcrumb'] = breadcrumb
        return namespace


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'title':
            title = item_resource.get_title()
            link = context.get_link(item_resource)
            if isinstance(item_resource, Folder):
                link += '/;manage_content'
            return (title, link)
        return Feed_View.get_item_value(self, resource, context, item, column)
