# -*- coding: UTF-8 -*-
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
from itools.web import STLView
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import File
from ikaaro.folder import Folder

# Import from itws
from base_views import ContentBar_View, SideBar_View
from bar_aware import ContentBarAware, SideBarAware
from repository import Repository
from itws.views import AdvanceGoToSpecificDocument


class WSDataFolder(SideBarAware, ContentBarAware, Folder):

    class_id = 'neutral-ws-data'
    class_version = '20101012'
    class_title = MSG(u'Website data folder')
    class_views = ['commit_log']
    class_schema = Folder.class_schema


    __fixed_handlers__ = [SideBarAware.sidebar_name,
                          'order-resources', # FIXME
                          ContentBarAware.contentbar_name]


    def init_resource(self, **kw):
        # Initialize ikaaro website (Parent class)
        Folder.init_resource(self, **kw)
        # Sidebar Aware
        SideBarAware.init_resource(self, **kw)
        # ContentBar Aware
        ContentBarAware.init_resource(self, **kw)


    def get_document_types(self):
        return [File, Folder]


    def get_ordered_names(self, context=None):
        return self.parent.get_ordered_names(context)




class HomePage_BarAware(object):
    """
    All websites that contains homePage_BarAware
    contains a folder 'ws-data' that allow to sort
    sidebar and contenbar of homepage
    """

    __fixed_handlers__ = ['ws-data']
    class_control_panel = []

    sidebar_name = 'ws-data/%s' % SideBarAware.sidebar_name
    contentbar_name = 'ws-data/%s' % ContentBarAware.contentbar_name

    ####################################
    ## Views
    ####################################

    # Sidebar views
    order_contentbar = AdvanceGoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=contentbar_name,
        keep_query=True,
        title=MSG(u'Order Central Part Boxes'))
    order_sidebar = AdvanceGoToSpecificDocument(
        access='is_allowed_to_edit',
        specific_document=sidebar_name,
        keep_query=True,
        title=MSG(u'Order Sidebar Boxes'))

    # New sidebar/contenbar resource
    new_sidebar_resource = AdvanceGoToSpecificDocument(
        access='is_allowed_to_edit',
        keep_query=True,
        specific_document='%s/;add_box' % sidebar_name,
        title=MSG(u'Order Sidebar Boxes'))
    new_contentbar_resource = AdvanceGoToSpecificDocument(
            access='is_allowed_to_edit',
            keep_query=True,
            specific_document='%s/;add_box' % contentbar_name,
            title=MSG(u'Add Central Part Box'))


    def init_resource(self, **kw):
        self.make_resource('ws-data', self.wsdatafolder_class)



class NeutralWS_ContentBar_View(ContentBar_View):

    order_name = 'ws-data/order-contentbar'

    def _get_repository(self, resource, context):
        return resource.get_resource('ws-data')




class NeutralWS_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'Website View')
    template = '/ui/common/Neutral_view.xml'

    subviews = {'contentbar_view': NeutralWS_ContentBar_View(),
                'sidebar_view': SideBar_View(order_name='ws-data/order-sidebar')}

    def get_subviews_value(self, resource, context, view_name):
        view = self.subviews.get(view_name)
        if view is None:
            return None
        return view.GET(resource, context)


    def get_namespace(self, resource, context):
        namespace = {}

        # Subviews
        for view_name in self.subviews.keys():
            namespace[view_name] = self.get_subviews_value(resource,
                                                           context, view_name)

        return namespace



class Website_BarAware(object):
    """
    A website is Website_BarAware so it contain's a repository
    """

    class_control_panel = []
    __fixed_handlers__ = ['repository']

    wsdatafolder_class = WSDataFolder

    def init_resource(self, **kw):
        # Create repository
        self.make_resource('repository', Repository)


    view = NeutralWS_View()
