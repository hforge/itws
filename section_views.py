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
from ikaaro.buttons import Button
from ikaaro.forms import BooleanCheckBox, timestamp_widget
from ikaaro.forms import stl_namespaces, XHTMLBody
from ikaaro.forms import title_widget, description_widget, subject_widget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import DBResource_Edit
from ikaaro.views import CompositeForm

# Import from itws
from bar import ContentBar_View
from views import BaseManageLink, BaseManageContent
from views import SmartOrderedTable_View
from views import SmartOrderedTable_Ordered, SmartOrderedTable_Unordered
from views import ProxyContainerNewInstance



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
                                   title=MSG(u'Show webpage one by one')),
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
        messages = [ MSG_CHANGES_SAVED ]

        # Customize message for section which can be ordered
        site_root = resource.get_site_root()
        parent = resource.parent
        if type(parent) != type(site_root):
            # FIXME Assume that parent is a section
            order_names = parent.get_ordered_names()
            if resource.name not in order_names:
                order_resource = parent.get_resource(parent.order_path)
                path = context.get_link(order_resource)
                message = MSG(u'To make visible this section in the children '
                              u'TOC, please go to '
                              u'<a href="{path}">order interface</a>')
                message = message.gettext(path=path).encode('utf8')
                message = XHTMLBody.decode(message)
                messages.append(message)

        context.message = messages



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
                msg = MSG(u'Not visible, please %s at least one webpage'
                          % word)
                msg = msg.gettext().encode('utf-8')
            msg = MSG(msg)
        visibility['message'] = msg
        return stl(events=VisibilityTemplate, namespace=visibility)


class SectionOrderedTable_Ordered(SmartOrderedTable_Ordered):

    def get_table_columns(self, resource, context):
        columns = SmartOrderedTable_Ordered.get_table_columns(self,
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
        return SmartOrderedTable_Ordered.get_item_value(self, resource,
                                                        context, item, column)



class SectionOrderedTable_Unordered(SmartOrderedTable_Unordered):

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
        columns = SmartOrderedTable_Unordered.get_table_columns(self,
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
        return SmartOrderedTable_Unordered.get_item_value(self, resource,
                context, item, column)



class Section_ArticleNewInstance(ProxyContainerNewInstance):

    actions = [Button(access='is_allowed_to_edit',
                      name='new_article', title=MSG(u'Add'))]

    # SmartOrderedTable_View API
    title = title_description = None

    def _get_resource_cls(self, context):
        here = context.resource
        # Return parent section article class
        return here.parent.get_article_class()


    def _get_container(self, resource, context):
        # Parent section
        return resource.parent


    def _get_goto(self, resource, context, form):
        name = form['name']
        # Assume that the resource already exists
        container = self._get_container(resource, context)
        child = container.get_resource(name)
        return '%s/;edit' % context.get_link(child)


    def action_new_article(self, resource, context, form):
        return ProxyContainerNewInstance.action_default(self, resource,
                context, form)



class SectionOrderedTable_View(SmartOrderedTable_View):

    subviews = [Section_ArticleNewInstance(),
                SectionOrderedTable_Ordered(),
                SectionOrderedTable_Unordered()]


    def _get_form(self, resource, context):
        for view in self.subviews:
            method = getattr(view, context.form_action, None)
            if method is not None:
                form_method = getattr(view, '_get_form')
                return form_method(resource, context)
        return None



###########################################################################
# Section view
###########################################################################
class SectionContentBar_View(ContentBar_View):

    def get_manage_buttons(self, resource, context):
        return []



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
        namespace = {}

        # Add section id
        namespace['section_id'] = self.get_section_id(resource, context)

        # Subviews
        for view_name in self.subviews.keys():
            namespace[view_name] = self.get_subviews_value(resource, context,
                    section, view_name)
        return namespace



class Section_ManageLink(BaseManageLink):

    title = MSG(u'Manage the section')

    def get_items(self, resource, context):
        left_items = []
        right_items = []

        order_table = resource.get_resource(resource.order_path)
        ordered_classes = order_table.get_orderable_classes()

        left_items.append({'path': './;edit',
                           'class': 'edit',
                           'title': MSG(u'Edit the section')})

        left_items.append({'path': './;new_resource',
                           'class': 'add',
                           'title': MSG(u'Add Resource: Webpage, Subsection, '
                                        u'PDF, ODT')})

        left_items.append({'path': './;browse_content',
                           'class': 'edit',
                           'title': MSG(u'Manage section content '
                                        u'(cut, copy, rename, remove)')})

        # Do not show the link if there is nothing to order
        section_cls = resource.get_subsection_class()
        article_cls = resource.get_article_class()
        available_sections = list(resource.search_resources(cls=section_cls))
        available_articles = list(resource.search_resources(cls=article_cls))

        left_items.append({'path': './order-section',
                           'class': 'order child',
                           'title': MSG(u'Order webpages in the section '
                                        u'view'),
                           'disable': len(available_articles) == 0})

        left_items.append({'path': './order-section',
                           'class': 'order child',
                           'title': MSG(u'Order subsections in the TOC'),
                           'disable': len(available_sections) == 0})

        left_items.append({'path': '/repository/;new_contentbar_resource',
                           'class': 'add',
                           'title': MSG(u'Create new central part box')})

        left_items.append({'path': './;order_contentbar',
                           'class': 'order child',
                           'title': MSG(u'Order central part boxes')})

        right_items.append({'path': '/repository/;new_sidebar_resource',
                            'class': 'add',
                            'title': MSG(u'Create new sidebar box')})

        right_items.append({'path': './;order_sidebar',
                            'class': 'order child',
                            'title': MSG(u'Order sidebar boxes')})

        return [{'items': left_items, 'class': 'left'},
                {'items': right_items, 'class': 'right'}]



class Section_ManageContent(BaseManageContent):

    title = MSG(u'Manage section')

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        editorial_cls = resource.get_editorial_documents_types()
        editorial_query = [ PhraseQuery('format', cls.class_id)
                            for cls in editorial_cls ]
        # allow images
        editorial_query.append(PhraseQuery('is_image', True))
        query = [
            PhraseQuery('parent_path', path),
            NotQuery(PhraseQuery('name', 'order-sidebar')),
            NotQuery(PhraseQuery('name', 'order-contentbar')),
            NotQuery(PhraseQuery('name', 'order-section')),
            OrQuery(*editorial_query)
                ]
        return context.root.search(AndQuery(*query))



class Section_ManageView(CompositeForm):

    title = MSG(u'Manage Section')
    access = 'is_allowed_to_edit'

    subviews = [Section_ManageLink(),
                Section_ManageContent()]

