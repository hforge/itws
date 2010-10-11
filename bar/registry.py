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
from itools.core import freeze


##############################
# Registry
##############################

boxes_registry = {}
def register_box(resource_class):
    is_content = resource_class.is_content
    is_side = resource_class.is_side
    allow_instanciation = resource_class.allow_instanciation
    if is_content is False and is_side is False:
        msg = u'Box should be at least content box or side box'
        raise ValueError, msg

    boxes_registry[resource_class] = {'instanciation': allow_instanciation,
                                      'content': is_content, 'side': is_side}


def get_boxes_registry():
    # TODO Expose the dictionary through an user friendly API
    return freeze(boxes_registry)
