# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Enumerate
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.workflow import WorkflowAware


class OrderBoxEnumerate(Enumerate):

    options = [{'name': 'do-not-order',
                'value': MSG(u"Do not order (won't be displayed)")},
               {'name': 'order-top', 'value': MSG(u'Order top')},
               {'name': 'order-bottom', 'value': MSG(u'Order bottom')}]





class MyAuthorized_Classid(Enumerate):

    site_root = None

    @classmethod
    def get_options(cls):
        options = []
        # XXX migration (Use a beautiful widget to show classid)
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



class StaticStateEnumerate(Enumerate):

    workflow = WorkflowAware.workflow

    def get_options(cls):
        states = cls.workflow.states

        # Options
        options = [
           {'name': x, 'value': states[x].metadata['title'].gettext()}
           for x in states.keys() ]

        options.sort(key=lambda x: x['value'])
        return options



