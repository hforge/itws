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

# Import from itools
from itools.core import get_abspath
from itools.datatypes import String
from itools.handlers import ro_database
from itools.relaxng import RelaxNGFile
from itools.xml import XMLNamespace, register_namespace

# Import from itws
from sitemap import SiteMap


#############################################################################
# SITEMAP
#############################################################################
# Required by the SiteMap
xsins_uri = 'http://www.w3.org/2001/XMLSchema-instance'
xsi_namespace = XMLNamespace(
    xsins_uri, 'xsi',
    free_attributes={'schemaLocation': String})
register_namespace(xsi_namespace)

# Read the Relax NG schema of SiteMap and register its namespace
rng_file = ro_database.get_handler(get_abspath('SiteMap-schema.rng'),
                                   RelaxNGFile)
for namespace in rng_file.namespaces.itervalues():
    # Remove sitemap prefix
    namespace.prefix = None
rng_file.auto_register()

# Silent pyflakes
SiteMap
