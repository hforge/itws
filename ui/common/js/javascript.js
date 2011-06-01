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

$(document).ready(function() {
  /* Rel = popup */
  $("a[rel='popup']").click(function(e){
     popup($(this).attr('href'), 800, 600);
     return false;
  });
  /* Admin bar */
  $(".fancybox-buttons a[rel='fancybox']").click(function(e){
    $.fancybox(
      {'type': 'iframe',
       'transitionIn': 'none',
       'transitionOut': 'none',
       'href': this.href + '?is_admin_popup=1',
       'overlayColor': '#333',
       'overlayOpacity': 0.8,
       'onCleanup': function () {
            var fancy_iframe = $("#fancybox-frame");
            var messages = fancy_iframe.contents().find("#popup-message #message");
            this.reload_parent_window_on_close = messages.children('div').size() ? true : false;
       },
       'onClosed': function() {
           // Reload parent if changes have been done, ie #message is not empty
            if (this.reload_parent_window_on_close)
                window.location.reload();
        },
       'hideOnOverlayClick': false,
       'width': 800,
       'height': 550,
       'centerOnScroll': true});
    return false;
  });
});


/*
 * Toggle Simple/Advanced Search
 */
function toggle_advanced_search_form(item){
  var form = item.parents('form');
  form.find('div.advanced').toggle();
};

function init_advanced_search(first){
  toggle_advanced_search_form(first);
}
