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
from itools.datatypes import Boolean, XMLContent
from itools.gettext import MSG
from itools.html import xhtml_uri
from itools.stl import stl, rewrite_uris
from itools.uri import get_reference, Path, Reference
from itools.web import get_context, INFO
from itools.xml import TEXT, START_ELEMENT, XMLParser

# Import from ikaaro
from ikaaro.forms import stl_namespaces, RTEWidget, SelectWidget, XHTMLBody
from ikaaro.workflow import WorkflowAware



# Only use one time in ITWS
def to_box(resource, stream, template=None, css=None):
    """ Decorate stream with a box. """
    if template is None:
        template = '/ui/common/box.xml'
    template = resource.get_resource(template)
    namespace = {'content': stream, 'class': css}
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


def set_prefix_with_hostname(stream, prefix, uri, ns_uri=xhtml_uri,
                             fix_absolute_path=False):
    if isinstance(prefix, str):
        prefix = Path(prefix)

    ref = Reference(scheme=uri.scheme, authority=uri.authority,
                    path='/', query={})

    rewrite = partial(resolve_pointer_with_hostname, prefix, ref,
                      fix_absolute_path)

    return rewrite_uris(stream, rewrite, ns_uri)


def resolve_pointer_with_hostname(offset, ref, fix_absolute_path, value):
    # FIXME Exception for STL
    if value[:2] == '${':
        return value

    # Absolute URI or path
    uri = get_reference(value)
    if uri.scheme or uri.authority:
        return value
    if fix_absolute_path is False and uri.path.is_absolute():
        return value

    # Resolve Path
    path = offset.resolve(uri.path)
    value = Reference(ref.scheme, ref.authority, path,
                      uri.query.copy(), uri.fragment)
    return str(value)


############################################################
# Forms
############################################################

state_widget = SelectWidget('state', title=MSG(u'State'),
                            has_empty_option=False)


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
  <div class="admin-bar">
    <a href="${link}" title="${title}" rel="${rel}">
      <img src="/ui/icons/16x16/edit.png"/>
      <strong stl:if="workflow" class="wf-${workflow/state}">
        ${workflow/title}
      </strong>
    </a>
  </div>
  """, stl_namespaces))

admin_bar_icon_template = list(XMLParser("""
  <div class="admin-icons-bar" stl:if="buttons">
    <div class="box-content">
      <table>
        <tr>
          <td stl:repeat="button buttons">
            <img src="${button/icon}" title="${button/label}"/>
            <a href="${button/path}" target="${button/target}">
              ${button/label}
            </a>
          </td>
        </tr>
      </table>
    </div>
  </div>""", stl_namespaces))

def get_admin_bar(resource, buttons=[]):
    context = get_context()
    if is_navigation_mode(context):
        return
    ac = resource.get_access_control()
    if not ac.is_allowed_to_edit(context.user, resource):
        return
    events = admin_bar_template if not buttons else admin_bar_icon_template
    if hasattr(resource, 'get_admin_edit_link'):
        link = resource.get_admin_edit_link(context)
    else:
        link = '%s/;edit' % context.get_link(resource)
    use_fancybox = getattr(resource, 'use_fancybox', True)
    # workflow
    workflow = None
    if isinstance(resource, WorkflowAware):
        statename = resource.get_statename()
        state = resource.get_state()
        workflow = {'state': statename,
                    'title': state['title'].gettext().encode('utf-8')}

    title = MSG(u"Edit box '{title}'").gettext(title=resource.get_title())
    namespace = {'link': link,
                 'rel': 'fancybox' if use_fancybox else None,
                 'buttons': buttons,
                 'title': title,
                 'workflow': workflow}
    return stl(events=events, namespace=namespace)


############################################################
# Links
############################################################

MSG_AUTO_PUBLISHED = INFO(
    u'Some resources have been automatically published. '
    u'See <a href="{path}/;backlinks">links interface</a>.')

def build_auto_published_msg(resource, context):
    path = context.get_link(resource)
    path = XMLContent.encode(path)
    message = MSG_AUTO_PUBLISHED(path=path)
    message = message.gettext().encode('utf8')
    return XHTMLBody.decode(message)


def auto_publish_resources(resource, context, state):
    # Publish referenced resources which are not public/pending
    site_root = resource.get_site_root()
    tag_class = site_root.tagsfolder_class.tag_class
    referenced_resources = list(get_linked_resources(resource))
    # FIXME Skip tags, Do not make tag public if it is pending/private
    # not published tags do not appear in tags cloud.
    referenced_resources = [ x for x in referenced_resources
                             if not isinstance(x, tag_class) ]
    for item in referenced_resources:
        item.set_workflow_state(state)
    if len(referenced_resources):
        return build_auto_published_msg(resource, context)
    return None


def get_linked_resources(resource, state='public'):
    """Return the list of resources which are used by resource.
    If resource is WorkflowAware:
    resource.state is public -> return 'private', 'pending' resources
    resource.state is pending -> return 'private' resource
    """

    map = {'public': ['pending', 'private'],
           'pending': ['private'],
           'private': []}

    links = resource.get_links()
    links = list(set(links))
    # default state
    resource_state = state

    if isinstance(resource, WorkflowAware):
        resource_state = resource.get_workflow_state()
    filtered_states = map.get(resource_state, [])

    for link in links:
        item = resource.get_resource(link, soft=True)
        if isinstance(item, WorkflowAware) is False:
            continue
        state = item.get_workflow_state()
        if state in filtered_states:
            yield item


def get_linked_resources_message(resource, context, state='public'):
    # Customize message if webpage uses private/pending resources
    referenced_resources = list(get_linked_resources(resource))
    if len(referenced_resources) == 0:
        return None

    message = MSG(u'This {title} uses pending/private resources '
                  u'please go to '
                  u'<a href="{path}/;backlinks">links interface</a>')
    path = context.get_link(resource)
    path = XMLContent.encode(path)
    class_title = resource.class_title.gettext()
    message = message.gettext(title=class_title,
                              path=path).encode('utf8')
    message = XHTMLBody.decode(message)
    # Return custom message
    return message


############################################################
# Navigation modes
############################################################

def is_navigation_mode(context):
    return context.get_cookie('itws_fo_edit', Boolean(default=False)) is False


def set_navigation_mode_as_navigation(context):
    context.set_cookie('itws_fo_edit', '0')


def set_navigation_mode_as_edition(context):
    context.set_cookie('itws_fo_edit', '1')
