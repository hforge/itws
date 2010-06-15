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

# Import from itools
from itools.core import  merge_dicts
from itools.datatypes import String, Unicode, Enumerate
from itools.gettext import MSG
from itools.web import STLView
from itools.xapian import split_unicode, PhraseQuery, AndQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import ImageSelectorWidget, PathSelectorWidget, TextWidget
from ikaaro.forms import SelectRadio, rte_widget, timestamp_widget
from ikaaro.forms import stl_namespaces
from ikaaro.forms import title_widget, description_widget, subject_widget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import DBResource_Edit
from ikaaro.views import CompositeForm
from ikaaro.webpage import HTMLEditView

# Import from itws
from datatypes import PositiveIntegerNotNull
from tags import TagsAware_Edit, Tag_ItemView
from views import ProxyContainerNewInstance



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



class Slide_Edit(HTMLEditView, TagsAware_Edit):

    def get_schema(self, resource, context):
        return merge_dicts(HTMLEditView.get_schema(self, resource, context),
                           TagsAware_Edit.get_schema(self, resource, context),
                           long_title=Unicode, href=String,
                           image=String, template_type=SlideTemplateType)


    def get_widgets(self, resource, context):
        return ([title_widget,
                 TextWidget('long_title', title=MSG(u'Long title'), size=70),
                 ImageSelectorWidget('image', title=MSG(u'Image')),
                 PathSelectorWidget('href', title=MSG(u'Hyperlink')),
                 subject_widget, timestamp_widget, rte_widget,
                 SlideTemplateTypeWidget('template_type',
                                         title=MSG('Slide layout'),
                                         has_empty_option=True,
                                         is_inline=True)]
                + TagsAware_Edit.get_widgets(self, resource, context))


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



class Slide_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    styles = ['/ui/slideshow/style.css']
    base_template = '/ui/slideshow/Slide_view_type_%s.xml'
    only_content = False


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

        # css
        template_type = resource.get_property('template_type')
        if not template_type:
            # Get the template from the slideshow
            template_type = resource.parent.get_property('template_type')
        css = 'slideshow-type-%s' % template_type

        namespace = {}
        namespace['slideshow_title'] = slides_long_title
        namespace['slide_title'] = slide_long_title
        namespace['toc'] = toc_ns
        namespace['slide_content'] = resource.get_html_data()
        namespace['slide_href'] = href
        namespace['slide_image'] = image
        namespace['previous_slide'] = previous_slide
        namespace['next_slide'] = next_slide
        namespace['only_content'] = self.only_content
        namespace['css'] = css

        return namespace



class Tag_SlideView(Tag_ItemView):

    def get_content(self, resource, context):
        view = resource.view_only_content
        return view.GET(resource, context)



############################################################
# Manage view
############################################################

class SlideShow_BrowseContent(Folder_BrowseContent):

    # Table
    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('workflow_state', MSG(u'State'))]

    def get_items(self, resource, context, *args):
        # Get the parameters from the query
        query = context.query
        search_term = query['search_term'].strip()
        field = query['search_field']

        abspath = resource.get_abspath()
        slide_cls = resource.slide_class
        query = [PhraseQuery('parent_path', str(abspath)),
                 PhraseQuery('format', slide_cls.class_id)]
        if search_term:
            language = resource.get_content_language(context)
            terms_query = [ PhraseQuery(field, term)
                            for term in split_unicode(search_term, language) ]
            query.append(AndQuery(*terms_query))
        query = AndQuery(*query)

        return context.root.search(query)



class SlideShow_SlideNewInstance(ProxyContainerNewInstance):

    actions = [Button(access='is_allowed_to_edit',
                      name='new_slide', title=MSG(u'Add'))]

    def _get_resource_cls(self, context):
        here = context.resource
        return here.slide_class


    def _get_container(self, resource, context):
        return resource


    def _get_goto(self, resource, context, form):
        name = form['name']
        # Assume that the resource already exists
        container = self._get_container(resource, context)
        child = container.get_resource(name)
        return '%s/;edit' % context.get_link(child)


    def action_new_slide(self, resource, context, form):
        return ProxyContainerNewInstance.action_default(self, resource,
                context, form)



class SlideShow_ManageView(CompositeForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage view')

    subviews = [ SlideShow_SlideNewInstance(),
                 SlideShow_BrowseContent() ]


    def _get_form(self, resource, context):
        for view in self.subviews:
            method = getattr(view, context.form_action, None)
            if method is not None:
                form_method = getattr(view, '_get_form')
                return form_method(resource, context)
        return None

