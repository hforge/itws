# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 Nicolas Deram <nicolas@itaapy.com>
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
from copy import deepcopy

# Import from itools
from itools.core import get_abspath, merge_dicts
from itools.datatypes import String, Boolean, Integer, Enumerate
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import get_context
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.forms import SelectWidget
from ikaaro.future.menu import Target
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.future.order import ResourcesOrderedTable_Unordered
from ikaaro.future.order import ResourcesOrderedTable_View
from ikaaro.registry import register_resource_class
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.skins import register_skin

# Import from itws
from datatypes import PositiveInteger, TagsAwareClassEnumerate
from repository_views import BarItem_Edit
from repository_views import BarItem_Preview
from repository_views import ContentBarItem_Articles_View
from repository_views import ContentBarItem_SectionChildrenToc_Edit
from repository_views import ContentBarItem_SectionChildrenToc_View
from repository_views import Repository_BrowseContent, Repository_NewResource
from repository_views import SidebarItem_NewsSiblingsToc_Edit
from repository_views import SidebarItem_NewsSiblingsToc_View
from repository_views import SidebarItem_Preview, SidebarItem_View
from repository_views import SidebarItem_SectionChildrenToc_View
from repository_views import SidebarItem_SectionSiblingsToc_Edit
from repository_views import SidebarItem_SectionSiblingsToc_View
from repository_views import SidebarItem_Section_News_Edit
from repository_views import SidebarItem_Section_News_Preview
from repository_views import SidebarItem_Section_News_View
from repository_views import SidebarItem_Tags_Edit
from repository_views import SidebarItem_Tags_View
from repository_views import SidebarItem_ViewBoth, SidebarItem_Edit
from repository_views import WSNeutral_ContentBarItem_Articles_View
from webpage import WebPage
from utils import get_path_and_view
from views import EasyNewInstance



###########################################################################
# Register & Base classes
###########################################################################
bar_item_registry = {}
def register_bar_item(resource_class, allow_instanciation=True,
                           allow_order=True, is_content=False):
    bar_item_registry[resource_class] = [allow_instanciation,
                                         allow_order, is_content]

def get_bar_item_registry():
    return bar_item_registry


class BarItem(File):

    class_description = MSG(u'Sidebar item')
    preview = order_preview = BarItem_Preview()
    edit = BarItem_Edit()
    download = None
    externaledit = None
    new_instance = EasyNewInstance()

    item_widgets = []
    item_schema = {}

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(File.get_metadata_schema(),
                           cls.item_schema,
                           state=String(default='public'))



###########################################################################
# Sidebar resources
###########################################################################
class SidebarItem(WebPage):

    class_id = 'sidebar-item'
    class_version = '20091127'
    class_title = MSG(u'Sidebar item')
    class_description = MSG(u'Sidebar item')

    # Views
    view_both = SidebarItem_ViewBoth()
    preview = order_preview = SidebarItem_Preview()
    edit = SidebarItem_Edit()
    view = SidebarItem_View()


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(WebPage.get_metadata_schema(),
                           title_link=String(),
                           title_link_target=Target(default='_top'))


    def can_paste_into(self, target):
        return isinstance(target, self.parent.__class__)


    def get_links(self):
        links = WebPage.get_links(self)
        base = self.get_canonical_path()
        path = self.get_property('title_link')
        if path:
            ref = get_reference(path)
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                links.append(str(base.resolve2(path)))
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

        get_context().server.change_resource(self)


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



class SidebarItem_Section_News(BarItem):

    class_id = 'sidebar-item-section-news'
    class_title = MSG(u'Sidebar item section news')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    preview = order_preview = SidebarItem_Section_News_Preview()
    view = SidebarItem_Section_News_View()
    edit = SidebarItem_Section_News_Edit()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(BarItem.get_metadata_schema(),
                           tags=String(multiple=True),
                           count=PositiveInteger(default=0))



class SidebarItem_Tags(BarItem):

    class_id = 'sidebar-item-tags'
    class_version = '20100226'
    class_title = MSG(u'Sidebar item tag')

    view = SidebarItem_Tags_View()
    edit = SidebarItem_Tags_Edit()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(BarItem.get_metadata_schema(),
                           format=TagsAwareClassEnumerate(multiple=True),
                           count=PositiveInteger(default=0),
                           show_number=Boolean(), random=Boolean())



class SidebarItem_SectionSiblingsToc(BarItem):

    class_id = 'sidebar-item-section-siblings-toc'
    class_title = MSG(u'Sidebar item section siblings toc')

    edit = SidebarItem_SectionSiblingsToc_Edit()
    view = SidebarItem_SectionSiblingsToc_View()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(BarItem.get_metadata_schema(),
                           hide_if_only_one_item=Boolean())



class SidebarItem_SectionChildrenToc(SidebarItem_SectionSiblingsToc):

    class_id = 'sidebar-item-section-children-toc'
    class_title = MSG(u'Sidebar item section children toc')

    view = SidebarItem_SectionChildrenToc_View()



class SidebarItem_NewsSiblingsToc(BarItem):

    class_id = 'sidebar-item-news-siblings-toc'
    class_title = MSG(u'Sidebar item news siblings toc')

    edit = SidebarItem_NewsSiblingsToc_Edit()
    view = SidebarItem_NewsSiblingsToc_View()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(BarItem.get_metadata_schema(),
                           hide_if_only_one_item=Boolean(),
                           count=PositiveInteger(default=30))



###########################################################################
# Contentbar resources
###########################################################################
class ContentBarItem_Articles(BarItem):

    class_id = 'contentbar-item-articles'
    class_title = MSG(u'Contentbar item articles view')

    view = ContentBarItem_Articles_View()



class WSNeutral_ContentBarItem_Articles(ContentBarItem_Articles):

    class_id = 'ws-neutral-item-articles'
    class_title = MSG(u'Website contentbar item articles view')

    view = WSNeutral_ContentBarItem_Articles_View()



class ContentBarItem_SectionChildrenToc(BarItem):

    class_id = 'contentbar-item-children-toc'
    class_title = MSG(u'Contentbar item children toc')

    edit = ContentBarItem_SectionChildrenToc_Edit()
    view = ContentBarItem_SectionChildrenToc_View()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(BarItem.get_metadata_schema(),
                           hide_if_only_one_item=Boolean())



###########################################################################
# Repository
###########################################################################
class BarItemsOrderedTable_Ordered(ResourcesOrderedTable_Ordered):

    query_schema = {}

    def sort_and_batch(self, resource, context, items):
        # Sort by order regardless query
        reverse = False
        ordered_ids = list(resource.handler.get_record_ids_in_order())
        f = lambda x: ordered_ids.index(x.id)
        items.sort(cmp=lambda x,y: cmp(f(x), f(y)), reverse=reverse)

        # Always display all items
        return items


    def get_table_columns(self, resource, context):
        columns = ResourcesOrderedTable_Ordered.get_table_columns(self,
                resource, context)

        # Column to remove
        indexes = [ x for x, column in enumerate(columns)
                    if column[0] in ('name', 'order') ]
        indexes.sort(reverse=True)
        for index in indexes:
            columns.pop(index)

        return columns



class BarItemsOrderedTable_Unordered(ResourcesOrderedTable_Unordered):

    query_schema = merge_dicts(ResourcesOrderedTable_Ordered.query_schema,
                               batch_size=Integer(default=0),
                               format=String)
    search_template = '/ui/bar_items/browse_search.xml'

    def get_query_schema(self):
        return self.query_schema


    def get_query(self, resource, context):
        query = ResourcesOrderedTable_Unordered.get_query(self, resource,
                                                          context)
        # Add format filter
        format = context.query['format']
        if format:
            query = AndQuery(query, PhraseQuery('format', format))

        return query


    def get_table_columns(self, resource, context):
        columns = ResourcesOrderedTable_Unordered.get_table_columns(self,
                resource, context)

        column = ('format', MSG(u'Type'), False)
        columns.insert(3, column)

        # Column to remove
        indexes = [ x for x, column in enumerate(columns)
                    if column[0] == 'path' ]
        indexes.sort(reverse=True)
        for index in indexes:
            columns.pop(index)

        return columns


    def get_search_namespace(self, resource, context):
        orderable_classes = resource.orderable_classes
        enum = Enumerate()
        options = []
        for cls in orderable_classes:
            options.append({'name': cls.class_id, 'value': cls.class_title})
        enum.options = options

        format = context.query['format']
        widget = SelectWidget('format')
        namespace = {}
        namespace['format_widget'] = widget.to_html(enum, format)

        return namespace



class BarItemsOrderedTable_View(ResourcesOrderedTable_View):

    subviews = [BarItemsOrderedTable_Ordered(),
                BarItemsOrderedTable_Unordered()]



class BarItemsOrderedTable(ResourcesOrderedTable):

    view = BarItemsOrderedTable_View()

    def get_order_root(self):
        return self.get_site_root().get_repository()


    def _get_order_root_path(self):
        root = self.get_order_root()
        if root:
            return self.get_pathto(root)
        return None

    order_root_path = property(_get_order_root_path)



class SidebarItemsOrderedTable(BarItemsOrderedTable):

    class_id = 'sidebar-items-ordered-table'
    class_title = MSG(u'Order sidebar items')

    def _orderable_classes(self):
        registry = get_bar_item_registry()
        types = [ cls for cls, allow in registry.iteritems()
                  if not allow[2] ] # is content
        return types

    orderable_classes = property(_orderable_classes)



class ContentbarItemsOrderedTable(BarItemsOrderedTable):

    class_id = 'contentbar-items-ordered-table'
    class_title = MSG(u'Order sidebar items')

    def _orderable_classes(self):
        registry = get_bar_item_registry()
        types = [ cls for cls, allow in registry.iteritems()
                  if allow[2] ] # is content
        return types

    orderable_classes = property(_orderable_classes)



class Repository(Folder):

    class_id = 'repository'
    class_title = MSG(u'Sidebar items repository')
    class_description = MSG(u'Sidebar items repository')
    class_icon16 = 'bar_items/icons/16x16/repository.png'
    class_icon48 = 'bar_items/icons/48x48/repository.png'
    class_views = ['browse_content', 'new_resource_form',
                   'new_sidebar_resource', 'new_contentbar_resource']
    __fixed_handlers__ = (Folder.__fixed_handlers__
                          + ['tags', 'website-articles-view',
                             'articles-view', 'news-siblings',
                             'children-toc'])

    # configuration
    news_siblings_view_cls = SidebarItem_NewsSiblingsToc
    news_siblings_view_name = 'news-siblings'
    section_articles_view_cls = ContentBarItem_Articles
    section_articles_view_name = 'articles-view'
    section_children_toc_view_cls = ContentBarItem_SectionChildrenToc
    section_children_toc_view_name = 'children-toc'
    website_articles_view_cls = WSNeutral_ContentBarItem_Articles
    website_articles_view_name = 'website-articles-view'

    new_resource = None
    new_sidebar_resource = Repository_NewResource(
            title=MSG(u'Add Sidebar Resource'))
    new_contentbar_resource = Repository_NewResource(
            title=MSG(u'Add Contentbar Resource'), is_content=True)
    browse_content = Repository_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        Folder._make_resource(cls, folder, name, **kw)
        # Website view item
        _cls = cls.website_articles_view_cls
        _cls._make_resource(_cls, folder,
                            '%s/%s' % (name, cls.website_articles_view_name))
        # section view item
        _cls = cls.section_articles_view_cls
        _cls._make_resource(_cls, folder,
                            '%s/%s' % (name, cls.section_articles_view_name))
        # section children toc
        _cls = cls.section_children_toc_view_cls
        _cls._make_resource(_cls, folder,
                '%s/%s' % (name, cls.section_children_toc_view_name))
        # news siblings item
        _cls = cls.news_siblings_view_cls
        _cls._make_resource(_cls, folder,
                            '%s/%s' % (name, cls.news_siblings_view_name))


    def _get_document_types(self, allow_instanciation=None, is_content=None,
                            allow_order=None):
        registry = get_bar_item_registry()
        types = []
        for cls, allow in registry.iteritems():
            if allow_instanciation is not None and \
                    allow_instanciation <> allow[0]:
                continue
            if is_content is not None and is_content <> allow[2]:
                continue
            if allow_order is not None and allow_order <> allow[1]:
                continue
            types.append(cls)
        return types


    def get_document_types(self):
        return self._get_document_types(allow_instanciation=True)


    def can_paste(self, source):
        """Is the source resource can be pasted into myself.
        Allow RightItem and BarItem
        but BarItem cannot be directly instanciated
        """
        allowed_types = self.get_document_types() + [BarItem]
        return isinstance(source, tuple(allowed_types))



###########################################################################
# Register
###########################################################################
register_resource_class(Repository)
register_resource_class(SidebarItem)
register_resource_class(SidebarItem_Section_News)
register_resource_class(SidebarItem_Tags)
register_resource_class(SidebarItem_SectionSiblingsToc)
register_resource_class(SidebarItem_SectionChildrenToc)
register_resource_class(SidebarItem_NewsSiblingsToc)
register_resource_class(SidebarItemsOrderedTable)
register_resource_class(ContentbarItemsOrderedTable)
register_resource_class(ContentBarItem_Articles)
register_resource_class(WSNeutral_ContentBarItem_Articles)
register_resource_class(ContentBarItem_SectionChildrenToc)

register_bar_item(SidebarItem, allow_instanciation=True)
register_bar_item(SidebarItem_Section_News, allow_instanciation=True)
register_bar_item(SidebarItem_Tags, allow_instanciation=True)
register_bar_item(SidebarItem_SectionSiblingsToc,
                  allow_instanciation=False)
register_bar_item(SidebarItem_SectionChildrenToc,
                  allow_instanciation=False)
register_bar_item(SidebarItem_NewsSiblingsToc, allow_instanciation=False)
register_bar_item(ContentBarItem_Articles, allow_instanciation=False,
                  is_content=True)
register_bar_item(WSNeutral_ContentBarItem_Articles, allow_instanciation=False,
                  is_content=True)
register_bar_item(ContentBarItem_SectionChildrenToc, allow_instanciation=False,
                  is_content=True)
# Register skin
path = get_abspath('ui/bar_items')
register_skin('bar_items', path)
