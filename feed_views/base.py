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

# Import from itools
from itools.core import merge_dicts
from itools.database import AndQuery, NotQuery, OrQuery, PhraseQuery
from itools.database import StartQuery, TextQuery
from itools.datatypes import Enumerate, Integer, String, Boolean
from itools.gettext import MSG
from itools.uri import Path

# Import from ikaaro
from ikaaro.autoform import SelectWidget
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.registry import get_resource_class
from ikaaro.utils import get_base_path_query
from ikaaro.website import WebSite



###########################################
# See bug:
# http://bugs.hforge.org/show_bug.cgi?id=1100
# Add in ikaaro:
#   > self.search_on_current_folder
###########################################

class Feed_View(Folder_BrowseContent):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    table_template = None

    # View configuration
    view_name = None
    view_resource = None
    template = '/ui/feed_views/base_feed_view_div.xml'
    search_template = '/ui/folder/browse_search.xml'
    content_template = '/ui/feed_views/Tag_item_viewbox.xml'
    context_menus = []
    styles = []
    show_first_batch = False
    show_second_batch = True
    display_title = True
    batch_size = 25
    sort_by = 'title'
    reverse = False
    ignore_internal_resources = False
    ignore_box_aware = True
    search_on_current_folder = True
    search_on_current_folder_recursive = False
    content_keys = ('pub_datetime', 'title', 'long_title',
                    'link', 'is_image', 'preview',
                    'tags', 'workflow_state',
                    'image', 'css', 'class_icon16', 'class_icon48',
                    'type', 'abspath')
    # Add an id to a wrapper div based on resource name
    specific_id_wrapper = True

    # Query suffix
    query_suffix = None


    def _get_query_suffix(self):
        return self.query_suffix


    def _get_query_value(self, resource, context, name):
        query_suffix = self._get_query_suffix()
        key = name
        hidden = key in self.hidden_fields
        if query_suffix not in (None, ''):
            key = '%s_%s' % (name, query_suffix)
        if hidden:
            return context.get_query_value(key)
        return context.query[key]


    def _context_uri_replace(self, context, **kw):
        """Implement context.uri.replace. Take into account
        the query_suffix

        _context_uri_replace(context, batch_size=x)
        """
        query_suffix = self._get_query_suffix()
        if query_suffix:
            d = {}
            for key, value in kw.iteritems():
                d['%s_%s' % (key, query_suffix)] = value
            return context.uri.replace(**d)
        else:
            return context.uri.replace(**kw)


    def get_query_schema(self):
        """We allow to define 2 variable (sort_by and batch_size)"""
        d = merge_dicts(Folder_BrowseContent.get_query_schema(self),
                batch_size=Integer(default=self.batch_size),
                sort_by=String(default=self.sort_by),
                reverse=Boolean(default=self.reverse))

        query_suffix = self._get_query_suffix()
        if query_suffix is None:
            return d

        prefixed_d = {}
        for key, value in d.iteritems():
            prefixed_d['%s_%s' % (key, query_suffix)] = value
        return prefixed_d


    @property
    def table_template(self):
        return self.content_template


    def get_search_types(self, resource, context):
        # 1. Build the query of all objects to search
        path = resource.get_canonical_path()
        if self.search_on_current_folder_recursive:
            query = get_base_path_query(str(path))
        else:
            query = PhraseQuery('parent_path', str(path))

        if resource.get_abspath() == '/':
            theme_path = path.resolve_name('theme')
            theme = get_base_path_query(str(theme_path), True)
            query = AndQuery(query, NotQuery(theme))

        if self.ignore_internal_resources:
            method = getattr(resource, 'get_internal_use_resource_names', None)
            if method:
                sub_query = []
                resource_abspath = resource.get_abspath()
                for name in method():
                    abspath = path.resolve2(name)
                    sub_query.append(PhraseQuery('abspath', str(abspath)))
                query = AndQuery(query, NotQuery(OrQuery(*sub_query)))

        # 2. Compute children_formats
        children_formats = set()
        for child in context.root.search(query).get_documents():
            children_formats.add(child.format)

        # 3. Do not show two options with the same title
        formats = {}
        for type in children_formats:
            cls = get_resource_class(type)
            title = cls.class_title.gettext()
            formats.setdefault(title, []).append(type)

        # 4. Build the namespace
        types = []
        for title, type in formats.items():
            type = ','.join(type)
            types.append({'name': type, 'value': title})
        types.sort(key=lambda x: x['value'].lower())

        return types


    def get_search_namespace(self, resource, context):
        types = self.get_search_types(resource, context)

        # Build dynamic datatype and widget
        search_type = self._get_query_value(resource, context, 'search_type')
        datatype = Enumerate(options=types)
        widget = SelectWidget(name='search_type', datatype=datatype,
                              value=search_type)
        search_text = self._get_query_value(resource, context, 'search_text')

        # Hidden widgets
        hidden_widgets = []
        for name in self.hidden_fields:
            value = self._get_query_value(resource, context, name)
            hidden_widgets.append({'name': name, 'value': value})

        return {'search_text': search_text,
                'search_types_widget': widget.render(),
                'hidden_widgets': hidden_widgets}


    def _get_container(self, resource, context):
        if self.search_on_current_folder is True:
            return resource
        # Current website
        return context.resource.get_site_root()


    def get_items(self, resource, context, *args):
        """ Same that Folder_BrowseContent but we allow to
            define var 'search_on_current_folder'"""
        # Check parameters
        if self.search_on_current_folder and self.search_on_current_folder_recursive:
            msg = '{0} and {1} are mutually exclusive.'
            raise ValueError, msg.format('search_on_current_folder',
                                         'search_on_current_folder_recursive')

        root = context.root
        # Query
        args = list(args)

        # Get the container
        container = self._get_container(resource, context)
        container_abspath = container.get_canonical_path()
        if self.search_on_current_folder is True:
            # Limit result to direct children
            args.append(PhraseQuery('parent_path', str(container_abspath)))
        else:
            # Limit results to whole sub children
            args.append(get_base_path_query(str(container_abspath)))

        # Search only on current folder ?
        if self.search_on_current_folder_recursive is True:
            # Already done before, because if search_on_current_folder and
            # search_on_current_folder_recursive are exclusive

            # Exclude '/theme/'
            if isinstance(resource, WebSite):
                theme_path = container_abspath.resolve_name('theme')
                theme = get_base_path_query(str(theme_path), True)
                args.append(NotQuery(theme))

        # Filter by type
        if self.search_template:
            search_type = self._get_query_value(resource, context,
                                                'search_type')
            if search_type:
                if ',' in search_type:
                    search_type = search_type.split(',')
                    search_type = [ PhraseQuery('format', x)
                                    for x in search_type ]
                    search_type = OrQuery(*search_type)
                else:
                    search_type = PhraseQuery('format', search_type)
                args.append(search_type)

            # Text search
            search_text = self._get_query_value(resource, context,
                                                'search_text')
            search_text = search_text.strip()
            if search_text:
                args.append(OrQuery(TextQuery('title', search_text),
                                    TextQuery('text', search_text),
                                    PhraseQuery('name', search_text)))

        if self.ignore_internal_resources:
            exclude_folders_path = []
            exclude_files_path = []
            # Exclude internal use resources
            method = getattr(resource, 'get_internal_use_resource_names', None)
            if method:
                resource_abspath = resource.get_abspath()
                for name in method():
                    abspath = resource_abspath.resolve2(name)
                    if name[-1] == '/':
                        # folder
                        exclude_folders_path.append(str(abspath))
                    else:
                        # file
                        exclude_files_path.append(str(abspath))
            if self.search_on_current_folder_recursive is True:
                q = AndQuery(get_base_path_query(str(container_abspath)),
                             PhraseQuery('internal_resource_aware', True))
                folder_results = root.search(q)
                for doc in folder_results.get_documents():
                    p_abspath = Path(doc.abspath)
                    for name in doc.internal_resource_names:
                        abspath = p_abspath.resolve2(name)
                        if name[-1] == '/':
                            # folder
                            exclude_folders_path.append(str(abspath))
                        else:
                            # file
                            exclude_files_path.append(str(abspath))

            exclude_query = []
            for abspath in exclude_files_path:
                exclude_query.append(PhraseQuery('abspath', abspath))

            for abspath in exclude_folders_path:
                # Make get_base_path_query(xxx, include_container=True)
                exclude_query.append(PhraseQuery('abspath', abspath))
                exclude_query.append(StartQuery('abspath', '%s/' % abspath))

            if exclude_query:
                args.append(NotQuery(OrQuery(*exclude_query)))

        if self.ignore_box_aware:
            args.append(NotQuery(PhraseQuery('box_aware', True)))

        # Ok
        if len(args) == 1:
            query = args[0]
        else:
            query = AndQuery(*args)

        return root.search(query)


    def sort_and_batch(self, resource, context, results):
        user = context.user
        root = context.root

        start = self._get_query_value(resource, context, 'batch_start')
        size = self._get_query_value(resource, context, 'batch_size')
        sort_by = self._get_query_value(resource, context, 'sort_by')
        reverse = self._get_query_value(resource, context, 'reverse')

        if sort_by is None:
            get_key = None
        else:
            get_key = getattr(self, 'get_key_sorted_by_' + sort_by, None)
        if get_key:
            # Custom but slower sort algorithm
            items = results.get_documents()
            items.sort(key=get_key(), reverse=reverse)
            if size:
                items = items[start:start+size]
            elif start:
                items = items[start:]
        else:
            # Faster Xapian sort algorithm
            items = results.get_documents(sort_by=sort_by, reverse=reverse,
                                          start=start, size=size)

        # Access Control (FIXME this should be done before batch)
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        return allowed_items


    ###############################################
    ## Namespace
    ###############################################
    def get_batch_namespace(self, resource, context, items):
        if self.show_first_batch is False and self.show_second_batch is False:
            return None

        namespace = {}
        query_suffix = self._get_query_suffix()
        batch_start = self._get_query_value(resource, context, 'batch_start')
        uri = context.uri

        # Total & Size
        size = self._get_query_value(resource, context, 'batch_size')
        total = len(items)
        if size == 0:
            nb_pages = 1
            current_page = 1
        else:
            nb_pages = total / size
            if total % size > 0:
                nb_pages += 1
            current_page = (batch_start / size) + 1

        namespace['control'] = nb_pages > 1

        # Message (singular or plural)
        if total == 1:
            namespace['msg'] = self.batch_msg1.gettext()
        else:
            namespace['msg'] = self.batch_msg2.gettext(n=total)

        # See previous button ?
        if current_page != 1:
            previous = max(batch_start - size, 0)
            uri = self._context_uri_replace(context, batch_start=previous)
            namespace['previous'] = uri
        else:
            namespace['previous'] = None

        # See next button ?
        if current_page < nb_pages:
            uri = self._context_uri_replace(context,
                                            batch_start=batch_start+size)
            namespace['next'] = uri
        else:
            namespace['next'] = None

        # Add middle pages
        middle_pages = range(max(current_page - 3, 2),
                             min(current_page + 3, nb_pages-1) + 1)

        # Truncate middle pages if nedded
        if self.batch_max_middle_pages:
            middle_pages_len = len(middle_pages)
            if middle_pages_len > self.batch_max_middle_pages:
                delta = middle_pages_len - self.batch_max_middle_pages
                delta_start = delta_end = delta / 2
                if delta % 2 == 1:
                    delta_end = delta_end +1
                middle_pages = middle_pages[delta_start:-delta_end]

        pages = [1] + middle_pages
        if nb_pages > 1:
            pages.append(nb_pages)

        namespace['pages'] = [
            {'number': i,
             'css': 'current' if i == current_page else None,
             'uri': self._context_uri_replace(context,
                 batch_start=((i-1) * size))}
             for i in pages ]

        # Add ellipsis if needed
        if nb_pages > 5:
            ellipsis = {'uri': None}
            if 2 not in middle_pages:
                namespace['pages'].insert(1, ellipsis)
            if (nb_pages - 1) not in middle_pages:
                namespace['pages'].insert(len(namespace['pages']) - 1,
                                          ellipsis)

        return namespace


    def get_css(self, resource, context):
        return self.view_name


    def get_namespace(self, resource, context):
        self.view_resource = resource
        namespace = Folder_BrowseContent.get_namespace(self, resource, context)
        id = None
        if self.specific_id_wrapper:
            id = 'section-%s' % resource.name
        namespace['id'] = id
        namespace['css'] = self.get_css(resource, context)
        namespace['title'] = resource.get_property('title')
        namespace['display_title'] = self.display_title
        namespace['show_first_batch'] = self.show_first_batch
        namespace['show_second_batch'] = self.show_second_batch
        if self.show_first_batch and self.show_second_batch:
            # Transform batch generator into a list of events
            namespace['batch'] = list(namespace['batch'])
        namespace['content'] = namespace['table']
        return namespace


    #######################################################################
    # Table
    def get_table_head(self, resource, context, items, actions=None):
        # Get from the query
        query = context.query
        sort_by = self._get_query_value(resource, context, 'sort_by')
        reverse = self._get_query_value(resource, context, 'reverse')

        columns = self._get_table_columns(resource, context)
        columns_ns = []
        for name, title, sortable, css in columns:
            if name == 'checkbox':
                # Type: checkbox
                if self.external_form or actions:
                    columns_ns.append({'is_checkbox': True})
            elif title is None or not sortable:
                # Type: nothing or not sortable
                columns_ns.append({
                    'is_checkbox': False,
                    'title': title,
                    'css': 'thead-%s' % name,
                    'href': None,
                    'sortable': False})
            else:
                # Type: normal
                base_href = self._context_uri_replace(context, sort_by=name,
                                                      batch_start=None)
                if name == sort_by:
                    sort_up_active = reverse is False
                    sort_down_active = reverse is True
                else:
                    sort_up_active = sort_down_active = False
                columns_ns.append({
                    'is_checkbox': False,
                    'title': title,
                    'css': 'thead-%s' % name,
                    'sortable': True,
                    'href': context.uri.path,
                    'href_up': base_href.replace(reverse=0),
                    'href_down': base_href.replace(reverse=1),
                    'sort_up_active': sort_up_active,
                    'sort_down_active': sort_down_active
                    })
        return columns_ns


    def get_table_namespace(self, resource, context, items):
        return self.get_content_namespace(resource, context, items)


    def get_content_namespace(self, resource, context, items):
        namespace = {'items': []}
        for item in items:
            kw = {}
            for key in self.content_keys:
                kw[key] = self.get_item_value(resource, context, item, key)
            namespace['items'].append(kw)
        return namespace


    def get_item_value(self, resource, context, item, column):
        from ikaaro.file import Image

        item_brain, item_resource = item
        if column == 'class_icon16':
            return item_resource.get_class_icon()
        elif column == 'class_icon48':
            return item_resource.get_class_icon(size='48')
        elif column == 'pub_datetime':
            if item_brain.is_tagsaware:
                return item_resource.get_pub_datetime_formatted()
            return None
        elif column == 'title':
            return item_resource.get_title()
        elif column == 'long_title':
            if item_brain.is_tagsaware:
                return item_resource.get_long_title()
            return item_resource.get_title()
        elif column == 'link':
            return context.get_link(item_resource)
        elif column == 'abspath':
            site_root = item_resource.get_site_root()
            return '/%s' % site_root.get_pathto(item_resource)
        elif column == 'type':
            return item_resource.class_title.gettext()
        elif column == 'preview':
            if item_brain.is_tagsaware:
                return item_brain.preview_content
            return item_resource.get_property('description')
        elif column == 'is_image':
            return isinstance(item_resource, Image)
        elif column == 'image':
            if item_brain.is_tagsaware:
                thumbnail = item_resource.get_preview_thumbnail()
                if thumbnail:
                    return context.get_link(thumbnail)
            elif isinstance(item_resource, Image):
                return context.get_link(item_resource)
            return None
        elif column == 'tags':
            if item_brain.is_tagsaware:
                return item_resource.get_tags_namespace(context)
            return []
        elif column == 'css':
            if item_brain.abspath == resource.abspath:
                return 'active'
            return None
        return Folder_BrowseContent.get_item_value(self, resource, context,
            item, column)
