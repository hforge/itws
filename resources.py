# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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
from datetime import datetime, timedelta

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import String, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.datatypes import Multilingual
from ikaaro.file import File
from ikaaro.file_views import File_Download, File_ExternalEdit_View
from ikaaro.autoform import SelectWidget, HTMLBody
from ikaaro.autoform import TextWidget, PathSelectorWidget
from ikaaro.menu import MenuFolder, Menu, MenuFile, Target
from ikaaro.registry import register_resource_class
from ikaaro.resource_ import DBResource
from ikaaro.text import Text, encodings
from ikaaro.text_views import Text_View
from ikaaro.webpage import WebPage

# Import from itws
from utils import XMLTitleWidget
from views import RobotsTxt_Edit
from views import FooterMenu_View, NotFoundPage_Edit


############################################################
# File (Monky patch)
############################################################
File.externaledit = File_ExternalEdit_View(
        template='/ui/common/externaledit.xml')
Text.externaledit = File_ExternalEdit_View(
        template='/ui/common/externaledit.xml', encodings=encodings)


############################################################
# Robots.txt
############################################################
RobotsTxt_body = """
User-agent: *
Disallow: /menu
Disallow: /footer
Disallow: /style
"""

class RobotsTxt(Text):

    class_id = 'robotstxt'
    class_title = MSG(u'Robots exclusion standard')
    class_views = ['view', 'edit', 'externaledit', 'download',
                   'upload', 'edit_state', 'commit_log']

    class_schema = merge_dicts(Text.class_schema,
                               state=String(source='metadata', default='public'))


    def init_resource(self, **kw):
        kw['extension'] = 'txt'
        Text.init_resource(self, **kw)


    ################
    ## Views
    ################
    download = File_Download(access=True)
    edit = RobotsTxt_Edit()
    view = Text_View(access='is_allowed_to_edit')




############################################################
# 404
############################################################
class NotFoundPage(WebPage):

    class_id = '404'
    class_title = MSG(u'404 page')

    edit = NotFoundPage_Edit()



############################################################
# Footer
############################################################
class FooterMenuFile(MenuFile):

    record_properties = {
        'title': Multilingual,
        # HACK datatype should be HTMLBody
        'html_content': Multilingual,
        'path': String,
        'target': Target(mandatory=True, default='_top')}


    def get_item_value(self, resource, context, item, column):
        if column == 'html_content':
            value = resource.handler.get_record_value(item, column)
            return HTMLBody.encode(Unicode.encode(value))
        return MenuFile.get_item_value(self, resource, context, item, column)



class FooterMenu(Menu):

    class_id = 'footer-menu'
    class_title = MSG(u'Footer Menu')
    class_handler = FooterMenuFile

    form = [TextWidget('title', title=MSG(u'Title')),
            XMLTitleWidget('html_content', title=MSG(u'HTML Content')),
            PathSelectorWidget('path', title=MSG(u'Path')),
            SelectWidget('target', title=MSG(u'Target'))]


    def _is_allowed_to_access(self, context, uri):
        # Check if uri == '' to avoid reference with a path = '.'
        if uri == '':
            # Allow empty link for the Footer
            return True
        return Menu._is_allowed_to_access(self, context, uri)


    view = FooterMenu_View()



class FooterFolder(MenuFolder):

    class_id = 'footer-folder'
    class_title = MSG(u'Footer Folder')
    # Your menu ressource (for overriding the record_properties and form)
    class_menu = FooterMenu

    use_fancybox = False


    def get_admin_edit_link(self, context):
        return context.get_link(self.get_resource('menu'))



############################################################
# Helper
############################################################
class MultilingualCatalogTitleAware(object):

    # multilingual title with language negociation
    # register_field('m_title', Unicode(is_stored=True, is_indexed=True))

    def get_catalog_values(self):
        # Get the languages
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')

        # Titles
        title = {}
        for language in languages:
            value = self._get_multilingual_catalog_title(language)
            if value:
                title[language] = value
        return {'m_title': title}


    def _get_multilingual_catalog_title(self, language):
        return self.get_property('title', language=language)



class ResourceWithCache(DBResource):
    """Resource with cache inside the metadata handler"""

    def __init__(self, metadata):
        DBResource.__init__(self, metadata)
        # Add cache API
        timestamp = getattr(metadata, 'timestamp', None)
        # If timestamp is None, the metadata handler could not exists on filesystem
        # -> make_resource, check if the metadata is already loaded before
        # setting the cache properties
        if timestamp and getattr(metadata, 'cache_mtime', None) is None:
            metadata.cache_mtime = None
            metadata.cache_data = None
            metadata.cache_errors = None


    def _update_data(self):
        raise NotImplementedError


    def get_cached_data(self):
        # Download or send the cache ??
        metadata = self.metadata
        now = datetime.now()
        cache_mtime = metadata.cache_mtime
        update_delta = timedelta(minutes=5) # 5 minutes
        if (cache_mtime is None or
            now - cache_mtime > update_delta):
            print u'UPDATE CACHE'
            self._update_data()

        return metadata.cache_data, metadata.cache_errors




register_resource_class(FooterFolder)
register_resource_class(FooterMenu)
register_resource_class(NotFoundPage, format='application/xhtml+xml')
register_resource_class(RobotsTxt)
