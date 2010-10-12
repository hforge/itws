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
from itools.datatypes import String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import ImageSelectorWidget, MultilineWidget
from ikaaro.autoform import SelectWidget, TextWidget
from ikaaro.datatypes import Multilingual
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_Edit
from ikaaro.theme import Theme as BaseTheme

# Import from itws
from datatypes import NeutralClassSkin


class Theme_Edit(DBResource_Edit):

    def _get_schema(self, resource, context):
        return merge_dicts(DBResource_Edit._get_schema(self, resource, context),
                           custom_data=String,
                           breadcrumb_title=Multilingual,
                           banner_title=Multilingual,
                           banner_path=Multilingual,
                           class_skin=NeutralClassSkin(mandatory=True))


    def _get_widgets(self, resource, context):
        return (DBResource_Edit._get_widgets(self, resource, context) + [
            MultilineWidget('custom_data', title=MSG(u"Custom data"), rows=19, cols=69),
            TextWidget('breadcrumb_title', title=MSG(u'Breadcrumb title')),
            TextWidget('banner_title', title=MSG(u'Banner title'),
                       tip=MSG(u'(Use as banner if there is no image banner)')),
            ImageSelectorWidget('banner_path', title=MSG(u'Banner path'),
                                width=640),
            SelectWidget('class_skin', title=MSG(u'Skin'), has_empty_option=False)])



class Theme(BaseTheme):

    class_id = 'itws-theme'

    class_schema = merge_dicts(BaseTheme.class_schema,
         custom_data=String(source='metadata', default=''),
         breadcrumb_title=Multilingual(source='metadata'),
         banner_title=Multilingual(source='metadata', default=''),
         banner_path=Multilingual(source='metadata', default=''),
         class_skin=NeutralClassSkin(source='metadata', default='/ui/k2'))

    edit = Theme_Edit()



register_resource_class(Theme)
