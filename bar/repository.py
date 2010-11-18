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


# Import from itools
from itools.core import get_abspath
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_PreviewContent, GoToSpecificDocument
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.skins import register_skin

# Import from itws.bar
from base import Box
from registry import get_boxes_registry
from repository_views import BoxesOrderedTable_Ordered
from repository_views import BoxesOrderedTable_Unordered
from repository_views import Repository_BrowseContent
from bar_aware_views import SideBarBox_NewInstance
from bar_aware_views import ContentBarBox_NewInstance
from tags import BoxTags


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


    @property
    def order_root_path(self):
        root = self.get_order_root()
        if root:
            return self.get_pathto(root)
        return None


    def update_relative_links(self, source):
        """Do not rewrite link, if the resource move."""
        pass


    def _reduce_orderable_classes(self, types):
        return types


    @property
    def orderable_classes(self):
        registry = get_boxes_registry()
        types = [ cls for cls, allow in registry.iteritems()
                  if allow[self.allow_filter_key] ]
        types.sort(lambda x, y : cmp(x.class_title.gettext(),
                                     y.class_title.gettext()))
        types = self._reduce_orderable_classes(types)
        return types


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
    new_box = SideBarBox_NewInstance(title=MSG(u'Create a new Sidebar Box'))



class ContentbarBoxesOrderedTable(BoxesOrderedTable):

    class_id = 'contentbar-boxes-ordered-table'
    class_title = MSG(u'Order Central Part Boxes')

    # _orderable_classes configuration
    allow_filter_key = 'content'

    # New box (Add a content bar)
    new_box = ContentBarBox_NewInstance(
                    title=MSG(u'Create a new ContentBar Box'))


    def get_order_root(self):
        return self.parent


    @property
    def order_root_path(self):
        root = self.get_order_root()
        if root:
            return self.get_pathto(root)
        return None



class Repository(Folder):

    class_id = 'repository'
    class_version = '20100625'
    class_title = MSG(u'Sidebar Boxes Repository')
    class_description = MSG(u'Sidebar boxes repository')
    class_icon16 = 'bar_items/icons/16x16/repository.png'
    class_icon48 = 'bar_items/icons/48x48/repository.png'
    class_views = ['browse_content', 'new_resource_form',
                   'new_sidebar_resource', 'backlinks', 'commit_log']

    tags_box = 'tags'
    news_box = 'news'

    __fixed_handlers__ = (Folder.__fixed_handlers__
                          + [tags_box, news_box])

    def init_resource(self, **kw):
        Folder.init_resource(self, **kw)
        # Tags (sidebar "tag cloud")
        self.make_resource(self.tags_box, BoxTags, state='public',
                           title={'en': BoxTags.class_title.gettext()})


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
    browse_content = Repository_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')



# Register skin
register_skin('bar_items', get_abspath('../ui/bar_items'))
