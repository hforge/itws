# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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
from itools.datatypes import Boolean, XMLContent
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.autoform import RadioWidget, CheckboxWidget, XHTMLBody
from ikaaro.resource_views import DBResource_Edit
from ikaaro.webpage import HTMLEditView

# Import from itws
from tags_views import TagsAware_Edit
from utils import get_warn_referenced_message



class WebPage_Edit(TagsAware_Edit, HTMLEditView, DBResource_Edit):

    def _get_schema(self, resource, context):
        return merge_dicts(HTMLEditView._get_schema(self, resource, context),
                           TagsAware_Edit._get_schema(self, resource, context),
                           display_title=Boolean)


    def _get_widgets(self, resource, context):
        widgets = HTMLEditView._get_widgets(self, resource, context)[:]
        # Add display title widget
        display_title_widget = RadioWidget('display_title',
                title=MSG(u'Display title on webpage view ?'))
        widgets.insert(2, display_title_widget)
        # Tags
        widgets.extend(TagsAware_Edit._get_widgets(self, resource, context))
        return widgets


    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            return HTMLEditView.get_value(self, resource, context, name,
                                          datatype)
        if name in TagsAware_Edit.keys:
            return TagsAware_Edit.get_value(self, resource, context, name,
                                            datatype)
        return DBResource_Edit.get_value(self, resource, context, name, datatype)


    def set_value(self, resource, context, name, form):
        if name == 'data':
            return HTMLEditView.set_value(self, resource, context, name, form)
        if name in TagsAware_Edit.keys:
            return TagsAware_Edit.set_value(self, resource, context, name,
                                            form)
        return DBResource_Edit.set_value(self, resource, context, name, form)


    def action(self, resource, context, form):
        print 'ok'
        return DBResource_Edit.action(self, resource, context, form)


    # XXX Migration See how do it
    ## Publish referenced resources which are not public/pending
    #message2 = get_warn_referenced_message(resource, context, form['state'])
    #if message2:
    #    # Add custom message
    #    context.message = [ context.message, message2 ]

    ## Customize message for webpage which can be ordered
    #site_root = resource.get_site_root()
    #section_class = site_root.section_class
    #wsdatafolder_class = site_root.wsdatafolder_class
    #parent = resource.parent
    #if isinstance(parent, (section_class, wsdatafolder_class)) is False:
    #    return

    ## Customize message
    #order_names = parent.get_ordered_names()
    #if resource.name in order_names:
    #    return

    #message2 = MSG(u'To make this webpage visible on "{parent_view}" '
    #               u'please go to <a href="{path}">order interface</a>')
    #if isinstance(parent, wsdatafolder_class):
    #    parent_view = MSG(u'home page').gettext()
    #    order_resource = site_root.get_resource(site_root.order_path)
    #else:
    #    parent_view = parent.class_title.gettext()
    #    order_resource = parent.get_resource(parent.order_path)
    #path = context.get_link(order_resource)
    #parent_view = XMLContent.encode(parent_view)
    #message2 = message2.gettext(parent_view=parent_view,
    #                            path=path).encode('utf8')
    #message2 = XHTMLBody.decode(message2)
    ## Add custom message
    #context.message = [ context.message, message2 ]



class WebPage_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    icon = 'view.png'

    template = '/ui/common/WebPage_view.xml'


    def get_namespace(self, resource, context):
        title = resource.get_property('display_title')
        if title:
            title = resource.get_title()
        return {'name': resource.name.replace('.', '-dot-'),
                'title': title,
                'content': resource.get_html_data()}
