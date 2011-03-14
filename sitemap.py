# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2008-2009 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2008-2010 Henry Obein <henry@itaapy.com>
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
from itools.datatypes import Integer
from itools.gettext import MSG
from itools.stl import stl
from itools.web import BaseView
from itools.xapian import AndQuery, OrQuery, PhraseQuery, NotQuery

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class
from ikaaro.utils import get_base_path_query



class SiteMapView(BaseView):

    template = '/ui/common/sitemap.xml'
    access = True
    query_schema = {'id': Integer}


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


    def get_namespace(self, resource, context):
        # Max urls according to sitemaps.org is 50000
        # Set to 5000 for performances
        max_urls = 5000
        urls = []
        sitemaps = []

        query = self.get_items_query(resource, context)
        items = context.root.search(query)

        nb_items = len(items)
        id_sitemap = context.query['id']
        if nb_items <= max_urls or id_sitemap:
            # id_sitemap is None if id is not specified in the query
            start = 0 if id_sitemap is None else (id_sitemap - 1) * max_urls
            base_uri = str(context.uri.resolve('/'))
            for brain in items.get_documents(sort_by='abspath',
                                             start=start, size=max_urls):
                uri = '/'.join(brain.abspath.split('/')[2:])
                urls.append(
                    {'loc': base_uri + uri,
                     'lastmod': brain.mtime.strftime('%Y-%m-%d')})
        else:
            nb_sitemaps = nb_items / max_urls
            if nb_items % max_urls > 0:
                nb_sitemaps += 1
            for i in range(1, nb_sitemaps+1):
                loc = context.uri.replace(id=i)
                sitemaps.append(str(loc))

        return {'urls': urls, 'sitemaps': sitemaps}


    def GET(self, resource, context):
        # Get the namespace
        namespace = self.get_namespace(resource, context)
        # Return xml
        context.set_content_type('text/xml')
        # Generate xml
        from time import time
        template = resource.get_resource(self.template)
        t0 = time()
        data = stl(template, namespace, mode='xml')
        t1 = time()
        print '--->', t1-t0
        return data




class SiteMap(Folder):

    class_id = "sitemap"
    class_title = MSG(u'Sitemap')
    class_views = ['view']

    view = SiteMapView()



register_resource_class(SiteMap)
