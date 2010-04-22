# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2010 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Alexis Huet <alexis@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
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
from itools.datatypes import String, Unicode, Enumerate
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import STLView, get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.forms import ImageSelectorWidget, PathSelectorWidget, TextWidget
from ikaaro.forms import rte_widget
from ikaaro.forms import timestamp_widget, SelectRadio, stl_namespaces
from ikaaro.forms import title_widget, description_widget, subject_widget
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.future.order import ResourcesOrderedContainer
from ikaaro.future.order import GoToFirstOrderedResource, GoToOrderedTable
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.registry import register_resource_class, register_document_type
from ikaaro.resource_views import DBResource_Edit
from ikaaro.skins import register_skin
from ikaaro.webpage import WebPage, HTMLEditView

# Import from itws
from datatypes import PositiveIntegerNotNull
from tags import TagsAware, TagsAware_Edit, Tag_ItemView
from utils import get_path_and_view
from views import STLBoxView



class SlideTemplateTypeWidget(SelectRadio):

    template = list(XMLParser("""
        <stl:block stl:if="has_empty_option">
          <input type="radio" name="${name}" value="" checked="checked"
            stl:if="none_selected"/>
          <input type="radio" name="${name}" value=""
            stl:if="not none_selected"/>
          <label for="${name}">
            <img src="/ui/slideshow/preview/type_default.png" />
          </label>
          <stl:block stl:if="not is_inline"><br/></stl:block>
        </stl:block>
        <stl:block stl:repeat="option options">
          <input type="radio" id="${name}-${option/name}" name="${name}"
            value="${option/name}" checked="checked"
            stl:if="option/selected"/>
          <input type="radio" id="${name}-${option/name}" name="${name}"
            value="${option/name}" stl:if="not option/selected"/>
          <label for="${name}_${option/name}">
            <img src="/ui/slideshow/preview/type${option/name}.png" />
          </label>
          <stl:block stl:if="not is_inline"><br/></stl:block>
        </stl:block>
        """, stl_namespaces))

    template_multiple = list(XMLParser("""
        <stl:block stl:repeat="option options">
          <input type="checkbox" name="${name}" id="${name}-${option/name}"
            value="${option/name}" checked="${option/selected}" />
          <label for="${name}_${option/name}">
            <img src="/ui/slideshow/preview/type${option/name}.png" />
          </label>
          <stl:block stl:if="not is_inline"><br/></stl:block>
        </stl:block>
        """, stl_namespaces))



class SlideTemplateType(Enumerate):

    options = [{'name': '1', 'value': u'Type 1'},
               {'name': '2', 'value': u'Type 2'},
               {'name': '3', 'value': u'Type 3'},
               {'name': '4', 'value': u'Type 4'}]



class Slide_View(STLBoxView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    styles = ['/ui/slideshow/style.css']
    base_template = '/ui/slideshow/Slide_view_type_%s.xml'
    content_only = False


    def get_template(self, resource, context):
        template_type = resource.get_property('template_type')
        if not template_type:
            # Get the template from the slideshow
            template_type = resource.parent.get_property('template_type')

        # Check there is a template defined
        if template_type is None:
            msg = "%s is missing the 'template' variable"
            raise NotImplementedError, msg % repr(self.__class__)
        # XXX A handler actually
        return resource.get_resource(self.base_template % template_type)


    def _get_box_css(self, resource, context):
        """STLBoxView API"""
        template_type = resource.get_property('template_type')
        if not template_type:
            # Get the template from the slideshow
            template_type = resource.parent.get_property('template_type')
        return 'slideshow-type-%s' % template_type


    def get_namespace(self, resource, context):
        user = context.user
        slides = resource.parent
        slides_long_title = slides.get_property('long_title')
        slides_long_title = slides_long_title or slides.get_title()
        slide_long_title = resource.get_property('long_title')
        slide_long_title = slide_long_title or resource.get_title()

        items = []
        previous_slide = None
        next_slide = None
        previous_index = next_index = 0
        for index, name in enumerate(slides.get_ordered_names()):
            item = slides.get_resource(name)
            # ACL
            ac = item.get_access_control()
            if ac.is_allowed_to_view(user, item) is False:
                continue
            selected = (item.name == resource.name)
            items.append({
                'title': item.get_title(),
                'href': context.get_link(item),
                'selected': selected})
            if selected:
                previous_index = index - 1
                next_index = index + 1
        nb_items = len(items)
        if items:
            # Get the previous and next slide path
            if previous_index >= 0:
                previous_slide = items[previous_index]
            if next_index < nb_items:
                next_slide = items[next_index]
        # TOC width
        toc_nb_col = resource.parent.get_property('toc_nb_col')
        toc_cols = [ None for x in range(toc_nb_col) ]
        c = nb_items / toc_nb_col
        if (nb_items - (toc_nb_col * c)):
            c += 1
        cols = []
        for i in range(toc_nb_col):
            css = ''
            if i == 0:
                css += 'first '
            if i == (toc_nb_col - 1):
                css += 'last '
            cols.append({'items': items[i*c:(i+1)*c], 'css': css})
        toc_ns = {'cols': cols}

        # Show slide's image or slideshow's image if any
        image = resource.get_property('image')
        if image is None:
            image = resource.parent.get_property('image')
            if image is not None:
                image = slides.get_resource(image, soft=True)
        else:
            image = resource.get_resource(image, soft=True)
        if image is not None:
            image = '%s/;download' % context.get_link(image)

        href = None
        if image:
            href = resource.get_property('href')
        namespace = {}
        namespace['slideshow_title'] = slides_long_title
        namespace['slide_title'] = slide_long_title
        namespace['toc'] = toc_ns
        namespace['slide_content'] = resource.get_html_data()
        namespace['slide_href'] = href
        namespace['slide_image'] = image
        namespace['previous_slide'] = previous_slide
        namespace['next_slide'] = next_slide
        namespace['content_only'] = self.content_only

        return namespace



class Slide_Edit(HTMLEditView, TagsAware_Edit):

    widgets = ([title_widget, TextWidget('long_title', title=MSG(u'Long title'),
                                         size=70),
                ImageSelectorWidget('image', title=MSG(u'Image')),
                PathSelectorWidget('href', title=MSG(u'Hyperlink')),
                subject_widget, timestamp_widget, rte_widget,
                SlideTemplateTypeWidget('template_type',
                                        title=MSG('Slide layout'),
                                        has_empty_option=True, is_inline=True)]
               +
               TagsAware_Edit.widgets
              )

    def get_schema(self, resource, context):
        return merge_dicts(HTMLEditView.get_schema(self, resource, context),
                           TagsAware_Edit.get_schema(self, resource, context),
                           long_title=Unicode, href=String,
                           image=String, template_type=SlideTemplateType)


    def get_value(self, resource, context, name, datatype):
        if name in TagsAware_Edit.get_schema(self, resource, context):
            # TODO To improve
            return TagsAware_Edit.get_value(self, resource, context, name,
                                           datatype)
        return HTMLEditView.get_value(self, resource, context, name, datatype)


    def action(self, resource, context, form):
        HTMLEditView.action(self, resource, context, form)
        TagsAware_Edit.action(self, resource, context, form)
        # Check edit conflict
        if context.edit_conflict:
            return

        language = resource.get_content_language(context)
        # Long title to appear only on slide view
        long_title = form['long_title']
        resource.set_property('long_title', long_title, language=language)
        # Image to appear on slide view
        image = form['image']
        if image:
            resource.set_property('image', image)
        href = form['href']
        if href:
            resource.set_property('href', href)
        # Template layout
        resource.set_property('template_type', form['template_type'])
        # Ok
        context.message = MSG_CHANGES_SAVED



class SlideShow_Edit(DBResource_Edit):

    schema = merge_dicts(DBResource_Edit.schema, long_title=Unicode,
                         image=String, toc_nb_col=PositiveIntegerNotNull,
                         template_type=SlideTemplateType)

    widgets = [title_widget, TextWidget('long_title', title=MSG(u'Long title'),
                                        size=70),
               ImageSelectorWidget('image', title=MSG(u'Image')),
               description_widget, subject_widget,
               TextWidget('toc_nb_col', title=MSG(u'TOC width (nb columns)'),
                          size=1),
               SlideTemplateTypeWidget('template_type',
                                       title=MSG('Slide layout'),
                                       has_empty_option=False, is_inline=True),
               timestamp_widget
               ]


    def action(self, resource, context, form):
        DBResource_Edit.action(self, resource, context, form)
        # Check edit conflict
        if context.edit_conflict:
            return

        language = resource.get_content_language(context)
        # Long title to appear only on slide view
        long_title = form['long_title']
        resource.set_property('long_title', long_title, language=language)
        # Image to appear on slide view
        image = form['image']
        if image:
            resource.set_property('image', image)
        # Toc width
        resource.set_property('toc_nb_col', form['toc_nb_col'])
        # Template layout
        resource.set_property('template_type', form['template_type'])
        # Ok
        context.message = MSG_CHANGES_SAVED



class Tag_SlideView(Tag_ItemView):

    def get_content(self, resource, context):
        # FIXME
        view = resource.view.__class__(content_only=True)
        return view.GET(resource, context)



class Slide(WebPage, TagsAware):

    class_id = 'slide'
    class_title = MSG(u'Slide')
    class_views = ['view', 'edit', 'edit_state']


    @classmethod
    def get_metadata_schema(cls):
        schema = merge_dicts(WebPage.get_metadata_schema(),
                             TagsAware.get_metadata_schema())
        schema['state'] = String(default='public')
        schema['long_title'] = Unicode
        # Image of the slide
        schema['image'] = String
        # Slide template type
        schema['template_type'] = SlideTemplateType(default='')
        # Slide title href
        schema['href'] = String
        return schema


    def _get_catalog_values(self):
        return merge_dicts(WebPage._get_catalog_values(self),
                           TagsAware._get_catalog_values(self))


    def get_available_languages(self, languages):
        available_langs = []
        for language in languages:
            handler = self.get_handler(language)
            if handler.is_empty() is False:
                available_langs.append(language)
        return available_langs


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

        site_root = self.get_site_root()
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


    edit = Slide_Edit()
    view = Slide_View()
    tag_view = Tag_SlideView()



class Slides_OrderedTable(ResourcesOrderedTable):

    class_id = 'slides-ordered-table'
    class_title = MSG(u'Slides Ordered Table')

    orderable_classes = (Slide,)



class SlideShow(ResourcesOrderedContainer):

    class_id = 'slides'
    class_title = MSG(u'SlideShow')
    class_icon16 = 'slideshow/icons/16x16/slideshow.png'
    class_icon48 = 'slideshow/icons/48x48/slideshow.png'
    class_views = ['browse_content', 'view', 'edit', 'order']

    __fixed_handlers__ = ['order-slides']

    order_path = 'order-slides'
    order_class = Slides_OrderedTable

    # Views
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    view = GoToFirstOrderedResource()
    edit = SlideShow_Edit()
    order = GoToOrderedTable(title=MSG(u'Order slides'))


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ResourcesOrderedContainer.get_metadata_schema(),
                           long_title=Unicode,
                           # Image of the slideshow
                           image=String,
                           # TOC width
                           toc_nb_col=PositiveIntegerNotNull(default=2),
                           # Slide template type
                           template_type=SlideTemplateType(default='1'))


    def get_document_types(self):
        return [Slide, Image]


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
