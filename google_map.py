# -*- coding: UTF-8 -*-
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009 Taverne Sylvain <sylvain@itaapy.com>
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

# Import from itools
from itools.gettext import MSG
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import Widget, stl_namespaces



class GoogleMapWidget(Widget):

    width = 400
    height = 400
    key = None

    template = list(XMLParser(
        """
        <script type="text/javascript" src="/ui/addresses/google_map.js"/>
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



class GPSWidget(GoogleMapWidget):

    width = 800
    height = 400

    find_gps_coords_label = MSG(u'Find the GPS coordinates')
    template = list(XMLParser(
        """
        <script type="text/javascript" src="/ui/addresses/google_map.js"/>
        <p>
          Address: <input type="text" name="address" id="address" value="${address}" size="50"/>
          <input  class="button-ok" type="button" value="${find_gps_coords_label}"
              onclick="selectGPS('map_${name}');"/><br/>
        <div id="map-${name}" style="width:${width}px;height:${height}px;"/>
          <label for="latitude">Latitude</label>
          <input type="text" id="latitude" name="latitude" value="${latitude}"/>
          <label for="longitude">Longitude</label>
          <input type="text" id="longitude" name="longitude" value="${longitude}"/>
          <label for="zoom">Zoom</label>
          <input type="text" id="zoom" name="zoom" value="${zoom}" size="4"/><br/>
        </p>
        <script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"/>
        <script language="javascript">
          $(document).ready(function(){
            initialize_gps_map('map-${name}', ${latitude}, ${longitude}, ${zoom});
          });
        </script>
        """,
        stl_namespaces))


    def get_namespace(self, datatype, value):
        context = get_context()
        here = context.resource
        # Build namespace
        namespace = {'find_gps_coords_label': self.find_gps_coords_label}
        namespace.update(Widget.get_namespace(self, datatype, value))
        for key in ['address', 'latitude', 'longitude', 'zoom']:
            namespace[key] = here.get_property(key)
        for key in ['width', 'height']:
            namespace[key] = getattr(self, key)
        return namespace