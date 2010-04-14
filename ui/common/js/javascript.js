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
