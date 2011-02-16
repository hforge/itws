# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Armel FORTUN <armel@maar.fr>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>
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

# Import sidebars
from bar_aware import ContentBarAware, SideBarAware
from base_views import SideBar_View
from contact import BoxContact
from diaporama import Diaporama
from feed_box import BoxFeed
from gallery import BoxGallery
from homepage import Website_BarAware
from html import HTMLContent
from map_box import MapBox
from menu import MenuSideBar
from navigation import BoxNavigation
from registry import register_box
from repository import Repository
from section import Section
from tags import BoxTags
from toc import BoxSectionChildrenToc, ContentBoxSectionChildrenToc
from twitter import IdenticaSideBar, TwitterSideBar


register_box(BoxContact)
register_box(BoxFeed)
register_box(BoxGallery)
register_box(BoxNavigation)
register_box(BoxSectionChildrenToc)
register_box(BoxTags)
register_box(ContentBoxSectionChildrenToc)
register_box(Diaporama)
register_box(HTMLContent)
register_box(IdenticaSideBar)
register_box(MapBox)
register_box(MenuSideBar)
register_box(TwitterSideBar)

# Silent Pyflakes
# other
ContentBarAware, Repository, Section, SideBarAware, SideBar_View
Website_BarAware
# boxes
BoxContact, BoxFeed, BoxGallery, BoxNavigation, BoxSectionChildrenToc, BoxTags
ContentBoxSectionChildrenToc, Diaporama, HTMLContent, IdenticaSideBar, MapBox
MenuSideBar, TwitterSideBar
