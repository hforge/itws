# -*- coding: UTF-8 -*-
# Copyright (C) 2009-2010 Henry Obein <henry@itaapy.com>
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
from operator import itemgetter

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Tokens, Enumerate, DateTime
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import timestamp_widget
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_Edit
from ikaaro.tracker import Tracker
from ikaaro.tracker.datatypes import UsersList, get_issue_fields
from ikaaro.tracker.issue import Issue
from ikaaro.tracker.issue_views import Issue_Edit
from ikaaro.tracker.tracker_views import Tracker_AddIssue
from ikaaro.tracker.tracker_views import Tracker_ChangeSeveralBugs
from ikaaro.tracker.tracker_views import Tracker_Search

# Import from itws
from utils import DualSelectWidget



class RolesList(Enumerate):

    @classmethod
    def get_options(cls):
        site_root = cls.tracker.get_site_root()
        options = []
        for name in site_root.get_role_names():
            option = {'name': name, 'value': site_root.get_role_title(name)}
            options.append(option)

        options.sort(key=itemgetter('value'))
        return options



def get_itws_issue_fields(tracker):
    # Hook assign_to list
    get_value = tracker.get_property
    assigned_to_excluded_roles = get_value('assigned_to_excluded_roles')
    assigned_to_userslist =  UsersList(tracker=tracker,
            excluded_roles=assigned_to_excluded_roles)
    # Hook cc list
    cc_excluded_roles = get_value('cc_excluded_roles')
    cc_list_userslist = UsersList(tracker=tracker, multiple=True,
                                  excluded_roles=cc_excluded_roles)

    return merge_dicts(get_issue_fields(tracker),
                       assigned_to=assigned_to_userslist,
                       cc_list=cc_list_userslist)


###########################################################################
# Views
###########################################################################

class ITWSIssue_Edit(Issue_Edit):

    def get_schema(self, resource, context):
        return get_itws_issue_fields(resource.parent)



class ITWSTracker_Search(Tracker_Search):

    def get_search_namespace(self, resource, context):
        namespace = Tracker_Search.get_search_namespace(self, resource,
                                                        context)
        # Search Form
        get_resource = resource.get_resource
        query = context.query
        search_name = query['search_name']
        if search_name:
            search = get_resource(search_name)
            get_values = search.get_values
        else:
            get_values = query.get

        # Build the namespace
        assigned_to = get_values('assigned_to')

        get_value = resource.get_property
        # Hook assign_to list
        assigned_to_excluded_roles = get_value('assigned_to_excluded_roles')
        userlist =  UsersList(tracker=resource,
                              excluded_roles=assigned_to_excluded_roles)
        namespace['assigned_to'] = userlist.get_namespace(assigned_to)

        return namespace



class ITWSTracker_ChangeSeveralBugs(Tracker_ChangeSeveralBugs):

    def get_namespace(self, resource, context):
        namespace = Tracker_ChangeSeveralBugs.get_namespace(self, resource,
                                                            context)

        get_value = resource.get_property
        # Hook assign_to list
        assigned_to_excluded_roles = get_value('assigned_to_excluded_roles')
        userlist =  UsersList(tracker=resource,
                              excluded_roles=assigned_to_excluded_roles)
        namespace['assigned_to'] = userlist.get_namespace('')

        return namespace



class ITWSTracker_AddIssue(Tracker_AddIssue):

    def get_schema(self, resource, context):
        return get_itws_issue_fields(resource)



class ITWSTracker_Configure(DBResource_Edit):

    title = MSG(u'Configure')
    access = 'is_admin'

    def get_schema(self, resource, context):
        schema = {'timestamp': DateTime(readonly=True),
                  'assigned_to_excluded_roles': RolesList(tracker=resource,
                                                          multiple=True),
                  'cc_excluded_roles': RolesList(tracker=resource,
                                                 multiple=True)
                 }
        return schema


    def get_widgets(self, resource, context):
        widgets = [timestamp_widget]
        widgets.append(DualSelectWidget('assigned_to_excluded_roles',
            title=MSG(u'excluded roles for assign to'),
            has_empty_option=False))
        widgets.append(DualSelectWidget('cc_excluded_roles',
            title=MSG(u'excluded roles for CC'),
            has_empty_option=False))
        return widgets


    def get_value(self, resource, context, name, datatype):
        if name in ('assigned_to_excluded_roles', 'cc_excluded_roles'):
            return list(resource.get_property(name))
        return DBResource_Edit.get_value(self, resource, context, name,
                                         datatype)


    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        for key in ('assigned_to_excluded_roles', 'cc_excluded_roles'):
            resource.set_property(key, form[key])
        # Ok
        context.message = messages.MSG_CHANGES_SAVED



###########################################################################
# Resources
###########################################################################

class ITWSIssue(Issue):

    class_id = 'itws-issue'
    class_title = MSG(u'ITWS Issue')

    edit = ITWSIssue_Edit()



class ITWSTracker(Tracker):

    class_id = 'itws-tracker'
    class_title = MSG(u'ITWS Tracker')
    class_description = MSG(u'A customizable tracker to manage issues')
    class_views = Tracker.class_views + ['configure']

    issue_class = ITWSIssue

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Tracker.get_metadata_schema(),
                           assigned_to_excluded_roles=Tokens(default=''),
                           cc_excluded_roles=Tokens(default=''))


    def get_document_types(self):
        new_types = []
        for _type in Tracker.get_document_types(self):
            if type(_type) is type(Issue):
                new_types.append(ITWSIssue)
            else:
                new_types.append(_type)
        return new_types


    configure = ITWSTracker_Configure()
    search = ITWSTracker_Search()
    change_several_bugs = ITWSTracker_ChangeSeveralBugs()
    add_issue = ITWSTracker_AddIssue()



###########################################################################
# Register
###########################################################################
register_resource_class(ITWSTracker)
register_resource_class(ITWSIssue)
