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

# Import from the Standard Library
from urllib import quote

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean, DateTime, String, Unicode
from itools.gettext import MSG
from itools.uri import get_reference

# Import from ikaaro
from ikaaro import messages
from ikaaro.autoform import TextWidget
from ikaaro.autoform import description_widget, subject_widget
from ikaaro.autoform import title_widget, timestamp_widget
from ikaaro.datatypes import Multilingual
from ikaaro.file import File, Image
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.folder_views import Folder_NewResource as BaseFolder_NewResource
from ikaaro.registry import get_resource_class, resources_registry
from ikaaro.resource_ import DBResource
from ikaaro.resource_views import DBResource_Edit, EditLanguageMenu
from ikaaro.root import Root
from ikaaro.utils import get_content_containers
from ikaaro.views_new import NewInstance

# Import from itws
from feed_views import Browse_Navigator
from popup import ITWS_DBResource_AddImage, ITWS_DBResource_AddLink
from popup import ITWS_DBResource_AddMedia
from itws.control_panel import ITWS_ControlPanel
from itws.control_panel import CPExternalEdit, CPDBResource_Links
from itws.control_panel import CPDBResource_Backlinks, CPDBResource_CommitLog
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

    base_schema = {'title': Multilingual,
                   'timestamp': DateTime(readonly=True, ignore=True)}

    # Add timestamp_widget in get_widgets method
    base_widgets = [title_widget]


    def _get_query_to_keep(self, resource, context):
        """Forward is_admin_popup if defined"""
        to_keep = DBResource_Edit._get_query_to_keep(self, resource, context)
        is_admin_popup = context.get_query_value('is_admin_popup')
        if is_admin_popup:
            to_keep.append({'name': 'is_admin_popup', 'value': '1'})
        return to_keep


    def _get_schema(self, resource, context):
        schema = {}
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


# Monkey patchs
# NEW RESOURCE
# Keep Root.new_resource intact
Root.new_resource = Folder.new_resource.__class__()
Folder.new_resource = Folder_NewResource()
# NEW INSTANCE
# Note: This monkey patch does not affect Blog, Tracker, Event, File
NewInstance.goto_view = 'edit'

# Add ITWS_ControlPanel for Folder resources
Folder.class_views = ['view', 'edit', 'control_panel']
Folder.class_control_panel = ['links', 'backlinks', 'commit_log']
Folder.links = CPDBResource_Links()
Folder.backlinks = CPDBResource_Backlinks()
Folder.commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')

# Add ITWS_ControlPanel for Images resources
Image.class_views = ['view', 'download', 'edit', 'control_panel']
Image.control_panel = ITWS_ControlPanel()
Image.class_control_panel = ['externaledit', 'links',
                             'backlinks', 'commit_log']
Image.externaledit = CPExternalEdit()
Image.links = CPDBResource_Links()
Image.backlinks = CPDBResource_Backlinks()
Image.commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')

# Add ITWS_ControlPanel for File resources
File.class_views = ['view', 'edit', 'control_panel']
File.control_panel = ITWS_ControlPanel()
File.class_control_panel = ['links', 'backlinks', 'commit_log']
File.links = CPDBResource_Links()
File.backlinks = CPDBResource_Backlinks()
File.commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')

# Add navigator to all resources
for cls in resources_registry.values():
    if issubclass(cls, Folder):
        cls.manage_content = Browse_Navigator()
    cls.add_image = ITWS_DBResource_AddImage()
    cls.add_link = ITWS_DBResource_AddLink()
    cls.add_media = ITWS_DBResource_AddMedia()




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
