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

##########################################################################
# API To get items
##########################################################################

def get_tagaware_query_terms(on_current_folder=False,
                             class_id=None, state=None, tags=[]):
    query = []
    # XXX
    #if on_current_folder is True:
    #    abspath = self.get_canonical_path()
    #    query.append(PhraseQuery('parent_path', str(abspath)))
    if class_id:
        query.append(PhraseQuery('format', class_id))
    if state:
        query.append(PhraseQuery('workflow_state', state))
    if tags:
        tags_query = [ PhraseQuery('tags', tag) for tag in tags ]
        if len(tags_query):
            tags_query = OrQuery(*tags_query)
        query.append(tags_query)
    return query


def get_tagaware_items(context, state='public', on_current_folder=False,
             class_id=None, language=None,
             number=None, tags=[], brain_only=False, brain_and_docs=False):
    query = get_tagaware_query_terms(on_current_folder, class_id, state, tags)
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
