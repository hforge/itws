# -*- coding: UTF-8 -*-
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010-2011 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.database import AndQuery, NotQuery, PhraseQuery
from itools.database import OrQuery, TextQuery
from itools.datatypes import Integer, String, Boolean
from itools.gettext import MSG
from itools.web import FormError

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.utils import get_base_path_query
from ikaaro.website import WebSite
from ikaaro.workflow import get_workflow_preview

# Import from itws
from itws.utils import ITWS_Autoform, render_for_datatype



###########################################
# See bug:
# http://bugs.hforge.org/show_bug.cgi?id=1100
###########################################

class Feed_View(Folder_BrowseContent):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    table_template = None

    # View configuration
    view_name = None
    template = '/ui/feed_views/base_feed_view_div.xml'
    content_template = '/ui/feed_views/Tag_item_viewbox.xml'
    context_menus = []
    styles = []
    show_first_batch = False
    show_second_batch = True
    display_title = True
    show_resource_title = True
    batch_size = 25
    sort_by = 'title'
    reverse = False
    content_keys = ('pub_datetime', 'title', 'long_title',
                    'link', 'is_image', 'preview',
                    'tags', 'workflow_state',
                    'image', 'css', 'class_icon16', 'class_icon48',
                    'type', 'abspath')

    # Add an id to a wrapper div based on resource name
    specific_id_wrapper = True

    # Search configuration
    search_title = MSG(u'Search')
    search_template = '/ui/feed_views/base_search_template.xml'
    search_class_id = None
    search_css = None
    search_on_current_folder = True
    search_on_current_folder_recursive = False
    search_widgets = []
    search_schema = {}
    search_advanced_title = MSG(u'(Switch to simple/advanded mode)')

    # Get items configuration
    ignore_internal_resources = False
    ignore_box_aware = True

    # We save view_resource to allow to add @property methods
    # that get view configuration from a resource
    # (Fox example to configure table_template directly on the resource)
    view_resource = None


    def get_query_schema(self):
        # We allow to define 2 variable (sort_by and batch_size)
        return merge_dicts(Folder_BrowseContent.get_query_schema(self),
                           batch_size=Integer(default=self.batch_size),
                           sort_by=String(default=self.sort_by),
                           reverse=Boolean(default=self.reverse))


    @property
    def table_template(self):
        # We rename table_template by content_template
        # That's more explicit
        return self.content_template


    def _get_container(self, resource, context):
        # XXX Add documentation
        if self.search_on_current_folder is True:
            return resource
        # Current website
        return context.resource.get_site_root()

    ###############################################
    ## Build query and get items
    ###############################################
    def on_query_error(self, resource, context):
        # XXX Should be donne in ikaaro
        context.message = context.query_error.get_message()
        # Keep max of query
        query = {}
        for name, datatype in self.get_query_schema().items():
            try:
                query[name] = context.get_query_value(name, type=datatype)
            except FormError:
                query[name] = datatype.get_default()
        context.query = query
        return self.GET


    def get_search_query(self, resource, context):
        queries = []
        form = context.query
        for key, datatype in self.search_schema.items():
            if form[key] and key == 'text':
                queries.append(TextQuery(key, form[key]))
            elif form[key] and datatype.multiple is True:
                queries.append(OrQuery(*[PhraseQuery(key, x) for x in form[key]]))
            elif form[key]:
                queries.append(PhraseQuery(key, form[key]))
        return queries


    def get_content_query(self, resource, context):
        args = []
        # Check parameters
        if self.search_on_current_folder and self.search_on_current_folder_recursive:
            msg = '{0} and {1} are mutually exclusive.'
            raise ValueError, msg.format('search_on_current_folder',
                                         'search_on_current_folder_recursive')
        # Get the container
        container = self._get_container(resource, context)
        container_abspath = container.get_canonical_path()
        if self.search_on_current_folder is True:
            # Limit result to direct children
            args.append(PhraseQuery('parent_path', str(container_abspath)))
        else:
            # Limit results to whole sub children
            args.append(get_base_path_query(str(container_abspath)))

        # Search specific format ?
        if self.search_class_id is not None:
            args.append(PhraseQuery('format', self.search_class_id))
        # Search only on current folder ?
        if self.search_on_current_folder_recursive is True:
            # Already done before, because if search_on_current_folder and
            # search_on_current_folder_recursive are exclusive

            # Exclude '/theme/'
            if isinstance(resource, WebSite):
                theme_path = container_abspath.resolve_name('theme')
                theme = get_base_path_query(str(theme_path), True)
                args.append(NotQuery(theme))

        # Ignore resources
        if self.ignore_internal_resources:
            args.append(PhraseQuery('is_content', True))

        if self.ignore_box_aware:
            args.append(NotQuery(PhraseQuery('box_aware', True)))
        return args


    def get_items(self, resource, context, *args):
        root = context.root
        # Query
        queries = list(args)

        # Content Query
        content_query = self.get_content_query(resource, context)
        if content_query:
            queries.extend(content_query)

        # Search Query
        search_query = self.get_search_query(resource, context)
        if search_query:
            queries.extend(search_query)

        # Transform list of queries into a query
        if len(queries) == 1:
            query = queries[0]
        else:
            query = AndQuery(*queries)

        # Search
        return root.search(query)

    ###############################################
    ## CSS Class / ID
    ###############################################
    def get_css(self, resource, context):
        return self.view_name


    def get_css_id(self, resource, context):
        if self.specific_id_wrapper:
            return 'section-%s' % resource.name
        return None

    ###############################################
    ## Namespace
    ###############################################
    def get_title(self, context):
        if self.show_resource_title:
            return context.resource.get_title()
        return self.title


    def get_namespace(self, resource, context):
        self.view_resource = resource
        # Build namespace
        namespace = Folder_BrowseContent.get_namespace(self, resource, context)
        namespace['id'] = self.get_css_id(resource, context)
        namespace['css'] = self.get_css(resource, context)
        namespace['title'] = self.get_title(context)
        namespace['display_title'] = self.display_title
        namespace['show_first_batch'] = self.show_first_batch
        namespace['show_second_batch'] = self.show_second_batch
        # If we show 2 batch, we transform generator into list
        if self.show_first_batch and self.show_second_batch:
            namespace['batch'] = list(namespace['batch'])
        namespace['content'] = namespace['table']
        return namespace


    def get_batch_namespace(self, resource, context, items):
        # Do not calculate batch if we don't show it
        if self.show_first_batch or self.show_second_batch:
            proxy = super(Feed_View, self)
            return proxy.get_batch_namespace(resource, context, items)
        return None


    def get_search_namespace(self, resource, context):
        # http://bugs.hforge.org/show_bug.cgi?id=997
        search_button = Button(access=True,
            resource=resource, context=context,
            css='button-search', title=self.search_title)
        form = ITWS_Autoform(
            css=self.search_css,
            title=self.search_title,
            schema=self.search_schema,
            advanced_title=self.search_advanced_title,
            get_value_method=context.get_query_value,
            widgets=self.search_widgets,
            actions=[search_button])
        return {'body': form.render(context)}


    def get_table_namespace(self, resource, context, items):
        # Just because we rename table_namespace by content_namespace
        return self.get_content_namespace(resource, context, items)


    def get_content_namespace(self, resource, context, items):
        namespace = {'items': []}
        for item in items:
            kw = {}
            for key in self.content_keys:
                kw[key] = self.get_item_value(resource, context, item, key)
            namespace['items'].append(kw)
        return namespace


    def get_schema_value(self, resource, column, datatype):
        if datatype.source == 'metadata':
            value = resource.get_property(column)
        elif datatype.source == 'computed':
            value = resource.get_computed_property(column)
        return value


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
        elif column == 'format':
            return item_resource.class_title.gettext()
        elif column == 'last_author':
            author =  item_brain.last_author
            return context.root.get_user_title(author) if author else None
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
        elif column == 'workflow_state':
            return get_workflow_preview(item_resource, context)
        # We guess from class_schema
        # http://bugs.hforge.org/show_bug.cgi?id=1202
        schema = item_resource.class_schema
        if  schema.has_key(column):
            datatype = schema[column]
            value = self.get_schema_value(item_resource, column, datatype)
            return render_for_datatype(value, datatype, context)
        return Folder_BrowseContent.get_item_value(self, resource, context,
            item, column)
