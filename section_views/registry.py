# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Henry Obein <henry@itaapy.com>
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
from itools.datatypes import Enumerate



##############################
# Registry
##############################
section_views_registry = {}

def register_section_view(view_class):
    section_views_registry[view_class.view_name] = view_class


def get_section_views_registry():
    return freeze(section_views_registry)


def get_section_view_from_registry(name):
    return section_views_registry[name]()


class SectionViews_Enumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        for cls in get_section_views_registry().values():
            options.append({'name': cls.view_name,
                            'value': cls.view_title})
        return options
