# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
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
from itools.datatypes import Integer, Enumerate, String, PathDataType, Time
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.registry import get_document_types
from ikaaro.workflow import WorkflowAware



class PositiveInteger(Integer):

    @staticmethod
    def is_valid(value):
        return value >= 0



class PositiveIntegerNotNull(Integer):

    @staticmethod
    def is_valid(value):
        return value > 0



class MultilingualString(String):

    @staticmethod
    def is_empty(value):
        """This is used by the multilingual code"""
        return value == ''



class TagsAwareClassEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        # Import from itws
        from tags import TagsAware

        options = []
        _classes = get_document_types(TagsAware.class_id)
        for _cls in _classes:
            title = _cls.class_title.gettext()
            options.append({'name': _cls.class_id,
                            'value': title.encode('utf-8')})
        options.sort(lambda x, y: cmp(x['value'], y['value']))
        return options



class NeutralClassSkin(Enumerate):

    options = [{'name': '/ui/neutral', 'value': u'Neutral'},
               #{'name': '/ui/neutral2', 'value': u"Neutral 2"},
               {'name': '/ui/k2', 'value': u"K2"}]



class StateEnumerate(Enumerate):

    default = ''

    @classmethod
    def get_options(cls):
        context = get_context()
        resource = context.resource
        states = resource.workflow.states
        state = resource.get_state()

        ac = resource.get_access_control()
        user = context.user

        # Possible states
        options = [
            trans.state_to
            for name, trans in state.transitions.items()
            if ac.is_allowed_to_trans(user, resource, name) ]
        options = set(options)
        options.add(resource.get_statename())

        # Options
        options = [
           {'name': x, 'value': states[x].metadata['title'].gettext()}
           for x in options ]

        options.sort(key=lambda x: x['value'])
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



class ImagePathDataType(PathDataType):

    @staticmethod
    def is_valid(value):
        here = get_context().resource
        try:
            ref = get_reference(value)
            if not ref.scheme:
                resource = here.get_resource(ref.path, soft=True)
                if resource and isinstance(resource, Image):
                    return True
        except Exception, e:
            return False
        return False



class OrderBoxEnumerate(Enumerate):

    options = [{'name': 'do-not-order',
                'value': MSG(u"Do not order (won't be displayed)")},
               {'name': 'order-top', 'value': MSG(u'Order top')},
               {'name': 'order-bottom', 'value': MSG(u'Order bottom')}]



class OpenLayerRender(Enumerate):

    options = [{'name': 'osm', 'value': MSG(u'Open Street Map')},
               {'name': 'google', 'value': MSG(u'Google Map')}]



class TimeWithoutSecond(Time):

    @staticmethod
    def encode(value):
        # We choose the extended format as the canonical representation
        if value is None:
            return ''
        return value.strftime('%H:%M')
