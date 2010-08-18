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

# Import from itools
from itools.core import guess_type
from itools.datatypes import PathDataType, Unicode
from itools.fs import FileName
from itools.gettext import MSG
from itools.handlers import checkid
from itools.handlers import guess_encoding
from itools.html import HTMLParser, stream_to_str_as_xhtml
from itools.i18n import guess_language
from itools.uri import Path
from itools.web import FormError

# Import from ikaaro
from ikaaro.file import Archive, TarArchive
from ikaaro.folder import Folder
from ikaaro.forms import PathSelectorWidget, AutoForm
from ikaaro.messages import MSG_NEW_RESOURCE, MSG_NAME_CLASH
from ikaaro.multilingual import Multilingual
from ikaaro.registry import get_resource_class
from ikaaro.resource_views import DBResource_AddLink



############################################################
# Archive
############################################################
class Archive_SelectFolder(DBResource_AddLink):

    def get_configuration(self):
        return {
            'show_browse': True,
            'show_external': False,
            'show_insert': False,
            'show_upload': False}


    def get_item_classes(self):
        return (Folder,)



class Archive_ExtractTo(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Extract archive')

    schema = {'target': PathDataType(madatory=True)}
    widgets = [PathSelectorWidget('target', title=MSG(u'Target'),
                                  action='select_folder')]

    def _get_form(self, resource, context):
        form = AutoForm._get_form(self, resource, context)

        target = form['target']
        target_resource = resource.get_resource(target, soft=True)
        if isinstance(target_resource, Folder) is False:
            raise FormError(invalid=['target'])

        # Check the name is free
        if target_resource.get_resource(resource.name, soft=True) is not None:
            raise FormError, MSG_NAME_CLASH

        return form


    def _make_resource(self, target, context, filename, body):
        # XXX filename can be an unicode
        if type(filename) is unicode:
            filename = Unicode.encode(filename)

        kk, _type, language = FileName.decode(filename)

        # FIXME default mimetype
        mimetype = 'text/plain'
        # Find out the mimetype
        guessed, encoding = guess_type(filename)
        if encoding is not None:
            encoding_map = {'gzip': 'application/x-gzip',
                            'bzip2': 'application/x-bzip2'}
            if encoding in encoding_map:
                mimetype = encoding_map[encoding]
        elif guessed is not None:
            mimetype = guessed

        # Web Pages are first class citizens
        if mimetype == 'text/html':
            body = stream_to_str_as_xhtml(HTMLParser(body))
            class_id = 'webpage'
        elif mimetype == 'application/xhtml+xml':
            class_id = 'webpage'
        else:
            class_id = mimetype
        cls = get_resource_class(class_id)

        # Multilingual resources, find out the language
        if issubclass(cls, Multilingual):
            if language is None:
                encoding = guess_encoding(body)
                text = cls.class_handler(string=body).to_text()
                language = guess_language(text)
                if language is None:
                    language = target.get_content_language(context)

        # Build the resource
        name, x, y = FileName.decode(filename)
        name = checkid(name)
        kw = {'format': class_id, 'filename': filename}
        if issubclass(cls, Multilingual):
            kw['language'] = language
        else:
            kw['extension'] = _type

        cls.make_resource(cls, target, name, body, **kw)


    def action(self, resource, context, form):
        target = form['target']
        fcls = Folder
        target_resource = resource.get_resource(target, soft=True)
        archive_folder = fcls.make_resource(fcls, target_resource,
                                            resource.name)

        handler = resource.handler
        names = handler.get_contents()
        if isinstance(resource, TarArchive):
            # Tar does not add trailing slash to directory
            tar_fd = handler._open_tarfile()
            new_names = []
            for name in names:
                member = tar_fd.getmember(name)
                if member.isdir():
                    new_names.append('%s/' % name)
                else:
                    new_names.append(name)
            names = new_names

        directories = [archive_folder]
        for name in names:
            slash_count = name.count('/')
            if name[-1] == '/':
                # make subfolder
                folder_name = Path(name).get_name()
                folder_name, x, y = FileName.decode(folder_name)
                subfolder = fcls.make_resource(fcls, directories[-1],
                                               folder_name)
                directories.append(subfolder)
                continue
            elif slash_count < (len(directories) - 1):
                # change subfolder
                directories.pop()
            data = handler.get_file(name)
            self._make_resource(directories[-1], context, name, data)

        # Ok
        goto = context.get_link(archive_folder)
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)



# Add Archive_ExtractTo view to Archive
Archive.extract_to = Archive_ExtractTo()
Archive.select_folder = Archive_SelectFolder()
Archive.class_views.insert(3, 'extract_to')
