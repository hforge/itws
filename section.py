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

# Import from itws
from bar import SideBarAware, ContentBarAware, ContentBoxSectionChildrenToc
from bar.repository import Repository
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



class Section(SideBarAware, ContentBarAware,
              ResourcesOrderedContainer):

    class_id = 'section'
    class_version = '20100624'
    class_title = MSG(u'Section')
    class_description = MSG(u'Section allows to customize the central part '
                            u'and the sidebar. Section can contain subsections')
    class_icon16 = 'common/icons/16x16/section.png'
    class_icon48 = 'common/icons/48x48/section.png'
    class_views = ['view', 'edit', 'manage_content', 'add_content',
                   'new_resource', 'order_items', 'backlinks', 'commit_log']
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


    def init_resource(self, **kw):
        SideBarAware.init_resource(self, **kw)
        ContentBarAware.init_resource(self, **kw)
        ResourcesOrderedContainer.init_resource(self, **kw)

        # XXX
        # Preorder specific sidebar items
        #table_name = cls.sidebar_name
        #table = root.get_resource('%s/%s/%s' % (folder.key, name, table_name))
        #name2 = Repository.news_items_name
        #table.add_new_record({'name': name2})
        #name2 = Repository.section_sidebar_children_toc_view_name
        #table.add_new_record({'name': name2})


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
