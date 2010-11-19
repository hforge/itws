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

# Import from the Standard Library
from urllib import quote

# Import from itools
from itools.core import thingy_property
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import BaseView, get_context

# Import from ikaaro
from ikaaro.cc import SubscribeForm
from ikaaro.control_panel import ControlPanelMenu
from ikaaro.file_views import File_ExternalEdit_View
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.registry import get_document_types
from ikaaro.resource_views import DBResource_Links, DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.views import IconsView

# Import from itws
from utils import is_navigation_mode

context_menus = [ControlPanelMenu()]

class CPEditTags(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Tags')
    icon = 'theme.png'
    description = MSG(u'Edit tags')
    specific_document = 'tags'
    specific_view = 'browse_content'


class CPManageFooter(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Footer')
    icon = 'theme.png'
    description = MSG(u'Edit footer')
    specific_document = 'theme/footer'


class CPManageTurningFooter(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Turning Footer')
    icon = 'theme.png'
    description = MSG(u'Edit turning footer')
    specific_document = 'theme/turning-footer'


class CPEdit404(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'404')
    icon = 'theme.png'
    description = MSG(u'Edit 404')
    specific_document = 'theme/404'
    specific_view = 'edit'


class CPEditRobotsTXT(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Robots.txt')
    icon = 'theme.png'
    description = MSG(u'Edit robots.txt')
    specific_document = 'robots.txt'
    specific_view = 'edit'


class CPDBResource_CommitLog(DBResource_CommitLog):

    description = MSG(u'Commit log')
    icon = '../../itws-icons/48x48/git.png' # XXX
    context_menus = context_menus


class CPDBResource_Links(DBResource_Links):

    icon = 'links.png'
    description = MSG(u'List links to this resource')
    context_menus = context_menus


class CPDBResource_Backlinks(DBResource_Backlinks):

    icon = 'backlinks.png'
    description = MSG(u'List backlinks')
    context_menus = context_menus


class CPOrderItems(GoToSpecificDocument):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage TOC')
    icon = 'theme.png'
    description = MSG(u'Manage TOC')
    specific_document = 'order-section'
    context_menus = context_menus


class CPSubscribe(SubscribeForm):

    icon = 'theme.png'
    description = MSG(u'Subscribe to modifications')
    context_menus = context_menus


class CPExternalEdit(File_ExternalEdit_View):

    icon = 'theme.png'
    description = MSG(u'Edit file with an external editor')
    context_menus = context_menus


class CP_AdvanceNewResource(IconsView):

    access = 'is_allowed_to_add'
    title = MSG(u'Add an advance resource')
    description = MSG(u'Add a complex resource')
    icon = 'new.png'

    def get_document_types(self):
        forbidden_class_id = ['file', 'webpage', 'folder', 'section']
        return [x for x in get_document_types() if
                    x.class_id not in forbidden_class_id]


    def get_namespace(self, resource, context):
        items = [
            {'icon': '/ui/' + cls.class_icon48,
             'title': cls.class_title.gettext(),
             'description': cls.class_description.gettext(),
             'url': ';new_resource?type=%s' % quote(cls.class_id)
            }
            for cls in self.get_document_types() ]

        return {
            'batch': None,
            'items': items}


class CPFOSwitchMode(BaseView):

    access = 'is_allowed_to_edit'
    query_schema = {'mode': Boolean(default=False)}

    title = MSG(u'Change mode')
    icon = 'theme.png'

    @thingy_property
    def description(self):
        context = get_context()
        if is_navigation_mode(context):
            return MSG(u'Go to edition mode')
        return MSG(u'Go to navigation mode')


    def GET(self, resource, context):
        edit = context.query['mode']
        if edit:
            context.set_cookie('itws_fo_edit', '1')
        else:
            context.set_cookie('itws_fo_edit', '0')

        referer = context.get_referrer()
        if referer:
            # FIXME Check if referer is fo_switch_mode
            goto = referer
        else:
            goto = '/'

        return get_reference(goto)
