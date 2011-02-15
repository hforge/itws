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
from copy import deepcopy

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean, String
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget, PathSelectorWidget, RadioWidget
from ikaaro.menu import Target
from ikaaro.webpage import HTMLEditView, WebPage_View
from ikaaro.workflow import state_widget

# Import from itws
from base_views import Box_View
from itws.bar.base import BoxAware
from itws.utils import get_path_and_view
from itws.views import EasyNewInstance
from itws.webpage import WebPage
from itws.widgets.base import advance_rte_widget



class HTMLContent_View(Box_View, WebPage_View):

    template = '/ui/bar_items/HTMLContent_view.xml'


    def GET(self, resource, context):
        return Box_View.GET(self, resource, context)


    def get_namespace(self, resource, context):
        title = resource.get_property('display_title')
        if title:
            title = resource.get_title()
        return {
            'name': resource.name,
            'title':title,
            'title_link': resource.get_property('title_link'),
            'title_link_target': resource.get_property('title_link_target'),
            'content': WebPage_View.GET(self, resource, context)}



class HTMLContent_Edit(HTMLEditView):


    def _get_query_to_keep(self, resource, context):
        """Forward is_admin_popup if defined"""
        to_keep = HTMLEditView._get_query_to_keep(self, resource, context)
        is_admin_popup = context.get_query_value('is_admin_popup')
        if is_admin_popup:
            to_keep.append({'name': 'is_admin_popup', 'value': '1'})
        return to_keep


    def _get_schema(self, resource, context):
        schema = merge_dicts(
                HTMLEditView._get_schema(self, resource, context),
                # BoxAware API
                resource.edit_schema,
                # other
                title_link=String,
                title_link_target=Target,
                display_title=Boolean)
        # Delete unused description/subject(keywords)
        del schema['description']
        del schema['subject']

        return schema


    def _get_widgets(self, resource, context):
        base_widgets = HTMLEditView._get_widgets(self, resource, context)
        # Delete unused description/subject(keywords)
        widgets = [ widget for widget in base_widgets
                    if widget.name not in ('description', 'subject', 'state',
                                           'data') ]
        return freeze(widgets + [
            CheckboxWidget('display_title', title=MSG(u'Display title')),
            PathSelectorWidget('title_link', title=MSG(u'Title link')),
            RadioWidget('title_link_target', title=MSG(u'Title link target'),
                        has_empty_option=False, oneline=True),
            advance_rte_widget, state_widget ]
            # BoxAware API
            + resource.edit_widgets)



class HTMLContent(BoxAware, WebPage):

    # XXX WebPage is tagsaaware but not HTMLContent

    class_id = 'html-content'
    class_version = '20100621'
    class_title = MSG(u'Content')
    class_description = MSG(u'Formatted Content (HTML)')
    class_icon16 = 'bar_items/icons/16x16/html_content.png'
    class_icon48 = 'bar_items/icons/48x48/html_content.png'

    class_schema = merge_dicts(WebPage.class_schema,
        BoxAware.class_schema,
        # Metadata
        title_link=String(source='metadata'),
        title_link_target=Target(source='metadata', default='_top'))

    # Configuration
    allow_instanciation = True
    is_contentbox = True
    is_sidebox = True


    def get_catalog_values(self):
        return merge_dicts(WebPage.get_catalog_values(self),
                           BoxAware.get_catalog_values(self),
                           is_tagsaware=False)


    ###########################
    ## Links API
    ###########################

    # BoxAware does not implement *_links
    def get_links(self):
        links = WebPage.get_links(self)
        base = self.get_canonical_path()
        path = self.get_property('title_link')
        if path:
            ref = get_reference(path)
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                links.add(str(base.resolve2(path)))
        return links


    def update_links(self, source, target):
        WebPage.update_links(self, source, target)

        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        path = self.get_property('title_link')
        if path:
            ref = get_reference(path)
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                path = str(old_base.resolve2(path))
                if path == source:
                    # Hit the old name
                    # Build the new reference with the right path
                    new_ref = deepcopy(ref)
                    new_ref.path = str(new_base.get_pathto(target)) + view
                    self.set_property('title_link', str(new_ref))

        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        WebPage.update_relative_links(self, source)

        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new
        path = self.get_property('title_link')
        if path:
            ref = get_reference(str(path))
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                # Calcul the old absolute path
                old_abs_path = source.resolve2(path)
                # Check if the target path has not been moved
                new_abs_path = resources_old2new.get(old_abs_path,
                                                     old_abs_path)
                # Build the new reference with the right path
                # Absolute path allow to call get_pathto with the target
                new_ref = deepcopy(ref)
                new_ref.path = str(target.get_pathto(new_abs_path)) + view
                # Update the title link
                self.set_property('title_link', str(new_ref))


    #########
    # Views
    #########
    edit = HTMLContent_Edit()
    view = HTMLContent_View()
    new_instance = EasyNewInstance()
