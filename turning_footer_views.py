# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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

# Import from the Standard Library
from random import choice

# Import from itools
from itools.datatypes import Unicode, Integer
from itools.gettext import MSG
from itools.stl import set_prefix
from itools.web import STLView

# Import from ikaaro
from ikaaro.forms import XHTMLBody, HTMLBody
from ikaaro.table import OrderedTable_View, Table_EditRecord



class TurningFooterFile_View(OrderedTable_View):

    schema = {
        'ids': Integer(multiple=True, mandatory=True),
    }

    def get_table_columns(self, resource, context):
        columns = [
            ('checkbox', None),
            ('id', MSG(u'id'))]
        # From the schema
        for widget in self.get_widgets(resource, context):
            column = (widget.name, getattr(widget, 'title', widget.name))
            columns.append(column)
        return columns


    def get_item_value(self, resource, context, item, column):
        value = OrderedTable_View.get_item_value(self, resource, context,
                                                 item, column)
        if column == 'data':
            return XHTMLBody.decode(Unicode.encode(value))
        return OrderedTable_View.get_item_value(self, resource, context, item,
                                                column)



class TurningFooterFile_EditRecord(Table_EditRecord):

    def get_value(self, resource, context, name, datatype):
        if name == 'data':
            handler = resource.get_handler()
            id = context.query['id']
            record = handler.get_record(id)
            language = resource.get_content_language(context)
            value = handler.get_record_value(record, name, language=language)
            # HTML for Tiny MCE
            return HTMLBody.decode(value)
        return Table_EditRecord.get_value(self, resource, context, name,
                                          datatype)



class TurningFooterFolder_View(STLView):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    template = '/ui/common/TurningFooterFolder_view.xml'

    def get_namespace(self, resource, context):
        namespace = {}
        # title
        title = resource.get_title(fallback=False)
        menu = resource.get_resource(resource.order_path)
        handler = menu.handler

        is_active = resource.get_property('active')
        ids = list(handler.get_record_ids_in_order())
        if not ids or not is_active:
            return {'content': None,
                    'title': title,
                    'display': False}

        if resource.get_property('random'):
            id = choice(ids)
        else:
            id = ids[0]

        record = handler.get_record(id)
        data = handler.get_record_value(record, 'data')
        data = Unicode.encode(data)
        data = XHTMLBody(sanitize_html=False).decode(data)
        here = context.resource
        content = set_prefix(data, prefix='%s/' % here.get_pathto(menu))
        return {'content': content,
                'title': title,
                'display': True}
