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
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.forms import SelectRadio, BooleanCheckBox, TextWidget
from ikaaro.future.menu import Target
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.registry import register_resource_class
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.skins import register_skin

# Import from itws
from datatypes import PositiveInteger, TagsAwareClassEnumerate
from repository_views import BoxNewsSiblingsToc_Preview
from repository_views import BoxNewsSiblingsToc_View
from repository_views import BoxSectionChildrenTree_View
from repository_views import BoxSectionNews_Edit
from repository_views import BoxSectionNews_Preview
from repository_views import BoxSectionNews_View
from repository_views import BoxSectionWebpages_View
from repository_views import BoxTags_View, BoxTags_Preview
from repository_views import BoxWebsiteWebpages_View
from repository_views import Box_Edit, Box_Preview
from repository_views import BoxesOrderedTable_View
from repository_views import ContentBoxSectionChildrenToc_View
from repository_views import HTMLContent_ViewBoth, HTMLContent_Edit
from repository_views import Repository_BrowseContent, Repository_NewResource
from repository_views import SidebarBox_Preview, HTMLContent_View
from utils import get_path_and_view
from views import EasyNewInstance
from webpage import WebPage


hide_single_schema = freeze({'hide_if_only_one_item': Boolean})
hide_single_widget = BooleanCheckBox('hide_if_only_one_item',
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


class Box(File):

    class_description = MSG(u'Sidebar box')
    preview = order_preview = Box_Preview()
    edit = Box_Edit()
    download = None
    externaledit = None
    new_instance = EasyNewInstance()


    box_schema = {}
    box_widgets = []

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(File.get_metadata_schema(),
                           cls.box_schema,
                           state=String(default='public'))



class BoxSectionNews(Box):

    class_id = 'box-section-news'
    class_title = MSG(u'Last News Box')
    class_description = MSG(u'Display the last N news filtered by tags')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']

    # Box configuration
    box_schema = {
        'tags': String(multiple=True),
        'count': PositiveInteger(default=0)
        }

    # Views
    preview = order_preview = BoxSectionNews_Preview()
    view = BoxSectionNews_View()
    edit = BoxSectionNews_Edit()



###########################################################################
# Sidebar resources
###########################################################################
class HTMLContent(WebPage):

    class_id = 'html-content'
    class_version = '20091127'
    class_title = MSG(u'HTML Content')
    class_description = MSG('HTML snippet which can be displayed in the '
                            'central and/or the sidebar')

    # Views
    view_both = HTMLContent_ViewBoth()
    preview = order_preview = SidebarBox_Preview()
    edit = HTMLContent_Edit()
    view = HTMLContent_View()
    new_instance = EasyNewInstance()


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



class BoxTags(Box):

    class_id = 'box-tags'
    class_version = '20100527'
    class_title = MSG(u'Tag Cloud')
    class_description = MSG(u'Display a tag cloud')
    class_views = ['edit', 'edit_state', 'backlinks', 'commit_log']

    # Box configuration
    box_schema = {'formats': TagsAwareClassEnumerate(multiple=True),
                  'count':PositiveInteger(default=0),
                  'show_number': Boolean,
                  'random': Boolean}

    box_widgets = [
        TextWidget('count', size=4,
                   title=MSG(u'Tags to show (0 for all tags)')),
        BooleanCheckBox('show_number',
                        title=MSG(u'Show number of items for each tag')),
        BooleanCheckBox('random', title=MSG(u'Randomize tags')),
        SelectRadio('formats', has_empty_option=False,
                    title=MSG(u'This tag cloud will display only '
                              u'the tags from selected types of content'))
        ]

    def update_20100527(self):
        # format -> formats
        formats = self.get_property('format')
        if formats:
            self.set_property('formats', formats.split())
        self.del_property('format')


    # Views
    view = BoxTags_View()
    preview = order_preview = BoxTags_Preview()



class BoxSectionChildrenToc(Box):

    class_id = 'box-section-children-toc'
    class_title = MSG(u'Subsections and Webpages TOC')
    class_description = MSG(u'Table Of Content (TOC) to display choosen '
                            u'subsections and webpages')

    # Box comfiguration
    box_schema = hide_single_schema
    box_widgets = [hide_single_widget]

    # Views
    view = BoxSectionChildrenTree_View()



class BoxNewsSiblingsToc(Box):

    class_id = 'box-news-siblings-toc'
    class_title = MSG(u'News TOC')
    class_description = MSG(u'Display the list of news.')
    class_views = ['edit', 'edit_state', 'backlinks', 'commit_log']

    # Box configuration
    box_schema = merge_dicts(hide_single_schema,
                             count=PositiveInteger(default=30))

    box_widgets = [
        hide_single_widget,
        TextWidget('count', size=3,
                   title=MSG(u'Maximum number of news to display'))
        ]

    # Views
    view = BoxNewsSiblingsToc_View()
    preview = order_preview = BoxNewsSiblingsToc_Preview()



###########################################################################
# Contentbar resources
###########################################################################
class BoxSectionWebpages(Box):

    class_id = 'contentbar-box-articles'
    class_title = MSG(u"Section's Webpages")
    class_description = MSG(u'Display the ordered webpages of the section')
    class_views = ['edit_state', 'backlinks']

    use_fancybox = False

    view = BoxSectionWebpages_View()

    def get_admin_edit_link(self, context):
        return './order-section'


class BoxWebsiteWebpages(BoxSectionWebpages):

    class_id = 'ws-neutral-box-articles'
    class_title = MSG(u"Website's Webpages")
    class_description = MSG(u'Display the ordered webpages of the homepage')
    class_views = ['edit_state', 'backlinks']

    view = BoxWebsiteWebpages_View()

    def get_admin_edit_link(self, context):
        return '/ws-data/order-resources'


class ContentBoxSectionChildrenToc(Box):

    class_id = 'contentbar-box-children-toc'
    class_title = MSG(u'Subsections and Webpages TOC')
    class_description = MSG(u'Table Of Content (TOC) to display choosen '
                            u'subsections and webpages in the central part')
    class_views = ['edit_state', 'backlinks']

    # Box configuration
    box_schema = hide_single_schema
    box_widgets = [hide_single_widget]

    # Views
    view = ContentBoxSectionChildrenToc_View()



###########################################################################
# Repository
###########################################################################
class BoxesOrderedTable(ResourcesOrderedTable):

    view = BoxesOrderedTable_View()

    def get_order_root(self):
        return self.get_site_root().get_repository()


    def _get_order_root_path(self):
        root = self.get_order_root()
        if root:
            return self.get_pathto(root)
        return None

    order_root_path = property(_get_order_root_path)



class SidebarBoxesOrderedTable(BoxesOrderedTable):

    class_id = 'sidebar-boxes-ordered-table'
    class_title = MSG(u'Order Sidebar Boxes')

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


    def _orderable_classes(self):
        registry = get_boxes_registry()
        types = [ cls for cls, allow in registry.iteritems()
                  if allow['side'] ] # is side
        types.sort(lambda x, y : cmp(x.class_id, y.class_id))
        return types

    orderable_classes = property(_orderable_classes)



class ContentbarBoxesOrderedTable(BoxesOrderedTable):

    class_id = 'contentbar-boxes-ordered-table'
    class_title = MSG(u'Order Central Part Boxes')

    # Order view title & description configuration
    ordered_view_title = MSG(u'Order Central Part Boxes')
    ordered_view_title_description = MSG(
            u'This website has a sidebar and a central part. '
            u'The central part can be composed of several kinds of '
            u'boxes: "Webpages Slot", "Last News View", Slideshow... '
            u'Here you can order these boxes.')
    unordered_view_title = MSG(u'Available Central Part Boxes')
    unordered_view_title_description = MSG(
            u'These boxes are available, you can make them visible '
            u'in the central part by adding them to the above ordered list.')

    def _orderable_classes(self):
        registry = get_boxes_registry()
        types = [ cls for cls, allow in registry.iteritems()
                  if allow['content'] ] # is content
        types.sort(lambda x, y : cmp(x.class_id, y.class_id))
        return types

    orderable_classes = property(_orderable_classes)



class Repository(Folder):

    class_id = 'repository'
    class_version = '20100611'
    class_title = MSG(u'Sidebar Boxes Repository')
    class_description = MSG(u'Sidebar boxes repository')
    class_icon16 = 'bar_items/icons/16x16/repository.png'
    class_icon48 = 'bar_items/icons/48x48/repository.png'
    class_views = ['browse_content', 'new_resource_form',
                   'new_sidebar_resource', 'new_contentbar_resource',
                   'backlinks', 'commit_log']
    __fixed_handlers__ = (Folder.__fixed_handlers__
                          + ['tags', 'website-articles-view',
                             'articles-view', 'news-siblings',
                             'content-children-toc', 'sidebar-children-toc',
                             'news'])

    # configuration
    news_items_cls = BoxSectionNews
    news_items_name = 'news'
    news_siblings_view_cls = BoxNewsSiblingsToc
    news_siblings_view_name = 'news-siblings'
    section_articles_view_cls = BoxSectionWebpages
    section_articles_view_name = 'articles-view'
    section_content_children_toc_view_cls = ContentBoxSectionChildrenToc
    section_content_children_toc_view_name = 'content-children-toc'
    section_sidebar_children_toc_view_cls = BoxSectionChildrenToc
    section_sidebar_children_toc_view_name = 'sidebar-children-toc'
    website_articles_view_cls = BoxWebsiteWebpages
    website_articles_view_name = 'website-articles-view'

    new_resource = None
    new_sidebar_resource = Repository_NewResource(
            title=MSG(u'Add Sidebar Resource'))
    new_contentbar_resource = Repository_NewResource(
            title=MSG(u'Add Central Part Resource'), is_content=True)
    browse_content = Repository_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        Folder._make_resource(cls, folder, name, **kw)
        # Website view box
        _cls = cls.website_articles_view_cls
        _cls._make_resource(_cls, folder,
                            '%s/%s' % (name, cls.website_articles_view_name),
                            title={'en': _cls.class_title.gettext()})
        # section view box
        _cls = cls.section_articles_view_cls
        _cls._make_resource(_cls, folder,
                            '%s/%s' % (name, cls.section_articles_view_name),
                            title={'en': _cls.class_title.gettext()})
        # section content children toc
        _cls = cls.section_content_children_toc_view_cls
        _cls._make_resource(_cls, folder,
                '%s/%s' % (name, cls.section_content_children_toc_view_name),
                           title={'en': _cls.class_title.gettext()})
        # section sidebar children toc
        _cls = cls.section_sidebar_children_toc_view_cls
        _cls._make_resource(_cls, folder,
                '%s/%s' % (name, cls.section_sidebar_children_toc_view_name),
                           title={'en': _cls.class_title.gettext()})
        # news siblings box
        _cls = cls.news_siblings_view_cls
        _cls._make_resource(_cls, folder,
                            '%s/%s' % (name, cls.news_siblings_view_name),
                            title={'en': _cls.class_title.gettext()})
        # news
        _cls = cls.news_items_cls
        _cls._make_resource(_cls, folder,
                            '%s/%s' % (name, cls.news_items_name),
                            title={'en': _cls.class_title.gettext()})


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
                                        is_content=True, is_side=True)


    def can_paste(self, source):
        """Is the source resource can be pasted into myself.
        Allow RightItem and Box
        but Box cannot be directly instanciated
        """
        allowed_types = self.get_document_types() + [Box]
        return isinstance(source, tuple(allowed_types))


    def update_20100519(self):
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')

        name = self.website_articles_view_name
        cls = self.website_articles_view_cls
        resource = self.get_resource(name, soft=True)
        if resource:
            resource.set_property('title', cls.class_title.gettext(),
                                  language=languages[0])

        name = self.section_articles_view_name
        cls = self.section_articles_view_cls
        resource = self.get_resource(name, soft=True)
        if resource:
            resource.set_property('title', cls.class_title.gettext(),
                                  language=languages[0])

        name = self.section_content_children_toc_view_name
        cls = self.section_content_children_toc_view_cls
        resource = self.get_resource(name, soft=True)
        if resource:
            resource.set_property('title', cls.class_title.gettext(),
                                  language=languages[0])

        name = self.news_siblings_view_name
        cls = self.news_siblings_view_cls
        resource = self.get_resource(name, soft=True)
        if resource:
            resource.set_property('title', cls.class_title.gettext(),
                                  language=languages[0])


    def update_20100527(self):
        # Fix commit 2c0dbce6f2
        from ikaaro.utils import generate_name

        old_children_toc = self.get_resource('children-toc', soft=True)
        children_toc_cls = self.section_content_children_toc_view_cls
        children_toc_name = self.section_content_children_toc_view_name
        if old_children_toc and isinstance(old_children_toc, children_toc_cls):
            # Rename children-toc -> content-children-toc
            self.move_resource('children-toc', children_toc_name)

        for name, cls in ((self.news_siblings_view_name,
                           self.news_siblings_view_cls),
                          (self.section_articles_view_name,
                           self.section_articles_view_cls),
                          (self.section_content_children_toc_view_name,
                           self.section_content_children_toc_view_cls),
                          (self.section_sidebar_children_toc_view_name,
                           self.section_sidebar_children_toc_view_cls)):
            box = self.get_resource(name, soft=True)
            create = False
            if box:
                # check format
                if isinstance(box, cls) is False:
                    name2 = generate_name(name, self.get_names(), '_bad_cls_')
                    self.move_resource(name, name2)
                    create = True
            else:
                create = True

            if create:
                cls.make_resource(cls, self, name,
                                  title={'en': cls.class_title.gettext()})


    def update_20100607(self):
        from ikaaro.utils import generate_name

        name = self.news_items_name
        cls = self.news_items_cls

        box = self.get_resource(name, soft=True)
        create = False

        if box:
            if isinstance(box, cls):
                # ok
                return
            else:
                # Move
                name2 = generate_name(name, self.get_names(), '_bad_cls_')
                self.move_resource(name, name2)
                create = True
        else:
            create = True

        if create:
            box = cls.make_resource(cls, self, name)
            box.set_property('title', cls.class_title.gettext(), 'en')


    def update_20100608(self):
        for box in self.search_resources(format='sidebar-item'):
            metadata = box.metadata
            metadata.set_changed()
            metadata.format = HTMLContent.class_id


    def update_20100609(self):
        # Remove obsolete SidebarBox_SectionSiblingsToc
        from itools.xapian import PhraseQuery

        old_name = 'sidebar-siblings-toc'
        box = self.get_resource(old_name, soft=True)
        if box is None:
            return

        children_toc_cls = ContentBoxSectionChildrenToc
        # Check referencial-integrity
        root = get_context().root
        results = root.search(PhraseQuery('links', str(box.get_abspath())))
        if len(results):
            print u'box %s is referenced by' % box.get_abspath()
            for doc in results.get_documents():
                resource = root.get_resource(doc.abspath)
                print u'-->', doc.abspath, doc.format
                #if isinstance(resource, BoxesOrderedTable):
                if isinstance(resource, ResourcesOrderedTable):
                    # Case 1: ordered table
                    handler = resource.handler
                    id_to_remove = None
                    children_toc_item = None
                    for record in handler.get_records():
                        name = handler.get_record_value(record, 'name')
                        if name == old_name:
                            id_to_remove = record.id
                            continue
                        box = self.get_resource(name, soft=True)
                        if box and isinstance(box, children_toc_cls):
                            children_toc_item = box
                            continue

                    if children_toc_item:
                        # Simply delete record
                        resource.del_record(id_to_remove)
                    else:
                        # Add at the same place a children toc
                        # -> update record
                        resource.update_record(id_to_remove,
                                               **{'name': 'content-children-toc'})
                else:
                    # Other type of resource
                    # Call update_link
                    source = box.get_abspath()
                    target = self.get_abspath().resolve2('content-children-toc')
                    resource.update_link(source, target)


    def update_20100610(self):
        # update_20100609 continuation
        # Delete SidebarBox_SectionSiblingsToc
        if self.get_resource('sidebar-siblings-toc', soft=True):
            self.del_resource('sidebar-siblings-toc')


    def update_20100611(self):
        # Update class_id
        for old_cls_id, new_cls_id in (
                ('sidebar-item-section-news','box-section-news'),
                ('sidebar-item-tags', 'box-tags'),
                ('sidebar-item-section-children-toc', 'box-section-children-toc'),
                ('sidebar-item-news-siblings-toc', 'box-news-siblings-toc'),
                ('contentbar-item-articles', 'contentbar-box-articles'),
                ('ws-neutral-item-articles', 'ws-neutral-box-articles'),
                ('contentbar-item-children-toc', 'contentbar-box-children-toc'),
                ('sidebar-items-ordered-table', 'sidebar-boxes-ordered-table'),
                ('contentbar-items-ordered-table', 'contentbar-boxes-ordered-table'),
                # sidebar/xxx
                ('sidebar-item-twitter', 'box-twitter'),
                ('sidebar-item-menu', 'box-menu')):
            for resource in self.search_resources(format=old_cls_id):
                metadata = resource.metadata
                metadata.set_changed()
                metadata.format = new_cls_id
                print old_cls_id, new_cls_id


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
register_resource_class(BoxSectionWebpages)
register_resource_class(BoxWebsiteWebpages)
register_resource_class(ContentBoxSectionChildrenToc)

register_box(HTMLContent, allow_instanciation=True, is_content=True)
register_box(BoxSectionNews, allow_instanciation=True,
             is_side=True, is_content=True)
register_box(BoxTags, allow_instanciation=True)
register_box(BoxSectionChildrenToc,
             allow_instanciation=False)
register_box(BoxNewsSiblingsToc, allow_instanciation=False)
register_box(BoxSectionWebpages, allow_instanciation=False,
             is_content=True, is_side=False)
register_box(BoxWebsiteWebpages, allow_instanciation=False,
             is_content=True, is_side=False)
register_box(ContentBoxSectionChildrenToc, allow_instanciation=False,
             is_content=True, is_side=False)
# Register skin
path = get_abspath('ui/bar_items')
register_skin('bar_items', path)
