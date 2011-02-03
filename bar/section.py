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
from itools.core import freeze, merge_dicts
from itools.datatypes import String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.folder_views import Folder_PreviewContent, GoToSpecificDocument
from ikaaro.future.order import ResourcesOrderedContainer
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.registry import register_document_type
from ikaaro.table import OrderedTableFile
from ikaaro.workflow import WorkflowAware

# Import from itws
from bar_aware import SideBarAware, ContentBarAware
from registry import get_boxes_registry
from section_views import Section_Edit
from itws.control_panel import CPDBResource_CommitLog, CPDBResource_Links
from itws.control_panel import CPDBResource_Backlinks, CPOrderItems
from itws.control_panel import ITWS_ControlPanel
from itws.feed_views import Browse_Navigator
from itws.section_views import SectionViews_Enumerate
from itws.tags import TagsAware, register_tags_aware
from itws.webpage import WebPage



################
# Order tables #
################
class SectionOrderedTableFile(OrderedTableFile):

    record_properties = {
        'name': String(mandatory=True, unique=True)}



class SectionOrderedTable(ResourcesOrderedTable):

    class_id = 'section-ordered-table'
    class_title = MSG(u'Order section')
    class_views = ['view', 'goto_parent']
    class_handler = SectionOrderedTableFile


    @property
    def orderable_classes(self):
        # Orderable classes should be
        # 1 - my parent
        # 2 - my_parent.get_article_class
        return (WebPage, Section)


    # views
    goto_parent = GoToSpecificDocument(specific_document='..',
            title=MSG(u'Back to parent section'))



class Section(WorkflowAware, TagsAware, SideBarAware, ContentBarAware,
              ResourcesOrderedContainer):

    class_id = 'section'
    class_version = '20101124'
    class_title = MSG(u'Section')
    class_description = MSG(u'Sections allow to customize the central part '
            u'and the sidebar. Sections can contain subsections.')
    class_icon16 = 'common/icons/16x16/section.png'
    class_icon48 = 'common/icons/48x48/section.png'
    class_schema = merge_dicts(
        WorkflowAware.class_schema,
        TagsAware.class_schema,
        ResourcesOrderedContainer.class_schema,
        view=SectionViews_Enumerate(source='metadata',
                                    default='composite-view'))


    class_views = ['view', 'edit', 'configure_view', 'control_panel']

    class_control_panel = ['order_items', 'links', 'backlinks', 'commit_log']

    __fixed_handlers__ = (Folder.__fixed_handlers__
                          + SideBarAware.__fixed_handlers__
                          + ContentBarAware.__fixed_handlers__
                          + ['order-section', 'children-toc'])
    # Order Webpage/Section
    order_path = 'order-section'
    order_class = SectionOrderedTable


    def init_resource(self, **kw):
        if 'add_boxes' in kw:
            add_boxes = kw.get('add_boxes')
            del kw['add_boxes']
        else:
            add_boxes = True

        SideBarAware.init_resource(self, **kw)
        ContentBarAware.init_resource(self, **kw)
        ResourcesOrderedContainer.init_resource(self, **kw)

        # Preorder items
        if kw.get('add_boxes', True) is True:
            repository = self.get_site_root().get_repository()
            sidebar_table = self.get_resource(self.sidebar_name)
            # tags cloud (created by repository)
            sidebar_table.add_new_record({'name': repository.tags_box})


    def get_catalog_values(self):
        return merge_dicts(ResourcesOrderedContainer.get_catalog_values(self),
                           TagsAware.get_catalog_values(self),
                           SideBarAware.get_catalog_values(self),
                           ContentBarAware.get_catalog_values(self))


    # InternalResourcesAware API
    def get_internal_use_resource_names(self):
        return freeze(SideBarAware.get_internal_use_resource_names(self) +
                      ContentBarAware.get_internal_use_resource_names(self) +
                      ['order-section', 'children-toc'])


    def get_document_types(self):
        return [ self.get_article_class(), self.get_subsection_class(), File ]


    def get_subsection_class(self):
        return type(self)


    def get_article_class(self):
        return WebPage


    def to_text(self):
        return TagsAware.to_text(self)


    def can_paste(self, source):
        """Is the source resource can be pasted into myself.
        """
        allowed_types = self.get_document_types()
        # extend allowed type with content boxes
        registry = get_boxes_registry()
        boxe_cls = [ cls for cls, allow in registry.iteritems()
                     if allow['content'] ]
        allowed_types.extend(boxe_cls)
        return isinstance(source, tuple(allowed_types))


    def update_20101124(self):
        self.set_property('state', 'public')


    # Views
    edit = Section_Edit()
    manage_content = Browse_Navigator()
    order_items = CPOrderItems()
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    control_panel = ITWS_ControlPanel()

    # Control panel
    commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')
    links = CPDBResource_Links()
    backlinks = CPDBResource_Backlinks()



register_document_type(Section, 'neutral')
register_tags_aware(Section)
