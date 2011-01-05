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
from itools.core import thingy_property
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import BaseView, get_context

# Import from ikaaro
from ikaaro.cc import SubscribeForm
from ikaaro.control_panel import ControlPanelMenu, ControlPanel
from ikaaro.file_views import File_ExternalEdit_View
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.resource_views import DBResource_Links, DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog

# Import from itws
from utils import is_navigation_mode



###################################################
# Control panel Views
###################################################
class ITWS_ControlPanelMenu(ControlPanelMenu):

    title = MSG(u'Advanced')

    def get_items(self):
        items = super(ITWS_ControlPanelMenu, self).get_items()
        # Hook icons
        resource = self.resource
        for item in items:
            name = item['href'][1:] # remove ';'
            view = resource.get_view(name)
            if hasattr(view, 'itws_icon'):
                icon = '/ui/itws-icons/16x16/%s/' % view.itws_icon
                item['src'] = icon

        return items



class ITWS_ControlPanel(ControlPanel):

    title = MSG(u'Advanced')

    context_menus = [ITWS_ControlPanelMenu()]

    def get_namespace(self, resource, context):
        # XXX We override get_namespace just to fix problem
        # with icons uri
        proxy = super(ITWS_ControlPanel, self)
        namespace = proxy.get_namespace(resource, context)
        items = namespace['items']
        # Hook icons
        for item in items:
            name = item['url'][1:] # remove ';'
            view = resource.get_view(name)
            if hasattr(view, 'itws_icon'):
                icon = '/ui/itws-icons/48x48/%s/' % view.itws_icon
                item['icon'] = icon

        namespace['batch'] = None
        namespace['title'] = MSG(u'Control Panel')
        return namespace



###############################################
# Control panel items
###############################################

context_menus = [ITWS_ControlPanelMenu()]

class CPEditTags(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Tags')
    description = MSG(u'Edit tags')
    itws_icon = 'tags.png'
    specific_document = 'tags'
    specific_view = 'browse_content'



class CPEdit404(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'404')
    itws_icon = '404.png'
    description = MSG(u'Edit 404')
    specific_document = 'theme/404'
    specific_view = 'edit'



class CPEditRobotsTXT(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Robots.txt')
    itws_icon = 'robots.png'
    description = MSG(u'Edit robots.txt')
    specific_document = 'robots.txt'
    specific_view = 'edit'



class CPDBResource_CommitLog(DBResource_CommitLog):

    description = MSG(u'See last modifications')
    itws_icon = 'git.png'
    context_menus = context_menus



class CPDBResource_Links(DBResource_Links):

    description = MSG(u'List resources that links to this resource')
    itws_icon = 'links.png'

    context_menus = context_menus



class CPDBResource_Backlinks(DBResource_Backlinks):

    description = MSG(u'List backlinks of this resource')
    itws_icon = 'backlinks.png'

    context_menus = context_menus



class CPOrderItems(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    itws_icon = 'toc.png'

    title = MSG(u'Manage TOC')
    description = MSG(u'Order items in TOC of section')
    specific_document = 'order-section'
    context_menus = context_menus



class CPSubscribe(SubscribeForm):

    itws_icon = 'subscriptions.png'
    description = MSG(u'Subscribe to resources modifications')
    context_menus = context_menus



class CPExternalEdit(File_ExternalEdit_View):

    itws_icon = 'editor.png'
    description = MSG(u'Edit file with an external editor')
    context_menus = context_menus



class CPFOSwitchMode(BaseView):

    access = 'is_allowed_to_edit'
    query_schema = {'mode': Boolean(default=False)}

    title = MSG(u'Change mode')
    itws_icon = 'switch.png'

    @thingy_property
    def description(self):
        context = get_context()
        if is_navigation_mode(context):
            return MSG(u'Go to edition mode')
        return MSG(u'Go to navigation mode')


    def GET(self, resource, context):
        if context.get_cookie('itws_fo_edit', Boolean):
            context.set_cookie('itws_fo_edit', '0')
        else:
            context.set_cookie('itws_fo_edit', '1')

        referer = context.get_referrer()
        if referer:
            ref = get_reference(referer)
            if ref.path == '/;fo_switch_mode':
                # Do no loop
                goto = '/'
            else:
                goto = referer
        else:
            goto = '/'

        return get_reference(goto)
