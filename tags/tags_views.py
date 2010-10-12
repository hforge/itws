# -*- coding: UTF-8 -*-
# Copyright (C) 2008, 2010 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import from standard Library
from datetime import date, datetime, time
from math import ceil
from random import shuffle

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, Date, Enumerate, Integer, String
from itools.gettext import MSG
from itools.html import stream_to_str_as_xhtml
from itools.uri import encode_query
from itools.web import STLView, get_context
from itools.database import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.autoform import DateWidget, TextWidget

# Import from itws
from itws.datatypes import TimeWithoutSecond
from itws.rss import BaseRSS
from itws.utils import is_navigation_mode
from itws.utils import set_prefix_with_hostname
from itws.widgets import DualSelectWidget


class TagsList(Enumerate):

    site_root = None

    @staticmethod
    def decode(value):
        if not value:
            return None
        return str(value)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value)


    @classmethod
    def get_options(cls):
        tags_folder = cls.site_root.get_resource('tags')
        context = get_context()
        options = [ {'name': brain.name,
                     'value': brain.title or brain.name}
                    for brain in tags_folder.get_tag_brains(context) ]

        return options



############################################################
# Views
############################################################
class Tag_RSS(BaseRSS):
    """RSS export of a tag's results.
    """

    def get_base_query(self, resource, context):
        query = BaseRSS.get_base_query(self, resource, context)
        tags_query = resource.parent.get_tags_query_terms(state='public',
                tags=[resource.name])
        query.extend(tags_query)
        return query


    def get_excluded_container_paths(self, resource, context):
        site_root = resource.get_site_root()
        site_root_abspath = site_root.get_abspath()
        excluded = []
        for name in ('./menu/', './repository/', './ws-data/'):
            excluded.append(site_root_abspath.resolve2(name))
        return excluded


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column == 'description':
            view = getattr(item_resource, 'tag_view',
                           getattr(item_resource, 'view'))
            if view:
                content = view.GET(item_resource, context)
                # set prefix
                prefix = site_root.get_pathto(item_resource)
                content = set_prefix_with_hostname(content, '%s/' % prefix,
                                                   uri=context.uri)
                content = stream_to_str_as_xhtml(content)
                return content.decode('utf-8')
            else:
                return item_resource.get_property('description')

        return BaseRSS.get_item_value(self, resource, context, item,
                                      column, site_root)


class TagView_Viewbox(STLView):

    template = '/ui/common/Tag_item_viewbox.xml'

    brain = None

    # Configuration
    more_title = MSG(u'Read more')
    thumb_width = thumb_height = 96


    def _get_namespace(self, resource, context, column):
        if column == 'pub_datetime':
            return resource.get_pub_datetime_formatted()
        elif column == 'title':
            return resource.get_property('title')
        elif column == 'link':
            return context.get_link(resource)
        elif column == 'preview':
            return self.brain.preview_content
        elif column == 'thumbnail':
            thumbnail = resource.get_preview_thumbnail()
            if thumbnail:
                return context.get_link(thumbnail)
            return None
        elif column == 'tags':
            tags = self.brain.tags
            if tags:
                return resource.get_tags_namespace(context)
            return []


    def get_namespace(self, resource, context):
        namespace = {}
        for key in ('pub_datetime', 'title', 'link', 'preview', 'tags',
                    'thumbnail'):
            namespace[key] = self._get_namespace(resource, context, key)
        namespace['more_title'] = self.more_title
        namespace['thumb_width'] = self.thumb_width
        namespace['thumb_height'] = self.thumb_height
        return namespace



class Tag_View(Folder_BrowseContent):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    template = '/ui/common/Tag_view.xml'
    context_menus = []
    styles = []
    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               batch_size=Integer(default=20),
                               sort_by=String(default='pub_datetime'),
                               reverse=Boolean(default=True))
    search_template = None
    table_template = None
    max_middle_pages = 5


    def get_items(self, resource, context, *args):
        # Build the query
        args = list(args)
        tag = resource.name
        get_query_value = context.get_query_value
        formats = get_query_value('format', type=String(multiple=True),
                                  default=[])
        query = resource.parent.get_tags_query_terms(state='public',
                tags=[tag], formats=formats)
        args.append(AndQuery(*query))

        # Ok
        return context.root.search(AndQuery(*args))



    def get_namespace(self, resource, context):
        namespace = Folder_BrowseContent.get_namespace(self, resource, context)
        namespace['title'] = resource.get_property('title')
        # Get viewboxes
        base_viewbox = TagView_Viewbox()
        items = self.get_items(resource, context)
        items = self.sort_and_batch(resource, context, items)
        namespace['viewboxes'] = []
        for item in items:
            brain, item_resource = item
            viewbox = getattr(item_resource, 'viewbox', base_viewbox)
            viewbox.brain = brain
            namespace['viewboxes'].append(viewbox.GET(item_resource, context))
        return namespace



class TagsFolder_TagCloud(STLView):
    """Public view of the tags folder.
    """
    title = MSG(u'Tag Cloud Preview')
    access = 'is_allowed_to_view'
    template = '/ui/common/Tags_tagcloud.xml'

    formats = []
    show_number = False
    random_tags = False
    tags_to_show = 0
    show_description = True
    # Css class from tag-1 to tag-css_index_max
    css_index_max = 5


    def _get_tags_folder(self, resource, context):
        return resource


    def get_namespace(self, resource, context):
        namespace = {}
        tags_folder = self._get_tags_folder(resource, context)

        # description (help text)
        bo_description = False
        ac = tags_folder.get_access_control()
        if ac.is_allowed_to_edit(context.user, tags_folder):
            if is_navigation_mode(context) is False and \
                    self.show_description and \
                    type(context.resource) is type(tags_folder):
                bo_description = True

        tag_brains = tags_folder.get_tag_brains(context)
        tag_base_link = '%s/%%s' % context.get_link(tags_folder)
        if self.formats:
            query = {'format': self.formats}
            tag_base_link = '%s?%s' % (tag_base_link, encode_query(query))

        # query
        root = context.root
        tags_query = tags_folder.get_tags_query_terms(state='public',
                                                      formats=self.formats)
        tags_results = root.search(AndQuery(*tags_query))

        items_nb = []
        tags = []
        for brain in tag_brains:
            if self.tags_to_show and len(items_nb) == self.tags_to_show:
                break
            sub_results = tags_results.search(PhraseQuery('tags', brain.name))
            nb_items = len(sub_results)
            if nb_items:
                d = {}
                title = brain.title or brain.name
                if self.show_number:
                    title = u'%s (%s)' % (title, nb_items)
                d['title'] = title
                d['xml_title'] = title.replace(u' ', u'\u00A0')
                d['link'] = tag_base_link % brain.name
                d['css'] = None
                items_nb.append(nb_items)
                d['nb_items'] = nb_items
                tags.append(d)

        if not tags:
            return {'tags': [], 'bo_description': bo_description}

        max_items_nb = max(items_nb) if items_nb else 0
        min_items_nb = min(items_nb) if items_nb else 0

        css_index_max = self.css_index_max
        delta = (max_items_nb - min_items_nb) or 1
        percentage_per_item = float(css_index_max - 1) / delta

        # Special case of there is only one item
        default_css = 'tag-1'

        for tag in tags:
            if min_items_nb == max_items_nb:
                tag['css'] = default_css
            else:
                nb_items = tag['nb_items']
                css_index = int(ceil(nb_items) * percentage_per_item) or 1
                # FIXME sometimes css_index = 0, this should never append
                # set css_index to 1
                css_index = abs(css_index_max - css_index + 1) or 1
                tag['css'] = 'tag-%s' % css_index

        # Random
        if self.random_tags:
            shuffle(tags)

        return {'tags': tags, 'bo_description': bo_description}



class TagsAware_Edit(object):
    """Mixin to merge with the TagsAware edit view.
    """
    # Little optimisation not to compute the schema too often
    keys = ['tags', 'pub_datetime', 'pub_date', 'pub_time']


    def _get_schema(self, resource, context):
        site_root = resource.get_site_root()
        return {'tags': TagsList(site_root=site_root, multiple=True),
                'pub_date': Date, 'pub_time': TimeWithoutSecond}


    def _get_widgets(self, resource, context):
        return [DualSelectWidget('tags', title=MSG(u'TAGS'), is_inline=True,
            has_empty_option=False),
            DateWidget('pub_date',
                       title=MSG(u'Publication date (use by RSS and TAGS)')),
            TextWidget('pub_time', tip=MSG(u'hour:minute'), size=5, maxlength=5,
                       title=MSG(u'Publication time (use by RSS and TAGS)'))]


    def get_value(self, resource, context, name, datatype):
        if name == 'tags':
            tags = resource.get_property('tags')
            # tuple -> list (enumerate.get_namespace expects list)
            return list(tags)
        elif name in ('pub_date', 'pub_time'):
            pub_datetime = resource.get_property('pub_datetime')
            if pub_datetime is None:
                return None
            if name == 'pub_date':
                return date(pub_datetime.year, pub_datetime.month,
                            pub_datetime.day)
            else:
                return time(pub_datetime.hour, pub_datetime.minute)


    def set_value(self, resource, context, name, form):
        if name == 'tags':
            resource.set_property('tags', form['tags'])
        elif name in ('pub_date', 'pub_time'):
            pub_date = form['pub_date']
            pub_time = form['pub_time']
            if pub_date:
                dt_kw = {}
                if pub_time:
                    dt_kw = {'hour': pub_time.hour,
                             'minute': pub_time.minute}
                dt = datetime(pub_date.year, pub_date.month, pub_date.day,
                              **dt_kw)
                resource.set_property('pub_datetime', dt)



class TagsFolder_BrowseContent(Folder_BrowseContent):
    """Browse content with preview of tagged items number. Used in the
    Tags_ManageView composite.
    """
    access = 'is_allowed_to_edit'

    # Table
    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('items_nb', MSG(u'Items number')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('workflow_state', MSG(u'State'))]


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'items_nb':
            # Build the search query
            query = resource.get_tags_query_terms()
            query.append(PhraseQuery('tags', brain.name))
            query = AndQuery(*query)

            # Search
            results = context.root.search(query)
            return len(results), './%s' % brain.name

        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)
