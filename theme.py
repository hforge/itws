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
from itools.core import merge_dicts, get_abspath
from itools.csv import Property
from itools.datatypes import PathDataType, String
from itools.gettext import MSG
from itools.handlers import ro_database, File as FileHandler
from itools.uri import Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.autoform import ImageSelectorWidget, MultilineWidget
from ikaaro.autoform import SelectWidget, TextWidget
from ikaaro.datatypes import Multilingual
from ikaaro.file import Image
from ikaaro.registry import register_resource_class
from ikaaro.theme import Theme as BaseTheme, Theme_Edit as BaseTheme_Edit

# Import from itws
from datatypes import NeutralClassSkin
from footer import FooterFolder
from notfoundpage import NotFoundPage
from turning_footer import TurningFooterFolder



class Theme_Edit(BaseTheme_Edit):

    def _get_schema(self, resource, context):
        return merge_dicts(BaseTheme_Edit._get_schema(self, resource, context),
                           custom_data=String,
                           breadcrumb_title=Multilingual,
                           banner_title=Multilingual,
                           banner_path=PathDataType(multilingual=True,
                                          parameters_schema={'lang': String}),
                           class_skin=NeutralClassSkin(mandatory=True))


    def _get_widgets(self, resource, context):
        # Remove logo widget
        return (BaseTheme_Edit._get_widgets(self, resource, context)[:2] + [
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
         banner_path=PathDataType(source='metadata', multilingual=True,
                                  parameters_schema={'lang': String}),
         class_skin=NeutralClassSkin(source='metadata', default='/ui/k2'))

    # XXX Migration
    # Add an API in ikaaro that allow to easily change CSS...

    def init_resource(self, **kw):
        # Init resource
        BaseTheme.init_resource(self, **kw)
        # Get language
        website = self.parent
        language = website.get_default_language()
        # Banner
        path = get_abspath('data/k2-banner-ties.jpg')
        image = ro_database.get_handler(path, FileHandler)
        self.make_resource('banner-itws', Image, body=image.to_str(),
                           extension='jpg', filename='banner-itws.jpg',
                           format='image/jpeg', state='public')
        self.set_property('banner_path', '/theme/banner-itws/', language=language)
        # Set banner title
        vhosts = website.get_property('vhosts')
        if vhosts:
            banner_title = vhosts[0]
        else:
            banner_title = website.get_title()
        self.set_property('banner_title', banner_title, language=language)
        # CSS file
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


    ##########################
    # Links API
    ##########################

    def get_links(self):
        links = BaseTheme.get_links(self)
        base = self.get_canonical_path()

        # banner_path
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        for language in available_languages:
            path = self.get_property('banner_path', language=language)
            links.add(str(base.resolve2(path)))

        return links


    def update_links(self, source, target):
        # FIXME BaseTheme does not take into account 'child'
        BaseTheme.update_links(self, source, target)
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        # banner_path
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        for language in available_languages:
            value = self.get_property('banner_path', language=language)
            if not value:
                continue
            path = old_base.resolve2(value)
            if path == source:
                # Hit the old name
                # Build the new reference with the right path
                self.set_property('banner_path', new_base.get_pathto(target),
                                  language=language)

        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        # FIXME BaseTheme does not take into account 'child'
        BaseTheme.update_relative_links(self, source)
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        # banner_path
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        for language in available_languages:
            value = self.get_property('banner_path', language=language)
            if not value:
                continue

            # Calcul the old absolute path
            old_abs_path = source.resolve2(value)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path,
                                                 old_abs_path)

            self.set_property('banner_path', target.get_pathto(new_abs_path),
                              language=language)


    # Views
    edit = Theme_Edit()



# Register
register_resource_class(Theme)
