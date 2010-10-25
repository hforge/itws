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
from itools.datatypes import Enumerate

# Import from ikaaro
from ikaaro.registry import get_document_types


class TagsAwareClassEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        # Import from itws
        from tags import TagsAware

        options = []
        _classes = get_document_types(TagsAware.class_id)
        for _cls in _classes:
            title = _cls.class_title.gettext()
            options.append({'name': _cls.class_id,
                            'value': title.encode('utf-8')})
        options.sort(lambda x, y: cmp(x['value'], y['value']))
        return options

