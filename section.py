# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
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
from itools.datatypes import String, Boolean
from itools.gettext import MSG
from itools.stl import rewrite_uris
from itools.uri import get_reference, Path, Reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.folder_views import Folder_PreviewContent, GoToSpecificDocument
from ikaaro.future.order import ResourcesOrderedTable, ResourcesOrderedContainer
from ikaaro.multilingual import Multilingual
from ikaaro.registry import register_resource_class
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.table import OrderedTableFile
from ikaaro.webpage import _get_links, _change_link

# Import from itws
from bar import SideBarAware, ContentBarAware
from repository import Repository
from section_views import SectionOrderedTable_View
from section_views import Section_Edit, Section_View, Section_ManageView
from webpage import WebPage



################
# Order tables #
###########################################################################

class SectionOrderedTableFile(OrderedTableFile):

    record_properties = {
        'name': String(mandatory=True, unique=True, is_indexed=True)}



class SectionOrderedTable(ResourcesOrderedTable):

    class_id = 'section-ordered-table'
    class_title = MSG(u'Order section')
    class_views = ['view']
    class_handler = SectionOrderedTableFile
    view = SectionOrderedTable_View(title=MSG(u'Order Webpages/Sections'))

    # Order view title & description configuration
    ordered_view_title = MSG(u'Order Sections and Webpages')
    ordered_view_title_description = None
    unordered_view_title = MSG(u'Available Sections and Webpages')
    unordered_view_title_description = MSG(
            u'This Sections/Webpages are available, '
            u'you can make them visible in this section '
            u'by adding them to the ordered list')

    def get_orderable_classes(self):
        # Orderable classes should be
        # 1 - my parent
        # 2 - my_parent.get_article_class
        return (WebPage, Section)

    orderable_classes = property(get_orderable_classes, None, None, '')



class Section(SideBarAware, ContentBarAware, ResourcesOrderedContainer):

    class_id = 'section'
    class_title = MSG(u'Section')
    class_description = MSG(u'Section allows to customize the "central part" '
                            u'and the sidebar. Section can contain subsections')
    class_version = '20100403'
    class_icon16 = 'common/icons/16x16/section.png'
    class_icon48 = 'common/icons/48x48/section.png'
    class_views = ['view', 'manage_view', 'backlinks', 'commit_log']
    __fixed_handlers__ = (Folder.__fixed_handlers__
                          + SideBarAware.__fixed_handlers__
                          + ContentBarAware.__fixed_handlers__
                          + ['order-section'])
    # Order Articles
    order_path = 'order-section'
    order_class = SectionOrderedTable

    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        root = get_context().root
        ResourcesOrderedContainer._make_resource(cls, folder, name, **kw)
        SideBarAware._make_resource(cls, folder, name, **kw)
        ContentBarAware._make_resource(cls, folder, name, **kw)
        # Preorder specific contentbar items
        table_name = cls.contentbar_name
        table = root.get_resource('%s/%s/%s' % (folder.key, name, table_name))
        for name2 in (Repository.section_content_children_toc_view_name,
                      Repository.section_articles_view_name):
            table.add_new_record({'name': name2})

        # Preorder specific sidebar items
        table_name = cls.sidebar_name
        table = root.get_resource('%s/%s/%s' % (folder.key, name, table_name))
        name2 = Repository.section_sidebar_children_toc_view_name
        table.add_new_record({'name': name2})


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           show_one_article=Boolean)


    def get_editorial_documents_types(self):
        # FIXME Should be merge with get_document_types
        types = [ self.get_subsection_class(),
                  self.get_article_class() ]
        return types


    def get_document_types(self):
        types = Folder.get_document_types(self)[:]
        # Do not add format twice
        cls_id_types = [ cls.class_id for cls in types ]
        subsection_cls = self.get_subsection_class()
        article_cls = self.get_article_class()
        if subsection_cls.class_id not in cls_id_types:
            types.append(subsection_cls)
        if article_cls.class_id not in cls_id_types:
            types.append(article_cls)
        return types


    def get_links(self):
        base = self.get_canonical_path()
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')

        links = []
        for language in languages:
            events = self.get_property('data', language=language)
            if not events:
                continue
            if events:
                links.extend(_get_links(base, events))

        return links


    def update_links(self, source, target):
        # Caution multilingual property
        site_root = self.get_site_root()
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        available_languages = site_root.get_property('website_languages')
        for language in available_languages:
            events = self.get_property('data', language=language)
            if not events:
                continue
            events = _change_link(source, target, old_base, new_base,
                                  events)
            self.set_property('data', list(events), language=language)

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        def my_func(value):
            # Absolute URI or path
            uri = get_reference(value)
            if uri.scheme or uri.authority or uri.path.is_absolute():
                return value
            path = uri.path
            if not path or path.is_absolute() and path[0] == 'ui':
                return value

            # Strip the view
            name = path.get_name()
            if name and name[0] == ';':
                view = '/' + name
                path = path[:-1]
            else:
                view = ''

            # Resolve Path
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Get the 'new' absolute parth
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)

            path = str(target.get_pathto(new_abs_path)) + view
            value = Reference('', '', path, uri.query.copy(), uri.fragment)
            return str(value)

        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')
        for language in available_languages:
            events = self.get_property('data', language=language)
            if not events:
                continue
            events = rewrite_uris(events, my_func)
            self.set_property('data', events, language=language)


    def get_subsection_class(self):
        return type(self)


    def get_article_class(self):
        return WebPage


    def is_empty(self):
        # XXX And the ACLs ???
        if self.get_ordered_names():
            return False
        return True


    def get_available_languages(self, languages):
        available_langs = []
        names = list(self.get_ordered_names())

        for language in languages:
            for name in names:
                if name.startswith('../'):
                    name = name[3:]
                item = self.get_resource(name)
                if isinstance(item, Multilingual):
                    if item.get_handler(language=language).is_empty() is False:
                        # get_handler always returns a handler
                        available_langs.append(language)
                        break
                else:
                    available_langs.append(language)
                    break
                    # TODO Check Multilingual objects into current folder
                    # inner_languages = item.get_available_languages(languages)
                    # available_langs.extend(inner_languages)
        return available_langs


    def get_sub_sections(self, not_empty=False):
        section_cls = self.get_subsection_class()
        for name in self.get_ordered_names():
            item = self.get_resource(name)
            if not isinstance(item, section_cls):
                continue
            if not_empty is True and item.is_empty():
                continue
            yield item


    def get_n_articles_by_state(self):
        article_cls = self.get_article_class()
        states = {'public': 0, 'pending': 0, 'private': 0}
        for name in self.get_ordered_names():
            item = self.get_resource(name)
            if not isinstance(item, article_cls):
                continue
            states[item.get_statename()] += 1
        return states


    edit = Section_Edit()
    order_items = GoToSpecificDocument(specific_document='order-section',
            title=MSG(u'Order the webpages/sections'))
    view = Section_View()
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    manage_view = Section_ManageView()



register_resource_class(Section)
register_resource_class(SectionOrderedTable)
