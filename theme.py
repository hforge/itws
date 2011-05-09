# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2011 Nicolas Deram <nicolas@itaapy.com>
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
from itools.core import freeze, get_abspath, merge_dicts
from itools.csv import Property
from itools.datatypes import String, URI
from itools.gettext import MSG
from itools.handlers import ro_database, File as FileHandler

# Import from ikaaro
from ikaaro.autoform import ImageSelectorWidget, MultilineWidget
from ikaaro.autoform import SelectWidget, TextWidget
from ikaaro.datatypes import Multilingual
from ikaaro.file import Image
from ikaaro.folder_views import Folder_BrowseContent, GoToSpecificDocument
from ikaaro.registry import register_resource_class
from ikaaro.theme import Theme as BaseTheme
from ikaaro.theme_views import Theme_Edit as BaseTheme_Edit

# Import from itws
from control_panel import ITWS_ControlPanel
from datatypes import NeutralClassSkin
from footer import FooterFolder
from notfoundpage import NotFoundPage
from turning_footer import TurningFooterFolder



class Theme_Edit(BaseTheme_Edit):

    title = MSG(u'Edit theme')


    def _get_schema(self, resource, context):
        return freeze(merge_dicts(
            BaseTheme_Edit._get_schema(self, resource, context),
            custom_data=String,
            banner_title=Multilingual,
            banner_path=URI(multilingual=True,
                            parameters_schema={'lang': String}),
            class_skin=NeutralClassSkin(mandatory=True)))


    def _get_widgets(self, resource, context):
        # Remove logo widget
        return freeze(
            BaseTheme_Edit._get_widgets(self, resource, context)[:2]
            + [MultilineWidget('custom_data', title=MSG(u"Custom data"),
                               rows=19, cols=69),
               TextWidget('banner_title', title=MSG(u'Banner title'),
                      tip=MSG(u'(Use as banner if there is no image banner)')),
               ImageSelectorWidget('banner_path', title=MSG(u'Banner path'),
                                   width=640),
               SelectWidget('class_skin', title=MSG(u'Skin'),
                            has_empty_option=False)])



class Theme(BaseTheme):

    class_id = 'itws-theme'

    __fixed_handlers__ = (BaseTheme.__fixed_handlers__
                          + ['404', 'turning-footer', 'footer'])

    class_schema = merge_dicts(BaseTheme.class_schema,
         custom_data=String(source='metadata', default=''),
         banner_title=Multilingual(source='metadata', default=''),
         banner_path=URI(source='metadata', multilingual=True,
                         parameters_schema={'lang': String}),
         class_skin=NeutralClassSkin(source='metadata', default='/ui/k2'))

    class_views = ['edit', 'edit_css', 'edit_menu', 'edit_footer',
                   'edit_turning_footer', 'browse_content', 'control_panel']
    class_control_panel = ['links', 'backlinks', 'commit_log']

    is_content = True

    def init_resource(self, **kw):
        # Init resource
        BaseTheme.init_resource(self, **kw)
        # Get language
        website = self.parent
        language = website.get_default_language()
        # Banner (background set with CSS)
        path = get_abspath('data/k2-banner-ties.jpg')
        image = ro_database.get_handler(path, FileHandler)
        self.make_resource('banner-itws', Image, body=image.to_str(),
                           extension='jpg', filename='banner-itws.jpg',
                           format='image/jpeg', state='public')
        # Set banner title
        vhosts = website.get_property('vhosts')
        if vhosts:
            banner_title = vhosts[0]
        else:
            banner_title = website.get_title()
        self.set_property('banner_title', banner_title, language=language)
        # Drop logo property since itws uses banner_path property
        self.del_property('logo')
        # CSS file
        # TODO Add an API in ikaaro that allow to easily change CSS...
        path = get_abspath('ui/themes/style.css')
        body = open(path).read()
        style = self.get_resource('style')
        style.handler.load_state_from_string(body)
        style.handler.set_changed()
        # Custom 404
        self.make_resource('404', NotFoundPage)
        # Add footer
        self.make_resource('footer', FooterFolder)
        menu = self.get_resource('footer/menu')
        title = Property(MSG(u'Powered by itws').gettext(),
                         language=language)
        menu.add_new_record({'title': title, 'path': '/about-itws'})
        title = Property(MSG(u'Contact us').gettext(),
                         language=language)
        menu.add_new_record({'title': title, 'path': '/;contact'})
        # Turning footer
        self.make_resource('turning-footer', TurningFooterFolder)


    # Views
    edit = Theme_Edit()
    control_panel = ITWS_ControlPanel()
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    edit_footer = GoToSpecificDocument(
            access='is_allowed_to_edit',
            specific_document='footer/menu',
            title=MSG(u'Edit footer'))
    edit_turning_footer = GoToSpecificDocument(
            access='is_allowed_to_edit',
            specific_document='turning-footer/menu',
            title=MSG(u'Edit turning footer'))



# Register
register_resource_class(Theme)
