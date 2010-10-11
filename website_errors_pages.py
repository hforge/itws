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

# Import from the Standard Library
from types import GeneratorType

# Import from itools
from itools.gettext import MSG
from itools.uri import Reference
from itools.stl import stl, set_prefix
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.webpage import WebPage
from ikaaro.website import NotFoundView as BaseNotFoundView


class NotFoundPage_View(BaseNotFoundView):

    not_found_template = '404'

    def get_template(self, resource, context):
        site_root = resource.get_site_root()
        template = site_root.get_resource(self.not_found_template, soft=True)
        if template and not template.handler.is_empty():
            # When 404 occurs context.resource is the last valid resource
            # in the context.path. We need to compute prefix from context.path
            # instead of context.resource
            path = site_root.get_abspath().resolve2('.%s' % context.path)
            prefix = path.get_pathto(template.get_abspath())
            return set_prefix(template.handler.events, '%s/' % prefix)
        # default
        return BaseNotFoundView.get_template(self, resource, context)


    def GET(self, resource, context):
        # Get the namespace
        namespace = self.get_namespace(resource, context)
        if isinstance(namespace, Reference):
            return namespace

        # STL
        template = self.get_template(resource, context)
        if isinstance(template, (GeneratorType, XMLParser)):
            return stl(events=template, namespace=namespace)
        return stl(template, namespace)



class NotFoundPage(WebPage):

    class_id = '404'
    class_title = MSG(u'404 page')
