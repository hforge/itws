# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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
from types import GeneratorType

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.stl import stl, set_prefix
from itools.uri import get_reference, Reference
from itools.web import get_context, BaseView, STLView
from itools.database import PhraseQuery, NotQuery, OrQuery, AndQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import ImageSelectorWidget, SelectWidget, TextWidget
from ikaaro.datatypes import Multilingual
from ikaaro.resource_views import DBResource_Edit
from ikaaro.website import NotFoundView as BaseNotFoundView

# Import from itws
from bar import ContentBar_View, SideBar_View
from datatypes import NeutralClassSkin
from section import Section
from tags import TagsAware
from utils import set_navigation_mode_as_edition
from utils import set_navigation_mode_as_navigation
from views import BaseManageContent
from views import BaseRSS, ProxyContainerNewInstance
from views import BarAwareBoxAwareNewInstance




############################################################
# Views
############################################################
class NotFoundPage_View(BaseNotFoundView):

    not_found_template = '404'

    def get_template(self, resource, context):
        site_root = resource.get_site_root()
        template = site_root.get_resource(self.not_found_template, soft=True)
        if template and not template.handler.is_empty():
            # When 404 occurs context.resource is the last valid resource
            # in the context.path. We need to compute prefix from context.path
            # instead of context.resource
            path = site_root.get_abspath().resolve2('.%s' % context.path)
            prefix = path.get_pathto(template.get_abspath())
            return set_prefix(template.handler.events, '%s/' % prefix)
        # default
        return BaseNotFoundView.get_template(self, resource, context)


    def GET(self, resource, context):
        # Get the namespace
        namespace = self.get_namespace(resource, context)
        if isinstance(namespace, Reference):
            return namespace

        # STL
        template = self.get_template(resource, context)
        if isinstance(template, (GeneratorType, XMLParser)):
            return stl(events=template, namespace=namespace)
        return stl(template, namespace)



class NeutralWS_Edit(DBResource_Edit):

    def _get_schema(self, resource, context):
        return merge_dicts(DBResource_Edit._get_schema(self, resource, context),
                           breadcrumb_title=Multilingual,
                           banner_title=Multilingual,
                           banner_path=Multilingual,
                           class_skin=NeutralClassSkin(mandatory=True))


    def _get_widgets(self, resource, context):
        widgets = DBResource_Edit._get_widgets(self, resource, context)[:]
        # Breadcrumb title
        widgets.append(
            TextWidget('breadcrumb_title', title=MSG(u'Breadcrumb title')))
        # banner_title
        widgets.append(
            TextWidget('banner_title', title=MSG(u'Banner title'),
                       tip=MSG(u'(Use as banner if there is no image banner)')))
        # banner_path
        widgets.append(
            ImageSelectorWidget('banner_path', title=MSG(u'Banner path'),
                                width=640))
        # class_skin
        widgets.append(
            SelectWidget('class_skin', title=MSG(u'Skin'),
                         has_empty_option=False))

        # ok
        return widgets





class NeutralWS_RSS(BaseRSS):

    excluded_formats = freeze(['rssfeeds', 'text/css'])


    def get_base_query(self, resource, context):
        query = BaseRSS.get_base_query(self, resource, context)
        query.append(PhraseQuery('workflow_state', 'public'))
        return query


    def get_excluded_paths(self, resource, context):
        site_root = resource.get_site_root()
        site_root_abspath = site_root.get_abspath()
        excluded = []
        for name in ('./404',):
            excluded.append(site_root_abspath.resolve2(name))
        return excluded


    def get_excluded_container_paths(self, resource, context):
        site_root = resource.get_site_root()
        site_root_abspath = site_root.get_abspath()
        excluded = []
        for name in ('./menu/', './repository/', './ws-data/',
                     './footer/', './turning-footer/', './tags/'):
            excluded.append(site_root_abspath.resolve2(name))
        return excluded


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column == 'pubDate':
            if isinstance(item_resource, TagsAware):
                return brain.pub_datetime
            else:
                return brain.mtime
        elif column == 'title':
            # Special case for the title
            title = item_resource.get_title()
            # FIXME
            if brain.name == 'index':
                parent = item_resource.parent
                if isinstance(parent, Section):
                    title = parent.get_title()
            return title

        return BaseRSS.get_item_value(self, resource, context, item,
                                      column, site_root)




class NeutralWS_BarAwareBoxAwareNewInstance(BarAwareBoxAwareNewInstance):

    is_content = True
    is_side = None

    def _get_container(self, resource, context):
        site_root = resource.get_site_root()
        return site_root.get_resource('ws-data')



class NeutralWS_ContentBar_View(ContentBar_View):

    order_name = 'ws-data/order-contentbar'

    def _get_repository(self, resource, context):
        return resource.get_resource('ws-data')



class NeutralWS_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'Website View')
    template = '/ui/common/Neutral_view.xml'

    subviews = {'contentbar_view': NeutralWS_ContentBar_View(),
                'sidebar_view':
            SideBar_View(order_name='ws-data/order-sidebar')}

    def get_subviews_value(self, resource, context, view_name):
        view = self.subviews.get(view_name)
        if view is None:
            return None
        return view.GET(resource, context)


    def get_namespace(self, resource, context):
        namespace = {}

        # Subviews
        for view_name in self.subviews.keys():
            namespace[view_name] = self.get_subviews_value(resource,
                                                           context, view_name)

        return namespace



class NeutralWS_FOSwitchMode(BaseView):

    access = 'is_allowed_to_edit'
    query_schema = {'mode': Boolean(default=False)}

    def GET(self, resource, context):
        edit = context.query['mode']
        if edit:
            set_navigation_mode_as_edition(context)
        else:
            set_navigation_mode_as_navigation(context)

        referer = context.get_referrer()
        if referer:
            # FIXME Check if referer is fo_switch_mode
            goto = referer
        else:
            goto = '/'

        return get_reference(goto)





class WSDataFolder_ManageContent(BaseManageContent):

    title = MSG(u'Manage Homepage')

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        excluded_names = resource.get_internal_use_resource_names()
        query = [ PhraseQuery('parent_path', path),
                  NotQuery(OrQuery(*[ PhraseQuery('name', name)
                                      for name in excluded_names ]))]
        return context.root.search(AndQuery(*query))
