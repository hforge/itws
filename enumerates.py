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
from itools.database import PhraseQuery, AndQuery, NotQuery
from itools.datatypes import Enumerate
from itools.web import get_context

# Import from ikaaro
from ikaaro.registry import get_resource_class
#resources_registry
from ikaaro.utils import get_base_path_query
from ikaaro.website import WebSite


class SearchTypes_Enumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        resource = context.resource
        view = context.view
        # Get the container
        container = view._get_container(resource, context)
        container_abspath = container.get_canonical_path()

        # 1. Build the query of all objects to search
        if view.search_on_current_folder_recursive:
            query = get_base_path_query(str(container_abspath))
        else:
            query = PhraseQuery('parent_path', str(container_abspath))

        # Exclude '/theme/'
        if isinstance(resource, WebSite):
            theme_path = container_abspath.resolve_name('theme')
            theme = get_base_path_query(str(theme_path), True)
            query = AndQuery(query, NotQuery(theme))

        if view.ignore_internal_resources:
            query = AndQuery(query, PhraseQuery('is_content', True))

        if view.ignore_box_aware:
            query = AndQuery(query, NotQuery(PhraseQuery('box_aware', True)))

        print query
        # 2. Compute children_formats
        children_formats = set()
        for child in root.search(query).get_documents():
            children_formats.add(child.format)

        # 3. Do not show two options with the same title
        formats = {}
        for type in children_formats:
            cls = get_resource_class(type)
            title = cls.class_title.gettext()
            formats.setdefault(title, []).append(type)

        # 4. Build the namespace
        types = []
        for title, type in formats.items():
            type = ','.join(type)
            types.append({'name': type, 'value': title})
        types.sort(key=lambda x: x['value'].lower())

        return types
