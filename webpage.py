# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
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
from itools.datatypes import Boolean

# Import from ikaaro
from ikaaro.registry import register_resource_class, register_document_type
from ikaaro.webpage import WebPage as BaseWebPage

# Import from itws
from control_panel import CPDBResource_CommitLog, CPDBResource_Links
from control_panel import CPDBResource_Backlinks, CPSubscribe
from control_panel import CPExternalEdit, ITWS_ControlPanel
from tags import TagsAware, register_tags_aware
from webpage_views import WebPage_Edit, WebPage_View



class WebPage(BaseWebPage, TagsAware):
    """
    We override the ikaaro webpage to:
      - Override RTE to allow to add iframe
      - Add tags to webpages
      - Add publication date and time
      - Allow to configure if we display title or not
    """

    # TODO When publish webpage add a mechanism to check public pages
    # XXX We override ikaaro class_id

    class_id = 'webpage'
    class_version = '20100621'
    class_schema = merge_dicts(BaseWebPage.class_schema,
                               TagsAware.class_schema,
                               display_title=Boolean(source='metadata',
                                                     default=True))

    class_views = ['view', 'edit', 'control_panel']

    class_control_panel = ['externaledit', 'subscribe',
                           'links', 'backlinks', 'commit_log']


    def get_catalog_values(self):
        return merge_dicts(BaseWebPage.get_catalog_values(self),
                           TagsAware.get_catalog_values(self))

    #########################################################
    # Links API
    #########################################################
    def get_links(self):
        links = BaseWebPage.get_links(self)
        links.update(TagsAware.get_links(self))
        return links


    def update_links(self, source, target):
        BaseWebPage.update_links(self, source, target)
        TagsAware.update_links(self, source, target)


    def update_relative_links(self, source):
        BaseWebPage.update_relative_links(self, source)
        TagsAware.update_relative_links(self, source)


    ##########################
    # Views
    ##########################
    edit = WebPage_Edit()
    view = WebPage_View()
    control_panel = ITWS_ControlPanel()

    # Control panel
    commit_log = CPDBResource_CommitLog(access='is_allowed_to_edit')
    links = CPDBResource_Links()
    backlinks = CPDBResource_Backlinks()
    subscribe = CPSubscribe()
    externaledit = CPExternalEdit()



register_resource_class(WebPage, format='application/xhtml+xml')
register_document_type(WebPage)
register_tags_aware(WebPage)
