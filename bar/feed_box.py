# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
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
from itools.core import freeze, merge_dicts
from itools.database import OrQuery, PhraseQuery
from itools.datatypes import Boolean, Enumerate, PathDataType
from itools.gettext import MSG
from itools.uri import Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget, SelectWidget, TextWidget
from ikaaro.autoform import RadioWidget
from ikaaro.utils import get_content_containers
from ikaaro.workflow import state_widget, StaticStateEnumerate

# Import from itws
from base import Box
from base import display_title_widget, title_link_schema, title_link_widgets
from base_views import Box_View
from itws.datatypes import PositiveInteger, SortBy_Enumerate
from itws.feed_views import Details_View
from itws.tags import TagsList, TagsAwareClassEnumerate
from itws.tags import get_registered_tags_aware_classes
from itws.utils import automatic_get_links
from itws.widgets import DualSelectWidget



class TagsAwareContainerPathDatatype(Enumerate):

    def get_allowed_class_ids(cls):
        _classes = get_registered_tags_aware_classes()
        return [ _cls.class_id for _cls in _classes ]


    def get_options(cls):
        context = get_context()

        allowed_class_ids = cls.get_allowed_class_ids()
        skip_formats = set()
        items = []
        for resource in get_content_containers(context, skip_formats):
            for cls in resource.get_document_types():
                if cls.class_id in allowed_class_ids:
                    break
            else:
                skip_formats.add(resource.class_id)
                continue

            path = context.site_root.get_pathto(resource)
            title = '/' if not path else ('/%s/' % path)
            # Next
            items.append({'name': path, 'value': title, 'selected': False})

        # Sort
        items.sort(key=lambda x: x['name'])
        return items



class BoxFeed_Enumerate(Enumerate):

    options = [
      {'name': '/ui/feed_views/Tag_item_viewbox.xml',
       'value': MSG(u'Preview'), 'css': 'v3'},
      {'name': '/ui/feed_views/NewsItem_preview_with_thumbnail.xml',
       'value': MSG(u'Title with thumbnail'), 'css': 'v2'},
      {'name': '/ui/feed_views/NewsItem_preview.xml',
       'value': MSG(u'Title only'), 'css': 'v1'}]



class BoxFeed_View(Box_View, Details_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    template = '/ui/bar_items/BoxFeed_view.xml'

    view_name = 'feed-box'

    # Configuration
    batch_template = None

    search_on_current_folder = False
    search_on_current_folder_recursive = False

    specific_id_wrapper = False


    def get_query_schema(self):
        return {}


    @property
    def table_template(self):
        view_resource = self.view_resource
        return view_resource.get_property('view')


    def _get_container(self, resource, context):
        site_root = context.resource.get_site_root()
        path = resource.get_property('container_path')
        # path is relative to current website
        if path == '/':
            return site_root
        return site_root.get_resource(path)


    def get_items(self, resource, context, *args):
        args = list(args)
        tags = resource.get_property('tags')
        if tags:
            tags_query = [ PhraseQuery('tags', x) for x in tags ]
            if len(tags_query) == 1:
                args.append(tags_query[0])
            else:
                args.append(OrQuery(*tags_query))
        formats = resource.get_property('feed_class_id')
        if formats:
            formats_query = [ PhraseQuery('format', x) for x in formats ]
            if len(formats_query) == 1:
                args.append(formats_query[0])
            else:
                args.append(OrQuery(*formats_query))
        proxy = super(BoxFeed_View, self)
        return proxy.get_items(resource, context, *args)


    def sort_and_batch(self, resource, context, results):
        root = context.root
        user = context.user
        items = results.get_documents(sort_by=resource.get_property('sort_by'),
                                      reverse=resource.get_property('reverse'),
                                      start=0,
                                      size=resource.get_property('count'))
        # Access Control (FIXME this should be done before batch)
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        # FIXME BoxView API
        allowed_to_edit = self.is_admin(resource, context)
        if allowed_to_edit is False and len(allowed_items) == 0:
            self.set_view_is_empty(True)

        return allowed_items


    def get_css(self, resource, context):
        # get css from template
        template = self.table_template
        for option in BoxFeed_Enumerate.get_options():
            if option['name'] == template:
                css = option['css']
                break
        else:
            css = ''
        return '%s %s' % (self.view_name, css)


    def get_namespace(self, resource, context):
        proxy = super(BoxFeed_View, self)
        namespace = proxy.get_namespace(resource, context)
        for name in ('display_title', 'title_link', 'title_link_target'):
            namespace[name] = resource.get_property(name)
        return namespace



class BoxFeed(Box):
    # XXX We have to refactor BoxFeed_View

    class_id = 'box-feed'
    class_title = MSG(u'Feed')
    class_description = MSG(u'Display the feed of a content from the website')
    class_version = '20101228'
    class_icon16 = 'bar_items/icons/16x16/box_feed.png'
    class_icon48 = 'bar_items/icons/48x48/box_feed.png'
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    class_schema = merge_dicts(
            Box.class_schema,
            title_link_schema,
            container_path=PathDataType(source='metadata', default='/'),
            count=PositiveInteger(source='metadata', default=3),
            sort_by=SortBy_Enumerate(source='metadata', default='pub_datetime'),
            reverse=Boolean(source='metadata', default=True),
            display_title=Boolean(source='metadata', default=True),
            feed_class_id=TagsAwareClassEnumerate(source='metadata',
                                                  multiple=True),
            tags=TagsList(source='metadata', multiple=True, default=[]),
            view=BoxFeed_Enumerate(source='metadata',
                default='/ui/feed_views/NewsItem_preview_with_thumbnail.xml'))

    # Configuration
    allow_instanciation = True
    is_sidebox = True
    is_contentbox = True

    # Automatic Edit View
    edit_schema = freeze(merge_dicts({
             'container_path': TagsAwareContainerPathDatatype,
             'count': PositiveInteger(default=3),
             'display_title': Boolean,
             'feed_class_id': TagsAwareClassEnumerate(multiple=True,
                                                      mandatory=True),
             'sort_by': SortBy_Enumerate,
             'reverse': Boolean(default=True),
             'tags': TagsList(multiple=True, states=[]),
             'view': BoxFeed_Enumerate,
             'state': StaticStateEnumerate},
             title_link_schema))


    edit_widgets = freeze(
        [ display_title_widget ] +
        title_link_widgets +
        [ SelectWidget('container_path', title=MSG(u'Container'),
                     has_empty_option=False),
        CheckboxWidget('feed_class_id', title=MSG(u'Feed Source'),
                       has_empty_option=True),
        SelectWidget('view', title=MSG(u'Feed template'),
                     has_empty_option=False),
        SelectWidget('sort_by', title=MSG(u'Sort by'),
                     has_empty_option=False),
        RadioWidget('reverse', title=MSG(u'Reverse'), oneline=True),
        TextWidget('count',
                   title=MSG(u'Number of items to show (0 = All)'), size=3),
        DualSelectWidget('tags', title=MSG(u'Show only items with these tags'),
                         is_inline=True, has_empty_option=False),
        state_widget])


    # Views
    view = BoxFeed_View()


    def get_links(self):
        base = self.get_canonical_path()
        links = super(BoxFeed, self).get_links()
        container_path = self.get_property('container_path')
        if container_path:
            site_root = self.get_site_root()
            if container_path == '/':
                # site root
                links.add(str(site_root.abspath))
            else:
                abs_path = site_root.abspath.resolve2(container_path)
                links.add(str(abs_path))
        links.update(automatic_get_links(self, ['title_link']))
        return links


    def update_links(self, source, target):
        super(BoxFeed, self).update_links(source, target)

        container_path = self.get_property('container_path')
        if container_path:
            if container_path == '/':
                # Even if site_root is renammed, '/' is '/'
                pass
            else:
                resources_new2old = get_context().database.resources_new2old
                site_root_abspath = self.get_site_root().abspath
                base = str(site_root_abspath)
                old_base = resources_new2old.get(base, base)
                old_base = Path(old_base)
                # Path is relative to site_root
                path = old_base.resolve2(container_path)

                if path == source:
                    # Hit the old name
                    new_path = site_root_abspath.get_pathto(target)
                    self.set_property('container_path', new_path)


    def update_relative_links(self, source):
        super(BoxFeed, self).update_relative_links(source)

        container_path = self.get_property('container_path')
        if container_path:
            if container_path == '/':
                # Even if site_root is renammed, '/' is '/'
                pass
            else:
                # FIXME Should do nothing since container_path
                # is inside the site_root
                site_root = self.get_site_root()
                site_root_abspath = site_root.abspath

                target = self.get_canonical_path()
                resources_old2new = get_context().database.resources_old2new
                # Calcul the old absolute path
                # Path is relative to site_root
                old_abs_path = site_root_abspath.resolve2(container_path)
                # Check if the target path has not been moved
                new_abs_path = resources_old2new.get(old_abs_path,
                                                     old_abs_path)
                new_path = site_root_abspath.get_pathto(new_abs_path)
                self.set_property('container_path', new_path)

