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
from itools.core import freeze, merge_dicts
from itools.database import OrQuery, PhraseQuery
from itools.datatypes import Boolean, Enumerate
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import RadioWidget, SelectWidget, TextWidget

# Import from itws
from base import BaseFeedView_Configuration
from itws.datatypes import PositiveIntegerNotNull
from itws.feed_views.base import Feed_View
from itws.tags import get_registered_tags_aware_classes



class GalleryClassesEnumerate(Enumerate):

    options = [{'name': 'image', 'value': MSG(u'Image')},
               {'name': 'tagsaware', 'value': MSG(u'TagsAware')}]



class ImagesView_Configuration(BaseFeedView_Configuration):

    class_id = 'images_view_configuration'
    class_title = MSG(u'Gallery view')
    class_schema = merge_dicts(
        BaseFeedView_Configuration.class_schema,
        # Filter
        filtered_class=GalleryClassesEnumerate(default='image',
                                               source='metadata'),
        # Thumb size
        thumb_width=PositiveIntegerNotNull(default=128, source='metadata'),
        thumb_height=PositiveIntegerNotNull(default=128, source='metadata'),
        thumb_strict=Boolean(default=False, source='metadata'))

    edit_schema = freeze(merge_dicts(
        BaseFeedView_Configuration.edit_schema,
        filtered_class=GalleryClassesEnumerate(mandatory=True),
        thumb_width=PositiveIntegerNotNull,
        thumb_height=PositiveIntegerNotNull,
        thumb_strict=Boolean))

    edit_widgets = freeze(
        BaseFeedView_Configuration.edit_widgets
        + [SelectWidget('filtered_class',
                        title=MSG(u'Type of content to display')),
           TextWidget('thumb_width', title=MSG(u'Thumb width')),
           TextWidget('thumb_height', title=MSG(u'Thumb height')),
           RadioWidget('thumb_strict', title=MSG(u'Force thumbnail size'))])



class ImagesView_View(Feed_View):

    content_template = '/ui/feed_views/images_view.xml'
    search_template = None
    styles = ['/ui/feed_views/images_view.css',
              '/ui/common/js/fancybox/jquery.fancybox-1.3.1.css']
    scripts = ['/ui/common/js/fancybox/jquery.fancybox-1.3.1.pack.js']

    # Section view properties
    view_name = 'images-view'
    view_title = MSG(u'Gallery view')
    view_configuration_cls = ImagesView_Configuration


    def _get_configuration_file(self, resource):
        return resource.get_resource('section_view')


    def get_items(self, resource, context, *args):
        args = list(args)
        conf_resource = self._get_configuration_file(resource)
        filtered_class = conf_resource.get_property('filtered_class')
        if filtered_class == 'image':
            args.append(PhraseQuery('is_image', True))
        else:
            # tagsaware
            query = []
            _classes = get_registered_tags_aware_classes()
            for _cls in _classes:
                query.append(PhraseQuery('format', _cls.class_id))
            args.append(OrQuery(*query))

        return Feed_View.get_items(self, resource, context, *args)


    def get_content_namespace(self, resource, context, items):
        proxy = super(ImagesView_View, self)
        namespace = proxy.get_content_namespace(resource, context, items)
        conf_resource = self._get_configuration_file(resource)
        for key in ['thumb_width', 'thumb_height', 'thumb_strict']:
            namespace[key] = conf_resource.get_property(key)
        return namespace
