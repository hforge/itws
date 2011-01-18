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
from itools.core import freeze, merge_dicts
from itools.datatypes import DateTime, String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.autoform import timestamp_widget, MultilineWidget
from ikaaro.control_panel import ControlPanel
from ikaaro.file_views import File_Download
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.text import Text
from ikaaro.text_views import Text_View, Text_Edit



RobotsTxt_body = """
User-agent: *
Disallow: /theme
Disallow: /repository
"""


class RobotsTxt_Edit(Text_Edit):

    schema = freeze({'timestamp': DateTime(readonly=True), 'data': String})
    widgets = freeze([
        timestamp_widget,
        MultilineWidget('data', title=MSG(u"Content"), rows=19, cols=69)])


    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        data = form['data']
        resource.handler.load_state_from_string(data)
        # Ok
        context.message = messages.MSG_CHANGES_SAVED



class RobotsTxt(Text):

    class_id = 'robotstxt'
    class_title = MSG(u'Robots exclusion standard')
    class_views = ['view', 'edit', 'externaledit', 'download',
                   'upload', 'edit_state', 'commit_log', 'control_panel']

    class_schema = merge_dicts(
            Text.class_schema,
            state=String(source='metadata', default='public'))


    def init_resource(self, **kw):
        kw['extension'] = 'txt'
        kw['body'] = RobotsTxt_body
        Text.init_resource(self, **kw)


    # Views
    control_panel = GoToSpecificDocument(specific_document='../',
                                         specific_view='control_panel',
                                         title=ControlPanel.title)
    download = File_Download(access=True)
    edit = RobotsTxt_Edit()
    view = Text_View(access='is_allowed_to_edit')
