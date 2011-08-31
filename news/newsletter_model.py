# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.database import AndQuery, PhraseQuery
from itools.datatypes import Enumerate, PathDataType, String, Unicode
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaar
from ikaaro.autoform import ImageSelectorWidget, TextWidget, HiddenWidget
from ikaaro.utils import CMSTemplate, get_base_path_query

# Import from itws
from itws.widgets import DualSelectWidget

# Import from newsletter
from newsletter.model import NewsletterModel
from newsletter.model import register_newsletter_model



class News(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        query = [get_base_path_query(str(context.site_root.get_abspath())),
                 PhraseQuery('format','news'),
                 PhraseQuery('workflow_state', 'public')]
        search = root.search(AndQuery(*query))
        resources = [root.get_resource(brain.abspath)
              for brain in search.get_documents(sort_by='mtime', reverse=True)]
        return [{'name': str(res.get_abspath()),
                 'value': res.get_title()}
                   for res in resources]



class Newsletter_Model(NewsletterModel):

    name = 'itws-news'
    title = MSG(u'ITWS Newsletter')

    schema = {'title': Unicode,
              'banner': PathDataType,
              'news': News(multiple=True),
              'model': String(default='itws-news')}
    widgets = [
        TextWidget('title', title=MSG(u'Title')),
        DualSelectWidget('news', title=MSG(u'News')),
        ImageSelectorWidget('banner', title=MSG(u'You can choose a banner')),
        HiddenWidget('model')]

    def render(self, resource, context, form):
        # Banner
        banner = None
        if form['banner']:
            banner = resource.get_resource(form['banner'])
            banner = context.get_link(banner)
        # Get news
        news = []
        for abspath in form['news']:
            n = context.root.get_resource(abspath)
            thumbnail = n.get_preview_thumbnail()
            if thumbnail:
                thumbnail = context.get_link(thumbnail)
            news.append({'title': n.get_title(),
                         'thumbnail': thumbnail,
                         'description': n.get_property('description'),
                         'link': context.get_link(n)})
        # Render
        return CMSTemplate(template='/ui/news/newsletter.xml',
                           news=news, banner=banner,
                           title=form['title']).render()



register_newsletter_model(Newsletter_Model)
