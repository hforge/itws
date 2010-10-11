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
from itools.core import merge_dicts
from itools.datatypes import Integer
from itools.gettext import MSG
from itools.xapian import OrQuery, PhraseQuery

# Import from ikaaro
from ikaaro.buttons import PublishButton, RetireButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.resource_ import DBResource
from ikaaro.views import CompositeForm


############################################################
# View that list links and backlinks
############################################################

class DBResource_Links(Folder_BrowseContent):
    """Links are the list of resources used by this resource."""

    access = 'is_allowed_to_edit'
    title = MSG(u"Links")
    icon = 'rename.png'

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               batch_size=Integer(default=0))

    search_template = None
    search_schema = {}


    def get_items(self, resource, context):
        links = resource.get_links()
        links = list(set(links))
        query = OrQuery(*[ PhraseQuery('abspath', link)
                           for link in links ])
        return context.root.search(query)


    def action_links_publish(self, resource, context, form):
        Folder_BrowseContent.action_publish(self, resource, context, form)


    def action_links_retire(self, resource, context, form):
        Folder_BrowseContent.action_retire(self, resource, context, form)


    table_actions = [PublishButton(name='links_publish'),
                     RetireButton(name='links_retire')]



class DBResource_Backlinks(DBResource_Links):
    """Backlinks are the list of resources pointing to this resource. This
    view answers the question "where is this resource used?" You'll see all
    WebPages (for example) referencing it. If the list is empty, you can
    consider it is "orphan".
    """

    title = MSG(u"Backlinks")
    query_schema = {}


    def get_table_columns(self, resource, context):
        cols = DBResource_Links.get_table_columns(self, resource, context)
        return [ col for col in cols if col[0] != 'checkbox' ]


    def get_items(self, resource, context):
        query = PhraseQuery('links', str(resource.get_canonical_path()))
        return context.root.search(query)


    table_actions = []



class DBResource_CompositeLinks(CompositeForm):

    title = MSG(u'Links/Backlinks')
    access = 'is_allowed_to_edit'
    template = '/ui/common/cascade.xml'
    subviews = [ DBResource_Links(), DBResource_Backlinks() ]


    def get_namespace(self, resource, context):
        views = []
        for view in self.subviews:
            views.append({'title': view.title,
                          'view': view.GET(resource, context)})
        return {'views': views}




# Override DBResource backlinks view
DBResource.backlinks = DBResource_CompositeLinks()
