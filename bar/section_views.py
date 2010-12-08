# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@itaapy.com>
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
from itools.core import merge_dicts
from itools.gettext import MSG
from itools.uri import get_reference
from itools.database import AndQuery, OrQuery, PhraseQuery, NotQuery

# Import from ikaaro
from ikaaro.autoform import MultilineWidget, SelectWidget
from ikaaro.resource_views import DBResource_Edit
from ikaaro.workflow import state_widget, StaticStateEnumerate

# Import from itws
from bar_aware_views import EasyNewInstance_WithOrderer
from base_views import Bar_View
from itws.tags.tags_views import TagsAware_Edit
from itws.views import BaseManageContent
from itws.webpage import WebPage
from itws.feed_views import Feed_View, FeedViews_Enumerate, register_view



###########################################################################
# Section view
###########################################################################
class Section_ContentBar_View(Bar_View, Feed_View):

    title = MSG(u'View')
    access = 'is_allowed_to_view'

    view_name = 'composite-view'
    view_title = MSG(u'Composite view')

    order_name = 'order-contentbar'
    repository = '.'

    id = 'contentbar-items'
    order_name = 'order-contentbar'
    order_method = 'order_contentbar'
    order_label = MSG(u'Order Central Part Boxes')
    admin_bar_prefix_name = 'contentbar-box'
    boxes_css_class = 'contentbar-box'


    @property
    def container_cls(self):
        from bar_aware import ContentBarAware
        return ContentBarAware


    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        buttons = Bar_View.get_manage_buttons(self, resource, context)
        section_path = context.get_link(resource)
        buttons.append({'path': '%s/;new_contentbar_resource' % section_path,
                        'icon': '/ui/common/icons/16x16/new.png',
                        'rel': 'fancybox',
                        'label': MSG(u'Add Central Part Box'),
                        'target': None})

        return buttons


    def _get_item_id(self, item, context):
        return '%s-%s-%s' % (item.class_id, context._bar_aware.name, item.name)


    def _get_repository(self, resource, context):
        if resource.repository:
            return resource.get_resource(resource.repository)
        return resource


class Section_Edit(DBResource_Edit, TagsAware_Edit):


    def _get_schema(self, resource, context):
        return merge_dicts(DBResource_Edit._get_schema(self, resource, context),
                           TagsAware_Edit._get_schema(self, resource, context),
                           state=StaticStateEnumerate,
                           view=FeedViews_Enumerate(mandatory=True))


    def _get_widgets(self, resource, context):
        default_widgets = DBResource_Edit._get_widgets(self, resource, context)
        default_widgets[2] = MultilineWidget('description',
                                        title=MSG(u'Description (use by RSS and TAGS)'))
        return (default_widgets +
                [state_widget] +
                [SelectWidget('view', title=MSG(u'View'),
                              has_empty_option=False)] +
                TagsAware_Edit._get_widgets(self, resource, context))


    def get_value(self, resource, context, name, datatype):
        if name in ('tags', 'pub_date', 'pub_time'):
              return TagsAware_Edit.get_value(self, resource, context, name,
                        datatype)
        return DBResource_Edit.get_value(self, resource, context, name,
                  datatype)


    def set_value(self, resource, context, name, form):
        if name in ('tags', 'pub_date', 'pub_time'):
              return TagsAware_Edit.set_value(self, resource, context, name,
                        form)
        return DBResource_Edit.set_value(self, resource, context, name,
                  form)


class Section_AddContent(EasyNewInstance_WithOrderer):

    title=  MSG(u'Add content')

    order_widget_title = MSG(u'Order content in the TOC ?')


    def _get_container(self, resource, context):
        return resource

    def _get_order_table(self, resource, context):
        return resource.get_resource(resource.order_path)


    def _get_box_goto(self, child, context):
        link_child = '%s/;edit' % context.get_link(child)
        return get_reference(link_child)


    def get_aware_document_types(self, resource, context):
        from section import Section
        return [Section, WebPage]



class Section_ManageContent(BaseManageContent):

    title = MSG(u'Browse')

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        excluded_names = resource.get_internal_use_resource_names()
        query = [ PhraseQuery('parent_path', path),
                 NotQuery(OrQuery(*[ PhraseQuery('name', name)
                                     for name in excluded_names ]))]
        return context.root.search(AndQuery(*query))


register_view(Section_ContentBar_View)
