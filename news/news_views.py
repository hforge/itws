# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Henry Obein <henry@itaapy.com>
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

# Import from the Standard Library
from datetime import date

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import String, Boolean, Integer, PathDataType
from itools.gettext import MSG
from itools.uri import encode_query
from itools.web import get_context, STLView
from itools.database import PhraseQuery, AndQuery, NotQuery, RangeQuery

# Import from ikaaro
from ikaaro.datatypes import Multilingual
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.autoform import ImageSelectorWidget, TextWidget
from ikaaro.popup import DBResource_AddImage
from ikaaro.utils import get_base_path_query

# Import from itws
from itws.rss import BaseRSS
from itws.tags.tags_views import Tag_View, TagView_Viewbox
from itws.webpage_views import WebPage_Edit



class NewsItem_Viewbox(TagView_Viewbox):


    def _get_namespace(self, resource, context, column, current_path):
        if column == 'title':
            # Return title or long_title
            title = resource.get_property('title')
            if title:
                return title
            # long title
            long_title = resource.get_property('long_title')
            if long_title:
                return long_title
            # Fallback
            return resource.get_title()
        elif column == 'tags':
            tags = self.brain.tags
            if tags:
                return resource.get_news_tags_namespace(context)
            return []
        return TagView_Viewbox._get_namespace(self, resource, context, column,
                                              current_path)



class NewsItem_Preview(STLView):

    template = '/ui/news/NewsItem_preview.xml'

    def get_columns(self):
        return ('title', 'long_title', 'path', 'pub_datetime',
                'thumbnail', 'css', 'tags')


    def get_value(self, resource, context, column, language, current_path):
        if column == 'title':
            return resource.get_title()
        elif column == 'long_title':
            return resource.get_long_title(language=language)
        elif column == 'path':
            return context.get_link(resource)
        elif column == 'pub_datetime':
            return resource.get_pub_datetime_formatted()
        elif column == 'thumbnail':
            path = resource.get_property('thumbnail')
            if path:
                image = resource.get_resource(path, soft=True)
                if image:
                    return context.get_link(image)
            return None
        elif column == 'css':
            if resource.get_abspath() == current_path:
                return 'active'
            return None


    def get_namespace(self, resource, context):
        # Get Language
        site_root = context.site_root
        ws_languages = site_root.get_property('website_languages')
        accept = context.accept_language
        language = accept.select_language(ws_languages)

        # Build namespace
        namespace = {}

        here_abspath = context.resource.get_abspath()
        for col in self.get_columns():
            namespace[col] = self.get_value(resource, context, col, language,
                                            here_abspath)

        return namespace



class NewsItem_View(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    icon = 'view.png'
    template = '/ui/news/NewsItem_view.xml'
    styles = ['/ui/news/style.css']

    # customization (obsolete)
    id = 'news'
    title_link = None

    def get_namespace(self, resource, context):
        news_folder = resource.parent
        dow = resource.get_pub_datetime_formatted()
        # title
        title = resource.get_long_title()
        # content
        content = resource.get_html_data()
        # Allowed to edit
        ac = resource.get_access_control()
        if ac.is_allowed_to_edit(context.user, resource):
            edit = True
        else:
            edit = False

        namespace = {'id': self.id, 'pub_datetime': dow}
        namespace['title'] = title
        namespace['content'] = content
        namespace['is_allowed_to_edit'] = edit
        title_link = None
        if self.title_link:
            title_link = context.get_link(resource)
        namespace['title_link'] = title_link

        return namespace



class NewsItem_AddImage(DBResource_AddImage):

    def get_start(self, resource):
        return resource.get_resource('../images')



class NewsItem_Edit(WebPage_Edit):

    def _get_schema(self, resource, context):
        return merge_dicts(WebPage_Edit._get_schema(self, resource, context),
                           long_title=Multilingual,
                           thumbnail=PathDataType)


    def _get_widgets(self, resource, context):
        widgets = WebPage_Edit._get_widgets(self, resource, context)[:]
        widgets.insert(2, TextWidget('long_title', title=MSG(u'Long title')))
        widgets.append(
            ImageSelectorWidget('thumbnail', title=MSG(u'Thumbnail')))
        return widgets




class NewsFolder_View(Tag_View):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    template = '/ui/news/NewsFolder_view.xml'
    styles = ['/ui/news/style.css']
    query_schema = merge_dicts(Tag_View.query_schema,
                               batch_size=Integer(default=5),
                               tag=String(multiple=True))
    category_title = MSG(u"Category:") # FIXME Use plural forms
    category_title2 = MSG(u"Categories:")

    def get_query_schema(self):
        here = get_context().resource
        # FIXME May failed
        batch_size = here.get_property('batch_size')
        return merge_dicts(Tag_View.get_query_schema(self),
                           batch_size=Integer(default=batch_size))


    def get_items(self, resource, context, *args):
        from itws.tags.utils import get_tagaware_query_terms
        # XXX
        # Build the query
        args = list(args)
        # Filter by tag
        tags = context.get_query_value('tag', type=String(multiple=True))
        query_terms = get_tagaware_query_terms(context,
            on_current_folder=True, state='public', tags=tags,
            class_id=resource.news_class.class_id)
        args.append(AndQuery(*query_terms))

        if len(args) == 1:
            query = args[0]
        else:
            query = AndQuery(*args)

        # Ok
        return context.root.search(query)


    def get_tags_namespace(self, resource, context):
        tags_ns = []
        here_link = context.get_link(resource)
        tags_folder = resource.get_site_root().get_resource('tags')
        tags = context.get_query_value('tag', type=String(multiple=True))

        for tag_name in tags:
            query = encode_query({'tag': tag_name})
            tag = tags_folder.get_resource(tag_name, soft=True)
            if tag is None:
                continue
            tags_ns.append({'title': tag.get_title(),
                            'href': '%s?%s' % (here_link, query)})

        return tags_ns


    def get_namespace(self, resource, context):
        namespace = Tag_View.get_namespace(self, resource, context)

        # Tags
        tags = context.get_query_value('tag', type=String(multiple=True))
        if len(tags) > 1:
            category_title = self.category_title2
        else:
            category_title = self.category_title

        namespace['tags'] = self.get_tags_namespace(resource, context)
        namespace['category_title'] = category_title

        return namespace



class NewsFolder_RSS(BaseRSS):

    def get_base_query(self, resource, context):
        today = date.today()
        min_date = date(1900, 1, 1)
        # Filter by news folder
        abspath = resource.get_canonical_path()
        return [ get_base_path_query(str(abspath)),
                 PhraseQuery('workflow_state', 'public'),
                 RangeQuery('pub_datetime', min_date, today)]


    def get_allowed_formats(self, resource, context):
        return [resource.news_class.class_id]



############################################################
# Manage view
############################################################

class NewsFolder_BrowseContent(Folder_BrowseContent):

    access = 'is_allowed_to_edit'

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               sort_by=String(default='pub_datetime'),
                               reverse=Boolean(default=True))

    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('pub_datetime', MSG(u'Date of writing')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('format', MSG(u'Type')),
        ('workflow_state', MSG(u'State'))]

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        # Only remove 'order-sidebar'
        query = [ PhraseQuery('parent_path', path),
                  NotQuery(PhraseQuery('name', 'order-sidebar')) ]
        return context.root.search(AndQuery(*query))


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'pub_datetime':
            # FIXME If no news/tagsaware resources have not been indexed
            # pub_datetime index does not exist and brain.pub_datetime
            # raise an error
            newsfolder = item_resource.parent
            if isinstance(item_resource, newsfolder.news_class):
                return brain.pub_datetime
            return
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)
