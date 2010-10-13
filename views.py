# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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
from itools.core import freeze, merge_dicts
from itools.csv import Property
from itools.datatypes import Boolean, DateTime, Enumerate, Integer, String, Unicode
from itools.fs import FileName
from itools.gettext import MSG
from itools.handlers import checkid
from itools.uri import get_reference
from itools.web import get_context, ERROR, FormError
from itools.database import PhraseQuery

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton, RenameButton, PublishButton
from ikaaro.buttons import RetireButton, CopyButton, CutButton, PasteButton
from ikaaro.datatypes import Multilingual
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.autoform import AutoForm, TextWidget, HTMLBody, RadioWidget
from ikaaro.autoform import SelectWidget, MultilineWidget
from ikaaro.autoform import description_widget, subject_widget
from ikaaro.autoform import title_widget, timestamp_widget
from ikaaro.menu import Menu_View
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.future.order import ResourcesOrderedTable_Unordered
from ikaaro.future.order import ResourcesOrderedTable_View
from ikaaro.resource_views import DBResource_Edit
from ikaaro.registry import get_resource_class
from ikaaro.text_views import Text_Edit
from ikaaro.user import User
from ikaaro.views_new import NewInstance
from ikaaro.workflow import WorkflowAware

# Import from itws
from datatypes import StateEnumerate, StaticStateEnumerate, OrderBoxEnumerate
from utils import state_widget


class MyAuthorized_Classid(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        #selected = context.get_form_value('class_id')
        #items = [
        #    {'title': cls.class_title,
        #     'description': cls.class_description,
        #     'class_id': cls.class_id,
        #     'selected': cls.class_id == selected,
        #     'icon': '/ui/' + cls.class_icon16}
        #    for cls in self.get_aware_document_types(resource, context) ]
        for cls in cls.view.get_aware_document_types(cls.resource, cls.context):
            options.append({'name': cls.class_id,
                            'value': cls.class_title})
        return options



############################################################
# NewInstance
############################################################

class EasyNewInstance(NewInstance):
    """ ikaaro.views_new.NewInstance without field name.
    """

    query_schema = freeze({'type': String, 'title': Unicode})
    widgets = freeze([
        TextWidget('title', title=MSG(u'Title', mandatory=True))])

    goto_method = None

    def get_new_resource_name(self, form):
        # As we have no name, always return the title
        title = form['title'].strip()
        return title


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

    def _get_resource_cls(self, resource, context):
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
        cls = self._get_resource_cls(context.resource, context)
        class_title = cls.class_title.gettext()
        title = MSG(u'Add {class_title}')
        return title.gettext(class_title=class_title)


    def icon(self, resource, **kw):
        context = get_context()
        cls = self._get_resource_cls(context.resource, context)
        return cls.get_class_icon()


    def action_default(self, resource, context, form):
        name = form['name']
        title = form['title']

        # Create the resource
        cls = self._get_resource_cls(resource, context)
        container = self._get_container(resource, context)
        child = cls.make_resource(cls, container, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = self._get_goto(resource, context, form)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class ProxyContainerProxyEasyNewInstance(EasyNewInstance):


    query_schema = freeze({'title': Unicode})
    schema = {
        'name': String,
        'title': Unicode,
        'class_id': String}

    def _get_resource_class_id(self, context):
        # Use in action method
        raise NotImplementedError


    def _get_resource_cls(self, resource, context):
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
        cls = self._get_resource_cls(context.resource, context)
        class_title = cls.class_title.gettext()
        title = MSG(u'Add {class_title}')
        return title.gettext(class_title=class_title)


    def icon(self, resource, **kw):
        context = get_context()
        cls = self._get_resource_cls(context.resource, context)
        return cls.get_class_icon()


    def action(self, resource, context, form):
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


    def _get_resource_cls(self, resource, context):
        from repository import Box
        return Box


    def _get_container(self, resource, context):
        site_root = resource.get_site_root()
        repository = site_root.get_repository()
        return repository


    def get_aware_document_types(self, resource, context):
        site_root = resource.get_site_root()
        repository = site_root.get_repository()
        return repository._get_document_types(
                is_content=self.is_content, is_side=self.is_side,
                allow_instanciation=True)


    def action(self, resource, context, form):
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

    order_widget_title = MSG(u'Order box')
    is_content = True
    is_side = None

    def _get_container(self, resource, context):
        return resource.parent


    def _get_order_table(self, resource, context):
        if resource.parent.name == 'ws-data':
            bar_aware_resource = resource.parent.parent
        else:
            bar_aware_resource = resource.parent
        if self.is_side:
            bar_name = bar_aware_resource.sidebar_name
            order_table = bar_aware_resource.get_resource(bar_name)
        else:
            bar_name = bar_aware_resource.contentbar_name
            order_table = bar_aware_resource.get_resource(bar_name)
        return order_table


    def _get_box_goto(self, child, context):
        link_child = '%s/;edit' % context.get_link(child)
        goto = get_reference(link_child)
        # Is admin popup ?
        if ('is_admin_popup' in context.get_referrer() and
            getattr(child, 'use_fancybox', True) is True):
            goto.query['is_admin_popup'] = '1'
        else:
            goto = None
        return goto


    def get_schema(self, resource, context):
        return merge_dicts(BoxAwareNewInstance.get_schema(self, resource, context),
                           class_id=MyAuthorized_Classid(view=self, resource=resource, context=context),
                           order=OrderBoxEnumerate(default='order-bottom'),
                           state=StaticStateEnumerate(default='public'))


    def get_widgets(self, resource, context):
        return freeze(BoxAwareNewInstance.get_widgets(self, resource, context) +
                      [
                       state_widget,
                       SelectWidget('class_id', title=MSG(u'Class id')),
                       RadioWidget('order', title=self.order_widget_title,
                                  has_empty_option=False)])

    def action(self, resource, context, form):
        name = form['name']
        title = form['title']
        order = form['order']

        # Create the resource
        class_id = form['class_id']
        cls = get_resource_class(class_id)
        container = self._get_container(resource, context)
        child = container.make_resource(name, cls)

        # We order the resource in table if needed
        if order != 'do-not-order':
            order_table = self._get_order_table(resource, context)

            # Order child
            record = order_table.add_new_record({'name': name})
            if order == 'order-top':
                order_table.handler.order_top([record.id])
            else:
                order_table.handler.order_bottom([record.id])

        # The metadata
        metadata = child.metadata
        language = 'en'
        # XXX Migration
        #resource.get_content_language(context)
        title = Property(title, lang=language)
        metadata.set_property('title', title)

        # Workflow
        if isinstance(child, WorkflowAware):
            child.set_property('state', form['state'])

        # Calcul Goto
        goto = self._get_box_goto(child, context)

        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class SideBarAwareNewInstance(BarAwareBoxAwareNewInstance):

    is_side = True
    is_content = None

    def _get_container(self, resource, context):
        site_root = resource.get_site_root()
        return site_root.get_repository()



############################################################
# RobotsTxt
############################################################

class RobotsTxt_Edit(Text_Edit):

    schema = {'timestamp': DateTime(readonly=True), 'data': String}
    widgets = [
        timestamp_widget,
        MultilineWidget('data', title=MSG(u"Content"), rows=19, cols=69)]

    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        data = form['data']
        resource.handler.load_state_from_string(data)
        # Ok
        context.message = messages.MSG_CHANGES_SAVED




# Override User is_allowed_to_view
User.is_allowed_to_view = User.is_allowed_to_edit


############################################################
# Table
############################################################

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


    def get_title(self, context):
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


    def get_title(self, context):
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
            views.append({'title': view.get_title(context),
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
    table_actions = Menu_View.table_actions[1:]

    def get_item_value(self, resource, context, item, column):
        if column == 'html_content':
            value = resource.handler.get_record_value(item, column)
            return HTMLBody.decode(Unicode.encode(value))
        return Menu_View.get_item_value(self, resource, context, item, column)



############################################################
# Manage Content
############################################################

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



class AutomaticEditView(DBResource_Edit):

    base_schema = {'title': Multilingual,
                   'timestamp': DateTime(readonly=True, ignore=True)}

    # Add timestamp_widget in get_widgets method
    base_widgets = [title_widget]


    def _get_schema(self, resource, context):
        schema = {}
        if isinstance(resource, WorkflowAware):
            schema['state'] = StateEnumerate
        if getattr(resource, 'edit_show_meta', False) is True:
            schema['description'] = Unicode(multilingual=True)
            schema['subject'] = Unicode(multilingual=True)
        schema = merge_dicts(self.base_schema, schema, resource.edit_schema)
        # FIXME Hide/Show title
        if getattr(resource, 'display_title', True) is False:
            del schema['title']
        return schema


    def _get_widgets(self, resource, context):
        widgets = []
        if getattr(resource, 'edit_show_meta', False) is True:
            widgets.extend([description_widget, subject_widget])
        widgets = self.base_widgets + widgets + resource.edit_widgets
        # Add state widget in bottom
        if isinstance(resource, WorkflowAware):
            widgets.append(state_widget)
        # Add timestamp_widget
        widgets.append(timestamp_widget)
        # FIXME Hide/Show title
        if getattr(resource, 'display_title', True) is False:
            to_remove = [ w for w in widgets if w.name == 'title' ]
            if to_remove:
                widgets.remove(to_remove[0])
        return widgets


    def get_value(self, resource, context, name, datatype):
        if name == 'state':
            return resource.get_workflow_state()
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)
