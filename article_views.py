# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
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
from itools.gettext import MSG
from itools.web import BaseView

# Import from itws
from section_views import Section_View



############################################################
# Article View
############################################################
class Section_ArticleViewOneByOne(Section_View):

    def _get_real_section(self, resource, context):
        return resource.parent

    def get_section_id(self, resource, context):
        section = resource.parent
        return 'section-article-%s' % section.name



class Article_ProxyView(BaseView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')

    def GET(self, resource, context):
        section = resource.parent
        show_one_article = section.get_property('show_one_article')
        if show_one_article is False:
            return resource.article_view.GET(resource, context)
        return resource.section_view.GET(resource, context)
