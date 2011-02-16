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

# Import from itools
from itools.core import merge_dicts
from itools.database import AndQuery, PhraseQuery
from itools.datatypes import Enumerate, Integer, String
from itools.gettext import MSG
from itools.stl import stl
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.autoform import stl_namespaces, SelectWidget, make_stl_template
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.future.order import ResourcesOrderedTable_Unordered


# Helper
icon_with_title_template = make_stl_template(
    """<img src="${icon}" border="0" title="${title}" alt="${title}" />""")

def get_icon_with_title(resource, context):
    path_to_icon = resource.get_resource_icon(16)
    if path_to_icon.startswith(';'):
        path_to_resource = context.get_link(resource)
        path_to_icon = path_to_resource.resolve(path_to_icon)
    title = resource.class_title.gettext()
    return stl(events=icon_with_title_template,
            namespace={'icon': path_to_icon, 'title': title})


###############################################################################
# Repository views
###############################################################################
class Repository_BrowseContent(Folder_BrowseContent):

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               sort_by=String(default='format'))

    links_template = list(XMLParser("""
        <stl:block stl:repeat="item items">
            <a href="${item/path}" title="${item/title}">${item/name}</a>
            <span stl:if="not repeat/item/end">,</span>
        </stl:block>
        """, stl_namespaces))


    def get_table_columns(self, resource, context):
        columns = Folder_BrowseContent.get_table_columns(self, resource,
                                                         context)
        columns = list(columns) # create a new list
        columns.append(('links', MSG(u'Referenced by'), False))
        return columns


    def get_item_value(self, resource, context, item, column):
        if column == 'links':
            brain, item_resource = item
            root = context.root
            path = str(item_resource.get_canonical_path())
            results = root.search(links=path)
            if len(results) == 0:
                return 0
            links = []
            for index, doc in enumerate(results.get_documents()):
                links_resource = root.get_resource(doc.abspath)
                parent_resource = links_resource.parent
                # links_resource should be an ordered table
                links.append({'name': (index + 1),
                              'title': parent_resource.get_title(),
                              'path': context.get_link(links_resource)})

            events = self.links_template
            return stl(events=events, namespace={'items': links})

        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)



class BoxesOrderedTable_Ordered(ResourcesOrderedTable_Ordered):

    title = MSG(u'Order boxes')

    columns = [('checkbox', None),
               ('icon_with_title', None),
               ('title', MSG(u'Title'), False),
               ('name', MSG(u'Name'), False)]


    def sort_and_batch(self, resource, context, items):
        # Sort by order regardless query
        reverse = False
        ordered_ids = list(resource.handler.get_record_ids_in_order())
        f = lambda x: ordered_ids.index(x.id)
        items.sort(cmp=lambda x,y: cmp(f(x), f(y)), reverse=reverse)

        # Always display all items
        return items


    def get_table_columns(self, resource, context):
        return self.columns


    def get_item_value(self, resource, context, item, column):
        if column == 'icon_with_title':
            order_root = resource.get_order_root()
            item_resource = order_root.get_resource(item.name, soft=True)

            if item_resource is None:
                return None
            return get_icon_with_title(item_resource, context)
        elif column == 'name':
            return item.name

        proxy = super(BoxesOrderedTable_Ordered, self)
        return proxy.get_item_value(resource, context, item, column)



class BoxesOrderedTable_Unordered(ResourcesOrderedTable_Unordered):

    title = MSG(u'Add a box')

    query_schema = merge_dicts(ResourcesOrderedTable_Ordered.query_schema,
                               batch_size=Integer(default=0),
                               format=String, sort_by=String(default='title'))
    search_template = '/ui/bar_items/browse_search.xml'


    def get_query_schema(self):
        return self.query_schema


    def get_items_query(self, resource, context):
        proxy = super(BoxesOrderedTable_Unordered, self)
        query = proxy.get_items_query(resource, context)
        # Add format filter
        format = context.query['format']
        if format:
            query = AndQuery(query, PhraseQuery('format', format))

        return query


    def get_table_columns(self, resource, context):
        proxy = super(BoxesOrderedTable_Unordered, self)
        columns = proxy.get_table_columns(resource, context)

        columns = list(columns) # create a new list
        columns.insert(1, ('icon_with_title', None))
        columns.insert(3, ('name', MSG(u'Name'), False))

        # Column to remove
        indexes = [ x for x, column in enumerate(columns)
                    if column[0] == 'path' ]
        indexes.sort(reverse=True)
        for index in indexes:
            columns.pop(index)

        return columns


    def get_item_value(self, resource, context, item, column):
        if column == 'icon_with_title':
            item_brain, item_resource = item
            return get_icon_with_title(item_resource, context)
        elif column == 'name':
            item_brain, item_resource = item
            return item_brain.name
        proxy = super(BoxesOrderedTable_Unordered, self)
        return proxy.get_item_value(resource, context, item, column)


    def get_search_namespace(self, resource, context):
        orderable_classes = resource.orderable_classes
        enum = Enumerate()
        options = []
        for cls in orderable_classes:
            options.append({'name': cls.class_id, 'value': cls.class_title})
        enum.options = options

        format = context.query['format']
        widget = SelectWidget('format', datatype=enum, value=format)
        namespace = {}
        namespace['format_widget'] = widget.render()
        # is admin popup
        if context.method == 'POST' and context.form_action == 'action':
            # filter by type only forward is_admin_popup
            is_admin_popup = context.get_form_value('is_admin_popup')
        else:
            is_admin_popup = context.get_query_value('is_admin_popup')
        namespace['is_admin_popup'] = is_admin_popup

        return namespace
