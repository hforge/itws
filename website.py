# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009 Romain Gauthier <romain@itaapy.com>
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
from copy import deepcopy

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import String
from itools.gettext import MSG
from itools.uri import get_reference, Path
from itools.web import get_context, FormError

# Import from ikaaro
from ikaaro import messages
from ikaaro.file import Image
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.forms import MultilineWidget, ImageSelectorWidget
from ikaaro.future.menu import MenuFolder
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_Edit, DBResource_AddImage
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.text import CSS
from ikaaro.tracker import Tracker, Issue
from ikaaro.website import WebSite as BaseWebSite
# Special case for the Wiki
try:
    from ikaaro.wiki import WikiFolder
except ImportError:
    WikiFolder = None

# Import from itws
from resources import FooterFolder, NotFoundPage
from utils import get_path_and_view



class FavIcon(Image):

    class_id = 'favicon'

    @classmethod
    def get_metadata_schema(cls):
        schema = Image.get_metadata_schema()
        schema['state'] = String(default='public')
        return schema



class AddFavIcon(DBResource_AddImage):

    element_to_add = 'favicon'


    def is_item(self, resource):
        from ikaaro.file import Image
        if isinstance(resource, Image):
            mimetype = resource.handler.get_mimetype()
            if mimetype != 'image/x-icon':
                return False
            # Check the size, max 32x32
            width, height = resource.handler.get_size()
            if width > 32 or height > 32:
                return False
            return True
        return False



class WebSite_Edit(DBResource_Edit):

    def get_schema(self, resource, context):
        return merge_dicts(DBResource_Edit.get_schema(self, resource, context),
                           custom_data=String, favicon=String)


    def get_widgets(self, resource, context):
        widgets = DBResource_Edit.get_widgets(self, resource, context)[:]
        # custom_data
        widgets.append(
            MultilineWidget('custom_data', title=MSG(u'Custom Data'), rows=16))
        # favicon
        title = MSG(u'Replace favicon file (ICO 32x32 only)')
        title = title.gettext()
        widgets.append(ImageSelectorWidget('favicon', title=title,
                                            action='add_favicon'))

        # Ok
        return widgets


    def _get_form(self, resource, context):
        form = DBResource_Edit._get_form(self, resource, context)

        # Check favicon
        favicon = form['favicon']
        if favicon:
            favicon = resource.get_resource(favicon, soft=True)
            if favicon is None:
                message = MSG(u"The file doesn't exists")
                message = message.gettext()
                raise FormError, message

            # Check favicon properties
            mimetype = favicon.handler.get_mimetype()
            if mimetype != 'image/x-icon':
                message = MSG(u'Unexpected file of mimetype {mimetype}.')
                raise FormError, message.gettext(mimetype=mimetype)
            # Check the size, max 32x32
            width, height = favicon.handler.get_size()
            if width > 32 or height > 32:
                message = u'Unexpected file of size {width}x{height}.'
                message = MSG(message).gettext(width=width, height=height)
                raise FormError, message
        return form


    def action(self, resource, context, form):
        DBResource_Edit.action(self, resource, context, form)
        # Check edit conflict
        if context.edit_conflict:
            return

        custom_data = form['custom_data']
        resource.set_property('custom_data', custom_data)

        favicon = form['favicon']
        resource.set_property('favicon', favicon)
        # Ok
        context.message = messages.MSG_CHANGES_SAVED



class WebSite(BaseWebSite):

    class_version = '20100524'
    class_views = ['view', 'browse_content', 'preview_content', 'edit',
                   'control_panel', 'commit_log']
    # Remove 'index' but keep 'skin'
    __fixed_handlers__ = BaseWebSite.__fixed_handlers__[:0] + ['404']
    menus = ()
    footers = ()


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        BaseWebSite._make_resource(cls, folder, name, **kw)
        website = get_context().root.get_resource(name)
        ws_folder = website.handler

        # Add menus
        for item in cls.menus:
            MenuFolder._make_resource(MenuFolder, ws_folder, item)
        # Add footers
        for item in cls.footers:
            FooterFolder._make_resource(FooterFolder, ws_folder, item)

        # Add CSS
        CSS._make_resource(CSS, ws_folder, 'style', extension='css',
                           body='/* CSS */', title={'en': u'Style'},
                           state='public')
        # Add 404 page
        NotFoundPage._make_resource(NotFoundPage, ws_folder, '404')


    @classmethod
    def build_metadata(cls, owner=None, format=None, **kw):
        if format is None:
            format = cls.class_id
        metadata = BaseWebSite.build_metadata.im_func(cls, owner=owner,
                                                      format=format, **kw)
        metadata.set_property('website_is_open', True)
        return metadata


    @classmethod
    def get_metadata_schema(cls):
        schema = BaseWebSite.get_metadata_schema()
        schema['custom_data'] = String(default='')
        schema['favicon'] = String(default='')

        return schema


    def is_allowed_to_view(self, user, resource):
        if user is None:
            context = get_context()
            if self.get_skin(context).name == 'aruni':
                return False
            # Tracker is private
            if isinstance(resource, (Tracker, Issue)):
                return False
            # Wiki only if FrontPage published
            if WikiFolder and isinstance(resource, WikiFolder):
                frontpage = resource.get_resource('FrontPage')
                return frontpage.get_workflow_state() == 'public'
        return BaseWebSite.is_allowed_to_view(self, user, resource)


    def get_repository(self):
        return None


    def get_links(self):
        links = BaseWebSite.get_links(self)
        base = self.get_abspath()
        # favicon
        favicon_path = self.get_property('favicon')
        if favicon_path:
            links.append(str(base.resolve2(favicon_path)))
        return links


    def update_links(self, source, target):
        BaseWebSite.update_links(self, source, target)
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        # favicon
        path = self.get_property('favicon')
        if path:
            ref = get_reference(path)
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                path = str(old_base.resolve2(path))
                if path == source:
                    # Hit the old name
                    # Build the new reference with the right path
                    new_ref = deepcopy(ref)
                    new_ref.path = str(new_base.get_pathto(target)) + view
                    self.set_property('favicon', str(new_ref))

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        BaseWebSite.update_relative_links(self, source)
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new
        path = self.get_property('favicon')
        if path:
            ref = get_reference(str(path))
            if not ref.scheme:
                path, view = get_path_and_view(ref.path)
                # Calcul the old absolute path
                old_abs_path = source.resolve2(path)
                # Check if the target path has not been moved
                new_abs_path = resources_old2new.get(old_abs_path,
                                                     old_abs_path)
                # Build the new reference with the right path
                # Absolute path allow to call get_pathto with the target
                new_ref = deepcopy(ref)
                new_ref.path = str(target.get_pathto(new_abs_path)) + view
                # Update the title link
                self.set_property('favicon', str(new_ref))


    def update_20100524(self):
        from ikaaro.webpage import WebPage as BaseWebPage
        from webpage import WebPage
        # 404 webpage -> 404 not found page
        resource = self.get_resource('404', soft=True)
        if resource is None:
            cls = NotFoundPage
            cls.make_resource(cls, self, '404')
            return

        base_schema_keys = BaseWebPage.get_metadata_schema().keys()
        webpage_schema_keys = WebPage.get_metadata_schema().keys()
        diff = set(base_schema_keys).difference(set(webpage_schema_keys))
        diff2 = set(webpage_schema_keys).difference(set(base_schema_keys))
        # Remove obsolete property
        for key in diff:
            resource.del_property(key)
            print u'del %s' % key
        for key in diff2:
            resource.del_property(key)
            print u'del %s' % key

        metadata = resource.metadata
        metadata.set_changed()
        metadata.format = NotFoundPage.class_id
        metadata.version = NotFoundPage.class_version


    #######################################################################
    # User Interface
    #######################################################################
    edit = WebSite_Edit()
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    add_favicon = AddFavIcon()



register_resource_class(WebSite)
register_resource_class(FavIcon)
