# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class, register_document_type

# Import from itws
from article_views import Article_ProxyView
from article_views import Section_ArticleViewOneByOne
from tags import TagsAware
from webpage import WebPage
from webpage_views import WebPage_View



class Article(WebPage):
    """ An Article is a WebPage published on its making.
    """
    class_id = 'article'
    class_version = '20100107'
    class_title = MSG(u'Article')

    view = Article_ProxyView()
    article_view = WebPage_View()
    section_view = Section_ArticleViewOneByOne()



register_resource_class(Article)
register_document_type(Article, TagsAware.class_id)
