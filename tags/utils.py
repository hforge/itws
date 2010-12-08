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
from itools.database import PhraseQuery, OrQuery, AndQuery

# Import from ikaaro
from ikaaro.utils import get_base_path_query



##########################################################################
# API To get items
##########################################################################

def get_tagaware_query_terms(context, on_current_folder=False,
                             formats=[], state=None, tags=[]):
    query = []
    # Current website
    site_root = context.resource.get_site_root()
    abspath = site_root.get_abspath()
    query.append(get_base_path_query(str(abspath)))

    if on_current_folder is True:
        abspath = context.resource.get_canonical_path()
        query.append(PhraseQuery('parent_path', str(abspath)))
    if formats:
        q = [PhraseQuery('format', x) for x in formats]
        if len(q) > 1:
            query.append(OrQuery(*q))
        else:
            query.append(q[0])
    if state:
        query.append(PhraseQuery('workflow_state', state))
    if tags:
        tags_query = [ PhraseQuery('tags', tag) for tag in tags ]
        if len(tags_query):
            tags_query = OrQuery(*tags_query)
        query.append(tags_query)
    return query


def get_tagaware_items(context, state='public', on_current_folder=False,
             formats=[], language=None,
             number=None, tags=[], brain_only=False, brain_and_docs=False):
    query = get_tagaware_query_terms(context, on_current_folder, formats,
                                     state, tags)
    if language is None:
        # Get Language
        site_root = context.site_root
        ws_languages = site_root.get_property('website_languages')
        accept = context.accept_language
        language = accept.select_language(ws_languages)

    # size
    size = 0
    if number:
        size = number

    root = context.root
    results = root.search(AndQuery(*query))
    documents = results.get_documents(sort_by='pub_datetime',
                                      reverse=True, size=size)
    if brain_only:
        return documents

    if brain_and_docs:
        return [(doc, root.get_resource(doc.abspath))
                         for doc in documents ]

    return [ root.get_resource(doc.abspath)
             for doc in documents ]
