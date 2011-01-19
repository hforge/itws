# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
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
from itools.gettext import MSG
from itools.database import OrQuery, PhraseQuery
from itools.datatypes import PathDataType
from itools.datatypes import Enumerate, String
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget, SelectWidget, TextWidget
from ikaaro.utils import get_content_containers

# Import from itws
from base import Box
from base_views import Box_View
from itws.datatypes import PositiveInteger
from itws.feed_views import Details_View
from itws.tags import TagsList, TagsAwareClassEnumerate
from itws.tags import get_registered_tags_aware_classes
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

    # XXX Why V2 is commented ???
    options = [
      {'name': '/ui/feed_views/Tag_item_viewbox.xml', 'value': MSG(u'V3')},
#      {'name': '/ui/news/SectionNews_view.xml', 'value': MSG(u'V2')},
      {'name': '/ui/feed_views/NewsItem_preview.xml', 'value': MSG(u'V1')}]



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
            args.append(OrQuery(*[PhraseQuery('tags', x) for x in tags]))
        formats = resource.get_property('feed_class_id')
        if formats:
            args.append(OrQuery(*[PhraseQuery('format', x) for x in formats]))
        return Details_View.get_items(self, resource, context, *args)


    def sort_and_batch(self, resource, context, results):
        root = context.root
        user = context.user
        items = results.get_documents(sort_by='pub_datetime',
                                      reverse=True,
                                      start=0,
                                      size=resource.get_property('count'))
        # Access Control (FIXME this should be done before batch)
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))
        return allowed_items



class BoxFeed(Box):
    # XXX We have to refactor BoxFeed_View

    class_id = 'box-feed'
    class_title = MSG(u'Box to feed items')
    class_version = '20101228'
    class_icon16 = 'bar_items/icons/16x16/box_section_news.png'
    class_description = MSG(u'Display the last N items (Webpage/News) '
                            u'filtered by tags')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    class_schema = merge_dicts(
            Box.class_schema,
            feed_class_id=TagsAwareClassEnumerate(source='metadata',
                                                  multiple=True),
            feed_source=String(source='metadata', multiple=True),
            view=BoxFeed_Enumerate(source='metadata'),
            count=PositiveInteger(source='metadata', default=3),
            tags=TagsList(source='metadata', multiple=True, default=[]),
            container_path=PathDataType(source='metadata', default='/'))

    # Configuration
    allow_instanciation = True
    is_side = True
    is_content = True

    # Automatic Edit View
    edit_schema = freeze(
            {'feed_class_id': TagsAwareClassEnumerate(multiple=True),
             'view': BoxFeed_Enumerate,
             'count': PositiveInteger(default=3),
             'tags': TagsList(multiple=True),
             'container_path': TagsAwareContainerPathDatatype})


    edit_widgets = freeze([
        SelectWidget('container_path', title=MSG(u'Container'),
                     has_empty_option=False),
        CheckboxWidget('feed_class_id', title=MSG(u'Feed Source'),
                       has_empty_option=True),
        SelectWidget('view', title=MSG(u'Feed template'),
                     has_empty_option=False),
        TextWidget('count',
                   title=MSG(u'Number of items to show (0 = All)'), size=3),
        DualSelectWidget('tags', title=MSG(u'Show only items with this TAGS'),
                         is_inline=True, has_empty_option=False)])


    # Views
    view = BoxFeed_View()


    def update_20101228(self):
        # XXX Update for developers
        self.set_property('view', '/ui/feed_views/Tag_item_viewbox.xml')
