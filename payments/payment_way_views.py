# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.core import freeze
from itools.datatypes import Unicode, Boolean, DateTime
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import XHTMLBody, ImageSelectorWidget, TextWidget
from ikaaro.autoform import RTEWidget, RadioWidget
from ikaaro.autoform import timestamp_widget
from ikaaro.resource_views import DBResource_Edit

# Import from itws
from itws.datatypes import ImagePathDataType


class PaymentWay_Configure(DBResource_Edit):
    access = 'is_admin'

    schema = freeze({
        'timestamp': DateTime(readonly=True),
        'title': Unicode(mandatory=True, multilingual=True),
        'logo': ImagePathDataType(multilingual=True),
        'enabled': Boolean(mandatory=True),
        'data': XHTMLBody(multilingual=True)})

    widgets = freeze([
        timestamp_widget,
        TextWidget('title', title=MSG(u'Title')),
        ImageSelectorWidget('logo',  title=MSG(u'Logo')),
        RadioWidget('enabled', title=MSG(u'Enabled?')),
        RTEWidget('data', title=MSG(u"Description"))])
