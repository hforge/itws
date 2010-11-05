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

# Import from standard library
from warnings import warn

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.autoform import RadioWidget, TextWidget

# Import from itws
from base import Box
from base_views import Box_View
from news import BoxSectionNews_View, BoxNewsSiblingsToc_Preview
from itws.datatypes import PositiveInteger


hide_single_schema = freeze({'hide_if_only_one_item': Boolean(default=True)})
hide_single_widget = RadioWidget('hide_if_only_one_item',
        title=MSG(u'Hide if there is only one item'))





################################################################################
# View
################################################################################
class BoxSectionChildrenTree_View(Box_View):

    template = '/ui/bar_items/SectionChildrenTree_view.xml'

    def GET(self, resource, context):
        from itws.bar import Section

        section = context._bar_aware
        if isinstance(section, Section) is False:
            self.set_view_is_empty(True)
            return None

        section_class = section.get_subsection_class()
        base_section = self._get_base_section(section, section_class)
        if isinstance(base_section, section_class) is False:
            # Strange
            self.set_view_is_empty(True)
            return None

        return STLView.GET(self, base_section, context)


    def _get_base_section(self, section, section_cls):
        # FIXME section_cls may change
        resource = section
        while isinstance(resource.parent, section_cls):
            resource = resource.parent
        return resource


    def _get_items(self, section, context, here_abspath):
        user = context.user
        section_link = context.get_link(section)
        section_class = section.get_subsection_class()
        items = []

        for name in section.get_ordered_names():
            item = section.get_resource(name, soft=True)
            sub_items = []
            if item is None:
                warn(u'resource "%s" not found' % name)
                continue

            # Check security
            ac = item.get_access_control()
            if ac.is_allowed_to_view(user, item) is False:
                continue

            item_abspath = item.get_abspath()
            # css
            css = None
            if item_abspath == here_abspath:
                css = 'active'
            elif here_abspath.get_prefix(item_abspath) ==  item_abspath:
                css = 'in-path'
            # link
            is_section = type(item) == section_class
            path = context.get_link(item)
            # subsections
            if is_section:
                if item_abspath.get_prefix(here_abspath) == item_abspath:
                    # deploy sub sections
                    sub_items = self._get_items(item, context, here_abspath)
            items.append({'path': path, 'title': item.get_title(),
                'class': css, 'sub_items': sub_items})

        return items


    def get_toc_title(self, resource, context):
        return resource.get_property('title')


    def get_items(self, resource, context):
        here = context.resource
        # resource is the base section
        section_class = resource.get_subsection_class()
        items = self._get_items(resource, context, here.get_abspath())

        return items


    def get_namespace(self, resource, context):
        namespace = {}
        allowed_to_edit = self.is_admin(resource, context)

        # Subsections (siblings)
        items = self.get_items(resource, context)
        namespace['items'] = items
        namespace['title'] = self.get_toc_title(resource, context)

        # Hide siblings box if the user is not authenticated and
        # submenu is empty
        # FIXME hide_if_only_one_item is defined on bar_item
        # But we call GET with resource=section
        min_limit = 1 #if resource.get_property('hide_if_only_one_item') else 0
        hide_if_not_enough_items = len(items) <= min_limit
        if allowed_to_edit is False and hide_if_not_enough_items:
            self.set_view_is_empty(True)

        namespace['hide_if_not_enough_items'] = hide_if_not_enough_items
        namespace['limit'] = min_limit

        return namespace



class BoxNewsSiblingsToc_View(BoxSectionNews_View):

    template = '/ui/bar_items/NewsSiblingsToc_view.xml'
    more_title = MSG(u'Show all')

    def _get_items(self, resource, context, news_folder, brain_only=False):
        return news_folder.get_news(context, brain_only=brain_only)


    def get_namespace(self, resource, context):
        namespace = {'items': {'displayed': [], 'hidden': []},
                     'title': resource.get_property('title'),
                     'class': None}
        site_root = resource.get_site_root()
        newsfolder_cls = site_root.newsfolder_class
        if newsfolder_cls is None:
            self.set_view_is_empty(True)
            return namespace

        allowed_to_edit = self.is_admin(resource, context)
        here = context.resource
        here_is_newsfolder = isinstance(here, newsfolder_cls)
        if here_is_newsfolder:
            news_folder = here
            news = None
        else:
            news_folder = here.parent
            news = here

        if isinstance(news_folder, newsfolder_cls) is False:
            self.set_view_is_empty(True)
            return namespace

        # News (siblings)
        news_count = resource.get_property('count')
        title = resource.get_property('title')
        displayed_items = self._get_items_ns(resource, context, render=True)
        displayed_items = list(displayed_items)
        items_number = len(displayed_items)
        hidden_items = []
        if news_count:
            if not here_is_newsfolder:
                if news:
                    news_brains = self._get_items(resource, context,
                                                  news_folder, brain_only=True)
                    news_abspath = news.get_abspath()
                    news_index = 0
                    # Do not hide current news
                    for index, brain in enumerate(news_brains):
                        if brain.abspath == news_abspath:
                            news_index = index + 1
                            break
                    news_count = max(news_count, news_index)

                hidden_items = displayed_items[news_count:]
            displayed_items = displayed_items[:news_count]
        namespace['items'] = {'displayed': displayed_items,
                              'hidden': hidden_items}
        namespace['more_title'] = self.more_title.gettext().encode('utf-8')

        # Hide siblings box if the user is not authenticated and
        # there is not other items
        min_limit = 1 if news_count else 0
        hide_if_not_enough_items = len(displayed_items) <= min_limit
        if allowed_to_edit is False and hide_if_not_enough_items:
            self.set_view_is_empty(True)

        namespace['hide_if_not_enough_items'] = hide_if_not_enough_items
        namespace['limit'] = min_limit

        return namespace



class ContentBoxSectionChildrenToc_View(Box_View):

    template = '/ui/bar_items/ContentBoxSectionChildrenToc_view.xml'

    def get_items(self, resource, context):
        user = context.user
        # Only display on a section view
        section = context._bar_aware

        items = []
        names = list(section.get_ordered_names())
        for name in names:
            item = section.get_resource(name, soft=True)
            if not item:
                continue
            # Check security
            ac = item.get_access_control()
            if ac.is_allowed_to_view(user, item):
                items.append(item)

        return items


    def get_namespace(self, resource, context):
        namespace = {}
        # Items
        user = context.user
        # Only display on a section view
        section = context.resource
        items = list(self.get_items(resource, context))
        items_ns = []

        for item in items:
            ns = {'title': item.get_title(),
                  'path': context.get_link(item)}
            items_ns.append(ns)

        allowed_to_edit = self.is_admin(resource, context)
        min_limit = 1 if resource.get_property('hide_if_only_one_item') else 0
        hide_if_not_enough_items = False
        if allowed_to_edit is False:
            if len(items) <= min_limit:
                # Hide the box if there is no articles and
                # if the user cannot edit the box
                self.set_view_is_empty(True)
        elif len(items) <= min_limit:
            # If the user can edit the item and there is there is
            # not enough items reset items entry
            items_ns = []
            hide_if_not_enough_items = True

        namespace['items'] = items_ns
        namespace['title'] = section.get_title()
        namespace['hide_if_not_enough_items'] = hide_if_not_enough_items
        namespace['limit'] = min_limit

        return namespace



################################################################################
# Boxes
################################################################################


class BoxSectionChildrenToc(Box):

    class_id = 'box-section-children-toc'
    class_title = MSG(u'Subsections and Webpages TOC')
    class_description = MSG(u'Table Of Content (TOC) to display choosen '
                            u'subsections and webpages')
    class_schema = merge_dicts(Box.class_schema,
            hide_if_only_one_item=Boolean(source='metadata', default=True))

    # Box comfiguration
    edit_schema = hide_single_schema
    edit_widgets = [hide_single_widget]
    display_title = False
    allow_instanciation = False

    # Views
    view = BoxSectionChildrenTree_View()


class BoxNewsSiblingsToc(Box):

    class_id = 'box-news-siblings-toc'
    class_title = MSG(u'News TOC')
    class_description = MSG(u'Display the list of news.')
    class_views = ['edit', 'edit_state', 'backlinks', 'commit_log']
    class_schema = merge_dicts(Box.class_schema,
                               count=PositiveInteger(source='metadata', default=30))

    # Box configuration
    allow_instanciation = False
    edit_schema = merge_dicts(hide_single_schema,
                              count=PositiveInteger(default=30))

    edit_widgets = [
        hide_single_widget,
        TextWidget('count', size=3,
                   title=MSG(u'Maximum number of news to display'))
        ]

    # Views
    view = BoxNewsSiblingsToc_View()
    preview = order_preview = BoxNewsSiblingsToc_Preview()



class ContentBoxSectionChildrenToc(Box):

    class_id = 'contentbar-box-children-toc'
    class_title = MSG(u'Subsections and Webpages TOC')
    class_description = MSG(u'Table Of Content (TOC) to display choosen '
                            u'subsections and webpages in the central part')
    class_views = ['edit_state', 'backlinks']
    class_schema = merge_dicts(Box.class_schema,
            hide_if_only_one_item=Boolean(source='metadata', default=True))

    # Box configuration
    edit_schema = hide_single_schema
    edit_widgets = [hide_single_widget]
    allow_instanciation = False
    is_content = True
    is_side = False

    # Views
    view = ContentBoxSectionChildrenToc_View()
