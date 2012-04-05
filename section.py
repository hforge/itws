# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@itaapy.com>
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
from itools.datatypes import String
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.folder_views import Folder_PreviewContent, GoToSpecificDocument
from ikaaro.future.order import ResourcesOrderedTable, ResourcesOrderedContainer
from ikaaro.registry import register_resource_class
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.table import OrderedTableFile
from ikaaro.workflow import WorkflowAware

# Import from itws
from bar import SideBarAware, ContentBarAware
from repository import Repository, ContentBoxSectionChildrenToc
from resources import ManageViewAware
from section_views import Section_ManageContent
from section_views import Section_Edit, Section_View
from section_views import Section_AddContent
from views import SmartOrderedTable_View
from webpage import WebPage



################
# Order tables #
###########################################################################

class SectionOrderedTableFile(OrderedTableFile):

    record_properties = {
        'name': String(mandatory=True, unique=True, is_indexed=True)}



class SectionOrderedTable(ResourcesOrderedTable):

    class_id = 'section-ordered-table'
    class_title = MSG(u'Order section')
    class_views = ['view', 'manage_view']
    class_handler = SectionOrderedTableFile

    view = SmartOrderedTable_View(title=MSG(u'View'))

    # Order view title & description configuration
    @property
    def ordered_view_title(self):
        section = get_context().resource.parent
        msg = MSG(u'Order Webpages and Sub-sections in "{name}" TOC')
        return msg.gettext(name=section.get_title())


    @property
    def ordered_view_title_description(self):
        section = get_context().resource.parent
        msg = MSG(u'You can select and order these webpages and subsections, '
                  u'to make them accessible in the "{name}" section '
                  u'Table Of Content (TOC)')
        return msg.gettext(name=section.get_title())


    unordered_view_title = MSG(u'Available Sections and Webpages')
    unordered_view_title_description = MSG(
            u'These Subsections/Webpages are available, '
            u'you can make them visible in this section '
            u'by adding them to the section TOC')

    def get_orderable_classes(self):
        # Orderable classes should be
        # 1 - my parent
        # 2 - my_parent.get_article_class
        return (WebPage, Section)

    orderable_classes = property(get_orderable_classes, None, None, '')


    def get_view(self, name, query=None):
        # Add helper for manage view
        view = ResourcesOrderedTable.get_view(self, name, query)
        if view:
            return view
        if name == 'manage_view':
            parent_view = self.parent.get_view('manage_view')
            if parent_view is None:
                # not found
                return None
            return GoToSpecificDocument(specific_document='..',
                    access = parent_view.access,
                    specific_view='manage_view',
                    title=MSG(u'Manage section'))
        return None



class Section(ManageViewAware, SideBarAware, ContentBarAware,
              ResourcesOrderedContainer):

    class_id = 'section'
    class_version = '20100624'
    class_title = MSG(u'Section')
    class_description = MSG(u'Section allows to customize the central part '
                            u'and the sidebar. Section can contain subsections')
    class_icon16 = 'common/icons/16x16/section.png'
    class_icon48 = 'common/icons/48x48/section.png'
    class_views = ['view', 'edit', 'manage_content', 'add_content',
                   'new_resource', 'order_items', 'backlinks']
    __fixed_handlers__ = (Folder.__fixed_handlers__
                          + SideBarAware.__fixed_handlers__
                          + ContentBarAware.__fixed_handlers__
                          + ['order-section', 'children-toc'])
    # Order Articles
    order_path = 'order-section'
    order_class = SectionOrderedTable

    # Contentbar items
    # (name, cls, ordered)
    contentbar_items = [('children-toc', ContentBoxSectionChildrenToc, True)]


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        root = get_context().root
        ResourcesOrderedContainer._make_resource(cls, folder, name, **kw)
        SideBarAware._make_resource(cls, folder, name, **kw)
        ContentBarAware._make_resource(cls, folder, name, **kw)

        # Preorder specific sidebar items
        table_name = cls.sidebar_name
        table = root.get_resource('%s/%s/%s' % (folder.key, name, table_name))
        name2 = Repository.news_items_name
        table.add_new_record({'name': name2})
        name2 = Repository.section_sidebar_children_toc_view_name
        table.add_new_record({'name': name2})


    def get_internal_use_resource_names(self):
        return freeze(SideBarAware.__fixed_handlers__ +
                      ContentBarAware.__fixed_handlers__ +
                      ['order-section', 'children-toc'])


    def get_document_types(self):
        types = Folder.get_document_types(self)[:]
        # Do not add format twice
        cls_id_types = [ cls.class_id for cls in types ]
        subsection_cls = self.get_subsection_class()
        article_cls = self.get_article_class()
        if subsection_cls.class_id not in cls_id_types:
            types.append(subsection_cls)
        if article_cls.class_id not in cls_id_types:
            types.append(article_cls)
        return types


    def get_subsection_class(self):
        return type(self)


    def get_article_class(self):
        return WebPage


    def is_empty(self):
        # XXX And the ACLs ???
        if self.get_ordered_names():
            return False
        return True


    def get_sub_sections(self, not_empty=False):
        section_cls = self.get_subsection_class()
        for name in self.get_ordered_names():
            item = self.get_resource(name)
            if not isinstance(item, section_cls):
                continue
            if not_empty is True and item.is_empty():
                continue
            yield item


    def get_n_articles_by_state(self):
        article_cls = self.get_article_class()
        states = {'public': 0, 'pending': 0, 'private': 0}
        for name in self.get_ordered_names():
            item = self.get_resource(name)
            if not isinstance(item, article_cls):
                continue
            states[item.get_statename()] += 1
        return states


    def update_20100621(self):
        SideBarAware.update_20100621(self)


    def update_20100622(self):
        ContentBarAware.update_20100622(self)


    def update_20100623(self):
        """
        Remove show_one_article
        Add children-toc into current section
        And remove articles-view from ordered contentbar
        Copy contentbar htmlcontent inside the current section
        """
        from itools.xapian import PhraseQuery
        from ikaaro.utils import generate_name
        from repository import HTMLContent
        from repository import BoxSectionNews, ContentBoxSectionNews

        database = get_context().database
        cls = ContentBoxSectionChildrenToc
        contentbar_table = self.get_resource(self.contentbar_name)
        contentbar_handler = contentbar_table.handler
        repository = self.get_site_root().get_repository()

        contentbar_records = contentbar_handler.get_records_in_order()
        for index, record in enumerate(contentbar_records):
            name = contentbar_handler.get_record_value(record, 'name')
            if name == 'articles-view':
                continue
            item = repository.get_resource(name, soft=True)
            if item is None or name == 'website-articles-view':
                contentbar_table.del_record(record.id)
                continue
            elif item.class_id == cls.class_id:
                self.copy_resource(str(item.get_abspath()),
                                   'children-toc')
                contentbar_table.update_record(record.id,
                                               **{'name': 'children-toc'})

        # Create the toc
        if self.get_resource('children-toc', soft=True) is None:
            cls.make_resource(cls, self, 'children-toc')

        # Remove articles-view record
        articles_view_index = None
        contentbar_records = list(contentbar_handler.get_records_in_order())
        records_len = len(contentbar_records)
        for index, record in enumerate(contentbar_records):
            name = contentbar_handler.get_record_value(record, 'name')
            if name == 'articles-view':
                contentbar_table.del_record(record.id)
                articles_view_index = index
                if index > (len(contentbar_records) - 1):
                    articles_view_index = index-1
                break

        # Webpage was display one by one or not ?
        one_by_one = self.get_property('show_one_article')
        try:
            one_by_one = bool(one_by_one)
        except ValueError:
            one_by_one = False

        new_record_ids = []
        if one_by_one is False and articles_view_index is not None:
            order_resources = self.get_resource('order-section')
            or_handler = order_resources.handler
            webpages_order = []

            # Webpage -> HTMLContent
            wp_schema = WebPage.get_metadata_schema()
            htmlcontent_schema = HTMLContent.get_metadata_schema()
            schema_diff = set(wp_schema).difference(set(htmlcontent_schema))

            for record in or_handler.get_records_in_order():
                name = or_handler.get_record_value(record, 'name')
                item = self.get_resource(name, soft=True)
                if item is None:
                    order_resources.del_record(record.id)
                    continue
                if isinstance(item, WebPage):
                    webpages_order.append(name)
                    for key in schema_diff:
                        item.del_property(key)
                    metadata = item.metadata
                    metadata.set_changed()
                    metadata.format = HTMLContent.class_id
                    metadata.version = HTMLContent.class_version

            # Order old webpages
            order = list(contentbar_handler.get_record_ids_in_order())
            for name in webpages_order:
                res = contentbar_handler.search(PhraseQuery('name', name))
                if len(res):
                    # rename the webpage if there is an item with the same name
                    names = self.get_names() + repository.get_names()
                    new_name = generate_name(name, names, '-html-content')
                    self.move_resource(name, new_name)
                    name = new_name
                r = contentbar_table.add_new_record({'name': name})
                new_record_ids.append(r.id)

            # Tweak order
            order = (order[:articles_view_index] + new_record_ids
                     + order[articles_view_index:])
            # Update the order
            order = [ str(x) for x in order ]
            contentbar_handler.update_properties(order=tuple(order))

        # Copy/rename contentbar items
        content_classes = repository._get_document_types(is_content=True)
        content_classes = tuple(content_classes)
        for record in contentbar_handler.get_records():
            # Check if the content item is not an old webpage
            if record.id in new_record_ids:
                continue
            name = contentbar_handler.get_record_value(record, 'name')
            item = repository.get_resource(name, soft=True)
            if isinstance(item, content_classes) \
                    or isinstance(item, BoxSectionNews):
                name = generate_name(name, self.get_names(), '_content')
                # Resources that link to me
                query = PhraseQuery('links', str(item.get_abspath()))
                results = database.catalog.search(query).get_documents()
                if len(results) < 2:
                    # Just move the resource
                    self.move_resource(str(item.get_abspath()), name)
                else:
                    self.copy_resource(str(item.get_abspath()), name)
                    contentbar_table.update_record(record.id, **{'name': name})
                    # Keep state
                    if isinstance(item, WorkflowAware):
                        state = item.get_workflow_state()
                        copy_resource = self.get_resource(name)
                        copy_resource.set_workflow_state(state)
                # FIXME To improve
                if isinstance(item, BoxSectionNews):
                    new_item = self.get_resource(name)
                    metadata = new_item.metadata
                    metadata.set_changed()
                    metadata.format = ContentBoxSectionNews.class_id
                    metadata.version = ContentBoxSectionNews.class_version

        self.del_property('show_one_article')


    def update_20100624(self):
        """Remove obsolete box-section-children-toc format"""
        site_root = self.get_site_root()
        repository = site_root.get_repository()
        box_name = repository.section_sidebar_children_toc_view_name
        box_cls = repository.section_sidebar_children_toc_view_cls

        table = self.get_resource(self.sidebar_name)
        handler = table.handler

        record_ids = []
        for record in handler.get_records_in_order():
            name = handler.get_record_value(record, 'name')
            item = repository.get_resource(name)
            if type(item) is box_cls:
                record_ids.append(record.id)

        if record_ids:
            # remove [1:] and update the first one
            for id in record_ids[1:]:
                table.del_record(id)
            table.update_record(record_ids[0], name=box_name)


    view = Section_View()
    edit = Section_Edit()
    manage_content = Section_ManageContent()
    add_content = Section_AddContent()
    order_items = GoToSpecificDocument(specific_document='order-section',
            title=MSG(u'Manage TOC'))
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')



register_resource_class(Section)
register_resource_class(SectionOrderedTable)
