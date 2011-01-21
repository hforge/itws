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
from itools.database import PhraseQuery
from itools.gettext import MSG
from itools.web import get_context

# Import from itws
from base import BaseFeedView_Configuration
from itws.feed_views import Feed_View



class TagsAwareView_Configuration(BaseFeedView_Configuration):

    class_id = 'tagsaware_view_configuration'
    class_title = MSG(u'Feed view configuration')



class TagsAwareView_View(Feed_View):

    view_name = 'tags_view'
    view_title = MSG(u'Feed view')
    view_configuration_cls = TagsAwareView_Configuration

    search_template = None
    content_template = '/ui/feed_views/Tag_item_viewbox.xml'


    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])
        # Init some informations
        context = get_context()
        resource = context.resource
        conf_resource = resource.get_resource('section_view')
        self.sort_by = conf_resource.get_property('view_sort_by')
        self.reverse = conf_resource.get_property('view_reverse')
        self.batch_size = conf_resource.get_property('view_batch_size')


    def get_items(self, resource, context, *args):
        # Get configuration
        args = list(args)
        args.append(PhraseQuery('is_tagsaware', True))
        return Feed_View.get_items(self, resource, context, *args)


    def get_content_namespace(self, resource, items, context):
        proxy = super(TagsAwareView_View, self)
        namespace = proxy.get_content_namespace(resource, items, context)
        namespace['thumb_width'] = 90
        namespace['thumb_height'] = 90
        namespace['more_title'] = MSG(u'Read more')
        return namespace
