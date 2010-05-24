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
from itools.core import freeze, merge_dicts
from itools.datatypes import String, Unicode, Boolean
from itools.gettext import MSG
from itools.handlers import checkid
from itools.html import stream_to_str_as_xhtml
from itools.rss import RSSFile
from itools.uri import Path, Reference
from itools.web import get_context, BaseView, STLView, FormError
from itools.xapian import AndQuery, RangeQuery, NotQuery, PhraseQuery, OrQuery

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton, RenameButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm, TextWidget, HTMLBody
from ikaaro.future.menu import Menu_View
from ikaaro.future.order import ResourcesOrderedTable_View
from ikaaro.future.order import ResourcesOrderedTable_Ordered
from ikaaro.future.order import ResourcesOrderedTable_Unordered
from ikaaro.utils import get_base_path_query
from ikaaro.views_new import NewInstance
from ikaaro.webpage import WebPage

# Import from itws
from utils import set_prefix_with_hostname, to_box



############################################################
# NewInstance
############################################################

class EasyNewInstance(NewInstance):
    """ ikaaro.views_new.NewInstance without field name.
    """
    query_schema = freeze({'type': String, 'title': Unicode})
    widgets = freeze([
        TextWidget('title', title=MSG(u'Title', mandatory=True))])

    def get_new_resource_name(self, form):
        # As we have no name, always return the title
        title = form['title'].strip()
        return title



class ProxyContainerNewInstance(EasyNewInstance):

    query_schema = freeze({'title': Unicode})

    def _get_resource_cls(self, context):
        raise NotImplementedError


    def _get_container(self, resource, context):
        raise NotImplementedError


    def _get_form(self, resource, context):
        form = AutoForm._get_form(self, resource, context)
        name = self.get_new_resource_name(form)

        # Check the name
        if not name:
            raise FormError, messages.MSG_NAME_MISSING

        try:
            name = checkid(name)
        except UnicodeEncodeError:
            name = None

        if name is None:
            raise FormError, messages.MSG_BAD_NAME

        # Check the name is free
        container = self._get_container(resource, context)
        if container.get_resource(name, soft=True) is not None:
            raise FormError, messages.MSG_NAME_CLASH

        # Ok
        form['name'] = name
        return form


    def get_title(self, context):
        cls = self._get_resource_cls(context)
        class_title = cls.class_title.gettext()
        title = MSG(u'Add {class_title}')
        return title.gettext(class_title=class_title)


    def icon(self, resource, **kw):
        cls = self._get_resource_cls(get_context())
        return cls.get_class_icon()


    def action(self, resource, context, form):
        name = form['name']
        title = form['title']

        # Create the resource
        cls = self._get_resource_cls(context)
        container = self._get_container(resource, context)
        child = cls.make_resource(cls, container, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        metadata.set_property('title', title, language=language)

        goto = '%s/%s' % (context.get_link(container), name)
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class SmartOrderedTable_Ordered(ResourcesOrderedTable_Ordered):

    def get_title(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'ordered_view_title', None)

    title = property(get_title)

    def get_title_description(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'ordered_view_title_description', None)

    title = property(get_title)
    title_description = property(get_title_description)



class SmartOrderedTable_Unordered(ResourcesOrderedTable_Unordered):

    def get_title(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'unordered_view_title', None)


    def get_title_description(self):
        context = get_context()
        resource = context.resource
        return getattr(resource, 'unordered_view_title_description', None)

    title = property(get_title)
    title_description = property(get_title_description)



class SmartOrderedTable_View(ResourcesOrderedTable_View):

    template = '/ui/common/order_view.xml'

    subviews = [ SmartOrderedTable_Ordered(),
                 SmartOrderedTable_Unordered() ]

    def get_namespace(self, resource, context):
        views = []
        for view in self.subviews:
            views.append({'title': view.title,
                          'description': view.title_description,
                          'view': view.GET(resource, context)})
        return {'views': views}



############################################################
# Footer
############################################################

class FooterMenu_View(Menu_View):

    access = 'is_allowed_to_edit'

    def get_item_value(self, resource, context, item, column):
        if column == 'html_content':
            value = resource.handler.get_record_value(item, column)
            return HTMLBody.decode(Unicode.encode(value))
        return Menu_View.get_item_value(self, resource, context, item, column)



############################################################
# Manage link view
############################################################
class BaseManageLink(STLView):

    template = '/ui/neutral/manage_link.xml'
    title = MSG(u'Manage view')

    def get_items(self, resource, context):
        items_list = [[]]

        return items_list


    def get_namespace(self, resource, context):
        items_list = self.get_items(resource, context)

        # Post process link
        # FIXME Does not work for absolute links
        here_link = Path(context.get_link(resource))
        for list in items_list:
            for item in list['items']:
                new_path = here_link.resolve2(item['path'])
                item['path'] = new_path
                disable = item.get('disable', False)
                item['disable'] = disable
                if disable:
                    item['class'] = '%s disable' % item['class']

        return {'lists': items_list, 'title': self.title}



class BaseManageContent(Folder_BrowseContent):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage')

    search_template = None

    table_actions = [RemoveButton, RenameButton]
    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('format', MSG(u'Format')),
        ('mtime', MSG(u'Last Modified')),
        ('workflow_state', MSG(u'State')),
        ]

    def get_query_schema(self):
        return merge_dicts(Folder_BrowseContent.get_query_schema(self),
                           sort_by=String(default='mtime'),
                           reverse=Boolean(default=True))


    def get_items(self, resource, context, *args):
        return Folder_BrowseContent.get_items(self, resource, context, *args)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'name':
            return brain.name, context.get_link(item_resource)
        return Folder_BrowseContent.get_item_value(self, resource,
                  context, item, column)



############################################################
# Numeric batch
############################################################

class BrowseFormBatchNumeric(Folder_BrowseContent):

    batch_template = '/ui/common/browse_batch.xml'
    max_middle_pages = None

    def get_batch_namespace(self, resource, context, items):
        namespace = {}
        batch_start = context.query['batch_start']
        size = context.query['batch_size']
        uri = context.uri

        # Calcul nb_pages and current_page
        total = len(items)
        end = min(batch_start + size, total)
        nb_pages = total / size
        if total % size > 0:
            nb_pages += 1
        current_page = (batch_start / size) + 1

        namespace['control'] = nb_pages > 1

        # Message (singular or plural)
        total = len(items)
        if total == 1:
            namespace['msg'] = self.batch_msg1.gettext()
        else:
            namespace['msg'] = self.batch_msg2.gettext(n=total)

        # Add start & end value in namespace
        namespace['start'] = batch_start + 1
        namespace['end'] = end

        # See previous button ?
        if current_page != 1:
            previous = max(batch_start - size, 0)
            namespace['previous'] = uri.replace(batch_start=previous)
        else:
            namespace['previous'] = None

        # See next button ?
        if current_page < nb_pages:
            namespace['next'] = uri.replace(batch_start=batch_start+size)
        else:
            namespace['next'] = None

        # Add middle pages
        middle_pages = range(max(current_page - 3, 2),
                             min(current_page + 3, nb_pages-1) + 1)

        # Truncate middle pages if nedded
        if self.max_middle_pages:
            middle_pages_len = len(middle_pages)
            if middle_pages_len > self.max_middle_pages:
                delta = middle_pages_len - self.max_middle_pages
                delta_start = delta_end = delta / 2
                if delta % 2 == 1:
                    delta_end = delta_end +1
                middle_pages = middle_pages[delta_start:-delta_end]

        pages = [1] + middle_pages
        if nb_pages > 1:
            pages.append(nb_pages)

        namespace['pages'] = []
        for i in pages:
            namespace['pages'].append(
                {'number': i,
                 'css': 'current' if i == current_page else None,
                 'uri': uri.replace(batch_start=((i-1) * size))})

        # Add ellipsis if needed
        if nb_pages > 5:
            ellipsis = {'number': u'…',
                        'css': 'ellipsis',
                        'uri': None}
            if 2 not in middle_pages:
                namespace['pages'].insert(1, ellipsis)
            if (nb_pages - 1) not in middle_pages:
                namespace['pages'].insert(len(namespace['pages']) - 1,
                                          ellipsis)

        return namespace



############################################################
# RSS
############################################################

class BaseRSS(BaseView):

    access = True

    def get_base_query(self, resource, context):
        # Filter by website
        abspath = resource.get_site_root().get_canonical_path()
        return [ get_base_path_query(str(abspath)) ]


    def get_allowed_formats(self, resource, context):
        return []


    def get_excluded_formats(self, resource, context):
        return []


    def get_excluded_paths(self, resource, context):
        return []


    def get_excluded_container_paths(self, resource, context):
        return []


    def get_max_items_number(self, resource, context):
        return 0


    def get_if_modified_since_query(self, resource, context, if_modified_since):
        if not if_modified_since:
            return []
        return AndQuery(RangeQuery('mtime', if_modified_since, None),
                        NotQuery(PhraseQuery('mtime', if_modified_since)))


    def get_items(self, resource, context, if_modified_since=None):
        # Base query (workflow aware, image, state ...)
        query = self.get_base_query(resource, context)

        # Allowed formats
        formats = self.get_allowed_formats(resource, context)
        if formats:
            if len(formats) > 2:
                query2 = OrQuery(*[ PhraseQuery('format', format)
                                    for format in formats ])
            else:
                query2 = PhraseQuery('format', formats[0])
            query.append(query2)

        # Excluded formats
        excluded_formats = self.get_excluded_formats(resource, context)
        if excluded_formats:
            if len(excluded_formats) > 2:
                query2 = OrQuery(*[ PhraseQuery('format', format)
                                    for format in excluded_formats ])
            else:
                query2 = PhraseQuery('format', excluded_formats[0])
            query.append(NotQuery(query2))

        # An If-Modified-Since ?
        query2 = self.get_if_modified_since_query(resource, context,
                                                  if_modified_since)
        if query2:
            query.append(query2)

        query = AndQuery(*query)
        return resource.get_root().search(query)


    def _sort_and_batch(self, resource, context, results):
        size = self.get_max_items_number(resource, context)
        items = results.get_documents(sort_by='mtime', reverse=True, size=size)
        return items


    def sort_and_batch(self, resource, context, results):
        items = self._sort_and_batch(resource, context, results)
        # Excluded path
        excluded_paths = self.get_excluded_paths(resource, context)
        excluded_paths = [ str(x)
                          for x in excluded_paths ]
        excluded_container_paths = self.get_excluded_container_paths(resource,
                                                                     context)
        excluded_container_paths = [ str(x) for x in excluded_container_paths ]

        # Access Control (FIXME this should be done before batch)
        user = context.user
        root = context.root
        allowed_items = []
        for item in items:
            abspath = item.abspath
            # TODO To improve
            # excluded path
            if excluded_paths:
                if abspath in excluded_paths:
                    print u'SKIP path', abspath
                    continue
            # excluded container
            if excluded_container_paths:
                skip = False
                for path in excluded_container_paths:
                    if abspath.startswith(path):
                        skip = True
                        break
                if skip:
                    print u'SKIP Container', abspath
                    continue
            resource = root.get_resource(abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        return allowed_items


    def get_mtime(self, resource):
        context = get_context()
        items = self.get_items(resource, context)
        items = self.sort_and_batch(resource, context, items)
        # FIXME If there is no modifications ?
        if not items:
            return
        last_brain = items[0][0]
        return last_brain.mtime


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column in ('link', 'guid'):
            value = context.uri.resolve(context.get_link(item_resource))
            return str(value)
        elif column == 'pubDate':
            return brain.mtime
        elif column == 'title':
            return item_resource.get_title()
        elif column == 'description':
            if isinstance(item_resource, WebPage):
                data = item_resource.get_html_data()
                if data is None:
                    # Skip empty content
                    return ''
                # Set the prefix
                prefix = site_root.get_pathto(item_resource)
                data = set_prefix_with_hostname(data, '%s/' % prefix,
                                                uri=context.uri)
                data = stream_to_str_as_xhtml(data)
                return data.decode('utf-8')
            else:
                return item_resource.get_property('description')


    def GET(self, resource, context):
        language = context.get_query_value('language')
        if language is None:
            language = resource.get_content_language(context)
        if_modified_since = context.get_header('if-modified-since')
        items = self.get_items(resource, context, if_modified_since)
        items = self.sort_and_batch(resource, context, items)

        # Construction of the RSS flux
        feed = RSSFile()

        site_root = resource.get_site_root()
        host = context.uri.authority
        # The channel
        channel = feed.channel
        channel['title'] = site_root.get_property('title')
        channel['link'] = 'http://%s/?language=%s' % (host, language)
        channel['description'] = MSG(u'Last News').gettext()
        channel['language'] = language

        # The new items
        feed_items = feed.items
        for item in items:
            ns = {}
            for key in ('link', 'guid', 'title', 'pubDate', 'description'):
                ns[key] = self.get_item_value(resource, context, item, key,
                                              site_root)
            feed_items.append(ns)

        # Filename and Content-Type
        context.set_content_disposition('inline', "last_news.rss")
        context.set_content_type('application/rss+xml')
        return feed.to_str()



############################################################
# Rounded Box
############################################################

class STLBoxView(STLView):

    box_template = '/ui/common/box.xml'

    def GET(self, resource, context):
        stream = STLView.GET(self, resource, context)

        return self.render_box(resource, context, stream)


    def _get_box_css(self, resource, context):
        return None


    def render_box(self, resource, context, stream):
        if isinstance(stream, Reference):
            return stream
        css = self._get_box_css(resource, context)
        return to_box(resource, stream, self.box_template, css)

