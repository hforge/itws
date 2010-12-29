# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import from itools
from itools.core import merge_dicts
from itools.database import AndQuery, OrQuery, PhraseQuery, NotQuery
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import MultilineWidget, SelectWidget
from ikaaro.resource_views import DBResource_Edit
from ikaaro.workflow import state_widget, StaticStateEnumerate

# Import from itws
from itws.section_views import SectionViews_Enumerate
from itws.tags.tags_views import TagsAware_Edit
from itws.section_views import section_views_registry
from itws.views import BaseManageContent



class Section_Edit(DBResource_Edit, TagsAware_Edit):


    def _get_schema(self, resource, context):
        return merge_dicts(DBResource_Edit._get_schema(self, resource, context),
                           TagsAware_Edit._get_schema(self, resource, context),
                           view=SectionViews_Enumerate,
                           state=StaticStateEnumerate)


    def _get_widgets(self, resource, context):
        default_widgets = DBResource_Edit._get_widgets(self, resource, context)
        default_widgets[2] = MultilineWidget('description',
                title=MSG(u'Description (use by RSS and TAGS)'))

        return (default_widgets +
                [state_widget] +
                [SelectWidget('view', title=MSG(u'View'),
                              has_empty_option=False)] +
                TagsAware_Edit._get_widgets(self, resource, context))


    def get_value(self, resource, context, name, datatype):
        if name in ('tags', 'pub_date', 'pub_time'):
              return TagsAware_Edit.get_value(self, resource, context, name,
                        datatype)
        return DBResource_Edit.get_value(self, resource, context, name,
                  datatype)


    def set_value(self, resource, context, name, form):
        if name in ('tags', 'pub_date', 'pub_time'):
              return TagsAware_Edit.set_value(self, resource, context, name,
                        form)
        return DBResource_Edit.set_value(self, resource, context, name,
                  form)


    def action(self, resource, context, form):
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return
        if form['view'] != resource.get_property('view'):
            resource.del_resource('section_view', soft=True)
            view = section_views_registry[form['view']]
            cls = view.view_configuration_cls
            if cls:
                resource.make_resource('section_view', view.view_configuration_cls)
        return DBResource_Edit.action(self, resource, context, form)




class Section_ManageContent(BaseManageContent):

    title = MSG(u'Browse')

    def get_items(self, resource, context, *args):
        path = str(resource.get_canonical_path())
        excluded_names = resource.get_internal_use_resource_names()
        query = [ PhraseQuery('parent_path', path),
                 NotQuery(OrQuery(*[ PhraseQuery('name', name)
                                     for name in excluded_names ]))]
        return context.root.search(AndQuery(*query))
