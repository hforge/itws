# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010-2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.core import freeze
from itools.gettext import MSG
from itools.web import STLView

# Import from itws
from views import FieldsAutomaticEditView

class WebPage_Edit(FieldsAutomaticEditView):

    # XXX Here we do not send email to suscribers
    edit_fields = freeze(['title', 'display_title',
                          'data', 'tags', 'thumbnail', 'pub_datetime'])

    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            value = {}
            for language in resource.get_edit_languages(context):
                value[language] = resource.get_html_data(language=language)
            return value
        proxy = super(WebPage_Edit, self)
        return proxy.get_value(resource, context, name, datatype)


    def set_value(self, resource, context, name, form):
        if name == 'data':
            changed = False
            for language, data in form['data'].iteritems():
                handler = resource.get_handler(language=language)
                if handler.set_body(data):
                    changed = True
            if changed:
                context.database.change_resource(resource)
            return False
        proxy = super(WebPage_Edit, self)
        return proxy.set_value(resource, context, name, form)



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
