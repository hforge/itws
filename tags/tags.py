# -*- coding: UTF-8 -*-
# Copyright (C) 2008, 2010 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Hervé Cauwelier <herve@itaapy.com>
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
from itools.datatypes import Boolean, DateTime, PathDataType, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.uri import Path, encode_query, get_reference
from itools.web import get_context
from itools.database import AndQuery, PhraseQuery, StartQuery, OrQuery

# Import from ikaaro
from ikaaro.control_panel import ControlPanel
from ikaaro.file import File
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.multilingual import Multilingual
from ikaaro.resource_views import DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.utils import reduce_string
from ikaaro.views_new import NewInstance

# Import from itws
from tags_views import Tag_View, Tag_Edit, Tag_RSS, TagsFolder_TagCloud
from tags_views import TagsList, TagsFolder_BrowseContent



class Tag(File):

    class_id = 'tag'
    class_title = MSG(u'Tag')
    class_version = '20100618'
    class_icon16 = 'itws-icons/16x16/tag.png'
    class_icon48 = 'itws-icons/48x48/tag.png'

    class_views = ['view', 'edit', 'commit_log', 'backlinks']

    backlinks = DBResource_Backlinks(access='is_allowed_to_edit')
    edit = Tag_Edit()
    edit_state = GoToSpecificDocument(specific_document='.',
                                      specific_view='edit')
    externaledit = None
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    new_instance = NewInstance()
    view = Tag_View()
    rss = Tag_RSS()


    def init_resource(self, **kw):
        kw.setdefault('state', 'public')
        File.init_resource(self, **kw)


    def get_title(self, language=None, fallback=True):
        title = self.get_property('title', language=language)
        if title:
            return title
        # Fallback to the resource's name
        if fallback:
            return unicode(self.name)


    def can_paste_into(self, target):
        return isinstance(target, TagsFolder)



class TagsFolder(Folder):

    class_id = 'tags-folder'
    class_title = MSG(u'Tags')
    class_version = '20100118'
    class_icon16 = 'itws-icons/16x16/tags.png'
    class_icon48 = 'itws-icons/48x48/tags.png'
    class_views = ['tag_cloud', 'browse_content', 'new_resource?type=tag',
                   'control_panel']

    # Hide in browse_content
    is_content = False

    tag_class = Tag

    tag_cloud = TagsFolder_TagCloud()
    browse_content = TagsFolder_BrowseContent()
    control_panel = GoToSpecificDocument(specific_document='../',
                                         specific_view='control_panel',
                                         title=ControlPanel.title)

    # Tags to create when creating the tags folder
    default_tags = [('odf', u'ODF'), ('python', u'Python'),
                    ('cms', u'CMS'), ('git', u'GIT')]


    def init_resource(self, **kw):
        site_root = self.get_site_root()
        language = site_root.get_property('website_languages')[0]
        # Create default tags
        for tag in self.default_tags:
            tag_name, title = tag
            self.make_resource(tag_name, Tag, title={language: title})


    def get_document_types(self):
        return [Tag]


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


    def get_tag_brains(self, context, sort_by='name', size=0, state='public'):
        # tags
        abspath = self.get_canonical_path()
        tags_query = AndQuery(PhraseQuery('parent_path', str(abspath)),
                              PhraseQuery('format', Tag.class_id),
                              PhraseQuery('workflow_state', state))
        tags_results = context.root.search(tags_query)
        documents = tags_results.get_documents(sort_by=sort_by, size=size)
        return [ x for x in documents ]



class TagsAware(object):

    class_schema = {
            # Metadata
            'tags': TagsList(source='metadata', multiple=True, indexed=True,
                             stored=True),
            'pub_datetime': DateTime(source='metadata', indexed=True,
                                     stored=True),
            'thumbnail': PathDataType(source='metadata', multilingual=True,
                                      parameters_schema={'lang': String}),
            # Catalog
            'is_tagsaware': Boolean(indexed=True, stored=True),
            'preview_content': Unicode(stored=True, indexed=True),
            }


    def get_catalog_values(self):
        indexes = {'tags': self.get_property('tags')}
        indexes['pub_datetime'] = self.get_property('pub_datetime')
        indexes['is_tagsaware'] = True
        indexes['preview_content'] = self.get_preview_content()
        return indexes

    ##########################################################################
    # TagsAware API
    ##########################################################################

    def get_tags_namespace(self, context):
        tags_folder = self.get_site_root().get_resource('tags')
        # query
        query = encode_query(context.uri.query)

        tags = []
        for tag_name in self.get_property('tags'):
            tag = tags_folder.get_resource(tag_name)
            href = context.get_link(tag)
            if query:
                href = '%s?%s' % (href, query)
            tags.append({'title': tag.get_title(), 'href': href})
        return tags


    def get_pub_datetime(self):
        return self.get_property('pub_datetime')


    def get_long_title(self, language=None):
        return self.get_title(language)


    def get_pub_datetime_formatted(self, language=None):
        pub_datetime = self.get_pub_datetime()
        if pub_datetime is None:
            return None
        return format_datetime(self.get_pub_datetime())


    def has_pub_datetime(self):
        pub_datetime = self.get_pub_datetime()
        return pub_datetime is not None


    def _get_preview_content(self, languages):
        """"Return the preview content used in the tag view
            Method to be overriden by sub-classes.

            By default, return resource.to_text()
        """
        if isinstance(self, Multilingual):
            return self.to_text(languages=languages)
        return self.to_text()


    def get_preview_content(self):
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        content = self._get_preview_content(languages)
        # Reduce content size
        if type(content) is dict:
            for key in content.keys():
                content[key] = reduce_string(content[key], 10000, 255)
        elif isinstance(content, (str, unicode)):
            content = reduce_string(content)

        return content


    def to_text(self, languages=None):
        if languages is None:
            site_root = self.get_site_root()
            languages = site_root.get_property('website_languages')
        proxy = super(TagsAware, self)
        try:
            if isinstance(self, Multilingual):
                return proxy.to_text(languages=languages)
            else:
                return proxy.to_text()
        except NotImplementedError:
            pass
        # Default implementation for "_get_preview_content"
        result = {}
        for language in languages:
            description = self.get_property('description', language=language)
            result[language] = description
        return result


    def get_preview_thumbnail(self):
        path = self.get_property('thumbnail')
        if not path:
            return None
        ref = get_reference(path)
        if ref.scheme:
            return None
        return self.get_resource(path, soft=True)


    ##########################################################################
    # Links API
    ##########################################################################
    def get_links(self):
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        tags_base = site_root.get_abspath().resolve2('tags')
        links = set()

        # Tags
        for tag in self.get_property('tags'):
            links.add(str(tags_base.resolve2(tag)))

        # Thumbnail
        for lang in available_languages:
            path = self.get_property('thumbnail', lang)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            base = self.get_canonical_path()
            links.add(str(base.resolve2(ref.path)))

        return links


    def update_links(self, source, target):
        source = Path(source)
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        # Tags
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

        # Thumbnail
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        for lang in available_languages:
            path = self.get_property('thumbnail', lang)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            path = old_base.resolve2(path)
            if path == source:
                # Hit
                self.set_property('thumbnail', new_base.get_pathto(target),
                                  lang)

        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        # Tags: do nothing

        # Thumbnail
        for lang in available_languages:
            path = self.get_property('thumbnail', lang)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            # Calcul the old absolute path
            old_abs_path = source.resolve2(ref.path)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path,
                                                 old_abs_path)
            self.set_property('thumbnail', target.get_pathto(new_abs_path),
                              lang)
