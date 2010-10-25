# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2010 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Alexis Huet <alexis@itaapy.com>
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

# Import from the Standard Library
from copy import deepcopy

# Import from itools
from itools.core import get_abspath, merge_dicts
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.future.order import ResourcesOrderedContainer
from ikaaro.future.order import GoToFirstOrderedResource, GoToOrderedTable
from ikaaro.registry import register_resource_class, register_document_type
from ikaaro.skins import register_skin
from ikaaro.webpage import WebPage

# Import from itws
from datatypes import PositiveIntegerNotNull, ImagePathDataType
from slides_views import SlideShow_Edit, Slide_Edit, Slide_View
from slides_views import SlideShow_BrowseContent, SlideTemplateType
from tags import TagsAware
from utils import get_path_and_view



class Slide(TagsAware, WebPage):

    class_id = 'slide'
    class_version = '20100618'
    class_title = MSG(u'Slide')
    class_description = MSG(u'Slide')
    class_views = ['view', 'edit', 'edit_state', 'backlinks', 'commit_log']


    class_schema = merge_dicts(WebPage.class_schema,
                       TagsAware.class_schema,
                       long_title=Unicode(source='metadata'),
                       image=ImagePathDataType(source='metadata'),
                       template_type=SlideTemplateType(source='metadata', default=''),
                       href=String(source='metadata'))


    def get_catalog_values(self):
        return merge_dicts(WebPage.get_catalog_values(self),
                           TagsAware.get_catalog_values(self))


    def get_slide_image(self):
        # FIXME PathDatatype is 'buggy'
        path = self.get_property('image')
        image = self.get_resource(path, soft=True)
        if isinstance(image, Image) is False:
            # parent
            parent = self.parent
            path = parent.get_property('image')
            image = parent.get_resource(path)

        if isinstance(image, Image) is False:
            return None

        return image


    ##########################################################################
    # TagsAware API
    ##########################################################################
    def get_preview_thumbnail(self):
        return self.get_slide_image()


    ##########################################################################
    # Links API
    ##########################################################################
    def get_links(self):
        links = WebPage.get_links(self)
        links.extend(TagsAware.get_links(self))

        base = self.get_canonical_path()
        for key in ('image', 'href'):
            value = self.get_property(key)
            if value:
                uri = get_reference(value)
                if not uri.scheme:
                    path, view = get_path_and_view(uri.path)
                    links.append(str(base.resolve2(path)))
        return links


    def update_links(self, source, target):
        WebPage.update_links(self, source, target)
        TagsAware.update_links(self, source, target)

        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        for key in ('image', 'href'):
            path = self.get_property(key)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            path, view = get_path_and_view(ref.path)
            path = str(old_base.resolve2(path))
            if path == source:
                # Hit the old name
                # Build the new reference with the right path
                new_ref = deepcopy(ref)
                new_ref.path = str(new_base.get_pathto(target)) + view
                self.set_property(key, str(new_ref))

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        WebPage.update_relative_links(self, source)
        # Not need for TagsAware

        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        for key in ('img_path', 'img_link'):
            path = self.get_property(key)
            if not path:
                continue
            ref = get_reference(str(path))
            if ref.scheme:
                continue
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
            # Update the property
            self.set_property(key, str(new_ref))


    ###################
    ## Views
    ###################
    edit = Slide_Edit()
    view = Slide_View()

    # XXX Not used
    # use by tag_view
    view_only_content = Slide_View(only_content=True)



class Slides_OrderedTable(ResourcesOrderedTable):

    class_id = 'slides-ordered-table'
    class_title = MSG(u'Slides Ordered Table')

    orderable_classes = (Slide,)



class SlideShow(ResourcesOrderedContainer):

    class_id = 'slides'
    class_title = MSG(u'Slideshow')
    class_description = MSG(u'Slideshow allows to create and organize slides')
    class_icon16 = 'slideshow/icons/16x16/slideshow.png'
    class_icon48 = 'slideshow/icons/48x48/slideshow.png'
    class_views = ['new_resource', 'manage_view', 'view', 'edit', 'order']
    class_schema = merge_dicts(ResourcesOrderedContainer.class_schema,
                   long_title=Unicode(source='metadata'),
                   image=ImagePathDataType(source='metadata'),
                   toc_nb_col=PositiveIntegerNotNull(source='metadata', default=2),
                   template_type=SlideTemplateType(source='metadata', default='1'))


    __fixed_handlers__ = ['order-slides']

    order_path = 'order-slides'
    order_class = Slides_OrderedTable
    slide_class = Slide

    # Views
    manage_view = SlideShow_BrowseContent()
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    view = GoToFirstOrderedResource()
    edit = SlideShow_Edit()
    order = GoToOrderedTable(title=MSG(u'Order slides'))


    def get_document_types(self):
        return [Slide, Image]


    ##########################################################################
    # Links API
    ##########################################################################
    def get_links(self):
        base = self.get_canonical_path()
        links = ResourcesOrderedContainer.get_links(self)
        value = self.get_property('image')
        if value:
            uri = get_reference(value)
            if not uri.scheme:
                path, view = get_path_and_view(uri.path)
                links.append(str(base.resolve2(path)))
        return links


    def update_links(self, source, target):
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        path = self.get_property('image')
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
                    self.set_property('image', str(new_ref))

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        ResourcesOrderedContainer.update_relative_links(self, source)

        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new
        path = self.get_property('image')
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
                self.set_property('image', str(new_ref))



register_resource_class(Slide)
register_resource_class(SlideShow)
register_resource_class(Slides_OrderedTable)
register_document_type(Slide, TagsAware.class_id)

# Register skin
path = get_abspath('ui/slideshow')
register_skin('slideshow', path)
