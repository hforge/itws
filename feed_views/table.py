# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.web import get_context

# Import from ikaaro
from ikaaro.views import BrowseForm

# Import from itws
from base import Feed_View


class TableFeed_View(Feed_View):
    """
    It's a BrowseFormbut with Feed_View API
    """

    content_template = '/ui/generic/browse_table.xml'

    @property
    def content_keys(self):
        context = get_context()
        resource = context.resource
        columns = self.get_table_columns(resource, context)
        print [x for x, y in columns]
        return [x for x, y in columns]


    def get_content_namespace(self, resource, context, items):
        return BrowseForm.get_table_namespace(self, resource, context, items)


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        # Default columns
        if column == 'name':
            name = item_brain.name
            return name, name
        elif column == 'title':
            return item_resource.get_title(), context.get_link(item_resource)
        # Super
        proxy = super(TableFeed_View, self)
        return proxy.get_item_value(resource, context, item, column)
