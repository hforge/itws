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

# Import from ikaaro
from ikaaro.autoform import get_default_widget

# Import from itws
from base import Feed_View
from table import TableFeed_View

###################################################################
# Feed_View where we do not define search_schema
# and search_widgets (or table_columns) but just a list of fields
# We automaticaly get schema from search_cls schema and
# widgets from get_default_widgets. Example:
#
#    search_fields = ['title']
#    table_fields = ['title', 'firstname']
#
# See the bug 1203 for the concept:
# http://bugs.hforge.org/show_bug.cgi?id=1203
###################################################################


class BaseFieldsFeed_View(object):

    search_cls = None
    search_fields = []

    @property
    def search_schema(self):
        kw = {}
        schema = self.search_cls.class_schema
        for name in self.search_fields:
            kw[name] = schema[name]
        return kw


    @property
    def search_widgets(self):
        widgets = []
        schema = self.search_cls.class_schema
        for name in self.search_fields:
            datatype = schema[name]
            title = getattr(datatype, 'title', name)
            widget = get_default_widget(datatype)(name, title=title)
            widgets.append(widget)
        return widgets



class FieldsTableFeed_View(BaseFieldsFeed_View, TableFeed_View):

    table_fields = []

    def get_table_columns(self, resource, context):
        columns = []
        schema = self.search_cls.class_schema
        for name in self.table_fields:
            datatype = schema[name]
            title = getattr(datatype, 'title', name)
            columns.append((name, title))
        return columns


class FieldsFeed_View(BaseFieldsFeed_View, Feed_View):

    pass
