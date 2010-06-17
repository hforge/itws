/*
 * MENU
 */
function show_sub_item(id) {
  var elt = document.getElementById(id);
  if (elt)
    elt.style.display = 'block';
}

function hide_sub_item(id) {
  var elt = document.getElementById(id);
  if (elt)
    elt.style.display = 'none';
}

/*
 * More news
 */
function show_more_news(link) {
    $(link).parent().parent().children('.hidden').show('fast');
    $(link).parent().hide();
    return false;
}

/* Admin bar */
$(document).ready(function() {
  $(".admin-bar[rel='fancybox']").click(function(e){
    $.fancybox(
      {'type': 'iframe',
       'transitionIn': 'none',
       'transitionOut': 'none',
       'href': this.href + '?is_admin_popup=1',
       'overlayColor': '#729FCF',
       'overlayOpacity': 0.8,
       'onClosed': function() { window.location.reload()},
       'height': 550,
       'centerOnScroll': true});
    return false;
  });
});
