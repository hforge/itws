# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Obein Henry <henry@itaapy.com>
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
from itools.database import AndQuery, OrQuery, PhraseQuery
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.stl import stl

# Import from ikaaro
from ikaaro.autoform import CheckboxWidget

# Import from itws
from base import Box
from base_views import Box_View



class BoxNavigation_View(Box_View):

    template = '/ui/bar_items/NavigationBox_view.xml'
    tree_template = '/ui/bar_items/NavigationBox_tree.xml'

    def get_classes(self):
        # XXX Should be customizable
        from itws.webpage import WebPage
        from itws.bar import Section

        return [WebPage, Section]


    def get_items(self, container, context, level=1):
        here_abspath = context.resource.abspath
        here_level = len(list(here_abspath))

        # Stop condition
        if here_level < level:
            return None

        root = context.root
        query = PhraseQuery('parent_path', str(container.abspath))

        # format
        format_query = [ PhraseQuery('format', cls.class_id)
                         for cls in self.get_classes() ]
        format_query = OrQuery(*format_query)
        query = AndQuery(query, format_query)
        results = root.search(query)

        # Compute 'in path' path for the current level
        prefix = ['..' for x in range(here_level-(level+1))]
        current_level_in_path = here_abspath.resolve2('/'.join(prefix))

        items = []
        # FIXME sort_by should not be case sensitive
        for doc in results.get_documents(sort_by='title'):
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
                    sub_items = self.get_items(doc, context, level+1)
                if doc.abspath == here_abspath:
                    css = 'active'
                else:
                    css = 'in-path'
            d['items'] = sub_items
            d['css'] = css
            items.append(d)

        template = context.resource.get_resource(self.tree_template)
        return stl(template, namespace={'items': items,
                                        'css': 'root' if level == 1 else None})


    def get_namespace(self, resource, context):
        site_root = resource.get_site_root()
        items = self.get_items(site_root, context)

        # TODO Allow to add title box
        title = resource.get_property('display_title')
        if title:
            title = resource.get_title()

        return {'tree': items, 'title': title}



class BoxNavigation(Box):

    class_id = 'box-navigation'
    class_version = '20100923'
    class_title = MSG(u'Navigation Box')
    class_description = MSG(u'Navigation Tree which display full tree from '
                            u'root')

    class_schema = merge_dicts(Box.class_schema,
                               display_title=Boolean(source='metadata',
                                                     default=True))
    edit_schema = {'display_title': Boolean}
    edit_widgets = [
        CheckboxWidget('display_title',
                        title=MSG(u'Display above the tree'))
        ]
    is_content = False

    # Views
    view = BoxNavigation_View()
