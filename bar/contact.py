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
from itools.gettext import MSG
from itools.uri import Path, Reference

# Import from ikaaro
from ikaaro.control_panel import CPEditContactOptions
from ikaaro.website_views import ContactForm

# Import from itws
from base import Box
from homepage import WSDataFolder



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


    def action(self, resource, context, form):
        site_root = context.resource.get_site_root()
        ret = ContactForm.action(self, site_root, context, form)
        # Hook goto
        if isinstance(resource.parent, WSDataFolder):
            # goto on website
            goto = context.get_link(site_root)
        else:
            # goto parent section
            goto = context.get_link(resource.parent)
        return context.come_back(context.message, goto=goto)



class BoxContact(Box):

    class_id = 'box-contact'
    class_version = '20100923'
    class_title = MSG(u'Contact Box')
    class_description = MSG(u'Put the Contact Form in a Box that can be '
                            'displayed in a central sidebar')

    is_content = True

    # Views
    view = BoxContact_View()
    # XXX edit contact options view should be available from edit view
    edit_contact_options = CPEditContactOptions()
