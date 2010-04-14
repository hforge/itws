# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
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
from itools.datatypes import Integer, Unicode, Enumerate, String
from itools.gettext import MSG
from itools.web import get_context
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.utils import get_base_path_query
from ikaaro.registry import get_document_types



class PositiveInteger(Integer):

    @staticmethod
    def is_valid(value):
        return value >= 0



class PositiveIntegerNotNull(Integer):

    @staticmethod
    def is_valid(value):
        return value > 0



class UnicodeString(Unicode):
    """Usefull to implement multlingual String"""

    @staticmethod
    def is_valid(value):
        if type(value) is str:
            return True
        # Check if the string representation of value is a string
        try:
            str(value)
        except UnicodeEncodeError:
            return False
        return True



class MultilingualString(String):

    @staticmethod
    def is_empty(value):
        """This is used by the multilingual code"""
        return value == ''



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



class FormatEnumerate(Enumerate):

    format = None
    container = None
    query_container = None

    @classmethod
    def get_options(cls):
        if cls.format is None or cls.query_container is None \
                or cls.container is None:
            msg = (u'the parameters "format", "container" and '
                   u'"query_container" must be defined')
            raise ValueError, msg

        options = []
        abspath = cls.container.get_abspath()
        query_container_abspath = cls.query_container.get_abspath()
        query = AndQuery(get_base_path_query(str(query_container_abspath)),
                         PhraseQuery('format', cls.format))
        context = get_context()
        root = context.root
        results = root.search(query)
        for doc in results.get_documents(sort_by='title'):
            options.append({'name': abspath.get_pathto(doc.abspath),
                            'value': doc.title})
        return options



class NeutralClassSkin(Enumerate):

    options = [{'name': '/ui/neutral', 'value': u'Neutral 1'},
               {'name': '/ui/neutral2', 'value': u"Neutral 2"}]



class RSSFeedsFormats(Enumerate):

    options = [{'name': 'news', 'value': MSG('News')},
               {'name': 'slide', 'value': MSG(u'Slide')},
               {'name': 'section', 'value': MSG(u'Section')}]

