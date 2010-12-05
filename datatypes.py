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
from itools.datatypes import Integer, Enumerate, PathDataType, Time
from itools.uri import get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.skins import skin_registry

# Import from itws



class PositiveInteger(Integer):

    @staticmethod
    def is_valid(value):
        return value >= 0



class PositiveIntegerNotNull(Integer):

    @staticmethod
    def is_valid(value):
        return value > 0



class NeutralClassSkin(Enumerate):

    @classmethod
    def get_options(cls):
        from skin import NeutralSkin
        options = []
        for key, skin in skin_registry.items():
            if isinstance(skin, NeutralSkin):
                options.append({'name': '/ui/%s' % key,
                                'value': skin.title})
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



class TimeWithoutSecond(Time):

    @staticmethod
    def encode(value):
        # We choose the extended format as the canonical representation
        if value is None:
            return ''
        return value.strftime('%H:%M')
