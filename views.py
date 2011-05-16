# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010-2011 Taverne Sylvain <sylvain@itaapy.com>
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
from urllib import quote

# Import from itools
from itools.core import freeze, merge_dicts
from itools.csv import Property
from itools.database import AndQuery, PhraseQuery
from itools.datatypes import Boolean, String, Unicode
from itools.gettext import MSG
from itools.handlers import checkid
from itools.uri import get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro import messages
from ikaaro.autoform import AutoForm, TextWidget, get_default_widget
from ikaaro.datatypes import Multilingual
from ikaaro.file import File
from ikaaro.folder_views import Folder_NewResource as BaseFolder_NewResource
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.registry import get_resource_class
from ikaaro.resource_views import DBResource_Edit, EditLanguageMenu
from ikaaro.utils import get_content_containers
from ikaaro.views_new import NewInstance
from ikaaro.workflow import StaticStateEnumerate, state_widget
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.tags import Tag, get_registered_tags_aware_classes



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
# AutomaticEditView
############################################################
class AutomaticEditView(DBResource_Edit):
    """
    Same that  DBResource_Edit but we add:
        - State (if workflowAware)
        - Allow to hide title widget
        - Fix a bug (with query to keep)
    """

    # Configuration
    display_title = True
    edit_schema = {}
    edit_widgets = []


    def _get_query_to_keep(self, resource, context):
        """Forward is_admin_popup if defined"""
        to_keep = DBResource_Edit._get_query_to_keep(self, resource, context)
        is_admin_popup = context.get_query_value('is_admin_popup')
        if is_admin_popup:
            to_keep.append({'name': 'is_admin_popup', 'value': '1'})
        return to_keep


    def _get_schema(self, resource, context):
        schema = merge_dicts(self.schema, self.edit_schema)
        # If Workfloware we add state
        if isinstance(resource, WorkflowAware):
            schema['state'] = StaticStateEnumerate
        # Hide title ?
        if self.display_title is False:
            schema['title'].hidden_by_default = True
        return freeze(schema)


    def _get_widgets(self, resource, context):
        widgets = self.widgets + self.edit_widgets
        # Cast frozen list into list
        widgets = list(widgets)
        # If workfloware we add state
        if isinstance(resource, WorkflowAware):
            widgets.append(state_widget)
        return freeze(widgets)


    def get_value(self, resource, context, name, datatype):
        if name == 'state':
            return resource.get_workflow_state()
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)



class FieldsAutomaticEditView(AutomaticEditView):
    """
    Same that AutomaticEditView but we replace

      edit_schema = {'title': Unicode}
      edit_widgets = [TextWidget('title', MSG(u'Title')]

    by

      edit_fields = ['title']

    We use get_default_widget to guess widgets.
    We use schema title to define widget title
    """

    edit_fields = []

    @property
    def edit_schema(self):
        kw = {}
        schema = get_context().resource.class_schema
        for name in self.edit_fields:
            kw[name] = schema[name]
        return kw


    @property
    def edit_widgets(self):
        widgets = []
        schema = get_context().resource.class_schema
        for name in self.edit_fields:
            datatype = schema[name]
            widget = self.get_widget(name, datatype)
            widgets.append(widget)
        return widgets


    def get_widget(self, name, datatype):
        title = getattr(datatype, 'title', name)
        return get_default_widget(datatype)(name, title=title)



class FieldsAdvance_NewInstance(AutoForm):

    goto_view = None

    query_schema = freeze({
        'type': String,
        'title': Unicode,
        'path': String,
        'name': String})

    @property
    def add_cls(self):
        context = get_context()
        class_id = context.query['type']
        return get_resource_class(class_id)


    def get_title(self, context):
        if self.title is not None:
            return self.title
        class_title = self.add_cls.class_title.gettext()
        title = MSG(u'Add {class_title}')
        return title.gettext(class_title=class_title)


    def get_schema(self, resource, context):
        kw = {}
        schema = self.add_cls.class_schema
        for name in self.fields:
            # No multilingual datatypes on creation forms
            datatype = schema[name]
            if issubclass(datatype, Multilingual):
                datatype = Unicode
            elif getattr(datatype, 'multilingual', False):
                datatype.multilingual = False
            kw[name] = datatype
        return kw


    def get_widgets(self, resource, context):
        widgets = []
        schema = self.add_cls.class_schema
        for name in self.fields:
            # No multilingual datatypes on creation forms
            datatype = schema[name]
            if issubclass(datatype, Multilingual):
                datatype = Unicode
            widget = self.get_widget(name, datatype)
            widgets.append(widget)
        return widgets


    def get_widget(self, name, datatype):
        title = getattr(datatype, 'title', name)
        return get_default_widget(datatype)(name, title=title)


    def get_new_resource_name(self, form):
        if form.has_key('name') and form['name'].strip():
            # Name
            name = form['name'].strip()
        elif form.has_key('title') and form['title'].strip():
            # Title
            name = form['title']
        else:
            # Number
            context = get_context()
            abspath = context.resource.get_canonical_path()
            query = AndQuery(
                    PhraseQuery('parent_path', str(abspath)),
                    PhraseQuery('format', self.add_cls.class_id))
            search = context.root.search(query)
            if len(search):
                doc = search.get_documents(sort_by='name', reverse=True)[0]
                name = int(doc.name) + 1
            else:
                name = 1
            name = str(name)
        return checkid(name)


    def action(self, resource, context, form):
        # Get the container
        container = resource
        # Make the resource
        name = self.get_new_resource_name(form)
        cls = get_resource_class(self.add_cls.class_id)
        child = container.make_resource(name, cls)
        # Set properies
        resource_schema = self.add_cls.class_schema
        for key in self.get_schema(resource, context):
            datatype = resource_schema[key]
            if getattr(datatype, 'multilingual', False) is True:
                language = container.get_edit_languages(context)[0]
                value = Property(form[key], lang=language)
            else:
                value = form[key]
            child.metadata.set_property(key, value)
        # Ok
        goto = str(resource.get_pathto(child))
        if self.goto_view:
            goto = '%s/;%s' % (goto, self.goto_view)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)

############################################################
# EditLanguageMenu (Only language selection)
############################################################
class EditOnlyLanguageMenu(EditLanguageMenu):
    """Only display form to select language
    fields selection are not displayed
    """

    def get_fields(self):
        return []



############################################################
# NEW RESOURCE VIEWS
############################################################
class Folder_NewResource(BaseFolder_NewResource):

    template = '/ui/common/itws_new_resource_view.xml'
    query_schema = {'advanced': Boolean}


    def get_document_types(self, resource, context):
        return resource.get_document_types()


    def get_not_advanced_types(self):
        return [File, Tag] + get_registered_tags_aware_classes()


    def get_namespace(self, resource, context):
        # 1. Find out the resource classes we can add
        document_types = self.get_document_types(resource, context)

        # Query
        if context.query['advanced'] is False:
            not_advanced_types = self.get_not_advanced_types()
            final_document_types = []
            for x in document_types:
                if x in not_advanced_types:
                    final_document_types.append(x)
            has_advanced = len(document_types) != len(final_document_types)
        else:
            final_document_types = document_types
            has_advanced = True

        # 2. Build the namespace
        items = [
            {'icon': '/ui/' + cls.class_icon48,
             'title': cls.class_title.gettext(),
             'description': cls.class_description.gettext(),
             'url': ';new_resource?type=%s' % quote(cls.class_id)}
            for cls in final_document_types ]

        return {'has_advanced': has_advanced,
                'advanced': context.query['advanced'],
                'items': items}



class Website_NewResource(Folder_NewResource):


    def get_document_types(self, resource, context):
        # On website we return all document_type
        document_types = []
        skip_formats = set()
        for resource in get_content_containers(context, skip_formats):
            skip_formats.add(resource.class_id)
            for cls in resource.get_document_types():
                if cls not in document_types:
                    document_types.append(cls)
        return document_types



############################################################
# TABLE VIEW WITHOUT ADD_RECORD BUTTON
############################################################
class TableViewWithoutAddRecordButton(object):

    # Delete add_record schema/action to be able to use
    # TableView inside a compositeform
    action_add_record_schema = None
    action_add_record = None



############################################################
# ContentBarAware edit view helper
############################################################
class EditView(object):


    def action(self, resource, context, form):
        from itws.section_views import section_views_registry

        if form['view'] != resource.get_property('view'):
            resource.del_resource('section_view', soft=True)
            view = section_views_registry[form['view']]
            cls = view.view_configuration_cls
            if cls:
                resource.make_resource('section_view',
                                       view.view_configuration_cls)
