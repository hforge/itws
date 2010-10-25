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
from itools.core import merge_dicts
from itools.datatypes import Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget, RadioWidget, TextWidget

# Import from itws
from base import Box
from base_views import Box_Preview, Box_View
from itws.datatypes import PositiveInteger
from itws.tags import TagsAwareClassEnumerate


class BoxTags_Preview(Box_Preview):

    def get_details(self, resource, context):
        count = resource.get_property('count')
        show_number = resource.get_property('show_number')
        random = resource.get_property('random')
        formats = resource.get_property('formats')
        details = []
        details.append(u'Tags to show (0 for all tags): %s' % count)
        details.append(u'Show number of items for each tag: %s' % show_number)
        details.append(u'This tag cloud will display only the tags '
                       u'from: %s' % ', '.join(formats))

        return details



class BoxTags_View(Box_View):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    template = '/ui/bar_items/Tags_view.xml'

    def _get_tags_folder(self, resource, context):
        site_root = resource.get_site_root()
        return site_root.get_resource('tags')


    def get_namespace(self, resource, context):
        tags_folder = self._get_tags_folder(resource, context)
        has_tags = tags_folder.is_empty(context) is False

        title = resource.get_property('display_title')
        if title:
            title = resource.get_title()

        # tag cloud
        box = None
        if has_tags:
            tags_to_show = resource.get_property('count')
            random = resource.get_property('random')
            show_number = resource.get_property('show_number')
            formats = resource.get_property('formats') or []
            # FIXME
            cls = tags_folder.tag_cloud.__class__
            view = cls(formats=formats, show_number=show_number,
                       random_tags=random, tags_to_show=tags_to_show,
                       show_description=False)
            box = view.GET(tags_folder, context)
        elif self.is_admin(resource, context) is False:
            # Hide the box if there is no tags and
            # if the user cannot edit the box
            self.set_view_is_empty(True)

        return {'title': title, 'box': box}



class BoxTags(Box):

    class_id = 'box-tags'
    class_version = '20100527'
    class_title = MSG(u'Tag Cloud')
    class_description = MSG(u'Display a tag cloud')
    class_icon16 = 'bar_items/icons/16x16/box_tags.png'
    class_views = ['edit', 'edit_state', 'backlinks', 'commit_log']
    class_schema = merge_dicts(Box.class_schema,
                      formats=TagsAwareClassEnumerate(source='metadata', multiple=True),
                      count=PositiveInteger(source='metadata', default=0),
                      show_number=Boolean(source='metadata'),
                      random=Boolean(source='metadata'),
                      display_title=Boolean(source='metadata'))

    # Configuration
    allow_instanciation=  True

    # Box configuration
    edit_schema = {'formats': TagsAwareClassEnumerate(multiple=True),
                   'count':PositiveInteger(default=0),
                   'show_number': Boolean,
                   'random': Boolean,
                   'display_title': Boolean}

    edit_widgets = [
        CheckboxWidget('display_title',
                        title=MSG(u'Display on tagcloud view')),
        TextWidget('count', size=4,
                   title=MSG(u'Tags to show (0 for all tags)')),
        CheckboxWidget('show_number',
                        title=MSG(u'Show number of items for each tag')),
        CheckboxWidget('random', title=MSG(u'Randomize tags')),
        RadioWidget('formats', has_empty_option=False,
                    title=MSG(u'This tag cloud will display only '
                              u'the tags from selected types of content'))
        ]

    # Views
    view = BoxTags_View()
    preview = order_preview = BoxTags_Preview()
