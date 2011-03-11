# -*- coding: UTF-8 -*-
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
# Copyright (C) 2011 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2011 Nicolas Deram <nicolas@itaapy.com>
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
from itools.database import AndQuery, OrQuery, PhraseQuery
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.stl import stl

# Import from ikaaro
from ikaaro.utils import get_base_path_query

# Import from itws
from bar_aware import SideBarAware
from base import Box
from base_views import Box_View
from itws.webpage import WebPage
from section import Section



class BoxNavigation_View(Box_View):

    template = '/ui/bar_items/NavigationBox_view.xml'
    tree_template = '/ui/bar_items/NavigationBox_tree.xml'


    def get_classes(self):
        return [WebPage, Section]


    def get_items(self, container, context, level=1, only_ordered=False):
        root = context.root
        here_abspath = context.resource.abspath
        here_level = len(list(here_abspath))

        # Stop condition
        if here_level < level:
            return None

        container_resource = root.get_resource(container.abspath)
        # XXX Site root should use menu as ordered resources
        if only_ordered is True and isinstance(container_resource, Section):
            # Only ordered resources are allowed
            container_abspath = container_resource.get_abspath()
            allowed = [ container_abspath.resolve2(name)
                        for name in container_resource.get_ordered_names() ]
            query = OrQuery(*[ PhraseQuery('abspath', str(abspath))
                               for abspath in allowed ])
            results = root.search(query)
            # Same API as below
            items_docs = []
            for path in allowed:
                item = container_resource.get_resource(name)
                sub_result = results.search(PhraseQuery('name',
                                                        path.get_name()))
                doc = sub_result.get_documents()[0]
                items_docs.append((item, doc))
        else:
            # Compute the query and get the documents
            query = get_base_path_query(container.abspath, depth=1)
            # format
            format_query = [ PhraseQuery('format', cls.class_id)
                             for cls in self.get_classes() ]
            format_query = OrQuery(*format_query)

            query = AndQuery(query, format_query)
            results = root.search(query)
            # Sort documents by title.lower
            docs = results.get_documents()
            docs.sort(key=lambda x: x.title.lower())
            items_docs = [ (root.get_resource(doc.abspath), doc)
                           for doc in docs ]

        # Compute 'in path' path for the current level
        prefix = ['..' for x in range(here_level-(level+1))]
        current_level_in_path = here_abspath.resolve2('/'.join(prefix))

        items = []
        user = context.user

        for item, doc in items_docs:
            # ACL
            ac = item.get_access_control()
            if ac.is_allowed_to_view(user, item) is False:
                continue
            d = {'href': context.get_link(doc),
                 'title': doc.title or doc.name,
                 'format': doc.format,
                 'abspath': doc.abspath}

            sub_items = []
            css = None
            if doc.abspath == current_level_in_path:
                q = AndQuery(PhraseQuery('abspath', str(doc.abspath)),
                             PhraseQuery('is_folder', True))
                if len(root.search(q)) == 1:
                    sub_items = self.get_items(doc, context, level+1,
                                               only_ordered)
                if doc.abspath == here_abspath:
                    css = 'active'
                else:
                    css = 'in-path'
            d['items'] = sub_items
            d['css'] = css
            items.append(d)

        # FIXME BoxView API
        if len(items):
            self.set_view_is_empty(False)

        template = context.resource.get_resource(self.tree_template)
        return stl(template, namespace={'items': items,
                                        'css': 'root' if level == 1 else None})


    def get_namespace(self, resource, context):
        ltcf = resource.get_property('limit_to_current_folder')
        ltor = resource.get_property('limit_to_ordered_resources')
        level = 1
        if ltcf:
            container = context.resource
            if isinstance(container, SideBarAware) is False:
                container = container.parent
            level = len(list(container.abspath))
        else:
            container = resource.get_site_root()

        # FIXME BoxView API
        self.set_view_is_empty(True)

        items = self.get_items(container, context, only_ordered=ltor,
                               level=level)
        title = resource.get_property('display_title')
        if title:
            title = resource.get_title()

        return {'tree': items, 'title': title}



class BoxNavigation(Box):

    class_id = 'box-navigation'
    class_version = '20100923'
    class_title = MSG(u'Navigation box')
    class_description = MSG(u'Navigation tree which displays a full tree from '
                            u'root.')
    class_icon16 = 'bar_items/icons/16x16/box_navigation.png'
    class_icon48 = 'bar_items/icons/48x48/box_navigation.png'

    class_schema = merge_dicts(
        Box.class_schema,
        display_title=Boolean(source='metadata', default=True,
                              title=MSG(u'Display title')),
        limit_to_current_folder=Boolean(
                       source='metadata', default=False,
                       title=MSG(u'Use current section as tree root')),
        limit_to_ordered_resources=Boolean(source='metadata',
                       title=MSG(u'Display ordered resources only.'),
                       default=False))

    # Configuration of automatic edit view
    # XXX Workflow state
    edit_fields = freeze(['display_title', 'limit_to_current_folder',
                          'limit_to_ordered_resources'])

    # Configuration
    is_contentbox = False

    # Views
    view = BoxNavigation_View()
