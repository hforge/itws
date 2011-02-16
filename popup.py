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
from itools.core import freeze
from itools.database import NotQuery, OrQuery, PhraseQuery

# Import from ikaaro
from ikaaro.autoform import SelectWidget
from ikaaro.file import Image
from ikaaro.popup import AddMedia_BrowseContent, AddImage_BrowseContent
from ikaaro.popup import DBResource_AddLink, DBResource_AddMedia
from ikaaro.popup import DBResource_AddImage, AddBase_BrowseContent
from ikaaro.utils import get_base_path_query

# Import from itws
from itws.datatypes import SortBy_Enumerate, Reverse_Enumerate
from itws.feed_views import Feed_View



##################################################
# Some methods
##################################################
def get_itws_namespace(cls, self, resource, context):
    namespace = cls.get_namespace(self, resource, context)
    # XXX Hack breadcrumb
    breadcrumb = []
    for x in namespace['breadcrumb']:
        x['url'] = x['url'].replace(batch_start=None)
        breadcrumb.append(x)
    namespace['breadcrumb'] = breadcrumb
    return namespace


def itws_get_item_value(self, resource, context, item, column):
    brain, item_resource = item
    if column == 'js_link':
        id = str(resource.get_canonical_path().get_pathto(brain.abspath))
        id += self.resource_action
        return id
    elif column == 'is_selectable':
        return isinstance(item_resource, self.get_item_classes())
    elif column == 'link':
        if self.is_folder(item_resource):
            path_to_item = context.site_root.get_pathto(item_resource)
            url_dic = {'target': str(path_to_item),
                       # Avoid search conservation
                       'search_text': None,
                       'search_type': None,
                       # Reset batch
                       'batch_start': None}
            return context.uri.replace(**url_dic)
        return None
    return Feed_View.get_item_value(self, resource, context, item, column)


def itws_get_table_namespace(self, resource, context, items):
    namespace =  Feed_View.get_table_namespace(self, resource, context, items)
    # Sort by
    widget = SelectWidget('sort_by',
                          datatype=SortBy_Enumerate,
                          value=context.query['sort_by'],
                          has_empty_option=False)
    namespace['sort_by'] = widget.render()
    widget = SelectWidget('reverse',
                          datatype=Reverse_Enumerate,
                          value=str(int(context.query['reverse'])),
                          has_empty_option=False)
    namespace['reverse'] = widget.render()
    for key in ['target', 'target_id', 'mode']:
        namespace[key] = context.get_form_value(key)
    # If target is no defined in the query (when we open the popup)
    # Get the target value from attributes
    if namespace['target'] is None:
        popup_root_abspath = self.popup_root.get_abspath()
        target = popup_root_abspath.get_pathto(self.target.get_abspath())
        namespace['target'] = target
    return namespace


def itws_get_additional_args(resource):
    args = []
    # Current folder
    abspath = resource.get_canonical_path()
    args.append(PhraseQuery('parent_path', str(abspath)))
    # Ignore query
    method = getattr(resource, 'get_internal_use_resource_names', None)
    if method:
        exclude_query = []
        resource_abspath = resource.get_abspath()
        for name in method():
            abspath = resource_abspath.resolve2(name)
            q = get_base_path_query(str(abspath), include_container=True)
            exclude_query.append(q)
        args.append(NotQuery(OrQuery(*exclude_query)))
    return args
##################################################
##################################################


class ITWS_AddBase_BrowseContent(Feed_View, AddBase_BrowseContent):

    table_template = '/ui/common/popup_browse_content.xml'
    content_keys = Feed_View.content_keys + ('js_link', 'link', 'is_selectable')

    hidden_fields = freeze(Feed_View.hidden_fields +
                           AddBase_BrowseContent.hidden_fields + ['target'])

    def _get_query_value(self, resource, context, name):
        if name == 'target':
            # Target is a special case
            site_root = resource.get_site_root()
            target = self._get_target(resource, context)
            return site_root.get_pathto(target)
        return Feed_View._get_query_value(self, resource, context, name)


    def _get_target(self, resource, context):
        query_target = context.get_form_value('target')
        if query_target is None:
            target = self.target
        else:
            site_root = resource.get_site_root()
            target = site_root.get_resource(query_target)
        return target


    def get_items(self, resource, context, *args):
        target = self._get_target(resource, context)
        args = list(args)
        args.extend(itws_get_additional_args(self.target))
        return AddBase_BrowseContent.get_items(self, target, context, *args)


    def get_search_types(self, resource, context):
        target = self._get_target(resource, context)
        return Feed_View.get_search_types(self, target, context)


    def get_table_namespace(self, resource, context, items):
        return itws_get_table_namespace(self, resource, context, items)


    def get_item_value(self, resource, context, item, column):
        return itws_get_item_value(self, resource, context, item, column)



class ITWS_AddMedia_BrowseContent(Feed_View, AddMedia_BrowseContent):

    table_template = '/ui/common/popup_browse_content.xml'
    content_keys = Feed_View.content_keys + ('js_link', 'link', 'is_selectable')


    def get_items(self, resource, context, *args):
        args = list(args)
        args.extend(itws_get_additional_args(self.target))
        return AddMedia_BrowseContent.get_items(self, resource, context, *args)


    def get_table_namespace(self, resource, context, items):
        return itws_get_table_namespace(self, resource, context, items)


    def get_item_value(self, resource, context, item, column):
        return itws_get_item_value(self, resource, context, item, column)



class ITWS_AddImage_BrowseContent(Feed_View, AddImage_BrowseContent):

    table_template = '/ui/common/popup_browse_content.xml'
    content_keys = Feed_View.content_keys + ('js_link', 'link', 'is_selectable')
    item_classes = (Image,)


    def get_items(self, resource, context, *args):
        args = list(args)
        args.extend(itws_get_additional_args(self.target))
        return AddImage_BrowseContent.get_items(self, resource, context, *args)


    def get_table_namespace(self, resource, context, items):
        return itws_get_table_namespace(self, resource, context, items)


    def get_item_value(self, resource, context, item, column):
        return itws_get_item_value(self, resource, context, item, column)



class ITWS_DBResource_AddLink(DBResource_AddLink):

    browse_content_class = ITWS_AddBase_BrowseContent


    def get_namespace(self, resource, context):
        return get_itws_namespace(DBResource_AddLink, self, resource, context)



class ITWS_DBResource_AddImage(DBResource_AddImage):

    browse_content_class = ITWS_AddImage_BrowseContent


    def get_namespace(self, resource, context):
        return get_itws_namespace(DBResource_AddImage, self, resource, context)



class ITWS_DBResource_AddMedia(DBResource_AddMedia):

    browse_content_class = ITWS_AddMedia_BrowseContent


    def get_namespace(self, resource, context):
        return get_itws_namespace(DBResource_AddMedia, self, resource, context)
