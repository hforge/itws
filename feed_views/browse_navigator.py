# -*- coding: UTF-8 -*-
# Copyright (C) 2010-2011 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Henry Obein <henry@itaapy.com>
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
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.web import INFO

# Import from ikaaro
from ikaaro.autoform import SelectWidget, TextWidget
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent, Folder_Rename

# Import from itws
from base import Feed_View
from itws.enumerates import SearchTypes_Enumerate


class Browse_Navigator_Rename(Folder_Rename):

    # XXX Modify form action
    template = '/ui/feed_views/browse_navigator_rename.xml'

    is_popup = True
    goto_after = ';manage_content'



class Browse_Navigator(Feed_View):

    access = 'is_allowed_to_edit'
    batch_size = 25
    sort_by = 'mtime'
    reverse = True
    is_popup = True
    title = MSG(u'Navigator')

    template = '/ui/feed_views/base_feed_view_div.xml'
    #search_template = '/ui/folder/browse_search.xml'
    content_template = '/ui/feed_views/browse_navigator.xml'

    search_schema = {'text': Unicode,
                     'format': SearchTypes_Enumerate}
    search_widgets = [TextWidget('text', title=MSG(u'Text')),
                      SelectWidget('format', title=MSG(u'Format'))]

    search_on_current_folder = True
    ignore_internal_resources = True
    ignore_box_aware = True
    display_title = False

    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('title', MSG(u'Title')),
        ('actions', MSG(u'Actions'), False),
        ('format', MSG(u'Type')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('workflow_state', MSG(u'State'))]

    javascript = "javascript:window.opener.location.href='%s';window.close();"
    actions_template = """
    <stl:block stl:repeat="action actions">
        <a href="${action/href}" title="${action/title}">${action/title}</a>
        <stl:inline stl:if="not repeat/action/end">,</stl:inline>
    </stl:block>"""
    actions_views = [(None, MSG(u'View')), ('edit', MSG(u'Edit'))]


    def get_content_namespace(self, resource, context, items):
        # Get namespace
        namespace = Folder_BrowseContent.get_table_namespace(self,
                        resource, context, items)
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
            if isinstance(item_resource, Folder):
                link = '%s/;manage_content' % context.get_link(item_resource)
                return (title, link)
            return title
        elif column == 'actions':
            link = context.get_link(item_resource)
            actions = []
            for view_name, title in self.actions_views:
                if view_name and item_resource.get_view(view_name):
                    href = '%s/;%s' % (link, view_name)
                else:
                    href = link
                actions.append({'href': self.javascript % href,
                                'title': title})
            return INFO(self.actions_template, format='stl', actions=actions)
        return Feed_View.get_item_value(self, resource, context, item, column)


    def action_rename(self, resource, context, form):
        proxy = super(Browse_Navigator, self)
        ret = proxy.action_rename(resource, context, form)
        # Tweak view
        path = ret.path
        path[-1] = ';manage_content_rename'
        return ret
