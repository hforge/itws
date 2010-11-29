# -*- coding: UTF-8 -*-
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2009-2010 Taverne Sylvain <sylvain@itaapy.com>
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

# Import from itools
from itools.gettext import MSG
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import Widget, stl_namespaces



class GoogleMapWidget(Widget):

    width = 400
    height = 400
    key = None

    template = list(XMLParser(
        """
        <script type="text/javascript" src="/ui/widgets/google_map.js"/>
        <div id="map-${name}" style="width:${width}px;height:${height}px;"/>
        <script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"/>
        <script language="javascript">
          $(document).ready(function(){
            initialize_map('map-${name}', ${latitude}, ${longitude}, ${zoom});
          });
        </script>
        """,
        stl_namespaces))


    def get_namespace(self, datatype, value):
        # Build namespace
        namespace = {}
        namespace.update(Widget.get_namespace(self, datatype, value))
        for key in ['latitude', 'longitude', 'zoom']:
            namespace[key] = value[key]
        for key in ['width', 'height']:
            namespace[key] = getattr(self, key)
        return namespace



class GoogleGPSWidget(GoogleMapWidget):

    width = 800
    height = 400
    latitude = None
    longitude = None
    zoom = 5
    scripts = ['/ui/widgets/google_map.js',
               'http://maps.google.com/maps/api/js?sensor=false']

    find_gps_coords_label = MSG(u'Find the GPS coordinates')
    template = list(XMLParser(
        """
        <script type="text/javascript" src="${script}"
          stl:repeat="script scripts"/>
        <label for="address">Address</label><br/>
        <p class="widget">
          <input type="text" name="address" id="address" value="${address}" style="width:50%"/>
          <a href="#" class="button button-ok" onclick="selectGPS('map_${name}');return;">
            ${find_gps_coords_label}
          </a>
        </p>
        <label for="map-${name}">Map:</label><br/>
        <p class="widget">
          <div id="map-${name}" style="width:${width}px;height:${height}px;"/>
        </p>
        <label for="latitude" class="title">Latitude</label><br/>
        <p class="widget">
          <input type="text" id="latitude" name="latitude" value="${latitude}"/>
        </p>
        <label for="longitude" class="title">Longitude</label><br/>
        <p class="widget">
          <input type="text" id="longitude" name="longitude" value="${longitude}"/>
        </p>
        <label for="zoom" class="title">Zoom</label><br/>
        <p class="widget">
          <input type="text" id="zoom" name="zoom" value="${zoom}" size="4"/><br/>
        </p>
        <script language="javascript">
          $(document).ready(function(){
            initialize_gps_map('map-${name}', ${latitude}, ${longitude}, ${zoom});
          });
        </script>
        """,
        stl_namespaces))
