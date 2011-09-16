# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Sylvain Taverne <sylvain@itaapy.com>
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
from cStringIO import StringIO


def get_orders(resource):
    return resource.get_site_root().get_resource('orders')


def join_pdfs(list_pdf):
    try:
        from pyPdf import PdfFileWriter, PdfFileReader
    except:
        return None
    n = len(list_pdf)
    if n == 0:
        raise ValueError, 'unexpected empty list'

    # Files == 1
    if n == 1:
        return open(list_pdf[0]).read()

    # Files > 1
    pdf_output = PdfFileWriter()
    for path in list_pdf:
        input = PdfFileReader(open(path, "rb"))
        for page in input.pages:
            pdf_output.addPage(page)

    output = StringIO()
    try:
        pdf_output.write(output)
        return output.getvalue()
    finally:
        output.close()
