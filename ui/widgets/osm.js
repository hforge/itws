var map;
var geocoder;
var ol_markers = null; // OpenLayers container
var markers = []; // standard array

function create_marker(latitude, longitude, map) {
  var lonLat = new OpenLayers.LonLat(longitude, latitude)
        .transform(
          new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
          map.getProjectionObject() // to Spherical Mercator Projection
        );
  return new OpenLayers.Marker(lonLat);
}

function add_marker(marker){
  ol_markers.addMarker(marker);
  markers.push(marker);
}

function clean_markers(){
  for(var i=0; i<markers.length; i++){
    marker = markers[i];
    ol_markers.removeMarker(marker);
    marker.erase();
  }
  markers = [];
}

function initialize_map(name, latitude, longitude, zoom) {
  // Google Map
  geocoder = new google.maps.Geocoder();
  // Open Street Map
  map = new OpenLayers.Map(name);
  map.addLayer(new OpenLayers.Layer.OSM());

  ol_markers = new OpenLayers.Layer.Markers("Markers");
  map.addLayer(ol_markers);

  var lonLat = new OpenLayers.LonLat(longitude, latitude)
        .transform(
          new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
          map.getProjectionObject() // to Spherical Mercator Projection
        );
  var marker = create_marker(latitude, longitude, map);
  add_marker(marker);
  map.setCenter(lonLat, zoom);
}

function initialize_gps_map(name, latitute, longitude, zoom){
  initialize_map(name, latitute, longitude, zoom);
  map.events.register('zoomend', null, function() {
     document.getElementById("zoom").value = this.getZoom();
  });
}


function updateFields(point){
  document.getElementById("latitude").value = point.lat().toFixed(7);
  document.getElementById("longitude").value = point.lng().toFixed(7);
  document.getElementById("zoom").value = map.getZoom();
}

function selectGPS(name){
  // Google Map API
  var address = document.getElementById("address").value;
  if (geocoder) {
    /* Search */
    clean_markers();
    geocoder.geocode( { 'address': address}, function(results, status) {
      if (status == google.maps.GeocoderStatus.OK) {
        if (status != google.maps.GeocoderStatus.ZERO_RESULTS) {
          point = results[0].geometry.location;
          // google -> open street map
          var lonLat = new OpenLayers.LonLat(point.lng(), point.lat())
          .transform(
            new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
            map.getProjectionObject() // to Spherical Mercator Projection
          );
          zoom = document.getElementById("zoom").value;
          map.setCenter (lonLat, zoom);
          var marker = create_marker(point.lat(), point.lng(), map);
          add_marker(marker);
          updateFields(point);
        } else {
          alert(address + " not found");
        }
      } else {
        alert("Geocode was not successful for the following reason: " + status);
      }
    });
  } else {
    alert('Geocode not available');
  }
  return false;
}
