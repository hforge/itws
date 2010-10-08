# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 Nicolas Deram <nicolas@itaapy.com>
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

# Import from the Standard Library
from copy import deepcopy
from warnings import warn

# Import from itools
from itools.core import get_abspath, merge_dicts, freeze
from itools.datatypes import String, Boolean
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_PreviewContent, GoToSpecificDocument
from ikaaro.autoform import RadioWidget, CheckboxWidget, TextWidget
from ikaaro.autoform import HTMLBody, PathSelectorWidget, rte_widget
from ikaaro.autoform import SelectWidget
from ikaaro.menu import Target
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.registry import register_resource_class
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.skins import register_skin
from ikaaro.webpage import WebPage

# Import from itws
from datatypes import PositiveInteger, TagsAwareClassEnumerate
from repository_views import BoxNewsSiblingsToc_Preview
from repository_views import BoxNewsSiblingsToc_View
from repository_views import BoxSectionChildrenTree_View
from repository_views import BoxSectionNews_Edit
from repository_views import BoxSectionNews_Preview
from repository_views import BoxSectionNews_View
from repository_views import BoxesOrderedTable_Ordered
from repository_views import BoxesOrderedTable_Unordered
from repository_views import ContentBoxSectionChildrenToc_View
from repository_views import BoxTags_View, BoxTags_Preview
from repository_views import Box_Preview
from repository_views import ContentBoxSectionNews_View
from repository_views import HTMLContent_ViewBoth, HTMLContent_Edit
from repository_views import Repository_BrowseContent
from repository_views import SidebarBox_Preview, HTMLContent_View
from tags_views import TagsList
from utils import get_path_and_view
from views import AutomaticEditView, BoxAwareNewInstance, EasyNewInstance
from views import SideBarAwareNewInstance
from views import BarAwareBoxAwareNewInstance



hide_single_schema = freeze({'hide_if_only_one_item': Boolean(default=True)})
hide_single_widget = RadioWidget('hide_if_only_one_item',
        title=MSG(u'Hide if there is only one item'))



###########################################################################
# Register & Base classes
###########################################################################
boxes_registry = {}
def register_box(resource_class, allow_instanciation=True,
                 is_content=False, is_side=True):
    if is_content is False and is_side is False:
        msg = u'Box should be at least content box or side box'
        raise ValueError, msg

    boxes_registry[resource_class] = {'instanciation': allow_instanciation,
                                      'content': is_content, 'side': is_side}


def get_boxes_registry():
    # TODO Expose the dictionary through an user friendly API
    return freeze(boxes_registry)


# TODO Remove in itws 0.61.2
def register_bar_item(resource_class, allow_instanciation=True,
                      is_content=False, is_side=True):
    warn("register_bar_item function is deprecated, "
         "use register_box instead", DeprecationWarning)
    register_box(resource_class, allow_instanciation,
                 is_content, is_side)


def get_bar_item_registry():
    warn("get_bar_item_registry function is deprecated, "
         "use get_boxes_registry instead", DeprecationWarning)
    return get_boxes_registry()


class BoxAware(object):

    edit = AutomaticEditView()
    new_instance = EasyNewInstance()
    preview = order_preview = Box_Preview()

    edit_schema = {}
    edit_widgets = []



class Box(BoxAware, File):

    class_version = '20100622'
    class_title = MSG(u'Box')
    class_description = MSG(u'Sidebar box')
    edit_schema = {}
    class_schema = merge_dicts(File.class_schema,
                               edit_schema)

    download = None
    externaledit = None


class BoxSectionNews(Box):

    class_id = 'box-section-news'
    class_title = MSG(u'Last News Box (Sidebar)')
    class_icon16 = 'bar_items/icons/16x16/box_section_news.png'
    class_description = MSG(u'Display the last N news filtered by tags')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    class_schema = merge_dicts(Box.class_schema,
                               count=PositiveInteger(default=3),
                               tags=TagsList)

    # Views
    preview = order_preview = BoxSectionNews_Preview()
    view = BoxSectionNews_View()
    edit = BoxSectionNews_Edit()



class ContentBoxSectionNews(BoxSectionNews):

    class_id = 'contentbar-box-section-news'
    class_title = MSG(u'Last News Box (Contentbar)')

    view = ContentBoxSectionNews_View()



###########################################################################
# Sidebar resources
###########################################################################
class HTMLContent(WebPage):

    class_id = 'html-content'
    class_version = '20100621'
    class_title = MSG(u'HTML Content')
    class_description = MSG(u'HTML snippet which can be displayed in the '
                             'central and/or the sidebar')

    class_schema = merge_dicts(WebPage.class_schema,
         # Metadata
         title_link=String(source='metadata'),
         title_link_target=Target(source='metadata', default='_top'))

    # Configuration of box for EditView
    edit_schema = {'title_link': String,
                   'title_link_target': Target,
                   'data': HTMLBody(ignore=True),
                   'display_title': Boolean}

    edit_widgets = [
        CheckboxWidget('display_title',
                        title=MSG(u'Display on webpage view')),
        PathSelectorWidget('title_link', title=MSG(u'Title link')),
        SelectWidget('title_link_target', title=MSG(u'Title link target')),
        rte_widget
        ]


    ###########################
    ## Links API
    ###########################

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


    #########
    # Views
    #########
    view_both = HTMLContent_ViewBoth()
    preview = order_preview = SidebarBox_Preview()
    edit = HTMLContent_Edit()
    view = HTMLContent_View()
    new_instance = EasyNewInstance()



class BoxTags(Box):

    class_id = 'box-tags'
    class_version = '20100527'
    class_title = MSG(u'Tag Cloud')
    class_description = MSG(u'Display a tag cloud')
    class_icon16 = 'bar_items/icons/16x16/box_tags.png'
    class_views = ['edit', 'edit_state', 'backlinks', 'commit_log']

    # Box configuration
    edit_schema = {'formats': TagsAwareClassEnumerate(multiple=True),
                   'count':PositiveInteger(default=0),
                   'show_number': Boolean,
                   'random': Boolean,
                   'display_title': Boolean}

    edit_widgets = [
        CheckboxWidget('display_title',
                        title=MSG(u'Display on tagcloud view')),
        TextWidget('count', size=4,
                   title=MSG(u'Tags to show (0 for all tags)')),
        CheckboxWidget('show_number',
                        title=MSG(u'Show number of items for each tag')),
        CheckboxWidget('random', title=MSG(u'Randomize tags')),
        RadioWidget('formats', has_empty_option=False,
                    title=MSG(u'This tag cloud will display only '
                              u'the tags from selected types of content'))
        ]

    # Views
    view = BoxTags_View()
    preview = order_preview = BoxTags_Preview()



class BoxSectionChildrenToc(Box):

    class_id = 'box-section-children-toc'
    class_title = MSG(u'Subsections and Webpages TOC')
    class_description = MSG(u'Table Of Content (TOC) to display choosen '
                            u'subsections and webpages')

    # Box comfiguration
    edit_schema = hide_single_schema
    edit_widgets = [hide_single_widget]
    display_title = False

    # Views
    view = BoxSectionChildrenTree_View()



class BoxNewsSiblingsToc(Box):

    class_id = 'box-news-siblings-toc'
    class_title = MSG(u'News TOC')
    class_description = MSG(u'Display the list of news.')
    class_views = ['edit', 'edit_state', 'backlinks', 'commit_log']

    # Box configuration
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

    # Box configuration
    edit_schema = hide_single_schema
    edit_widgets = [hide_single_widget]

    # Views
    view = ContentBoxSectionChildrenToc_View()



###########################################################################
# Repository
###########################################################################

class BoxesOrderedTable(ResourcesOrderedTable):

    class_views = ['view', 'add_box', 'new_box', 'commit_log']
    allow_filter_key = None


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
                    title=parent_view.title)
        return None


    def get_order_root(self):
        return self.get_site_root().get_repository()


    def _get_order_root_path(self):
        root = self.get_order_root()
        if root:
            return self.get_pathto(root)
        return None

    order_root_path = property(_get_order_root_path)


    def update_relative_links(self, source):
        """Do not rewrite link, if the resource move."""
        pass


    def _reduce_orderable_classes(self, types):
        return types


    def _orderable_classes(self):
        registry = get_boxes_registry()
        types = [ cls for cls, allow in registry.iteritems()
                  if allow[self.allow_filter_key] ]
        types.sort(lambda x, y : cmp(x.class_title.gettext(),
                                     y.class_title.gettext()))
        types = self._reduce_orderable_classes(types)
        return types

    orderable_classes = property(_orderable_classes)

    ############
    # Views
    ############
    view = BoxesOrderedTable_Ordered()
    add_box = BoxesOrderedTable_Unordered()
    new_box = None



class SidebarBoxesOrderedTable(BoxesOrderedTable):

    class_id = 'sidebar-boxes-ordered-table'
    class_title = MSG(u'Manage sidebar Boxes')
    class_description = None

    # _orderable_classes configuration
    allow_filter_key = 'side'

    # New box (Add a sidebar box)
    new_box = SideBarAwareNewInstance(title=MSG(u'Create a new Sidebar Box'))

    # Order view title & description configuration
    ordered_view_title = MSG(u'Order Sidebar Boxes')
    ordered_view_title_description = MSG(
            u'This website has a sidebar and a central part. '
            u'The sidebar can be composed of several kinds of boxes: '
            u'Tag Cloud, "last News View", HTML Content, Twitter Feeds, '
            u'Custom Menu... Here you can order these boxes.')
    unordered_view_title = MSG(u'Available Sidebar Boxes')
    unordered_view_title_description = MSG(
            u'These boxes are available, you can make them visible '
            u'in the sidebar by adding them to the above ordered list.')



class ContentbarBoxesOrderedTable(BoxesOrderedTable):

    class_id = 'contentbar-boxes-ordered-table'
    class_title = MSG(u'Order Central Part Boxes')

    # _orderable_classes configuration
    allow_filter_key = 'content'

    # New box (Add a content bar)
    new_box = BarAwareBoxAwareNewInstance(
                    title=MSG(u'Create a new ContentBar Box'))

    # Order view title & description configuration
    ordered_view_title = MSG(u'Order Central Part Boxes')
    ordered_view_title_description = MSG(
            u'This website has a sidebar and a central part. '
            u'The central part can be composed of several kinds of '
            u'boxes: "Last News View", Slideshow... '
            u'Here you can order these boxes.')
    unordered_view_title = MSG(u'Available Central Part Boxes')
    unordered_view_title_description = MSG(
            u'These boxes are available, you can make them visible '
            u'in the central part by adding them to the above ordered list.')


    def get_order_root(self):
        return self.parent
        #return self.get_site_root().get_repository()


    def _get_order_root_path(self):
        root = self.get_order_root()
        if root:
            return self.get_pathto(root)
        return None

    order_root_path = property(_get_order_root_path)



class Repository(Folder):

    class_id = 'repository'
    class_version = '20100625'
    class_title = MSG(u'Sidebar Boxes Repository')
    class_description = MSG(u'Sidebar boxes repository')
    class_icon16 = 'bar_items/icons/16x16/repository.png'
    class_icon48 = 'bar_items/icons/48x48/repository.png'
    class_views = ['browse_content', 'new_resource_form',
                   'new_sidebar_resource', 'backlinks', 'commit_log']
    __fixed_handlers__ = (Folder.__fixed_handlers__
                          + ['tags', 'website-articles-view',
                             'articles-view', 'news-siblings',
                             'sidebar-children-toc', 'news'])

    def init_resource(self, **kw):
        Folder.init_resource(self, **kw)
        # We initialize repository with some boxes
        kw = {'title': {'en': BoxNewsSiblingsToc.class_title.gettext()},
              'state': 'public'}
        self.make_resource('news-siblings', BoxNewsSiblingsToc)
        self.make_resource('sidebar-children-toc', BoxSectionChildrenToc)
        self.make_resource('news', BoxSectionNews)


    def _get_document_types(self, allow_instanciation=None, is_content=None,
                            is_side=None):
        registry = get_boxes_registry()
        types = []
        for cls, allow in registry.iteritems():
            if allow_instanciation is not None and \
                    allow_instanciation <> allow['instanciation']:
                continue
            if is_content is not None and is_content <> allow['content']:
                continue
            if is_side is not None and is_side <> allow['side']:
                continue
            types.append(cls)
        types.sort(lambda x, y : cmp(x.class_id, y.class_id))
        return types


    def get_document_types(self):
        return self._get_document_types(allow_instanciation=True,
                                        is_side=True)


    def can_paste(self, source):
        """Is the source resource can be pasted into myself.
        Allow RightItem and Box
        but Box cannot be directly instanciated
        """
        allowed_types = self.get_document_types() + [Box]
        return isinstance(source, tuple(allowed_types))


    #################
    # Views
    ################
    new_resource = None
    new_sidebar_resource = BoxAwareNewInstance(title=MSG(u'Create a new Sidebar Box'),
                                               is_side=True)
    browse_content = Repository_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')




###########################################################################
# Register
###########################################################################
register_resource_class(Repository)
register_resource_class(HTMLContent)
register_resource_class(BoxSectionNews)
register_resource_class(BoxTags)
register_resource_class(BoxSectionChildrenToc)
register_resource_class(BoxNewsSiblingsToc)
register_resource_class(SidebarBoxesOrderedTable)
register_resource_class(ContentbarBoxesOrderedTable)
register_resource_class(ContentBoxSectionChildrenToc)
register_resource_class(ContentBoxSectionNews)

register_box(HTMLContent, allow_instanciation=True, is_content=True)
register_box(BoxSectionNews, allow_instanciation=True,
             is_side=True, is_content=False)
register_box(BoxTags, allow_instanciation=True)
register_box(BoxSectionChildrenToc,
             allow_instanciation=False)
register_box(BoxNewsSiblingsToc, allow_instanciation=False)
register_box(ContentBoxSectionChildrenToc, allow_instanciation=False,
             is_content=True, is_side=False)
register_box(ContentBoxSectionNews, allow_instanciation=True,
             is_content=True, is_side=False)
# Register skin
path = get_abspath('ui/bar_items')
register_skin('bar_items', path)
