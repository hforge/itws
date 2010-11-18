# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2010 Taverne Sylvain <sylvain@itaapy.com>
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
from itools.gettext import MSG
from itools.stl import stl
from itools.web import BaseView
from itools.database import AndQuery, OrQuery, PhraseQuery, NotQuery

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.utils import get_base_path_query



class SiteMapView(BaseView):

    template = '/ui/common/sitemap.xml'
    access = True


    def get_items_query(self, resource, context):
        site_root = resource.parent
        query = AndQuery(PhraseQuery('workflow_state', 'public'),
                         PhraseQuery('is_image', False))

        # Allow news folder
        newsfolder_cls = site_root.newsfolder_class
        if newsfolder_cls:
            query = OrQuery(query,
                            PhraseQuery('format', newsfolder_cls.class_id))

        # Excluded paths
        excluded_paths = self.get_excluded_paths(resource, context)
        if excluded_paths:
            if len(excluded_paths) > 1:
                query2 = OrQuery(*[ PhraseQuery('abspath', str(path))
                                    for path in excluded_paths ])
            else:
                query2 = PhraseQuery('abspath', str(excluded_paths[0]))
            query = AndQuery(query, NotQuery(query2))

        # Excluded container paths
        excluded_cpaths = self.get_excluded_container_paths(resource, context)
        if excluded_cpaths:
            if len(excluded_cpaths) > 1:
                query2 = OrQuery(*[ get_base_path_query(str(path))
                                    for path in excluded_cpaths ])
            else:
                query2 = get_base_path_query(str(excluded_cpaths[0]))
            query = AndQuery(query, NotQuery(query2))

        abspath = site_root.get_canonical_path()
        query1 = get_base_path_query(str(abspath))
        query = AndQuery(query, query1)

        # Do not include content/side bar items
        repository = site_root.get_repository()
        bar_item_classes = repository._get_document_types()
        bar_query = [ PhraseQuery('format', cls.class_id)
                      for cls in bar_item_classes ]
        bar_query = NotQuery(OrQuery(*bar_query))
        query = AndQuery(query, bar_query)

        # Add site root -> /
        query = OrQuery(query,
                        PhraseQuery('abspath', str(abspath)))

        # FIXME Should be customizable
        # Add about-itws
        about_itws_abspath = abspath.resolve2('about-itws')
        query = OrQuery(query,
                        PhraseQuery('abspath', str(about_itws_abspath)))

        return query


    def get_items(self, resource, context):
        # items are brains
        query = self.get_items_query(resource, context)
        root = context.root
        results = root.search(query)
        return results.get_documents(sort_by='abspath')


    def get_excluded_paths(self, resource, context):
        site_root = resource.parent
        abspath = site_root.get_canonical_path()

        excluded = []
        for name in ('404', 'robots.txt', 'style'):
            excluded.append(str(abspath.resolve2(name)))

        return excluded


    def get_excluded_container_paths(self, resource, context):
        site_root = resource.parent
        abspath = site_root.get_canonical_path()

        excluded = []
        for name in ('footer', 'menu', 'repository', 'ws-data'):
            excluded.append(str(abspath.resolve2(name)))

        return excluded


    def get_item_value(self, resource, context, item, column, site_root):
        # items are brains
        brain = item

        if column == 'loc':
            path_reference = brain.abspath
            r_abspath = resource.get_abspath()
            path_to_brain_resource = r_abspath.get_pathto(path_reference)
            return context.uri.resolve('/%s' % path_to_brain_resource)
        elif column == 'lastmod':
            # FIXME To improve
            newsfolder_format = site_root.newsfolder_class.class_id
            if brain.format == newsfolder_format:
                # Return last news mtime
                # XXX get_news do no exist
                news_folder = resource.get_resource(brain.abspath)
                news_brains = news_folder.get_news(context, brain_only=True)
                if news_brains:
                    return news_brains[0].mtime.strftime('%Y-%m-%d')

            return brain.mtime.strftime('%Y-%m-%d')


    def get_namespace(self, resource, context):
        urls = []
        site_root = resource.parent

        for brain in self.get_items(resource, context):
            row = {}
            for column in ('loc', 'lastmod'):
                row[column] = self.get_item_value(resource, context, brain,
                                                  column, site_root)
            urls.append(row)

        return {'urls': urls}


    def GET(self, resource, context):
        # Get the namespace
        namespace = self.get_namespace(resource, context)
        # Return xml
        context.set_content_type('text/xml')
        # Ok
        template = resource.get_resource(self.template)
        return stl(template, namespace, mode='xml')



class SiteMap(Folder):

    class_id = "sitemap"
    class_title = MSG(u'Sitemap')
    class_views = ['view']

    view = SiteMapView()

