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

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import String, Boolean, Integer
from itools.gettext import MSG
from itools.web import get_context, STLView
from itools.xapian import PhraseQuery, AndQuery, NotQuery

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import ImageSelectorWidget
from ikaaro.forms import XHTMLBody, TextWidget
from ikaaro.resource_views import DBResource_AddImage, DBResource_Edit
from ikaaro.utils import get_base_path_query
from ikaaro.views import CompositeForm

# Import from itws
from datatypes import PositiveIntegerNotNull
from utils import get_admin_bar, xml_to_text, XMLTitleWidget
from views import BrowseFormBatchNumeric, BaseRSS
from views import ProxyContainerNewInstance
from webpage_views import WebPage_Edit



class NewsItem_Preview(STLView):

    template = '/ui/news/NewsItem_preview.xml'

    def get_columns(self):
        return ('title', 'long_title', 'path', 'date_of_writing',
                'thumbnail', 'css')


    def get_value(self, resource, context, column, language, current_path):
        if column == 'title':
            return resource.get_title()
        elif column == 'long_title':
            return resource.get_long_title(language=language)
        elif column == 'path':
            return context.get_link(resource)
        elif column == 'date_of_writing':
            return resource.get_date_of_writing_formatted()
        elif column == 'thumbnail':
            path = resource.get_property('thumbnail')
            if path:
                image = resource.get_resource(path, soft=True)
                if image:
                    return context.get_link(image)
            return None
        elif column == 'css':
            if resource.get_abspath() == current_path:
                return 'active'
            return None


    def get_namespace(self, resource, context):
        language = resource.get_content_language(context)
        namespace = {}

        here_abspath = context.resource.get_abspath()
        for col in self.get_columns():
            namespace[col] = self.get_value(resource, context, col, language,
                                            here_abspath)

        return namespace



class NewsItem_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    icon = 'view.png'
    template = '/ui/news/News_view.xml'
    styles = ['/ui/news/style.css']

    # customization
    id = 'news'
    title_link = None

    def get_manage_buttons(self, resource, context):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        buttons = []
        buttons.append({'path': './;edit',
                        'label': MSG(u'Edit news')})
        return buttons


    def get_namespace(self, resource, context):
        news_folder = resource.parent
        language = resource.get_content_language(context)
        dow = resource.get_date_of_writing_formatted()
        # title
        title = resource.get_long_title(language=language)
        # content
        content = resource.get_html_data()
        # Allowed to edit and highlight
        ac = resource.get_access_control()
        if ac.is_allowed_to_edit(context.user, resource):
            edit = True
        else:
            edit = False

        namespace = {'id': self.id, 'date_of_writing': dow}
        namespace['title'] = title #XMLParser(XHTMLBody.encode(title) or '')
        namespace['content'] = content
        namespace['is_allowed_to_edit'] = edit
        # FIXME Does not work
        #buttons = self.get_manage_buttons(resource, context)
        #namespace['admin_bar'] = get_admin_bar(buttons, 'content-column',
        #                            MSG(u'A news'))
        title_link = None
        if self.title_link:
            title_link = context.get_link(resource)
        namespace['title_link'] = title_link

        return namespace



class NewsItem_AddImage(DBResource_AddImage):

    def get_start(self, resource):
        return resource.get_resource('../images')



class NewsItem_Edit(WebPage_Edit):

    def get_schema(self, resource, context):
        return merge_dicts(WebPage_Edit.get_schema(self, resource, context),
                           long_title=XHTMLBody, thumbnail=String)


    def get_widgets(self, resource, context):
        widgets = WebPage_Edit.get_widgets(self, resource, context)[:]
        for index, widget in enumerate(widgets):
            if widget.name == 'display_title':
                widgets.pop(index)

        long_title_widget = XMLTitleWidget('long_title',
                                           title=MSG(u'Long title'))
        widgets.insert(2, long_title_widget)
        widgets.append(ImageSelectorWidget('thumbnail',
                                           title=MSG(u'Thumbnail')))

        return widgets


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        if name == 'long_title':
            long_title = resource.get_property('long_title', language)
            return long_title
        return WebPage_Edit.get_value(self, resource, context, name, datatype)


    def action(self, resource, context, form):
        WebPage_Edit.action(self, resource, context, form)
        # Check edit conflict
        if context.edit_conflict:
            return

        language = resource.get_content_language(context)
        # long title
        long_title = form['long_title']
        resource.set_property('long_title', long_title, language=language)
        # thumbnail
        thumbnail = form['thumbnail']
        resource.set_property('thumbnail', thumbnail, language=language)



class NewsFolder_Edit(DBResource_Edit):

    schema = merge_dicts(DBResource_Edit.schema,
                         batch_size=PositiveIntegerNotNull)

    def get_widgets(self, resource, context):
        widgets = DBResource_Edit.get_widgets(self, resource, context)[:]
        batch_size_widget = TextWidget('batch_size', title=MSG(u'Batch size'),
                                       size=3)
        widgets.insert(2, batch_size_widget)
        return widgets


    def action(self, resource, context, form):
        DBResource_Edit.action(self, resource, context, form)
        # Check edit conflict
        if context.edit_conflict:
            return

        resource.set_property('batch_size', form['batch_size'])



class NewsFolder_View(BrowseFormBatchNumeric, STLView):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    template = '/ui/news/NewsFolder_view.xml'
    context_menus = []
    styles = ['/ui/news/style.css']
    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               batch_size=Integer(default=5),
                               sort_by=String(default='date_of_writing'),
                               reverse=Boolean(default=True))
    table_template = None
    more_title = MSG(u'Read more')
    max_middle_pages = 5

    def get_query_schema(self):
        here = get_context().resource
        # FIXME May failed
        batch_size = here.get_property('batch_size')
        return merge_dicts(BrowseFormBatchNumeric.get_query_schema(self),
                           batch_size=Integer(default=batch_size))


    def get_manage_buttons(self, resource, context, name=None):
        ac = resource.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, resource)
        if not allowed:
            return []

        buttons = []
        path = context.get_link(resource)

        # Add news
        class_id = resource.news_class.class_id
        path = '%s/;new_resource?type=%s' % (path, class_id)
        buttons.append({'path':  path, 'target': None,
                        'icon': '/ui/common/icons/48x48/new.png',
                        'label': MSG(u'Add a news')})

        return buttons


    def get_items(self, resource, context, *args):
        # Build the query
        language = resource.get_content_language(context)
        args = list(args)
        query_terms = resource.get_news_query_terms(state='public')
        query_terms.append(PhraseQuery('available_languages', [language]))
        args.append(AndQuery(*query_terms))
        if len(args) == 1:
            query = args[0]
        else:
            query = AndQuery(*args)

        # Ok
        return context.root.search(query)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'date_of_writing':
            return item_resource.get_date_of_writing_formatted()
        elif column == 'title':
            # Return title or to_text(long_title)
            title = item_resource.get_property('title')
            if title:
                return title
            # long title as text
            long_title = item_resource.get_property('long_title')
            if long_title:
                return xml_to_text(long_title)
            # Fallback
            return item_resource.get_title()
        elif column == 'link':
            return context.get_link(item_resource)
        elif column == 'preview':
            return brain.preview_content
        elif column == 'tag':
            tags = brain.tags
            if tags:
                return tags[0]
            return None


    def get_rows_namespace(self, resource, context, items):
        rows = []
        for item in items:
            d = {}
            for key in ('date_of_writing', 'title', 'link', 'preview', 'tag'):
                d[key] = self.get_item_value(resource, context, item, key)
            rows.append(d)
        return rows


    def get_namespace(self, resource, context):
        from bar import SideBar_View

        namespace = Folder_BrowseContent.get_namespace(self, resource, context)
        # Get items
        items = self.get_items(resource, context)
        items = self.sort_and_batch(resource, context, items)
        site_root = resource.get_site_root()
        tags = site_root.get_resource('tags')
        rows = self.get_rows_namespace(resource, context, items)

        # Post process tag values
        tags_map = {}
        for tag_brain in tags.get_tag_brains(context):
            tags_map[tag_brain.name] = tag_brain.m_title
        for row in rows:
            row_tag = row['tag']
            if row_tag:
                row['tag'] = {'name': row_tag, 'title': tags_map[row_tag]}

        namespace['title'] = resource.get_property('title')
        namespace['tags_path'] = context.get_link(tags)
        namespace['news_format'] = resource.news_class.class_id
        namespace['rows'] = rows
        namespace['more_title'] = self.more_title
        manage_buttons = self.get_manage_buttons(resource, context)
        namespace['admin_bar'] = get_admin_bar(manage_buttons,
                                               'foldernews-items', icon=True)
        view = SideBar_View()
        namespace['sidebar_view'] = view.GET(resource, context)

        return namespace



class NewsFolder_RSS(BaseRSS):

    def get_base_query(self, resource, context):
        # Filter by news folder
        abspath = resource.get_canonical_path()
        return [ get_base_path_query(str(abspath)),
                 PhraseQuery('workflow_state', 'public') ]


    def get_allowed_formats(self, resource, context):
        return [resource.news_class.class_id]


    def _sort_and_batch(self, resource, context, results):
        items = results.get_documents(sort_by='date_of_writing', reverse=True)
        return items


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column == 'pubDate':
            return brain.date_of_writing

        return BaseRSS.get_item_value(self, resource, context, item,
                                      column, site_root)



############################################################
# Manage view
############################################################

class NewsFolder_BrowseContent(Folder_BrowseContent):

    access = 'is_allowed_to_edit'

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               sort_by=String(default='date_of_writing'),
                               reverse=Boolean(default=True))

    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('date_of_writing', MSG(u'Date of writing')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('format', MSG(u'Type')),
        ('workflow_state', MSG(u'State'))]

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        # Only remove 'order-sidebar'
        query = [ PhraseQuery('parent_path', path),
                  NotQuery(PhraseQuery('name', 'order-sidebar')) ]
        return context.root.search(AndQuery(*query))


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'date_of_writing':
            return brain.date_of_writing
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)



class NewsFolder_NewsNewInstance(ProxyContainerNewInstance):

    actions = [Button(access='is_allowed_to_edit',
                      name='new_news', title=MSG(u'Add'))]

    def _get_resource_cls(self, context):
        here = context.resource
        return here.news_class


    def _get_container(self, resource, context):
        return resource


    def _get_goto(self, resource, context, form):
        name = form['name']
        # Assume that the resource already exists
        container = self._get_container(resource, context)
        child = container.get_resource(name)
        return '%s/;edit' % context.get_link(child)


    def action_new_news(self, resource, context, form):
        return ProxyContainerNewInstance.action(self, resource, context, form)



class NewsFolder_ManageView(CompositeForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage view')

    subviews = [ NewsFolder_NewsNewInstance(),
                 NewsFolder_BrowseContent() ]


    def _get_form(self, resource, context):
        for view in self.subviews:
            method = getattr(view, context.form_action, None)
            if method is not None:
                form_method = getattr(view, '_get_form')
                return form_method(resource, context)
        return None

