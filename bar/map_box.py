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

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Unicode, Decimal, Enumerate, Integer, String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import SelectWidget, TextWidget
from ikaaro.resource_views import DBResource_Edit

# Import from itws
from base import Box
from base_views import Box_View
from itws.widgets import GoogleMapWidget, GoogleGPSWidget
from itws.widgets import OpenStreetMapWidget, OpenStreetMapGPSWidget


class OpenLayerRender(Enumerate):

    options = [{'name': 'osm', 'value': MSG(u'Open Street Map')},
               {'name': 'google', 'value': MSG(u'Google Map')}]


class MapBox_View(Box_View):

    template = '/ui/bar_items/map.xml'


    def get_namespace(self, resource, context):
        # XXX
        index = '1'
        kw = {}
        for key in ['latitude', 'longitude', 'zoom', 'width', 'height']:
            kw[key] = resource.get_property(key)
        # FIXME To improve, render
        render = resource.get_property('render')
        if render == 'google':
            map_widget_cls = GoogleMapWidget
        else:
            map_widget_cls = OpenStreetMapWidget
        map = map_widget_cls('map_%s' % index, **kw)
        return {'title': resource.get_title(),
                'map': map.render()}



class MapBox_Edit(DBResource_Edit):

    access = 'is_allowed_to_edit'
    title = MSG(u"Edit address")
    submit_value = MSG(u'Edit address')


    def _get_schema(self, resource, context):
        return merge_dicts(DBResource_Edit._get_schema(self, resource, context),
                           render=OpenLayerRender(mandatory=True),
                           width=Integer, height=Integer, address=Unicode,
                           latitude=Decimal, longitude=Decimal, zoom=Integer,
                           # Hack
                           gps=String)


    def _get_widgets(self, resource, context):
        # What type of map ?
        if resource.get_property('render') == 'google':
            gps_widget_cls = GoogleGPSWidget
        else:
            gps_widget_cls = OpenStreetMapGPSWidget
        # Map configuration
        config_map = {'width': resource.get_property('width'),
                      'height': resource.get_property('height'),
                      'address': resource.get_property('address'),
                      'latitude': resource.get_property('latitude'),
                      'longitude': resource.get_property('longitude'),
                      'zoom': resource.get_property('zoom')}
        # Return widgets
        return DBResource_Edit._get_widgets(self, resource, context) + [
                SelectWidget('render', title=MSG(u'Render map with')),
                TextWidget('width', title=MSG(u'Map width'), size=6),
                TextWidget('height', title=MSG(u'Map height'), size=6),
                gps_widget_cls('gps', title=MSG(u'GPS'), resource=resource,
                              **config_map)]


    def get_value(self, resource, context, name, datatype):
        if name == 'gps':
            return
        return DBResource_Edit.get_value(self, resource,
                  context, name, datatype)


    def set_value(self, resource, context, name, datatype):
        if name == 'gps':
            return
        return DBResource_Edit.set_value(self, resource,
                  context, name, datatype)



class MapBox(Box):

    class_id = 'box-map'
    class_title = MSG(u'Map box')
    class_description = MSG(u'Add a google map or a openstreet map')

    class_schema = merge_dicts(Box.class_schema,
          # Metadata
          address=Unicode(source='metadata'),
          latitude=Decimal(source='metadata', default=Decimal.encode('48.8566')),
          longitude=Decimal(source='metadata', default=Decimal.encode('2.3509')),
          width=Integer(source='metadata', default=400),
          height=Integer(source='metadata', default=300),
          zoom=Integer(source='metadata', default=15),
          render=OpenLayerRender(source='metadata', default='osm'))

    # Configuration
    allow_instanciation = True
    is_content = True
    is_side = True

    view = MapBox_View()
    edit = MapBox_Edit()
