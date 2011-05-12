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
from itools.core import merge_dicts
from itools.datatypes import Integer, Boolean, String

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent

# Import from itws
from base import Feed_View


class MultipleFeed_View(Feed_View):
    """
    Support one query different by viewbox
    """

    # Query suffix
    query_suffix = None

    def _get_query_suffix(self):
        return self.query_suffix


    def _get_query_value(self, resource, context, name):
        query_suffix = self._get_query_suffix()
        key = name
        hidden = key in self.hidden_fields
        if query_suffix not in (None, ''):
            key = '%s_%s' % (name, query_suffix)
        if hidden:
            return context.get_query_value(key)
        return context.query[key]


    def _context_uri_replace(self, context, **kw):
        """Implement context.uri.replace. Take into account
        the query_suffix

        _context_uri_replace(context, batch_size=x)
        """
        query_suffix = self._get_query_suffix()
        if query_suffix:
            d = {}
            for key, value in kw.iteritems():
                d['%s_%s' % (key, query_suffix)] = value
            return context.uri.replace(**d)
        else:
            return context.uri.replace(**kw)


    def get_query_schema(self):
        """We allow to define 2 variable (sort_by and batch_size)"""
        d = merge_dicts(Folder_BrowseContent.get_query_schema(self),
                batch_size=Integer(default=self.batch_size),
                sort_by=String(default=self.sort_by),
                reverse=Boolean(default=self.reverse))

        query_suffix = self._get_query_suffix()
        if query_suffix is None:
            return d

        prefixed_d = {}
        for key, value in d.iteritems():
            prefixed_d['%s_%s' % (key, query_suffix)] = value
        return prefixed_d


    def sort_and_batch(self, resource, context, results):
        user = context.user
        root = context.root

        start = self._get_query_value(resource, context, 'batch_start')
        size = self._get_query_value(resource, context, 'batch_size')
        sort_by = self._get_query_value(resource, context, 'sort_by')
        reverse = self._get_query_value(resource, context, 'reverse')

        if sort_by is None:
            get_key = None
        else:
            get_key = getattr(self, 'get_key_sorted_by_' + sort_by, None)
        if get_key:
            # Custom but slower sort algorithm
            items = results.get_documents()
            items.sort(key=get_key(), reverse=reverse)
            if size:
                items = items[start:start+size]
            elif start:
                items = items[start:]
        else:
            # Faster Xapian sort algorithm
            items = results.get_documents(sort_by=sort_by, reverse=reverse,
                                          start=start, size=size)

        # Access Control (FIXME this should be done before batch)
        allowed_items = []
        for item in items:
            resource = root.get_resource(item.abspath)
            ac = resource.get_access_control()
            if ac.is_allowed_to_view(user, resource):
                allowed_items.append((item, resource))

        return allowed_items


    def get_batch_namespace(self, resource, context, items):
        if self.show_first_batch is False and self.show_second_batch is False:
            return None

        namespace = {}
        batch_start = self._get_query_value(resource, context, 'batch_start')
        uri = context.uri

        # Total & Size
        size = self._get_query_value(resource, context, 'batch_size')
        total = len(items)
        if size == 0:
            nb_pages = 1
            current_page = 1
        else:
            nb_pages = total / size
            if total % size > 0:
                nb_pages += 1
            current_page = (batch_start / size) + 1

        namespace['control'] = nb_pages > 1

        # Message (singular or plural)
        if total == 1:
            namespace['msg'] = self.batch_msg1.gettext()
        else:
            namespace['msg'] = self.batch_msg2.gettext(n=total)

        # See previous button ?
        if current_page != 1:
            previous = max(batch_start - size, 0)
            uri = self._context_uri_replace(context, batch_start=previous)
            namespace['previous'] = uri
        else:
            namespace['previous'] = None

        # See next button ?
        if current_page < nb_pages:
            uri = self._context_uri_replace(context,
                                            batch_start=batch_start+size)
            namespace['next'] = uri
        else:
            namespace['next'] = None

        # Add middle pages
        middle_pages = range(max(current_page - 3, 2),
                             min(current_page + 3, nb_pages-1) + 1)

        # Truncate middle pages if nedded
        if self.batch_max_middle_pages:
            middle_pages_len = len(middle_pages)
            if middle_pages_len > self.batch_max_middle_pages:
                delta = middle_pages_len - self.batch_max_middle_pages
                delta_start = delta_end = delta / 2
                if delta % 2 == 1:
                    delta_end = delta_end +1
                middle_pages = middle_pages[delta_start:-delta_end]

        pages = [1] + middle_pages
        if nb_pages > 1:
            pages.append(nb_pages)

        namespace['pages'] = [
            {'number': i,
             'css': 'current' if i == current_page else None,
             'uri': self._context_uri_replace(context,
                 batch_start=((i-1) * size))}
             for i in pages ]

        # Add ellipsis if needed
        if nb_pages > 5:
            ellipsis = {'uri': None}
            if 2 not in middle_pages:
                namespace['pages'].insert(1, ellipsis)
            if (nb_pages - 1) not in middle_pages:
                namespace['pages'].insert(len(namespace['pages']) - 1,
                                          ellipsis)

        return namespace



    #######################################################################
    # Table
    def get_table_head(self, resource, context, items, actions=None):
        # Get from the query
        sort_by = self._get_query_value(resource, context, 'sort_by')
        reverse = self._get_query_value(resource, context, 'reverse')

        columns = self._get_table_columns(resource, context)
        columns_ns = []
        for name, title, sortable, css in columns:
            if name == 'checkbox':
                # Type: checkbox
                if self.external_form or actions:
                    columns_ns.append({'is_checkbox': True})
            elif title is None or not sortable:
                # Type: nothing or not sortable
                columns_ns.append({
                    'is_checkbox': False,
                    'title': title,
                    'css': 'thead-%s' % name,
                    'href': None,
                    'sortable': False})
            else:
                # Type: normal
                base_href = self._context_uri_replace(context, sort_by=name,
                                                      batch_start=None)
                if name == sort_by:
                    sort_up_active = reverse is False
                    sort_down_active = reverse is True
                else:
                    sort_up_active = sort_down_active = False
                columns_ns.append({
                    'is_checkbox': False,
                    'title': title,
                    'css': 'thead-%s' % name,
                    'sortable': True,
                    'href': context.uri.path,
                    'href_up': base_href.replace(reverse=0),
                    'href_down': base_href.replace(reverse=1),
                    'sort_up_active': sort_up_active,
                    'sort_down_active': sort_down_active
                    })
        return columns_ns
