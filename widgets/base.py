# -*- coding: UTF-8 -*-
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

# Import from itools
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.autoform import RTEWidget, SelectWidget
from ikaaro.autoform import rte_widget, stl_namespaces



class Advance_RTEWidget(RTEWidget):

    extended_valid_elements = (
            "iframe[src|name|id|class|style|frameborder|width|height],"
            "div[id|dir|class|align|style]")
    toolbar2 = RTEWidget.toolbar2 + ('|attribs')
    plugins = RTEWidget.plugins + (',xhtmlxtras')


advance_rte_widget = Advance_RTEWidget('data', title=rte_widget.title)



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



