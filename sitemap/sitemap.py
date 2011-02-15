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

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.gettext import MSG
from itools.stl import stl
from itools.web import BaseView
from itools.database import AndQuery, OrQuery, PhraseQuery, NotQuery
from itools.database import RangeQuery

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.utils import get_base_path_query


EPOCH = datetime(1970, 1, 1, 0, 0)


class SiteMapView(BaseView):

    template = '/ui/common/sitemap.xml'
    access = True


    def get_items_query(self, resource, context):
        site_root = resource.parent
        abspath = site_root.get_canonical_path()
        query = [
            get_base_path_query(str(abspath)),
            PhraseQuery('workflow_state', 'public'),
            PhraseQuery('is_image', False),
            PhraseQuery('is_content', True)]

        # Allow news folder
        newsfolder = site_root.get_news_folder(context)
        if newsfolder:
            news_query = list(query)
            news_format = newsfolder.news_class.class_id
            query.append(NotQuery(PhraseQuery('format', news_format)))
            news_query += [
                PhraseQuery('format', news_format),
                RangeQuery('pub_datetime', EPOCH, datetime.now())]
            query = OrQuery(AndQuery(*query), AndQuery(*news_query))
        else:
            query = AndQuery(*query)

        query = OrQuery(query, PhraseQuery('abspath', str(abspath)))

        return query


    def get_items(self, resource, context):
        # items are brains
        query = self.get_items_query(resource, context)
        root = context.root
        results = root.search(query)
        return results.get_documents(sort_by='abspath')


    def get_item_value(self, resource, context, item, column, site_root):
        # items are brains
        brain = item

        if column == 'loc':
            path_reference = brain.abspath
            r_abspath = resource.get_abspath()
            path_to_brain_resource = r_abspath.get_pathto(path_reference)
            return context.uri.resolve('/%s' % path_to_brain_resource)
        elif column == 'lastmod':
            # TODO Find a solution for aggregators of views/contents
            # (Aggregators of news/tags/webpages)
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

    # Hide in browse_content
    is_content = False

    view = SiteMapView()


    def get_document_types(self):
        return []
