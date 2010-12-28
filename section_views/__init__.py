# -*- coding: UTF-8 -*-
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

import base # XXX
from composite import Section_Composite_View
from images import ImagesView_View
from registry import get_section_view_from_registry, register_section_view
from registry import SectionViews_Enumerate, section_views_registry
from tagsaware import TagsAwareView_View

for view in [ImagesView_View,
             Section_Composite_View,
             TagsAwareView_View]:
    register_section_view(view)

# Silent pyflakes
get_section_view_from_registry, SectionViews_Enumerate, section_views_registry
