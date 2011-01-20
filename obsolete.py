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
from itools.csv import UniqueError
from itools.datatypes import String, PathDataType
from itools.datatypes import Unicode, Decimal, Integer
from itools.html import stream_is_empty
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.datatypes import Multilingual
from ikaaro.file import File, Image
from ikaaro.folder import Folder
from ikaaro.future.order import ResourcesOrderedContainer
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.registry import register_resource_class
from ikaaro.root import Root
from ikaaro.tracker import Tracker
from ikaaro.user import User
from ikaaro.webpage import WebPage

# Import from itws
from bar.base import Box
from bar.feed_box import BoxFeed
from bar.map_box import MapBox
from bar.html import HTMLContent
from bar.repository import SidebarBoxesOrderedTable
from bar.section import SectionOrderedTable, Section
from tags import TagsAware, TagsList
from ws_neutral import NeutralWS



###########################
# ROOT
###########################
class ITWSRoot(Root):

    class_id = 'itws'
    # 0.61 class_version + 1
    class_version = '20071216'

    def update_20071216(self):
        parent_method = getattr(Root, 'update_20071216', None)
        if parent_method:
            parent_method(self)
        metadata = self.metadata
        metadata.set_changed()
        metadata.version = '20071215' # Restore class version
        metadata.format = Root.class_id



###########################
# Website NeutralWS
###########################
class Old_NeutralWS(NeutralWS):
    """Hook class_schema"""

    # FIXME To remove during the update
    class_schema = merge_dicts(
            NeutralWS.class_schema,
            banner_path=String(source='metadata', multilingual=True,
                               parameters_schema={'lang': String}),
            class_skin=String(source='metadata'),
            favicon=String(source='metadata'),
            banner_title=Multilingual(source='metadata'),
            date_of_writing_format=String(source='metadata'),
            custom_data=String(source='metadata'),
            order=String(source='metadata'))


    def update_20100707(self):
        """Remove obsolete properties"""
        # itws.bar.section.SectionOrderedTable
        from bar.repository import SidebarBoxesOrderedTable
        from bar.section import SectionOrderedTable

        # Remove order property
        order_cls_ids = [SectionOrderedTable.class_id,
                         SidebarBoxesOrderedTable.class_id]

        for resource in self.traverse_resources():
            # Delete order property
            if resource.metadata.format in order_cls_ids:
                resource.del_property('order')
                continue



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
# assigned_to_excluded_roles #==> ikaaro.Tracker.included_roles
# cc_excluded_roles #===> ikaaro.Tracker.included_roles

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

    class_schema = merge_dicts(
            Tracker.class_schema,
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

        # OldIssue -> Issue
        issue_class = self.issue_class

        for issue in self.search_resources(cls=Old_Issue):
            metadata = issue.metadata
            metadata.format = issue_class.class_id
            # There is an update in ikaaro to fix issue between 0.61 and 0.62
            metadata.version = '20100506'
            metadata.set_changed()



class Old_Issue(Folder):

    class_id = 'itws-issue'
    class_version = '20071216'



################################
# Favicon
################################
class FavIcon(Image):

    class_id = 'favicon'



################################
# Address Item
###############################
class AddressItem(WebPage):

    class_id = 'address'
    class_version = '20100408'

    # Schema
    class_schema = merge_dicts(
            WebPage.class_schema,
            # Metadata
            address=Unicode(source='metadata'),
            latitude=Decimal(source='metadata',
                             default=Decimal.encode('48.8566')),
            longitude=Decimal(source='metadata',
                              default=Decimal.encode('2.3509')),
            width=Integer(source='metadata', default=400),
            height=Integer(source='metadata', default=5),
            zoom=Integer(source='metadata', default=5),
            render=String(source='metadata', default='osm'))



class AddressesFolder(Folder):

    class_id = 'addresses-folder'
    class_version = '20101115'

    def update_20101115(self):
        # XXX To test
        # XXX Check CSS
        old_name = self.name
        languages = self.get_site_root().get_property('website_languages')
        # Get list of addresses of addresses folder
        addresses = []
        for address in self.get_resources():
            if address.class_id == 'address':
                kw = {'name': address.name}
                for key in ['address', 'latitude', 'longitude', 'width',
                            'height', 'zoom', 'render']:
                    kw[key] = address.get_property(key)
                # state
                kw['state'] = address.get_workflow_state()
                kw['html'] = {}
                for lang in languages:
                    handler = address.get_handler(language=lang)
                    html =  handler.get_body().events
                    kw['html'][lang] = list(html)
                addresses.append(kw)
        # Delete addresses folder
        self.parent.del_resource(old_name, ref_action='force')
        # Create a section
        section = self.parent.make_resource(old_name, Section, add_boxes=False)
        # AddressFolder was not workflow aware, to not break acl
        # make section public
        section.set_workflow_state('public')
        # Content bar: Get order table
        table = section.get_resource('order-contentbar')
        # Add addresses into section
        for i, address in enumerate(addresses):
            # Add html
            name_html = 'html-map-%s' % i
            html = section.make_resource(name_html, HTMLContent,
                                         state='public', display_title=False)
            for lang in languages:
                if stream_is_empty(address['html'][lang]):
                    continue
                handler = html.get_handler(language=lang)
                handler.events = address['html'][lang]
                handler.set_changed()
            table.add_new_record({'name': name_html})
            # Add map
            name_map = 'map-box-%s' % i
            amap = section.make_resource(name_map, MapBox, state='public')
            for key in ['address', 'latitude', 'longitude', 'width', 'height',
                        'zoom', 'render', 'state']:
                amap.set_property(key, address[key])
            # Do not display the title on section view
            amap.set_property('display_title', False)
            table.add_new_record({'name': name_map})
        # Side bar: Restore boxes (take them from site root)
        # because AdresseFolder could not customized the sidebar
        table = section.get_site_root().get_resource('ws-data/order-sidebar')
        handler = table.handler
        section_table = section.get_resource('order-sidebar')
        for record in handler.get_records_in_order():
            name = handler.get_record_value(record, 'name')
            try:
                section_table.add_new_record({'name': record.name})
            except UniqueError:
                pass



############################
# Slides
############################
class Slide(TagsAware, WebPage):

    class_id = 'slide'
    class_version = '20100618'
    class_schema = merge_dicts(WebPage.class_schema,
                       TagsAware.class_schema,
                       long_title=Multilingual(source='metadata'),
                       image=PathDataType(source='metadata'),
                       template_type=Integer(source='metadata', default=''),
                       href=String(source='metadata'))



class Slides_OrderedTable(ResourcesOrderedTable):

    class_id = 'slides-ordered-table'
    class_schema = merge_dicts(ResourcesOrderedTable.class_schema,
                               order=String(source='metadata'))
    orderable_classes = (Slide,)



class SlideShow(ResourcesOrderedContainer):

    class_id = 'slides'
    class_version = '20101116'

    class_schema = merge_dicts(ResourcesOrderedContainer.class_schema,
                   long_title=Multilingual(source='metadata'),
                   image=PathDataType(source='metadata'),
                   toc_nb_col=Integer(source='metadata', default=2),
                   template_type=Integer(source='metadata', default='1'))

    order_path = 'order-slides'
    order_class = Slides_OrderedTable
    slide_class = Slide


    def update_20101116(self):
        from itws.bar import BoxNavigation

        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        # Get informations
        old_name = self.name
        #long_title = self.get_property('long_title')
        #image = self.get_property('image')
        #toc_nb_col = self.get_property('toc_nb_col')
        #template_type = self.get_property('template_type')
        title = {}
        for lang in languages:
            title[lang] = self.get_property('title', language=lang)
        # Copy resources
        files = self.parent.make_resource('%s_migration_files' % old_name,
                                          Folder)
        path = files.get_abspath()
        for resource in self.traverse_resources():
            if resource.name == self.name:
                continue
            if resource.class_id in ('slide', 'slides-ordered-table'):
                continue
            resource.parent.copy_resource(resource.name,
                                          '%s/%s' % (path, resource.name))
        ordered_slides = list(self.get_ordered_names())
        # Get slides
        slides = []
        for slide in self.get_resources():
            if slide.class_id != 'slide':
                continue
            kw = {'name': slide.name,
                  'state': slide.get_property('state')}
            for key in ['long_title', 'image', 'href',
                        'tags', 'subject', 'template_type']:
                kw[key] = slide.get_property(key)
            kw['html'] = {}
            for lang in languages:
                handler = slide.get_handler(language=lang)
                html =  handler.get_body().get_content_elements()
                kw['html'][lang] = list(html)
            for key in ['title', 'subject']:
                kw[key] = {}
                for lang in languages:
                    kw[key][lang] = slide.get_property(key, language=lang)
            slides.append(kw)
        # Del resource
        self.parent.del_resource(old_name, ref_action='force')
        # Create a section
        section = self.parent.make_resource(old_name, Section, state='public',
                                            add_boxes=False)
        for lang in languages:
            section.set_property('title', title[lang], language=lang)
        for i, slide in enumerate(slides):
            # Add html
            html = section.make_resource(slide['name'], WebPage,
                      state=slide['state'],
                      tags=slide['tags'],
                      display_title=True)

            at_least_one_lang = False
            for lang in languages:
                if stream_is_empty(slide['html'][lang]) is False:
                    at_least_one_lang = True

            for lang in languages:
                html.set_property('thumbnail', slide['image'], language=lang)
                handler = html.get_handler(language=lang)
                img = '<img src="%s/;download"/>' % slide['image']
                if slide['href']:
                    img = "<a href='%s'>%s</a>" % (slide['href'], img)
                data = None
                if at_least_one_lang:
                    # Do not erase ...
                    if stream_is_empty(slide['html'][lang]) is False:
                        data = list(XMLParser(img)) + slide['html'][lang]
                else:
                    data = list(XMLParser(img))
                if data:
                    handler.set_body(data)
                for key in ['title', 'subject']:
                    html.set_property(key,
                        slide[key][lang], language=lang)
        # Order slides
        table = section.get_resource('order-section')
        for name in ordered_slides:
            table.add_new_record({'name': name})
        # End
        for resource in files.traverse_resources():
            if resource.name == files.name:
                continue
            new_name = '../%s/%s' % (self.name, resource.name)
            resource.parent.move_resource(resource.name, new_name)
        # Delete files
        files = self.parent.del_resource('%s_migration_files' % old_name)
        # Add specific NavigationBox which display only ordered resources
        repository = site_root.get_repository()
        box = repository.make_resource('%s-slideshow-tree' % section.name,
                                       BoxNavigation)
        box.set_property('limit_to_current_folder', True)
        box.set_property('limit_to_ordered_resources', True)
        box.set_workflow_state('public')
        table = section.get_order_table_sidebar()
        table.add_new_record({'name': '%s-slideshow-tree' % section.name})
        # populate the section with a feed box which display 5 slides
        container_path = site_root.get_pathto(section)
        box = section.make_resource('feed', BoxFeed,
                state='public', container_path=container_path,
                display_title=False, feed_class_id='webpage',
                count=5, view='/ui/feed_views/Tag_item_viewbox.xml')
        table = section.get_order_table_contentbar()
        table.add_new_record({'name': 'feed'})



#######################################
## Box to feed (replace 3 boxes by one)
########################################
class BoxSectionNews(Box):

    class_id = 'box-section-news'
    class_version = '20101119'
    class_schema = merge_dicts(Box.class_schema,
                               count=Integer(source='metadata', default=3),
                               tags=TagsList(source='metadata', multiple=True,
                                             default=[]))


    def update_20101119(self):
        metadata = self.metadata
        metadata.set_changed()
        metadata.version = BoxFeed.class_version
        metadata.format = BoxFeed.class_id
        metadata.set_property('view', '2')



class ContentBoxSectionNews(BoxSectionNews):

    class_id = 'contentbar-box-section-news'
    class_version = '20101119'


    def update_20101119(self):
        metadata = self.metadata
        metadata.set_changed()
        metadata.version = BoxFeed.class_version
        metadata.format = BoxFeed.class_id
        metadata.set_property('view', '3')



class BoxNewsSiblingsToc(BoxSectionNews):

    class_id = 'box-news-siblings-toc'
    class_version = '20101119'

    def update_20101119(self):
        metadata = self.metadata
        metadata.set_changed()
        metadata.version = BoxFeed.class_version
        metadata.format = BoxFeed.class_id
        metadata.set_property('view', '1')



############################
# ImagesFolder
############################
class ImagesFolder(Folder):
    class_id = 'images-folder'



register_resource_class(ITWSRoot)
register_resource_class(OldUser)
register_resource_class(Old_NeutralWS)
register_resource_class(OldSectionOrderedTable)
register_resource_class(OldSidebarBoxesOrderedTable)
register_resource_class(Old_Tracker)
register_resource_class(Old_Issue)
register_resource_class(Old_TrackerCalendar)
register_resource_class(AddressesFolder)
register_resource_class(AddressItem)
register_resource_class(Slide)
register_resource_class(SlideShow)
register_resource_class(Slides_OrderedTable)
register_resource_class(BoxSectionNews)
register_resource_class(ContentBoxSectionNews)
register_resource_class(BoxNewsSiblingsToc)
register_resource_class(ImagesFolder)
