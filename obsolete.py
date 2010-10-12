# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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

from itools.datatypes import String

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class
from ikaaro.tracker import Tracker, Issue

###########################
# Tracker
###########################

# itws-tracker
# itws-issue
# assigned_to_excluded_roles #==> included_roles_assigned_to
# cc_excluded_roles #===> included_roles_cc

class Old_TrackerCalendar(Folder):
    class_id = 'tracker_calendar'
    class_version = '20090122'

class Old_Tracker(Tracker):

    class_id = 'itws-tracker'
    class_version = '20100429'

    def update_20100429(self):
        # Do parent
        Tracker.update_20100429(self)
        # Update format
        metadata = self.metadata
        metadata.format = 'tracker'
        metadata.set_changed()
        # Update roles
        site_root = self.get_site_root()
        for old_name, new_name in [('assigned_to_excluded_roles', 'included_roles_assigned_to'),
                                   ('cc_excluded_roles', 'included_roles_cc')]:
            roles = []
            excluded = self.get_property(old_name)
            metadata.del_property(old_name)
            for x in site_root.get_roles_namespace():
                if x['name'] not in excluded:
                    roles.append(x['name'])
            self.set_property(new_name, tuple(roles))



class Old_Issue(Folder):

    class_id = 'itws-issue'
    class_version = '20101108'

    def update_20101108(self):
        metadata = self.metadata
        metadata.format = 'issue'
        metadata.set_changed()

class New_Issue(Issue):
    class_id = 'issue'
    class_version = '20101108'

################################
# Favicon
################################
class FavIcon(Image):

    class_id = 'favicon'

    @classmethod
    def get_metadata_schema(cls):
        schema = Image.get_metadata_schema()
        schema['state'] = String(default='public')
        return schema

register_resource_class(Old_Tracker)
register_resource_class(Old_Issue)
register_resource_class(New_Issue)
register_resource_class(Old_TrackerCalendar)
