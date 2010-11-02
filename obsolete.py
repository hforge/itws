# -*- coding: UTF-8 -*-
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
from itools.datatypes import String

# Import from ikaaro
from ikaaro.datatypes import Multilingual
from ikaaro.file import File, Image
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class
from ikaaro.tracker import Tracker
from ikaaro.tracker.issue import Issue
from ikaaro.user import User

# Import from itws
from bar.repository import SidebarBoxesOrderedTable
from bar.section import SectionOrderedTable
from slides import Slides_OrderedTable
from ws_neutral import NeutralWS



###########################
# Website NeutralWS
###########################
class Old_NeutralWS(NeutralWS):
    """Hook class_schema"""
    # FIXME To remove during the update
    class_schema = merge_dicts(NeutralWS.class_schema,
                               {'google-site-verification': String(source='metadata')},
                               banner_path=String(source='metadata', multilingual=True,
                                                  parameters_schema={'lang': String}),
                               class_skin=String(source='metadata'),
                               favicon=String(source='metadata'),
                               banner_title=Multilingual(source='metadata'),
                               date_of_writing_format=String(source='metadata'),
                               custom_data=String(source='metadata'),
                               order=String(source='metadata'),
                               )


###########################
# Bar/Section
###########################
class OldSectionOrderedTable(SectionOrderedTable):
    """Hook class_schema"""
    class_schema = merge_dicts(SectionOrderedTable.class_schema,
                               order=String(source='metadata'))


class OldSidebarBoxesOrderedTable(SidebarBoxesOrderedTable):
    """Hook class_schema"""
    class_schema = merge_dicts(SidebarBoxesOrderedTable.class_schema,
                               order=String(source='metadata'))



###########################
# Slides
###########################
class OldSlides_OrderedTable(Slides_OrderedTable):
    """Hook class_schema"""
    class_schema = merge_dicts(Slides_OrderedTable.class_schema,
                               order=String(source='metadata'))



###########################
# User
###########################
class OldUser(User):
    """Hook class_schema"""
    class_schema = merge_dicts(User.class_schema,
                               gender=String(source='metadata'),
                               phone1=String(source='metadata'),
                               phone2=String(source='metadata'))



###########################
# Tracker
###########################

# itws-tracker
# itws-issue
# assigned_to_excluded_roles #==> included_roles_assigned_to
# cc_excluded_roles #===> included_roles_cc

class Old_TrackerCalendar(File):
    """Hook class_schema"""
    class_id = 'tracker_calendar'
    class_version = '20090122'

    class_schema = merge_dicts(File.class_schema,
                               state=String(source='metadata'))

class Old_Tracker(Tracker):
    """Hook class_schema"""
    class_id = 'itws-tracker'
    class_version = '20100429'

    class_schema = merge_dicts(Tracker.class_schema,
                               assigned_to_excluded_roles=String(source='metadata'),
                               cc_excluded_roles=String(source='metadata'))

    def update_20100429(self):
        # Do parent
        Tracker.update_20100429(self)
        # Update format
        metadata = self.metadata
        metadata.format = 'tracker'
        metadata.set_changed()
        # Update roles
        site_root = self.get_site_root()
        included_roles = []
        for old_name in ('assigned_to_excluded_roles', 'cc_excluded_roles'):
            excluded = self.get_property(old_name) or []
            metadata.del_property(old_name)
            for x in site_root.get_roles_namespace():
                if x['name'] not in excluded:
                    included_roles.append(x['name'])
        self.set_property('included_roles', tuple(included_roles))



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



register_resource_class(OldUser)
register_resource_class(OldSlides_OrderedTable)
register_resource_class(Old_NeutralWS)
register_resource_class(OldSectionOrderedTable)
register_resource_class(OldSidebarBoxesOrderedTable)
register_resource_class(Old_Tracker)
register_resource_class(Old_Issue)
register_resource_class(New_Issue)
register_resource_class(Old_TrackerCalendar)
