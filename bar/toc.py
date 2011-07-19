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

# Import from standard library
from warnings import warn

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.web import STLView

# Import from itws
from base import Box
from base_views import Box_View
from itws.utils import is_navigation_mode




###############################################################################
# View
###############################################################################
class BoxSectionChildrenTree_View(Box_View):

    template = '/ui/bar_items/SectionChildrenTree_view.xml'


    def GET(self, resource, context):
        from itws.bar import Section

        section = context._bar_aware
        if isinstance(section, Section) is False:
            self.set_view_is_empty(True)
            return ''

        section_class = section.get_subsection_class()
        base_section = self._get_base_section(section, section_class)
        if isinstance(base_section, section_class) is False:
            # Strange
            self.set_view_is_empty(True)
            return ''

        return STLView.GET(self, base_section, context)


    def _get_base_section(self, section, section_cls):
        # FIXME section_cls may change
        resource = section
        while isinstance(resource.parent, section_cls):
            resource = resource.parent
        return resource


    def _get_items(self, section, context, here_abspath):
        user = context.user
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

        # Admin link
        admin_link = None
        if allowed_to_edit and is_navigation_mode(context) is False:
            section_path = context.get_link(resource)
            admin_link = {'href': '%s/;order_items' % section_path,
                          'title': MSG(u'Select & Order')}
        namespace['admin_link'] = admin_link

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



###############################################################################
# Boxes
###############################################################################
class BoxSectionChildrenToc(Box):

    class_id = 'box-section-children-toc'
    class_title = MSG(u'Subsections and Webpages TOC')
    class_description = MSG(u'Table Of Content (TOC) to display choosen '
                            u'subsections and webpages')
    class_schema = merge_dicts(Box.class_schema,
            hide_if_only_one_item=Boolean(source='metadata', default=True,
                title=MSG(u'Hide if there is only one item')))

    # Box comfiguration
    edit_fields = freeze(['hide_if_only_one_item'])
    allow_instanciation = False

    # Views
    view = BoxSectionChildrenTree_View()



class ContentBoxSectionChildrenToc(Box):

    class_id = 'contentbar-box-children-toc'
    class_title = MSG(u'Subsections and Webpages TOC')
    class_description = MSG(u'Table Of Content (TOC) to display choosen '
                            u'subsections and webpages in the central part')
    class_views = ['edit_state', 'backlinks']
    class_schema = merge_dicts(Box.class_schema,
            hide_if_only_one_item=Boolean(source='metadata', default=True,
                title=MSG(u'Hide if there is only one item')))

    # Box configuration
    edit_fields = freeze(['hide_if_only_one_item'])
    allow_instanciation = False
    is_contentbox = True
    is_sidebox = False

    # Views
    view = ContentBoxSectionChildrenToc_View()
