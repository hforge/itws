# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
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
from itools.web import get_context

# Import from itws
from utils import get_registered_tags_aware_classes



class TagsList(Enumerate):

    @staticmethod
    def decode(value):
        if not value:
            return None
        return str(value)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value)


    @classmethod
    def get_options(cls):
        context = get_context()
        site_root = context.site_root
        tags_folder = site_root.get_resource('tags', soft=True)
        if tags_folder is None:
            return []
        context = get_context()
        options = [ {'name': brain.name,
                     'value': brain.title or brain.name}
                    for brain in tags_folder.get_tag_brains(context) ]

        return options



class TagsAwareClassEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        _classes = get_registered_tags_aware_classes()
        for _cls in _classes:
            title = _cls.class_title.gettext()
            options.append({'name': _cls.class_id,
                            'value': title.encode('utf-8')})
        options.sort(lambda x, y: cmp(x['value'], y['value']))
        return options

