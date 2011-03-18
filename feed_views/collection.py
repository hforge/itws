# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.database import PhraseQuery
from itools.gettext import MSG

# Import from itws
from base import Feed_View



class Details_View(Feed_View):

    view_name = 'details-view'
    view_title = MSG(u'Feed TagAware elements')
    search_template = None
    content_template = '/ui/feed_views/Tag_item_viewbox.xml'


    def get_items(self, resource, context, *args):
        args = list(args)
        args.append(PhraseQuery('is_tagsaware', True))
        return Feed_View.get_items(self, resource, context, *args)


    def get_content_namespace(self, resource, items, context):
        proxy = super(Details_View, self)
        namespace = proxy.get_content_namespace(resource, items, context)
        namespace['thumb_width'] = 90
        namespace['thumb_height'] = 90
        namespace['more_title'] = MSG(u'Read more')
        return namespace



class Search_View(Feed_View):

    view_name = 'search-view'
    view_title = MSG(u'Search view')

    styles = ['/ui/feed_views/search_view.css']
    content_template = '/ui/feed_views/search_view.xml'

    ignore_internal_resources = True
    search_on_current_folder = False
    search_on_current_folder_recursive = True



class DetailsWithoutPicture_View(Feed_View):

    view_name = 'details-without-picture-view'
    view_title = MSG(u'Details View (without pictures)')
    content_template = '/ui/news/SectionNews_view.xml'



class Title_View(Feed_View):

    view_name = 'view_title-view'
    view_title = MSG(u'Title view')
    content_template = '/ui/feed_views/NewsItem_preview.xml'
