# -*- coding: UTF-8 -*-
# Copyright (C) 2007-2010 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008-2009 Nicolas Deram <nicolas@itaapy.com>
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

# Import from the Standard Library
from functools import partial

# Import from itools
from itools.html import xhtml_uri
from itools.stl import stl, rewrite_uris
from itools.uri import get_reference, Path, Reference
from itools.web import get_context
from itools.xml import TEXT, START_ELEMENT, XMLParser

# Import from ikaaro
from ikaaro.forms import stl_namespaces, RTEWidget, SelectWidget



# Only use one time in ITWS
def to_box(resource, stream, template=None):
    """ Decorate stream with a box. """
    if template is None:
        template = '/ui/common/box.xml'
    template = resource.get_resource(template)
    namespace = {'content': stream, 'class': None}
    return stl(template, namespace)


def is_empty(events):
    """Return true if the events contains data"""
    # FIXME copy/paste from itools.html XHTMLFile.is_empty
    for type, value, line in events:
        if type == TEXT:
            if value.replace('&nbsp;', '').strip():
                return False
        elif type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in ('img', 'object'):
                # If the document contains at leat one image
                # or one object (i.e. flash object) it is not empty
                return False
    return True


def xml_to_text(events):
    """Removes the markup and returns a plain text string.
    """
    # FIXME copy/paste from itools.xmlfile XMLFile.to_text
    text = [ unicode(value, 'utf-8') for event, value, line in events
             if event == TEXT ]
    return u' '.join(text)


def get_path_and_view(path):
    view = ''
    name = path.get_name()
    # Strip the view
    if name and name[0] == ';':
        view = '/' + name
        path = path[:-1]

    return path, view


def set_prefix_with_hostname(stream, prefix, uri, ns_uri=xhtml_uri):
    if isinstance(prefix, str):
        prefix = Path(prefix)

    ref = Reference(scheme=uri.scheme, authority=uri.authority,
                    path=prefix, query={})

    rewrite = partial(resolve_pointer_with_hostname, ref)

    return rewrite_uris(stream, rewrite, ns_uri)


def resolve_pointer_with_hostname(offset, value):
    # FIXME Exception for STL
    if value[:2] == '${':
        return value

    # Absolute URI or path
    uri = get_reference(value)
    if uri.scheme or uri.authority or uri.path.is_absolute():
        return value

    # Resolve Path
    path = offset.path.resolve(uri.path)
    value = Reference(offset.scheme, offset.authority, path,
                      uri.query.copy(), uri.fragment)
    return str(value)


############################################################
# Forms
############################################################
class XMLTitleWidget(RTEWidget):

    title = None
    width = '512px'
    height = '100px'
    toolbar1 = ('code,removeformat,|,bold,italic,underline,strikethrough,|'
                ',undo,redo,|,link,unlink')
    toolbar2 = None
    plugins = None



class DualSelectWidget(SelectWidget):

    css = 'dual-select'
    template = list(XMLParser("""
        <script type="text/javascript">
            $(document).ready(function() {
                $("#${id}.${css}").multiselect2side({selectedPosition: 'right', moveOptions: false});
            });
        </script>
        <select id="${id}" name="${name}" multiple="${multiple}" size="${size}"
            class="${css}">
          <option value="" stl:if="has_empty_option"></option>
          <option stl:repeat="option options" value="${option/name}"
            selected="${option/selected}">${option/value}</option>
        </select>
        """, stl_namespaces))


############################################################
# Manage Buttons
############################################################

admin_bar_template = list(XMLParser("""
  <div id="admin-bar-${id}" class="admin-bar">
    <div class="admin-bar-title">${title}</div>
    <ul class="admin-bar-ul">
      <li stl:repeat="button buttons">
        <a href="${button/path}">
          ${button/label}
        </a>
      </li>
    </ul>
    <div class="clear" />
  </div>
  <script>
    $(document).ready(function(){
      var original_height = $("#${id}").height();
      var menu_height = $("#admin-bar-${id}").height();
      <![CDATA[
      var is_inf = original_height < menu_height;
      ]]>
      $("#admin-bar-${id}").hide();
      $("#${id}").hover(function(){
        $("#${id}").addClass('highlight');
        $("#admin-bar-${id}").show();
        if(is_inf){
          $("#${id}").height(menu_height);
        }
      },
      function(){
        $("#admin-bar-${id}").hide();
        $("#${id}").removeClass('highlight');
        if(is_inf){
          $("#${id}").height(original_height);
        }
      });
    });
  </script>""", stl_namespaces))

admin_bar_icon_template = list(XMLParser("""
  <div id="admin-bar-icon-${id}" class="admin-icons-bar"
    stl:if="buttons">
    <div class="box-content">
      <table>
        <tr>
          <td stl:repeat="button buttons">
            <a href="${button/path}" target="${button/target}">
            ${button/label}<br/>
              <img src="${button/icon}" title="${button/label}"/>
            </a>
          </td>
        </tr>
      </table>
    </div>
  </div>""", stl_namespaces))

def get_admin_bar(buttons, id, title='', icon=False):
    context = get_context()
    resource = context.resource
    ac = resource.get_access_control()
    if not ac.is_allowed_to_edit(context.user, resource):
        return None
    if not buttons:
        return None
    events = admin_bar_template if icon is False else admin_bar_icon_template
    return stl(events=events,
               namespace={'buttons': buttons, 'id': id, 'title': title})
