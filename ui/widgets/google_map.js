var map;
var geocoder;
var markers = [];

function add_marker(marker){
  markers[this.markers.length] = marker;
}

function clean_markers(){
  for(var i=0; i<markers.length; i++){
    markers[i].setMap(null);
  }
}

function initialize_map(name, latitude, longitude, zoom) {
  geocoder = new google.maps.Geocoder();
  var myLatlng = new google.maps.LatLng(latitude, longitude);
  var myOptions = {
   zoom: zoom,
   center: myLatlng,
   mapTypeId: google.maps.MapTypeId.ROADMAP
  }
  map = new google.maps.Map(document.getElementById(name), myOptions);
  var marker = new google.maps.Marker({
      position: myLatlng,
      map: map
  });
  add_marker(marker);
}

function initialize_gps_map(name, latitute, longitude, zoom){
  initialize_map(name, latitute, longitude, zoom);
  google.maps.event.addListener(map, 'zoom_changed', function() {
    document.getElementById("zoom").value = map.getZoom();
  });
}


function updateFields(point){
  document.getElementById("latitude").value = point.lat().toFixed(7);
  document.getElementById("longitude").value = point.lng().toFixed(7);
  document.getElementById("zoom").value = map.getZoom();
}

function selectGPS(name){
  var address = document.getElementById("address").value;
  if (geocoder) {
    /* Search */
    clean_markers();
    geocoder.geocode( { 'address': address}, function(results, status) {
      if (status == google.maps.GeocoderStatus.OK) {
        if (status != google.maps.GeocoderStatus.ZERO_RESULTS) {
          point = results[0].geometry.location;
          map.setCenter(point, 14);
          var marker = new google.maps.Marker({
              map: map,
              position: point,
              draggable: true
          });
          add_marker(marker);
          updateFields(point);
          google.maps.event.addListener(marker, 'dragend', function(){
              updateFields(this.getPosition());
          });
        } else {
          alert(address + " not found");
        }
      } else {
        alert("Geocode was not successful for the following reason: " + status);
      }
    });
  }
}
