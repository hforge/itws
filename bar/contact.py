# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Armel Fortun <armel@maar.fr>
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
from itools.datatypes import String
from itools.gettext import MSG
from itools.uri import Path, Reference

# Import from ikaaro
from ikaaro.autoform import ReadOnlyWidget, XHTMLBody
from ikaaro.website_views import ContactForm

# Import from itws
from base import Box
from homepage import WSDataFolder
from itws.views import AutomaticEditView



class BoxContact_View(ContactForm):

    # BOX VIEW API
    def get_view_is_empty(self):
        return getattr(self, '_view_is_empty', False)


    def set_view_is_empty(self, value):
        setattr(self, '_view_is_empty', value)


    def get_styles(self, context):
        return []


    def get_scripts(self, context):
        return []


    def is_admin(self, resource, context):
        ac = resource.get_access_control()
        return ac.is_allowed_to_edit(context.user, resource)


    def get_schema(self, resource, context):
        site_root = resource.get_site_root()
        return ContactForm.get_schema(self, site_root, context)


    def get_widgets(self, resource, context):
        site_root = resource.get_site_root()
        return ContactForm.get_widgets(self, site_root, context)


    def get_value(self, resource, context, name, datatype):
        site_root = resource.get_site_root()
        return ContactForm.get_value(self, site_root, context, name, datatype)


    def get_namespace(self, resource, context):
        # Hook action, action must be set to contact box uri
        site_root = context.resource.get_site_root()
        namespace = ContactForm.get_namespace(self, site_root, context)
        current_uri = context.uri
        uri = Reference(current_uri.scheme, current_uri.authority,
                        current_uri.path, current_uri.query,
                        current_uri.fragment)
        uri.path = Path(context.get_link(resource))
        namespace['action'] = uri
        return namespace


    def _get_parent_view_container(self, resource):
        if isinstance(resource.parent, WSDataFolder):
            return resource.get_site_root()
        else:
            return resource.parent


    def on_form_error(self, resource, context):
        # FIXME on_form_error should not return a GET
        # side-effect: error informations are lost
        context.message = context.form_error.get_message()
        parent_view_container = self._get_parent_view_container(resource)
        goto = context.get_link(parent_view_container)
        return context.come_back(context.message, goto=goto)


    def action(self, resource, context, form):
        site_root = context.resource.get_site_root()
        ret = ContactForm.action(self, site_root, context, form)
        # Hook goto
        parent_view_container = self._get_parent_view_container(resource)
        goto = context.get_link(parent_view_container)
        return context.come_back(context.message, goto=goto)



class BoxContact_Edit(AutomaticEditView):

    def get_value(self, resource, context, name, datatype):
        if name == 'configuration_shortcut':
            html = '<a href="/;edit_contact_options">configuration</a>'
            return XHTMLBody.decode(html)
        proxy = super(BoxContact_Edit, self)
        return proxy.get_value(resource, context, name, datatype)



class BoxContact(Box):

    class_id = 'box-contact'
    class_version = '20100923'
    class_title = MSG(u'Contact box')
    class_description = MSG(u'Contact form to collect messages from users.')

    edit_schema = {'configuration_shortcut': String(readonly=True)}
    edit_widgets = [
        ReadOnlyWidget('configuration_shortcut',
                       title=MSG(u'To configure the website email options, '
                                 u'please follow the link below'))]

    is_content = True

    # Views
    view = BoxContact_View()
    edit = BoxContact_Edit()
