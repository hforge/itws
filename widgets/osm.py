# -*- coding: UTF-8 -*-
# Copyright (C) 2009 J. David Ibanez <jdavid@itaapy.com>
# Copyright (C) 2009-2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2009-2011 Henry Obein <henry@itaapy.com>
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

# Import from ikaaro
from ikaaro.autoform import make_stl_template

# Import from itws
from google_map import GoogleMapWidget, GoogleGPSWidget



class OpenStreetMapWidget(GoogleMapWidget):

    template = make_stl_template("""
    <script type="text/javascript" src="/ui/widgets/osm.js"/>
    <div id="map-${name}" style="width:${width}px;height:${height}px;"/>
    <script type="text/javascript"
            src="http://maps.google.com/maps/api/js?sensor=false"/>
    <script type="text/javascript"
            src="http://www.openlayers.org/api/OpenLayers.js"/>
    <script language="javascript">
      $(document).ready(function(){
        initialize_map('map-${name}', ${latitude}, ${longitude}, ${zoom});
      });
    </script>""")



class OpenStreetMapGPSWidget(GoogleGPSWidget):

    scripts = ['/ui/widgets/osm.js',
               'http://maps.google.com/maps/api/js?sensor=false',
               'http://www.openlayers.org/api/OpenLayers.js']
