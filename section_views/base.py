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
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument

# Import from itws
from itws.views import AutomaticEditView


class BaseSectionView_Configuration(Folder):

    class_views = ['edit', 'back']

    edit_schema = {}
    edit_widgets = []
    display_title = False

    def get_document_types(self):
        return []


    # Views
    edit = AutomaticEditView(title=MSG(u'Configure view'))
    back = GoToSpecificDocument(
              title=MSG(u'Back to section'),
              adminbar_icon='/ui/icons/16x16/next.png',
              specific_document='../')
