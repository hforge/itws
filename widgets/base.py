# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Taverne Sylvain <sylvain@itaapy.com>
# Copyright (C) 2010-2011 Henry Obein <henry@itaapy.com>
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

# Import from standard library
from datetime import datetime

# Import from itools
from itools.datatypes import DateTime
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.autoform import RTEWidget, SelectWidget, Widget, rte_widget
from ikaaro.registry import get_resource_class
from ikaaro.utils import make_stl_template



class Advance_RTEWidget(RTEWidget):

    extended_valid_elements = (
            "iframe[src|name|id|class|style|frameborder|width|height],"
            "div[id|dir|class|align|style]")
    toolbar2 = RTEWidget.toolbar2 + (',|,attribs')
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
    selected_label = MSG(u'Selected')
    available_label = MSG(u'Available')

    template = make_stl_template("""
        <script type="text/javascript">
            $(document).ready(function() {
                $("#${id}.${css}").multiselect2side(
                    {
                        selectedPosition: 'right',
                        moveOptions: false,
                        labelsx: '${available_label}',
                        labeldx: '${selected_label}'
                    });
            });
        </script>
        <select id="${id}" name="${name}" multiple="${multiple}" size="${size}"
            class="${css}">
          <option value="" stl:if="has_empty_option"></option>
          <option stl:repeat="option options" value="${option/name}"
            selected="${option/selected}">${option/value}</option>
        </select>
        """)



class ClassSelectorWidget(SelectWidget):

    template = make_stl_template("""
        <table>
          <tr stl:repeat="item items">
            <td valign="top">
              <input id="${item/class_id}" name="class_id" type="radio"
                value="${item/class_id}" checked="${item/selected}" />
            </td>
            <td valign="top">
              <img border="0" src="${item/icon}" />
            </td>
            <td>
              <label for="${item/class_id}">${item/title}</label><br/>
              <p><em>${item/description}</em></p>
            </td>
          </tr>
        </table>
        """)


    def items(self):
        items = []
        for option in self.options():
            class_id = option['name']
            cls = get_resource_class(class_id)
            items.append({'class_id': class_id,
                          'selected': option['selected'],
                          'title': option['value'],
                          'icon': '/ui/' + cls.class_icon16,
                          'description': cls.class_description})
        return items



class JSDatetimeWidget(Widget):

    template = make_stl_template("""
    <table cellpadding="5" cellspacing="0">
      <tr>
        <td>Date</td>
        <td>
          <input type="text" name="${name}_date" value="${date_value}"
            id="${id}-date"
            class="dateField" size="10" />
          <button class="button-selector">...</button>
        </td>
      </tr>
      <tr>
        <td>Hour</td>
        <td>
          <input id="${id}-hour" type="text" name="${name}_hour"
            value="${hour_value}" size="2"/> : 
          <input id="${id}-min" type="text" name="${name}_min"
            value="${min_value}" size="2"/>
        </td>
      </tr>
    </table>
    <input type="hidden" id="${id}" name="${name}" value="${value}"/>
    <script type="text/javascript">
      jQuery( "input.dateField" ).dynDateTime({
        ifFormat: "%Y-%m-%d",
        timeFormat: "24",
        button: ".next()" });
      $("#${id}-date").change(function(){change_itws_datetime()});
      $("#${id}-hour").change(function(){change_itws_datetime()});
      $("#${id}-min").change(function(){change_itws_datetime()});
      function change_itws_datetime(){
          var date = $("#${id}-date").val();
          var hour = $("#${id}-hour").val();
          var min = $("#${id}-min").val();
          $("#${id}").val(date + "T" + hour + ":" + min +":00+0000");
      }
    </script>""")

    def get_date(self):
        try:
            return DateTime.decode(self.value)
        except Exception:
            return datetime.today()


    def date_value(self):
        d = self.get_date()
        return d.date() if d else d


    def hour_value(self):
        d = self.get_date()
        return d.hour if d else d


    def min_value(self):
        d = self.get_date()
        return d.minute if d else d
