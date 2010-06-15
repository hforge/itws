# -*- coding: UTF-8 -*-
# Copyright (C) 2008, 2010 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
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
from math import ceil
from random import shuffle

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Enumerate, Tokens, Boolean
from itools.datatypes import XMLContent, String, Date
from itools.gettext import MSG
from itools.html import stream_to_str_as_xhtml
from itools.stl import set_prefix
from itools.uri import Path, encode_query
from itools.web import STLView, get_context
from itools.xapian import AndQuery, PhraseQuery, StartQuery, OrQuery
from itools.xapian import RangeQuery, NotQuery, split_unicode

# Import from ikaaro
from ikaaro.buttons import Button
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import XHTMLBody, DateWidget
from ikaaro.registry import register_field, register_resource_class
from ikaaro.resource_views import DBResource_Edit, DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.views import CompositeForm

# Import from itws
from resources import MultilingualCatalogTitleAware, ManageViewAware
from utils import set_prefix_with_hostname, DualSelectWidget
from utils import is_navigation_mode
from views import EasyNewInstance, BaseRSS, ProxyContainerNewInstance



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
                     'value': brain.m_title or brain.name}
                    for brain in tags_folder.get_tag_brains(context) ]

        return options



############################################################
# Views
############################################################
class Tag_RSS(BaseRSS):

    def get_base_query(self, resource, context):
        query = BaseRSS.get_base_query(self, resource, context)
        tags_query = resource.parent.get_tags_query_terms(state='public',
                                                          tags=[resource.name])
        query.extend(tags_query)
        return query


    def get_if_modified_since_query(self, resource, context, if_modified_since):
        if not if_modified_since:
            return []
        return AndQuery(RangeQuery('date_of_writing', if_modified_since, None),
                        NotQuery(PhraseQuery('date_of_writing',
                                             if_modified_since)))


    def _sort_and_batch(self, resource, context, results):
        size = self.get_max_items_number(resource, context)
        items = results.get_documents(sort_by='date_of_writing', reverse=True,
                                      size=size)
        return items


    def get_excluded_container_paths(self, resource, context):
        site_root = resource.get_site_root()
        site_root_abspath = site_root.get_abspath()
        excluded = []
        for name in ('./menu/', './repository/', './ws-data/'):
            excluded.append(site_root_abspath.resolve2(name))
        return excluded


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if column == 'pubDate':
            return brain.date_of_writing
        elif column == 'description':
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



class Tag_ItemView(STLView):

    access = 'is_allowed_to_view'
    template = '/ui/common/Tag_item_view.xml'

    def get_content(self, resource, context):
        return resource.get_html_data()


    def get_namespace(self, resource, context):
        title = resource.get_title()
        link = context.get_link(resource)
        content = self.get_content(resource, context)
        namespace =  {'title': title, 'link': link, 'content': content}
        return namespace



class Tag_View(STLView):

    title = MSG(u'View')
    access = 'is_allowed_to_view'
    template = '/ui/common/Tag_view.xml'
    query_schema = {'formats': String(default=[], multiple=True)}

    def get_namespace(self, resource, context):
        root = context.root
        here = context.resource # equal to resource
        tag = resource.name
        query = self.get_query(context)
        formats = query['formats']
        query = resource.parent.get_tags_query_terms(state='public', tags=[tag],
                                                     formats=formats)
        results = root.search(AndQuery(*query))

        items = []
        for doc in results.get_documents(sort_by='date_of_writing',
                                         reverse=True):
            item = root.get_resource(doc.abspath)
            view = getattr(item, 'tag_view', getattr(item, 'view'))
            if view:
                content = view.GET(item, context)
                # set prefix
                prefix = here.get_pathto(item)
                content = set_prefix(content, '%s/' % prefix)
                items.append({'content': content, 'format': doc.format})

        tag_title = resource.get_title()
        return {'items': items, 'tag_title': tag_title}



class TagsFolder_TagCloud(STLView):

    title = MSG(u'Tag Cloud')
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
            query = {'formats': self.formats}
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
                title = brain.m_title or brain.name
                if self.show_number:
                    title = u'%s (%s)' % (title, nb_items)
                xml_title = title.encode('utf-8')
                xml_title = XMLContent.encode(xml_title)
                xml_title = xml_title.replace(' ', '&nbsp;')
                d['title'] = title
                d['xml_title'] = XHTMLBody.decode(xml_title)
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



class TagsAware_Edit(DBResource_Edit):

    def get_schema(self, resource, context):
        site_root = resource.get_site_root()
        return {'tags': TagsList(site_root=site_root, multiple=True),
                'date_of_writing': Date}


    def get_widgets(self, resource, context):
        return [DualSelectWidget('tags', title=MSG(u'TAGS'), is_inline=True,
            has_empty_option=False),
            DateWidget('date_of_writing', title=MSG(u'Date of writing'))]


    def get_value(self, resource, context, name, datatype):
        if name == 'tags':
            tags = resource.get_property('tags')
            # tuple -> list (enumerate.get_namespace expects list)
            return list(tags)
        elif name == 'date_of_writing':
            return resource.get_property('date_of_writing')


    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        # tags
        resource.set_property('tags', form['tags'])
        resource.set_property('date_of_writing', form['date_of_writing'])



class TagsFolder_BrowseContent(Folder_BrowseContent):

    # Table
    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('items_nb', MSG(u'Items number')),
        ('mtime', MSG(u'Last Modified')),
        ('last_author', MSG(u'Last Author')),
        ('workflow_state', MSG(u'State'))]

    def get_items(self, resource, context, *args):
        # Get the parameters from the query
        query = context.query
        search_term = query['search_term'].strip()
        field = query['search_field']

        abspath = resource.get_abspath()
        query = [PhraseQuery('parent_path', str(abspath)),
                 PhraseQuery('format', Tag.class_id)]
        if search_term:
            language = resource.get_content_language(context)
            terms_query = [ PhraseQuery(field, term)
                            for term in split_unicode(search_term, language) ]
            query.append(AndQuery(*terms_query))
        query = AndQuery(*query)

        return context.root.search(query)


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



class TagsFolder_TagNewInstance(ProxyContainerNewInstance):

    actions = [Button(access='is_allowed_to_edit',
                      name='new_tag', title=MSG(u'Add'))]

    def _get_resource_cls(self, context):
        # FIXME hardcoded
        return Tag


    def _get_container(self, resource, context):
        return resource


    def _get_goto(self, resource, context, form):
        referrer = context.get_referrer()
        if referrer:
            return referrer
        return '.'


    def action_new_tag(self, resource, context, form):
        return ProxyContainerNewInstance.action_default(self, resource,
                context, form)



class Tags_ManageView(CompositeForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Manage view')

    subviews = [ TagsFolder_TagNewInstance(),
                 TagsFolder_BrowseContent() ]


    def _get_form(self, resource, context):
        for view in self.subviews:
            method = getattr(view, context.form_action, None)
            if method is not None:
                form_method = getattr(view, '_get_form')
                return form_method(resource, context)
        return None


############################################################
# Resources
############################################################
class Tag(File, MultilingualCatalogTitleAware):

    class_id = 'tag'
    class_title = MSG(u'Tag')
    class_views = ['view', 'edit', 'commit_log', 'backlinks']

    backlinks = DBResource_Backlinks(access='is_allowed_to_edit')
    edit = DBResource_Edit()
    edit_state = None
    externaledit = None
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    new_instance = EasyNewInstance()
    view = Tag_View()
    rss = Tag_RSS()

    @classmethod
    def get_metadata_schema(cls):
        schema = File.get_metadata_schema()
        schema['state'] = String(default='public')
        return schema


    def _get_catalog_values(self):
        return merge_dicts(File._get_catalog_values(self),
                MultilingualCatalogTitleAware._get_catalog_values(self))


    def get_title(self, language=None, fallback=True):
        title = self.get_property('title', language=language)
        if title:
            return title
        # Fallback to the resource's name
        if fallback:
            return unicode(self.name)


    def can_paste_into(self, target):
        return isinstance(target, TagsFolder)



class TagsFolder(ManageViewAware, Folder):

    class_id = 'tags-folder'
    class_title = MSG(u'Tags')
    class_views = ['tag_cloud', 'manage_view']
    class_version = '20100118'

    tag_cloud = TagsFolder_TagCloud()
    browse_content = TagsFolder_BrowseContent()
    manage_view = Tags_ManageView()

    # Tags to create when creating the tags folder
    default_tags = [('odf', u'ODF'), ('python', u'Python'),
                    ('cms', u'CMS'), ('git', u'GIT')]


    @staticmethod
    def _make_resource(cls, folder, name, language=None, **kw):
        Folder._make_resource(cls, folder, name, **kw)
        if language is None:
            site_root = get_context().resource.get_site_root()
            language = site_root.get_property('website_languages')[0]
        # Create default tags
        for tag in cls.default_tags:
            tag_name, title = tag
            Tag._make_resource(Tag, folder, '%s/%s' % (name, tag_name),
                               title={language: title})


    def get_document_types(self):
        return [ Tag ]


    def get_tags_query_terms(self, state=None, tags=[], formats=[]):
        site_root = self.get_site_root()
        abspath = '%s/' % site_root.get_canonical_path()
        query = [ StartQuery('abspath', abspath),
                  PhraseQuery('is_tagsaware', True) ]

        if state:
            query.append(PhraseQuery('workflow_state', state))
        if tags:
            tags_query = [ PhraseQuery('tags', tag) for tag in tags ]
            if len(tags_query) > 1:
                tags_query = OrQuery(*tags_query)
            else:
                tags_query = tags_query[0]
            query.append(tags_query)
        if formats:
            tags_format = [ PhraseQuery('format', f) for f in formats ]
            if len(tags_format):
                tags_format = OrQuery(*tags_format)
            query.append(tags_format)
        return query


    def is_empty(self, context):
        all_tags_aware_query = self.get_tags_query_terms(state='public')
        all_tags_aware_query = AndQuery(*all_tags_aware_query)

        # tags
        tag_brains = self.get_tag_brains(context)

        # all tags
        all_tags_aware_results = context.root.search(all_tags_aware_query)
        query = [  PhraseQuery('tags', brain.name)
                   for brain in tag_brains ]
        results = all_tags_aware_results.search(OrQuery(*query))

        return len(results) == 0


    def get_tag_brains(self, context, sort_by='name', size=0):
        # tags
        abspath = self.get_canonical_path()
        tags_query = AndQuery(PhraseQuery('parent_path', str(abspath)),
                              PhraseQuery('format', Tag.class_id))
        tags_results = context.root.search(tags_query)
        documents = tags_results.get_documents(sort_by=sort_by, size=size)
        return [ x for x in documents ]



class TagsAware(object):

    # Only useful for the registry
    class_id = 'tags-aware'
    tag_view = Tag_ItemView()

    @classmethod
    def get_metadata_schema(cls):
        # FIXME Replace Tokens by TagsList
        return {'tags': Tokens(), 'date_of_writing': Date}


    def _get_catalog_values(self):
        indexes = {}
        indexes['tags'] = self.get_property('tags')
        indexes['date_of_writing'] = self.get_property('date_of_writing')
        indexes['is_tagsaware'] = True
        return indexes


    def get_tags_namespace(self, context):
        tags_folder = self.get_site_root().get_resource('tags')
        query = encode_query({'format': self.class_id})
        tags = []
        for tag_name in self.get_property('tags'):
            tag = tags_folder.get_resource(tag_name)
            tags.append({'title': tag.get_title(),
                'href': '%s?%s' % (context.get_link(tag), query)})
        return tags


    def get_date_of_writing(self):
        return self.get_property('date_of_writing')


    def get_date_of_writing_formatted(self, language=None):
        site_root = self.get_site_root()
        value = self.get_date_of_writing()
        return site_root.format_date(value, language)


    def has_date_of_writing(self):
        date_of_writing = self.get_date_of_writing()
        return date_of_writing is not None


    def get_links(self):
        site_root = self.get_site_root()
        tags_base = site_root.get_abspath().resolve2('tags')
        links = [ str(tags_base.resolve2(tag))
                  for tag in self.get_property('tags') ]
        return links


    def update_links(self, source, target):
        source = Path(source)
        site_root = self.get_site_root()
        tags_base = site_root.get_abspath().resolve2('tags')
        if tags_base.get_prefix(source) == tags_base:
            tags = list(self.get_property('tags'))
            source_name = source.get_name()
            target_name = Path(target).get_name()
            for tag in tags:
                if tag == source_name:
                    # Hit
                    index = tags.index(source_name)
                    tags[index] = target_name
                    self.set_property('tags', tags)
        get_context().database.change_resource(self)



register_resource_class(TagsFolder)
register_resource_class(Tag)

register_field('is_tagsaware', Boolean(is_indexed=True))
register_field('tags', String(is_stored=True, is_indexed=True, multiple=True))
register_field('date_of_writing', Date(is_stored=True, is_indexed=True))
