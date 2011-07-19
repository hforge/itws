# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.core import freeze

# Import from itws
from itws.views import FieldsAutomaticEditView, EditView


class Section_Edit(EditView, FieldsAutomaticEditView):
    """ EditView gives "view" helper. """

    edit_fields = freeze(['title', 'description', 'view',
                          'tags', 'thumbnail', 'pub_datetime'])

    def action(self, resource, context, form):
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return
        EditView.action(self, resource, context, form)
        return FieldsAutomaticEditView.action(self, resource, context, form)
