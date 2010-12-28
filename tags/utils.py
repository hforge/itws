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

# Import from ikaaro
from ikaaro.registry import get_resource_class


##########################################################################
# Registry
##########################################################################

tags_aware_registry = []
def register_tags_aware(resource_class):
    class_id = resource_class.class_id
    if class_id in tags_aware_registry:
        # Already registered
        return
    tags_aware_registry.append(class_id)


def get_registered_tags_aware_classes():
    return [ get_resource_class(class_id)
             for class_id in tags_aware_registry ]
