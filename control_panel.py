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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument


class CPEditTags(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Tags')
    icon = 'theme.png'
    description = MSG(u'Edit tags')
    specific_document = 'tags'
    specific_view = 'browse_content'


class CPManageFooter(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Footer')
    icon = 'theme.png'
    description = MSG(u'Edit footer')
    specific_document = 'footer'


class CPManageTurningFooter(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Turning Footer')
    icon = 'theme.png'
    description = MSG(u'Edit turning footer')
    specific_document = 'turning-footer'


class CPEdit404(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'404')
    icon = 'theme.png'
    description = MSG(u'Edit 404')
    specific_document = '404'


class CPEditRobotsTXT(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Robots.txt')
    icon = 'theme.png'
    description = MSG(u'Edit robots.txt')
    specific_document = 'robots.txt'
    specific_view = 'edit'
