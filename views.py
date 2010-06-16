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
from itools.core import freeze, merge_dicts
from itools.datatypes import String, Unicode, Boolean, DateTime
from itools.gettext import MSG
from itools.handlers import checkid
from itools.html import stream_to_str_as_xhtml
from itools.rss import RSSFile
from itools.uri import get_reference, Path
from itools.web import get_context, BaseView, STLView, FormError
from itools.xapian import AndQuery, RangeQuery, NotQuery, PhraseQuery, OrQuery

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import Button
from ikaaro.buttons import RemoveButton, RenameButton, PublishButton
from ikaaro.buttons import RetireButton, CopyButton, CutButton, PasteButton
from ikaaro.folder_views import Folder_BrowseContent, Folder_Rename
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import AutoForm, TextWidget, HTMLBody, SelectRadio
from ikaaro.forms import title_widget, timestamp_widget, rte_widget
from ikaaro.future.menu import Menu_View
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.future.order import ResourcesOrderedTable_Unordered
from ikaaro.future.order import ResourcesOrderedTable_View
from ikaaro.registry import get_resource_class, get_document_types
from ikaaro.utils import get_base_path_query
from ikaaro.views_new import NewInstance
from ikaaro.webpage import WebPage, HTMLEditView

# Import from itws
from utils import set_prefix_with_hostname, OrderBoxEnumerate



############################################################
# NewInstance
############################################################

class EasyNewInstance(NewInstance):
    """ ikaaro.views_new.NewInstance without field name.
    """
    template = '/ui/common/improve_auto_form.xml'
    actions = [Button(access='is_allowed_to_edit',
                      name='default', title=MSG(u'Add'))]

    query_schema = freeze({'type': String, 'title': Unicode})
    widgets = freeze([
        TextWidget('title', title=MSG(u'Title', mandatory=True))])

    goto_method = None

    def get_new_resource_name(self, form):
        # As we have no name, always return the title
        title = form['title'].strip()
        return title


    def get_actions(self, resource, context):
        return self.actions


    def _get_action_namespace(self, resource, context):
        # (1) Actions (submit buttons)
        actions = []
        for button in self.get_actions(resource, context):
            #if button.show(resource, context, []) is False:
            #    continue
            if button.confirm:
                confirm = button.confirm.gettext().encode('utf_8')
                onclick = 'return confirm("%s");' % confirm
            else:
                onclick = None
            actions.append(
                {'value': button.name,
                 'title': button.title,
                 'class': button.css,
                 'onclick': onclick})

        return actions


    def get_namespace(self, resource, context):
        namespace = NewInstance.get_namespace(self, resource, context)
        # actions namespace
        namespace['actions'] = self._get_action_namespace(resource, context)

        return namespace


    def _get_goto_method(self, resource, context, form):
        return self.goto_method


    def _get_goto(self, resource, context, form):
        name = form['name']
        goto_method = self._get_goto_method(resource, context, form)
        if goto_method:
            return './%s/;%s' % (name, goto_method)
        return './%s/' % name


    def action_default(self, resource, context, form):
        name = form['name']
        title = form['title']

        # Create the resource
        class_id = context.query['type']
        cls = get_resource_class(class_id)
        child = cls.make_resource(cls, resource, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = self._get_goto(resource, context, form)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class ProxyContainerNewInstance(EasyNewInstance):

    query_schema = freeze({'title': Unicode})

    def _get_resource_cls(self, context):
        raise NotImplementedError


    def _get_container(self, resource, context):
        raise NotImplementedError


    def _get_goto(self, resource, context, form):
        name = form['name']
        container = self._get_container(resource, context)
        goto_method = self._get_goto_method(resource, context, form)
        container_path = context.get_link(container)
        if goto_method:
            return '%s/%s/;%s' % (container_path, name, goto_method)
        return '%s/%s/' % (container_path, name)


    def _get_form(self, resource, context):
        form = AutoForm._get_form(self, resource, context)
        name = self.get_new_resource_name(form)

        # Check the name
        if not name:
            raise FormError, messages.MSG_NAME_MISSING

        try:
            name = checkid(name)
        except UnicodeEncodeError:
            name = None

        if name is None:
            raise FormError, messages.MSG_BAD_NAME

        # Check the name is free
        container = self._get_container(resource, context)
        if container.get_resource(name, soft=True) is not None:
            raise FormError, messages.MSG_NAME_CLASH

        # Ok
        form['name'] = name
        return form


    def get_title(self, context):
        cls = self._get_resource_cls(context)
        class_title = cls.class_title.gettext()
        title = MSG(u'Add {class_title}')
        return title.gettext(class_title=class_title)


    def icon(self, resource, **kw):
        cls = self._get_resource_cls(get_context())
        return cls.get_class_icon()


    def action_default(self, resource, context, form):
        name = form['name']
        title = form['title']

        # Create the resource
        cls = self._get_resource_cls(context)
        container = self._get_container(resource, context)
        child = cls.make_resource(cls, container, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = self._get_goto(resource, context, form)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class ProxyContainerProxyEasyNewInstance(EasyNewInstance):

    template = '/ui/common/proxy_improve_auto_form.xml'
    query_schema = freeze({'title': Unicode})
    schema = {
        'name': String,
        'title': Unicode,
        'class_id': String}

    def _get_resource_class_id(self, context):
        # Use in action method
        raise NotImplementedError


    def _get_resource_cls(self, context):
        raise NotImplementedError


    def _get_container(self, resource, context):
        raise NotImplementedError


    def _get_goto(self, resource, context, form):
        name = form['name']
        container = self._get_container(resource, context)
        goto_method = self._get_goto_method(resource, context, form)
        container_path = context.get_link(container)
        if goto_method:
            return '%s/%s/;%s' % (container_path, name, goto_method)
        return '%s/%s/' % (container_path, name)


    def _get_form(self, resource, context):
        form = AutoForm._get_form(self, resource, context)
        name = self.get_new_resource_name(form)

        # Check the name
        if not name:
            raise FormError, messages.MSG_NAME_MISSING

        try:
            name = checkid(name)
        except UnicodeEncodeError:
            name = None

        if name is None:
            raise FormError, messages.MSG_BAD_NAME

        # Check the name is free
        container = self._get_container(resource, context)
        if container.get_resource(name, soft=True) is not None:
            raise FormError, messages.MSG_NAME_CLASH

        # Ok
        form['name'] = name
        return form


    def get_namespace(self, resource, context):
        namespace = NewInstance.get_namespace(self, resource, context)
        # actions namespace
        namespace['actions'] = self._get_action_namespace(resource, context)
        # proxy items
        type = self._get_resource_class_id(context)
        cls = get_resource_class(type)

        document_types = get_document_types(type)
        items = []
        if document_types:
            # Multiple types
            if len(document_types) == 1:
                items = None
            else:
                selected = context.get_form_value('class_id')
                items = [
                    {'title': x.class_title.gettext(),
                     'class_id': x.class_id,
                     'selected': x.class_id == selected,
                     'icon': '/ui/' + x.class_icon16}
                    for x in document_types ]
                if selected is None:
                    items[0]['selected'] = True
        namespace['items'] = items
        # class title
        namespace['class_title'] = cls.class_title

        return namespace


    def get_title(self, context):
        cls = self._get_resource_cls(context)
        class_title = cls.class_title.gettext()
        title = MSG(u'Add {class_title}')
        return title.gettext(class_title=class_title)


    def icon(self, resource, **kw):
        cls = self._get_resource_cls(get_context())
        return cls.get_class_icon()


    def action_default(self, resource, context, form):
        name = form['name']
        title = form['title']

        # Create the resource
        class_id = form['class_id']
        if class_id is None:
            class_id = self._get_resource_class_id(context)
        cls = get_resource_class(class_id)
        container = self._get_container(resource, context)
        child = cls.make_resource(cls, container, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = self._get_goto(resource, context, form)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class BoxAwareNewInstance(ProxyContainerProxyEasyNewInstance):

    context_menus = []
    schema = merge_dicts(ProxyContainerProxyEasyNewInstance.schema,
                         class_id=String(mandatory=True))

    # configuration
    is_content = None
    is_side = None

    def get_title(self, context):
        return self.title


    def _get_resource_cls(self, context):
        from repository import Box
        return Box


    def _get_container(self, resource, context):
        site_root = resource.get_site_root()
        repository = site_root.get_repository()
        return repository


    def get_namespace(self, resource, context):
        namespace = EasyNewInstance.get_namespace(self, resource, context)
        # actions namespace
        namespace['actions'] = self._get_action_namespace(resource, context)
        # proxy items
        site_root = resource.get_site_root()
        repository = site_root.get_repository()
        document_types = repository._get_document_types(is_content=self.is_content,
                                                        is_side=self.is_side)
        items = []
        selected = context.get_form_value('class_id')
        items = [
            {'title': x.class_title.gettext(),
             'class_id': x.class_id,
             'selected': x.class_id == selected,
             'icon': '/ui/' + x.class_icon16}
            for x in document_types ]
        if selected is None:
            items[0]['selected'] = True
        namespace['items'] = items
        # class title
        cls = self._get_resource_cls(context)
        namespace['class_title'] = cls.class_title

        return namespace


    def action_default(self, resource, context, form):
        name = form['name']
        title = form['title']

        # Create the resource
        class_id = form['class_id']
        cls = get_resource_class(class_id)
        container = self._get_container(resource, context)
        child = cls.make_resource(cls, container, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = self._get_goto(resource, context, form)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class BarAwareBoxAwareNewInstance(BoxAwareNewInstance):

    widgets = freeze(BoxAwareNewInstance.widgets
                     + [SelectRadio('order', title=MSG(u'Order box'),
                                    has_empty_option=False)])

    schema = merge_dicts(BoxAwareNewInstance.schema,
                         order=OrderBoxEnumerate(default='not-order'))

    def get_value(self, resource, context, name, datatype):
        if name == 'order':
            return ''
        return BoxAwareNewInstance.get_value(self, resource, context,
                                             name, datatype)


    def _get_goto(self, resource, context, form):
        return context.get_link(resource)


    def action_default(self, resource, context, form):
        name = form['name']
        title = form['title']
        order = form['order']

        # Create the resource
        class_id = form['class_id']
        cls = get_resource_class(class_id)
        container = self._get_container(resource, context)
        child = cls.make_resource(cls, container, name)
        if order != 'do-not-order':
            if self.is_side:
                order_table = resource.get_resource(resource.sidebar_name)
            else:
                order_table = resource.get_resource(resource.contentbar_name)

            # Order child
            record = order_table.add_new_record({'name': name})
            if order == 'order-top':
                order_table.handler.order_top([record.id])
            else:
                order_table.handler.order_bottom([record.id])

        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = self._get_goto(resource, context, form)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class SmartOrderedTable_Ordered(ResourcesOrderedTable_Ordered):

    def get_table_columns(self, resource, context):
        func = ResourcesOrderedTable_Ordered.get_table_columns
        columns = func(self, resource, context)
        # Fix order_preview title
        new_columns = []
        for column in columns:
            if column[0] != 'order_preview':
                new_columns.append(column)
                continue
            if len(column) == 3:
                new_columns.append((column[0], MSG(u"Info"), column[2]))
            else:
                new_columns.append((column[0], MSG(u"Info")))
        return new_columns


    def get_title(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'ordered_view_title', None)

    title = property(get_title)

    def get_title_description(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'ordered_view_title_description', None)

    title = property(get_title)
    title_description = property(get_title_description)



class SmartOrderedTable_Unordered(ResourcesOrderedTable_Unordered):

    def get_table_columns(self, resource, context):
        func = ResourcesOrderedTable_Unordered.get_table_columns
        columns = func(self, resource, context)
        # Fix order_preview title
        new_columns = []
        for column in columns:
            if column[0] != 'order_preview':
                new_columns.append(column)
                continue
            if len(column) == 3:
                new_columns.append((column[0], MSG(u"Info"), column[2]))
            else:
                new_columns.append((column[0], MSG(u"Info")))
        return new_columns


    def get_title(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'unordered_view_title', None)


    def get_title_description(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'unordered_view_title_description', None)

    title = property(get_title)
    title_description = property(get_title_description)



class SmartOrderedTable_View(ResourcesOrderedTable_View):

    template = '/ui/common/order_view.xml'

    subviews = [ SmartOrderedTable_Ordered(),
                 SmartOrderedTable_Unordered() ]

    def get_namespace(self, resource, context):
        views = []
        for view in self.subviews:
            views.append({'title': view.title,
                          'description': view.title_description,
                          'view': view.GET(resource, context)})
        return {'views': views}



############################################################
# GoToSpecificItem
############################################################
class AdvanceGoToSpecificDocument(GoToSpecificDocument):

    title = MSG(u'View')
    keep_query = False
    keep_message = False

    def GET(self, resource, context):
        specific_document = self.get_specific_document(resource, context)
        specific_view = self.get_specific_view(resource, context)
        goto = '%s/%s' % (context.get_link(resource), specific_document)
        if specific_view:
            goto = '%s/;%s' % (goto, specific_view)
        goto = get_reference(goto)

        # Keep the query
        if self.keep_query and context.uri.query:
            goto.query = context.uri.query.copy()

        # Keep the message
        if self.keep_message:
            message = context.get_form_value('message')
            if message:
                goto = goto.replace(message=message)

        return goto



############################################################
# Footer
############################################################

class FooterMenu_View(Menu_View):

    access = 'is_allowed_to_edit'

    def get_item_value(self, resource, context, item, column):
        if column == 'html_content':
            value = resource.handler.get_record_value(item, column)
            return HTMLBody.decode(Unicode.encode(value))
        return Menu_View.get_item_value(self, resource, context, item, column)



############################################################
# Manage link view
############################################################

class BaseManageLink(STLView):

    template = '/ui/neutral/manage_link.xml'
    title = MSG(u'Manage view')

    def get_items(self, resource, context):
        items_list = [[]]

        return items_list


    def get_namespace(self, resource, context):
        items_list = self.get_items(resource, context)

        # Post process link
        # FIXME Does not work for absolute links
        here_link = Path(context.get_link(resource))
        for list in items_list:
            for item in list['items']:
                new_path = here_link.resolve2(item['path'])
                item['path'] = new_path
                disable = item.get('disable', False)
                item['disable'] = disable
                if disable:
                    item['class'] = '%s disable' % item['class']

        return {'lists': items_list, 'title': self.title}



class BaseManageContent(Folder_BrowseContent):

    access = 'is_allowed_to_edit'

    search_template = None

    table_actions = [
        RemoveButton, RenameButton, CopyButton, CutButton, PasteButton,
        PublishButton, RetireButton]

    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('format', MSG(u'Format')),
        ('mtime', MSG(u'Last Modified')),
        ('workflow_state', MSG(u'State')),
        ]

    def get_query_schema(self):
        return merge_dicts(Folder_BrowseContent.get_query_schema(self),
                           sort_by=String(default='mtime'),
                           reverse=Boolean(default=True))


    def get_items(self, resource, context, *args):
        return Folder_BrowseContent.get_items(self, resource, context, *args)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'name':
            return brain.name, context.get_link(item_resource)
        return Folder_BrowseContent.get_item_value(self, resource,
                  context, item, column)



class BaseManage_Rename(Folder_Rename):

    def action(self, resource, context, form):
        ret = Folder_Rename.action(self, resource, context, form)
        # Tweak goto
        ret.path = Path(';manage_view')
        return ret



############################################################
# Numeric batch
############################################################

class BrowseFormBatchNumeric(Folder_BrowseContent):

    batch_template = '/ui/common/browse_batch.xml'
    max_middle_pages = None

    def get_batch_namespace(self, resource, context, items):
        namespace = {}
        batch_start = context.query['batch_start']
        size = context.query['batch_size']
        uri = context.uri

        # Calcul nb_pages and current_page
        total = len(items)
        end = min(batch_start + size, total)
        nb_pages = total / size
        if total % size > 0:
            nb_pages += 1
        current_page = (batch_start / size) + 1

        namespace['control'] = nb_pages > 1

        # Message (singular or plural)
        total = len(items)
        if total == 1:
            namespace['msg'] = self.batch_msg1.gettext()
        else:
            namespace['msg'] = self.batch_msg2.gettext(n=total)

        # Add start & end value in namespace
        namespace['start'] = batch_start + 1
        namespace['end'] = end

        # See previous button ?
        if current_page != 1:
            previous = max(batch_start - size, 0)
            namespace['previous'] = uri.replace(batch_start=previous)
        else:
            namespace['previous'] = None

        # See next button ?
        if current_page < nb_pages:
            namespace['next'] = uri.replace(batch_start=batch_start+size)
        else:
            namespace['next'] = None

        # Add middle pages
        middle_pages = range(max(current_page - 3, 2),
                             min(current_page + 3, nb_pages-1) + 1)

        # Truncate middle pages if nedded
        if self.max_middle_pages:
            middle_pages_len = len(middle_pages)
            if middle_pages_len > self.max_middle_pages:
                delta = middle_pages_len - self.max_middle_pages
                delta_start = delta_end = delta / 2
                if delta % 2 == 1:
                    delta_end = delta_end +1
                middle_pages = middle_pages[delta_start:-delta_end]

        pages = [1] + middle_pages
        if nb_pages > 1:
            pages.append(nb_pages)

        namespace['pages'] = []
        for i in pages:
            namespace['pages'].append(
                {'number': i,
                 'css': 'current' if i == current_page else None,
                 'uri': uri.replace(batch_start=((i-1) * size))})

        # Add ellipsis if needed
        if nb_pages > 5:
            ellipsis = {'number': u'…',
                        'css': 'ellipsis',
                        'uri': None}
            if 2 not in middle_pages:
                namespace['pages'].insert(1, ellipsis)
            if (nb_pages - 1) not in middle_pages:
                namespace['pages'].insert(len(namespace['pages']) - 1,
                                          ellipsis)

        return namespace



############################################################
# RSS
############################################################

class BaseRSS(BaseView):

    access = True
    allowed_formats = freeze([])
    excluded_formats = freeze([])
    excluded_paths = freeze([])
    excluded_container_paths = freeze([])
    max_items_number = 20


    def get_base_query(self, resource, context):
        # Filter by website
        abspath = resource.get_site_root().get_canonical_path()
        return [ get_base_path_query(str(abspath)) ]


    def get_allowed_formats(self, resource, context):
        return self.allowed_formats


    def get_excluded_formats(self, resource, context):
        return self.excluded_formats


    def get_excluded_paths(self, resource, context):
        return self.excluded_paths


    def get_excluded_container_paths(self, resource, context):
        return self.excluded_container_paths


    def get_max_items_number(self, resource, context):
        return self.max_items_number


    def get_if_modified_since_query(self, resource, context,
                                    if_modified_since):
        if not if_modified_since:
            return []
        return AndQuery(RangeQuery('mtime', if_modified_since, None),
                        NotQuery(PhraseQuery('mtime', if_modified_since)))


    def get_items(self, resource, context, if_modified_since=None):
        # Base query (workflow aware, image, state ...)
        query = self.get_base_query(resource, context)

        # Allowed formats
        formats = self.get_allowed_formats(resource, context)
        if formats:
            if len(formats) > 1:
                query2 = OrQuery(*[ PhraseQuery('format', format)
                                    for format in formats ])
            else:
                query2 = PhraseQuery('format', formats[0])
            query.append(query2)

        # Excluded formats
        excluded_formats = self.get_excluded_formats(resource, context)
        if excluded_formats:
            if len(excluded_formats) > 1:
                query2 = OrQuery(*[ PhraseQuery('format', format)
                                    for format in excluded_formats ])
            else:
                query2 = PhraseQuery('format', excluded_formats[0])
            query.append(NotQuery(query2))

        # Excluded paths
        excluded_paths = self.get_excluded_paths(resource, context)
        if excluded_paths:
            if len(excluded_paths) > 1:
                query2 = OrQuery(*[ PhraseQuery('abspath', str(path))
                                    for path in excluded_paths ])
            else:
                query2 = PhraseQuery('abspath', str(excluded_paths[0]))
            query.append(NotQuery(query2))

        # Excluded container paths
        excluded_cpaths = self.get_excluded_container_paths(resource, context)
        if excluded_cpaths:
            if len(excluded_cpaths) > 1:
                query2 = OrQuery(*[ get_base_path_query(str(path))
                                    for path in excluded_cpaths ])
            else:
                query2 = get_base_path_query(str(excluded_cpaths[0]))
            query.append(NotQuery(query2))

        # An If-Modified-Since ?
        query2 = self.get_if_modified_since_query(resource, context,
                                                  if_modified_since)
        if query2:
            query.append(query2)

        query = AndQuery(*query)
        return resource.get_root().search(query)


    def _sort_and_batch(self, resource, context, results):
        size = self.get_max_items_number(resource, context)
        items = results.get_documents(sort_by='mtime', reverse=True,
                                      size=size)
        return items


    def sort_and_batch(self, resource, context, results):
        items = self._sort_and_batch(resource, context, results)

        # Access Control (FIXME this should be done before batch)
        user = context.user
        root = context.root
        allowed_items = []
        for item in items:
            abspath = item.abspath
            resource = root.get_resource(abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        return allowed_items


    def get_mtime(self, resource):
        context = get_context()
        items = self.get_items(resource, context)
        items = self.sort_and_batch(resource, context, items)
        # FIXME If there is no modifications ?
        if not items:
            return
        last_brain = items[0][0]
        return last_brain.mtime


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column in ('link', 'guid'):
            value = context.uri.resolve(context.get_link(item_resource))
            return str(value)
        elif column == 'pubDate':
            return brain.mtime
        elif column == 'title':
            return item_resource.get_title()
        elif column == 'description':
            if isinstance(item_resource, WebPage):
                data = item_resource.get_html_data()
                if data is None:
                    # Skip empty content
                    return ''
                # Set the prefix
                prefix = site_root.get_pathto(item_resource)
                data = set_prefix_with_hostname(data, '%s/' % prefix,
                                                uri=context.uri)
                data = stream_to_str_as_xhtml(data)
                return data.decode('utf-8')
            else:
                return item_resource.get_property('description')


    def GET(self, resource, context):
        language = context.get_query_value('language')
        if language is None:
            language = resource.get_content_language(context)
        if_modified_since = context.get_header('if-modified-since')
        items = self.get_items(resource, context, if_modified_since)
        items = self.sort_and_batch(resource, context, items)

        # Construction of the RSS flux
        feed = RSSFile()

        site_root = resource.get_site_root()
        host = context.uri.authority
        # The channel
        channel = feed.channel
        channel['title'] = site_root.get_property('title')
        channel['link'] = 'http://%s/?language=%s' % (host, language)
        channel['description'] = MSG(u'Last News').gettext()
        channel['language'] = language

        # The new items
        feed_items = feed.items
        for item in items:
            ns = {}
            for key in ('link', 'guid', 'title', 'pubDate', 'description'):
                ns[key] = self.get_item_value(resource, context, item, key,
                                              site_root)
            feed_items.append(ns)

        # Filename and Content-Type
        context.set_content_disposition('inline', "last_news.rss")
        context.set_content_type('application/rss+xml')
        return feed.to_str()



############################################################
# 404
############################################################

class NotFoundPage_Edit(HTMLEditView):

    schema = {
        'data': HTMLBody,
        'title': Unicode,
        'timestamp': DateTime(readonly=True)}

    widgets = [ timestamp_widget,
                title_widget,
                rte_widget ]

    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        # Save changes
        title = form['title']
        language = resource.get_content_language(context)
        resource.set_property('title', title, language=language)
        new_body = form['data']
        handler = resource.get_handler(language=language)
        handler.set_body(new_body)
        # Ok
        context.message = messages.MSG_CHANGES_SAVED

