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

# Import from itools
from itools.core import get_abspath

# Import from ikaaro
from ikaaro.skins import register_skin

# Import from itws
from base import Feed_View
from browse_navigator import Browse_Navigator, Browse_Navigator_Rename
from collection import Search_View, Details_View
from collection import DetailsWithoutPicture_View, Title_View
from futur import FieldsFeed_View, FieldsTableFeed_View
from multiple import MultipleFeed_View
from table import TableFeed_View

# Register skin
register_skin('feed_views', get_abspath('../ui/feed_views/'))

# Silent pyflakes
Feed_View, Details_View, DetailsWithoutPicture_View,
Browse_Navigator, Browse_Navigator_Rename, MultipleFeed_View, Search_View, Title_View
TableFeed_View, FieldsFeed_View, FieldsTableFeed_View
