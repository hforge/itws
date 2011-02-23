# -*- coding: UTF-8 -*-
# Copyright (C) 2007, 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2010 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import from Standard Library
import sys

# Import from itools
from itools.core import get_abspath, get_version
from itools.gettext import register_domain

# Import from ikaaro
from ikaaro.skins import register_skin
from ikaaro.user import User

import about
import bar
import news
import feed_views
import OPML
import sitemap
import skin
import theme
import turning_footer
import webpage
import widgets
import ws_neutral
import monkey_patch

# Import obsolete if command is icms-update.py
if sys.argv[0].endswith('icms-update.py'):
    import obsolete
    print 'Imported', obsolete.__name__

# Make the product version available to Python code
__version__ = get_version()

# Register the itws domain
register_domain('itws', get_abspath('locale'))

# Override User is_allowed_to_view
User.is_allowed_to_view = User.is_allowed_to_edit

# Silent pyflakes
skin, about, OPML, bar, sitemap, turning_footer, ws_neutral, webpage,
widgets, theme, feed_views, news, monkey_patch

register_skin('itws-icons', get_abspath('ui/itws-icons'))
