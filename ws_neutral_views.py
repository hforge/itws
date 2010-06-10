# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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
from math import floor
from types import GeneratorType

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean, Unicode, String
from itools.gettext import MSG
from itools.stl import stl, set_prefix
from itools.uri import get_reference, Reference
from itools.web import get_context, BaseView, FormError, STLView
from itools.xapian import PhraseQuery, NotQuery, OrQuery, AndQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import Button
from ikaaro.forms import ImageSelectorWidget, XHTMLBody
from ikaaro.forms import stl_namespaces, TextWidget, SelectRadio
from ikaaro.views import CompositeForm
from ikaaro.website import NotFoundView as BaseNotFoundView

# Import from itws
from bar import ContentBar_View, SideBar_View
from datatypes import NeutralClassSkin
from section import Section
from tags import TagsAware
from utils import set_navigation_mode_as_edition
from utils import set_navigation_mode_as_navigation
from views import BaseManageLink, BaseManageContent
from views import BaseRSS, ProxyContainerNewInstance
from views import SmartOrderedTable_View, SmartOrderedTable_Ordered
from views import SmartOrderedTable_Unordered
from website import WebSite_Edit



class NeutralClassSkinWidget(SelectRadio):

    template = list(XMLParser("""
        <table border="0">
          <tr>
            <td style="text-align:center">
              <input type="radio" id="${name}-${option_0/name}" name="${name}"
              value="${option_0/name}" checked="checked"
              stl:if="option_0/selected"/>
              <input type="radio" id="${name}-${option_0/name}" name="${name}"
                value="${option_0/name}" stl:if="not option_0/selected"/>
              <label for="${name}-${option_0/name}">${option_0/value}</label>
            </td>
            <td style="text-align:center">
              <input type="radio" id="${name}-${option_1/name}" name="${name}"
              value="${option_1/name}" checked="checked"
              stl:if="option_1/selected"/>
              <input type="radio" id="${name}-${option_1/name}" name="${name}"
                value="${option_1/name}" stl:if="not option_1/selected"/>
              <label for="${name}-${option_1/name}">${option_1/value}</label>
            </td>
            <td style="text-align:center">
              <input type="radio" id="${name}-${option_2/name}" name="${name}"
              value="${option_2/name}" checked="checked"
              stl:if="option_2/selected"/>
              <input type="radio" id="${name}-${option_2/name}" name="${name}"
                value="${option_2/name}" stl:if="not option_2/selected"/>
              <label for="${name}-${option_2/name}">${option_2/value}</label>
            </td>
          </tr>
          <tr>
            <td style="text-align:center"><img src="${option_0/name}/preview.png" /></td>
            <td style="text-align:center"><img src="${option_1/name}/preview.png" /></td>
            <td style="text-align:center"><img src="${option_2/name}/preview.png" /></td>
          </tr>
        </table>
        """, stl_namespaces))


    def get_namespace(self, datatype, value):
        namespace = SelectRadio.get_namespace(self, datatype, value)
        namespace['option_0'] = namespace['options'][0]
        namespace['option_1'] = namespace['options'][1]
        namespace['option_2'] = namespace['options'][2]
        return namespace



############################################################
# Views
############################################################
class NotFoundPage(BaseNotFoundView):

    not_found_template = '404'

    def get_template(self, resource, context):
        site_root = resource.get_site_root()
        template = site_root.get_resource(self.not_found_template, soft=True)
        if template and not template.handler.is_empty():
            # When 404 occurs context.resource is the last valid resource
            # in the context.path. We need to compute prefix from context.path
            # instead of context.resource
            path = site_root.get_abspath().resolve2('.%s' % context.path)
            prefix = path.get_pathto(template.get_abspath())
            return set_prefix(template.handler.events, '%s/' % prefix)
        # default
        return BaseNotFoundView.get_template(self, resource, context)


    def GET(self, resource, context):
        # Get the namespace
        namespace = self.get_namespace(resource, context)
        if isinstance(namespace, Reference):
            return namespace

        # STL
        template = self.get_template(resource, context)
        if isinstance(template, (GeneratorType, XMLParser)):
            return stl(events=template, namespace=namespace)
        return stl(template, namespace)



class NeutralWS_Edit(WebSite_Edit):

    scripts = ['/ui/common/js/strftime-min-1.3.js']

    def get_schema(self, resource, context):
        return merge_dicts(WebSite_Edit.get_schema(self, resource, context),
                           breadcrumb_title=Unicode,
                           banner_title=Unicode,
                           banner_path=String,
                           date_of_writing_format=String,
                           class_skin=NeutralClassSkin(mandatory=True))


    def get_widgets(self, resource, context):
        widgets = WebSite_Edit.get_widgets(self, resource, context)[:]
        language = resource.get_content_language(context)
        # Breadcrumb title
        widgets.append(
            TextWidget('breadcrumb_title', title=MSG(u'Breadcrumb title')))
        # banner_title
        widgets.append(
            TextWidget('banner_title', title=MSG(u'Banner title'),
                       tip=MSG(u'(Use as banner if there is no image banner)')))
        # banner_path
        widgets.append(
            ImageSelectorWidget('banner_path', title=MSG(u'Banner path'),
                                width=640))
        # Format date

        suffix_js = XHTMLBody(sanitize_html=False).decode("""
Preview
<span id="date-of-writing-format-preview"></span>
<script type="text/javascript">
    var dowfp_today = new Date();
    dowfp_today.locale = "%s";
    function update_date_of_writing_format_preview(source, target) {
        var format = $("#"+source).val();
        var preview = dowfp_today.strftime(format);
        $("#"+target).text(preview);
    }
    $("#date-of-writing-format").keyup(function () {
        update_date_of_writing_format_preview("date-of-writing-format",
                                              "date-of-writing-format-preview");
    });
    $(document).ready(function() {
        update_date_of_writing_format_preview("date-of-writing-format",
                                              "date-of-writing-format-preview");
    });
</script>""" % language)
        widgets.append(
            TextWidget('date_of_writing_format', size=16,
                   title=MSG(u'Date of writing format (e.g. %Y/%m/%d)'),
                   suffix=suffix_js))
        # class_skin
        widgets.append(
            NeutralClassSkinWidget('class_skin', title=MSG(u'Skin'),
                                   has_empty_option=False))

        # ok
        return widgets


    def get_value(self, resource, context, name, datatype):
        if name == 'date_of_writing_format':
            language = resource.get_content_language(context)
            data = resource.get_property(name, language=language)
            return data
        return WebSite_Edit.get_value(self, resource, context, name, datatype)


    def _get_form(self, resource, context):
        form = WebSite_Edit._get_form(self, resource, context)

        # Check banner
        banner_path = form['banner_path']
        if banner_path and not resource.get_resource(banner_path, soft=True):
            raise FormError(invalid=['banner_path'])
        return form


    def action(self, resource, context, form):
        WebSite_Edit.action(self, resource, context, form)
        # Check edit conflict
        if context.edit_conflict:
            return

        # Other (Multilingual)
        language = resource.get_content_language(context)
        for key in ['breadcrumb_title', 'banner_title',  'banner_path',
                    'date_of_writing_format']:
            resource.set_property(key, form[key], language=language)
        # Skin
        class_skin = form['class_skin']
        resource.set_property('class_skin', class_skin)
        # Ok
        context.message = messages.MSG_CHANGES_SAVED



class NeutralWS_RSS(BaseRSS):

    excluded_formats = freeze(['rssfeeds', 'text/css'])


    def get_base_query(self, resource, context):
        query = BaseRSS.get_base_query(self, resource, context)
        query.append(PhraseQuery('workflow_state', 'public'))
        query.append(PhraseQuery('is_image', False))
        return query


    def get_excluded_paths(self, resource, context):
        site_root = resource.get_site_root()
        site_root_abspath = site_root.get_abspath()
        excluded = []
        for name in ('./404',):
            excluded.append(site_root_abspath.resolve2(name))
        return excluded


    def get_excluded_container_paths(self, resource, context):
        site_root = resource.get_site_root()
        site_root_abspath = site_root.get_abspath()
        excluded = []
        for name in ('./menu/', './repository/', './ws-data/',
                     './footer/', './turning-footer/', './tags/'):
            excluded.append(site_root_abspath.resolve2(name))
        return excluded


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column == 'pubDate':
            if isinstance(item_resource, TagsAware):
                return brain.date_of_writing
            else:
                return resource.get_mtime()
        elif column == 'title':
            # Special case for the title
            title = item_resource.get_title()
            # FIXME
            if brain.name == 'index':
                parent = item_resource.parent
                if isinstance(parent, Section):
                    title = parent.get_title()
            return title

        return BaseRSS.get_item_value(self, resource, context, item,
                                      column, site_root)



class NeutralWSContentBar_View(ContentBar_View):

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []
        buttons = ContentBar_View.get_manage_buttons(self, resource, context)

        # webpage creation helper
        path = context.get_link(resource)
        article_cls = resource.get_article_class()
        msg = MSG(u'Create a new %s' % article_cls.class_title.gettext())
        buttons.append({'path': '%s/;add_new_article' % path,
                        'icon': '/ui/icons/48x48/html.png',
                        'label': msg,
                        'target': '_blank'})

        return buttons



class NeutralWS_ArticleNewInstance(ProxyContainerNewInstance):

    def _get_view_title(self):
        cls = self._get_resource_cls(get_context())
        return MSG(u'Add new {cls}').gettext(cls.class_title.gettext())


    def _get_resource_cls(self, context):
        here = context.resource
        return here.get_article_class()


    def _get_container(self, resource, context):
        return resource.get_resource('ws-data')


    title = property(_get_view_title)



class NeutralWS_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'Website View')
    template = '/ui/common/Neutral_view.xml'

    subviews = {'contentbar_view':
            NeutralWSContentBar_View(order_name='ws-data/order-contentbar'),
                'sidebar_view':
            SideBar_View(order_name='ws-data/order-sidebar')}

    def get_subviews_value(self, resource, context, view_name):
        view = self.subviews.get(view_name)
        if view is None:
            return None
        return view.GET(resource, context)


    def get_namespace(self, resource, context):
        namespace = {}

        # Subviews
        for view_name in self.subviews.keys():
            namespace[view_name] = self.get_subviews_value(resource,
                                                           context, view_name)

        return namespace



class NeutralWS_FOSwitchMode(BaseView):

    access = 'is_allowed_to_edit'
    query_schema = {'mode': Boolean(default=False)}

    def GET(self, resource, context):
        edit = context.query['mode']
        if edit:
            set_navigation_mode_as_edition(context)
        else:
            set_navigation_mode_as_navigation(context)

        referer = context.get_referrer()
        if referer:
            goto = referer
        else:
            goto = '/'

        return get_reference(goto)



class NeutralWS_ManageLink(BaseManageLink):

    title = MSG(u'Manage your website')

    def get_items(self, resource, context):
        items = []

        items.append({'path': './;edit',
                      'class': 'edit',
                      'title': MSG(u'Edit banner, favicon, skin...')})

        items.append({'path': './;new_resource',
                      'class': 'add',
                      'title': MSG(u'Add Resource: Section, Wiki, Tracker, '
                                   u'RSS agregator...')})

        items.append({'path': './tags',
                      'class': 'tags',
                      'title': MSG(u'Manage tags')})

        items.append({'path': './menu',
                      'class': 'menu',
                      'title': MSG(u'Manage menu')})

        items.append({'path': './footer',
                      'class': 'footer',
                      'title': MSG(u'Edit footer')})

        items.append({'path': './turning-footer/menu',
                      'class': 'turning-footer',
                      'title': MSG(u'Edit turning footer')})

        items.append({'path': './repository',
                      'class': 'repository',
                      'title': MSG(u'Manage repository')})

        items.append({'path': './;order_contentbar',
                      'class': 'order child',
                      'title': MSG(u'Edit the central part')})

        items.append({'path': './;order_sidebar',
                      'class': 'order child',
                      'title': MSG(u'Edit the sidebar')})

        items.append({'path': './style/;edit',
                      'class': 'css',
                      'title': MSG(u'Edit CSS')})

        items.append({'path': './404/;edit',
                      'class': 'manage-404',
                      'title': MSG(u'Edit 404')})

        items.append({'path': './robots.txt/;edit',
                      'class': 'robotstxt',
                      'title': MSG(u'Edit robots.txt')})

        items.append({'path': './;control_panel',
                      'class': 'controlpanel',
                      'title': MSG(u'Control Panel: Manage users, Email '
                                   u'options, Vhosts, SEO ...')})

        middle = int(floor(len(items) / 2.0))
        left_items = items[:middle]
        right_items = items[middle:]

        return [{'items': left_items, 'class': 'left'},
                {'items': right_items, 'class': 'right'}]



class NeutralWS_ManageContent(BaseManageContent):

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        editorial_cls = resource.get_editorial_documents_types()
        editorial_query = [ PhraseQuery('format', cls.class_id)
                            for cls in editorial_cls ]
        # allow images
        editorial_query.append(PhraseQuery('is_image', True))
        # allow "images" folder
        editorial_query.append(PhraseQuery('name', 'images'))
        query = [
            PhraseQuery('parent_path', path),
            NotQuery(PhraseQuery('name', '404')),
            OrQuery(*editorial_query)
                ]
        return context.root.search(AndQuery(*query))



class NeutralWS_ManageView(CompositeForm):

    title = MSG(u'Manage Website')
    access = 'is_allowed_to_edit'

    subviews = [NeutralWS_ManageLink(),
                NeutralWS_ManageContent()]



class WSDataFolder_ManageLink(BaseManageLink):

    title = MSG(u'Manage Homepage Content')

    def get_items(self, resource, context):
        left_items = []
        right_items = []

        site_root = resource.parent
        order_table = site_root.get_resource(site_root.order_path)
        ordered_classes = order_table.get_orderable_classes()

        left_items.append({'path': './;new_resource',
                           'class': 'add',
                           'title': MSG(u'Add Resource: Webpage, PDF, ODT...')})

        # Order resources
        # Do not show the link if there is nothing to order
        available_resources = []
        for cls in ordered_classes:
            l = [ x for x in resource.search_resources(cls=cls) ]
            available_resources.extend(l)

        left_items.append({'path': './order-resources',
                           'class': 'order child',
                           'title': MSG(u'Order webpages in the homepage '
                                        u'view'),
                           'disable': len(available_resources) == 0})

        left_items.append({'path': '/repository/;new_contentbar_resource',
                           'class': 'add',
                           'title': MSG(u'Create new central part box')})

        left_items.append({'path': './;order_contentbar',
                           'class': 'order child',
                           'title': MSG(u'Order central part boxes')})

        right_items.append({'path': '/repository/;new_sidebar_resource',
                            'class': 'add',
                            'title': MSG(u'Create new sidebar box')})

        right_items.append({'path': './;order_sidebar',
                            'class': 'order child',
                            'title': MSG(u'Order sidebar boxes')})

        return [{'items': left_items, 'class': 'left'},
                {'items': right_items, 'class': 'right'}]



class WSDataFolder_ManageContent(BaseManageContent):

    title = MSG(u'Manage Homepage')

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        editorial_cls = resource.get_editorial_documents_types()
        editorial_query = [ PhraseQuery('format', cls.class_id)
                            for cls in editorial_cls ]
        # allow images
        editorial_query.append(PhraseQuery('is_image', True))
        query = [
            PhraseQuery('parent_path', path),
            NotQuery(PhraseQuery('name', 'order-sidebar')),
            NotQuery(PhraseQuery('name', 'order-contentbar')),
            NotQuery(PhraseQuery('name', 'order-resources')),
            OrQuery(*editorial_query)
                ]
        return context.root.search(AndQuery(*query))



class WSDataFolder_ManageView(CompositeForm):

    title = MSG(u'Manage Homepage Content')
    access = 'is_allowed_to_edit'

    subviews = [WSDataFolder_ManageLink(),
                WSDataFolder_ManageContent()]



class WSDataFolder_ArticleNewInstance(ProxyContainerNewInstance):

    actions = [Button(access='is_allowed_to_edit',
                      name='new_article', title=MSG(u'Add'))]

    # SmartOrderedTable_View API
    title = title_description = None

    def _get_resource_cls(self, context):
        here = context.resource
        # FIXME Get the first orderable classes
        # orderable classes SHOULD always contains ONE class
        return here.get_orderable_classes()[0]


    def _get_container(self, resource, context):
        # Parent ws-data folder
        return resource.parent


    def _get_goto(self, resource, context, form):
        name = form['name']
        # Assume that the resource already exists
        container = self._get_container(resource, context)
        child = container.get_resource(name)
        return '%s/;edit' % context.get_link(child)


    def action_new_article(self, resource, context, form):
        return ProxyContainerNewInstance.action(self, resource, context, form)



class WSDataFolder_OrderedTable_View(SmartOrderedTable_View):

    subviews = [ WSDataFolder_ArticleNewInstance(),
                 SmartOrderedTable_Ordered(),
                 SmartOrderedTable_Unordered() ]

    def _get_form(self, resource, context):
        for view in self.subviews:
            method = getattr(view, context.form_action, None)
            if method is not None:
                form_method = getattr(view, '_get_form')
                return form_method(resource, context)
        return None

