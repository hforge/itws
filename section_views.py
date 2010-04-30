# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
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
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.stl import stl
from itools.uri import Path
from itools.web import STLView
from itools.xapian import AndQuery, OrQuery, PhraseQuery, NotQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import BooleanCheckBox, timestamp_widget
from ikaaro.forms import stl_namespaces
from ikaaro.forms import title_widget, description_widget, subject_widget
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.future.order import ResourcesOrderedTable_Unordered
from ikaaro.future.order import ResourcesOrderedTable_View
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import DBResource_Edit

# Import from itws
from bar import ContentBar_View



VisibilityTemplate = list(XMLParser(
    """<span class="wf-public">${public} Public</span>,
       <span class="wf-pending">${pending} Pending</span>,
       <span class="wf-private">${private} Private</span>
       <stl:block stl:if="message">${message}</stl:block>""",
    stl_namespaces))


class Section_Edit(DBResource_Edit):

    def get_schema(self, resource, context):
        repository = resource.get_site_root().get_repository()
        return merge_dicts(DBResource_Edit.schema, show_one_article=Boolean)


    def get_widgets(self, resource, context):
        # base widgets
        widgets = DBResource_Edit.get_widgets(self, resource, context)[:]
        widgets = [title_widget,
                   BooleanCheckBox('show_one_article',
                                   title=MSG(u'Show articles one by one')),
                   description_widget, subject_widget,
                   timestamp_widget]

        return widgets


    def action(self, resource, context, form):
        DBResource_Edit.action(self, resource, context, form)
        # Check edit conflict
        if context.edit_conflict:
            return

        # Sections
        resource.set_property('show_one_article', form['show_one_article'])

        # Ok
        context.message = MSG_CHANGES_SAVED



###########################################################################
# SectionOrderedTable
###########################################################################
def sectionorderedtable_get_item_value(resource, context, item, column):
    if column == 'visibility':
        if isinstance(item, tuple):
            item = item[1]
        else:
            item = resource.parent.get_resource(item.name)
        visibility = getattr(item, 'get_n_articles_by_state', None)
        if visibility is None:
            return None
        visibility = visibility()
        public = visibility['public']
        pending = visibility['pending']
        private = visibility['private']
        msg = None
        if public == 0:
            if len(list(item.get_sub_sections())) == 0:
                word = 'publish'
                if (pending + private) == 0:
                    word = 'add'
                msg = MSG(u'Not visible, please %s at least one article'
                          % word)
                msg = msg.gettext().encode('utf-8')
            msg = MSG(msg)
        visibility['message'] = msg
        return stl(events=VisibilityTemplate, namespace=visibility)


class SectionOrderedTable_Ordered(ResourcesOrderedTable_Ordered):

    def get_table_columns(self, resource, context):
        columns = ResourcesOrderedTable_Ordered.get_table_columns(self,
                resource, context)
        columns.insert(1, ('icon', None, False))
        columns.insert(-1, ('visibility', MSG(u'Visibility'), False))
        return columns


    def get_item_value(self, resource, context, item, column):
        if column == 'visibility':
            return sectionorderedtable_get_item_value(resource, context, item,
                                                      column)
        elif column == 'icon':
            # icon
            item_resource = resource.parent.get_resource(item.name)
            path_to_icon = item_resource.get_resource_icon(16)
            if path_to_icon.startswith(';'):
                base_path = Path('%s/' % item_resource.name)
                path_to_icon = base_path.resolve(path_to_icon)
            return path_to_icon
        return ResourcesOrderedTable_Ordered.get_item_value(self, resource,
                                                        context, item, column)



class SectionOrderedTable_Unordered(ResourcesOrderedTable_Unordered):

    def get_query(self, resource, context):
        order_root = resource.get_order_root()
        # Only in the given root
        parent_path = order_root.get_abspath()
        query_base_path = PhraseQuery('parent_path', str(parent_path))
        # Only the type to order
        orderable_classes = resource.get_orderable_classes()
        query_formats = [ PhraseQuery('format', cls.class_id)
                          for cls in orderable_classes ]
        query_formats = OrQuery(*query_formats)
        query_excluded = [NotQuery(PhraseQuery('name', name))
                          for name in resource.get_ordered_names()]
        # If we dont use parent_path field we must add the query below
        #query_base_path = get_base_path_query(str(parent_path))
        ## Do not include the resources inside the subfolders
        #subfolder_exluded = []
        #for subfolder in order_root.search_resources(cls=Folder):
        #    subfolder_path = subfolder.get_abspath()
        #    sub_query_base_path = get_base_path_query(str(subfolder_path))
        #    subfolder_exluded.append(get_base_path_query(str(subfolder_path)))
        #if subfolder_exluded:
        #    query_excluded.append(NotQuery(OrQuery(*subfolder_exluded)))
        return AndQuery(query_base_path, query_formats, *query_excluded)


    def get_table_columns(self, resource, context):
        columns = ResourcesOrderedTable_Unordered.get_table_columns(self,
                resource, context)
        columns.insert(1, ('icon', None, False))
        columns.insert(-1, ('visibility', MSG(u'Visibility'), False))
        return columns


    def get_item_value(self, resource, context, item, column):
        if column == 'visibility':
            return sectionorderedtable_get_item_value(resource, context, item,
                                                      column)
        elif column == 'icon':
            # icon
            brain, item_resource = item
            path_to_icon = item_resource.get_resource_icon(16)
            if path_to_icon.startswith(';'):
                path_to_icon = Path('%s/' % brain.name).resolve(path_to_icon)
            return path_to_icon
        return ResourcesOrderedTable_Unordered.get_item_value(self, resource,
                context, item, column)



class SectionOrderedTable_View(ResourcesOrderedTable_View):

    subviews = [SectionOrderedTable_Ordered(),
                SectionOrderedTable_Unordered()]



###########################################################################
# Section view
###########################################################################
class SectionContentBar_View(ContentBar_View):

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []
        buttons = ContentBar_View.get_manage_buttons(self, resource, context)

        # webpage creation helper
        article_cls = resource.get_article_class()
        path = context.get_link(resource)
        msg = MSG(u'Create a new %s' % article_cls.class_title.gettext())
        buttons.append({'path': '%s/;new_resource?type=%s' % (path, article_cls.class_id),
                        'icon': '/ui/icons/48x48/html.png',
                        'label': msg,
                        'target': '_blank'})

        return buttons



class Section_View(STLView):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    template = '/ui/common/Section_view.xml'
    order_path = 'order-section'
    # subviews = {view_name: view} OR {view_name: None}
    # The view can be dynamically generated and rendered inside
    # the method get_subviews_value.
    subviews = {'contentbar_view': SectionContentBar_View()}

    def _get_real_section(self, resource, context):
        return resource


    def get_subviews_value(self, resource, context, section, view_name):
        """resource must be the real section"""
        view = self.subviews.get(view_name)
        if view is None:
            return None
        return view.GET(section, context)


    def get_section_id(self, resource, context):
        section = self._get_real_section(resource, context)
        return 'section-%s' % section.name


    def get_namespace(self, resource, context):
        # Get the real section resource
        section = self._get_real_section(resource, context)
        user = context.user

        # Manage buttons and highlight
        namespace = {}

        # Add section id
        namespace['section_id'] = self.get_section_id(resource, context)

        # Subviews
        for view_name in self.subviews.keys():
            namespace[view_name] = self.get_subviews_value(resource, context,
                    section, view_name)
        return namespace
