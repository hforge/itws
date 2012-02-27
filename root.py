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

# Import from standard library
import traceback

# Import from itools
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.config import get_config
from ikaaro.root import Root as BaseRoot


class Root(BaseRoot):

    class_id = 'iKaaro'

    def internal_server_error(self, context):
        # Get administrator mail
        config = get_config(context.server.target)
        email = config.get_value('admin-email')
        # We send an email to administrator
        if email:
            headers = u'\n'.join([u'%s => %s' % (x, y)
                                    for x, y in context.get_headers()])
            subject = MSG(u'Internal server error').gettext()
            text = u'%s\n\n%s\n\n%s' % (context.uri,
                                        traceback.format_exc(),
                                        headers)
            self.send_email(email, subject, text=text)
        proxy = super(Root, self)
        return proxy.internal_server_error(context)
