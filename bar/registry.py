# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@itaapy.com>
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
    is_contentbox = resource_class.is_contentbox
    is_sidebox = resource_class.is_sidebox
    allow_instanciation = resource_class.allow_instanciation
    if is_contentbox is False and is_sidebox is False:
        msg = u'Box %s should be at least content box or side box'
        raise ValueError, msg % resource_class.class_id

    boxes_registry[resource_class] = {
        'instanciation': allow_instanciation,
        'content': is_contentbox,
        'side': is_sidebox}


def get_boxes_registry():
    # TODO Expose the dictionary through an user friendly API
    return freeze(boxes_registry)
