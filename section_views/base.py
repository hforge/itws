# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2011 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2011 Henry Obein <henry@itaapy.com>
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
from itools.core import freeze, merge_dicts
from itools.datatypes import Integer, Boolean
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder_views import GoToSpecificDocument

# Import from itws
from itws.datatypes import SortBy_Enumerate
from itws.enumerates import SearchTypes_Enumerate
from itws.views import FieldsAutomaticEditView


class BaseSectionView_ConfigurationEdit(FieldsAutomaticEditView):

    @property
    def edit_fields(self):
        context = get_context()
        return context.resource.edit_fields


class BaseSectionView_Configuration(File):

    class_views = ['edit', 'back']

    edit_fields = freeze([])
    display_title = False

    # Hide in browse_content
    is_content = False


    def get_document_types(self):
        return []


    # Views
    edit = BaseSectionView_ConfigurationEdit(title=MSG(u'Configure view'))
    back = GoToSpecificDocument(
              title=MSG(u'Back to section'),
              adminbar_icon='/ui/icons/16x16/next.png',
              specific_document='../')



class BaseFeedView_Configuration(BaseSectionView_Configuration):

    class_schema = merge_dicts(
        BaseSectionView_Configuration.class_schema,
        view_search_on_current_folder=Boolean(source='metadata', default=True,
            title=MSG(u'Only on current section'), oneline=True),
        view_search_on_current_folder_recursive=Boolean(source='metadata',
            title=MSG(u'Recursively'), oneline=True, default=False),
        # search_class_id : only one authorized
        view_search_class_id=SearchTypes_Enumerate(source='metadata'),
        view_sort_by=SortBy_Enumerate(source='metadata', default='title',
            title=MSG(u'Sort by'), has_empty_option=False),
        view_reverse=Boolean(source='metadata', title=MSG(u'Reverse'),
                             oneline=True),
        view_batch_size=Integer(source='metadata', default=20,
                                title=MSG(u'Batch size')))


    edit_fields = ['view_batch_size', 'view_sort_by', 'view_reverse',
                   'view_search_on_current_folder',
                   'view_search_on_current_folder_recursive']
