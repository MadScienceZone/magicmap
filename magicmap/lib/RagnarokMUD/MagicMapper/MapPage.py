#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: A single map page
# $Header$
#
# Copyright (c) 2010 by Steven L. Willoughby, Aloha, Oregon, USA.
# All Rights Reserved.  Licensed under the Open Software License
# version 3.0.  See http://www.opensource.org/licenses/osl-3.0.php
# for details.
#
# Based on earlier code from the Ragnarok MudShell (MSH) client,
# Copyright (c) 1993, 2000, 2001, 2002, 2003 by Steven L. Willoughby,
# Aloha, Oregon, USA.  All Rights Reserved.  MSH is licensed under
# the terms of the GNU General Public License (GPL) version 2.
#
# This product is provided for educational, experimental or personal
# interest use, in accordance with the terms and conditions of the
# aforementioned license agreement, ON AN "AS IS" BASIS AND WITHOUT
# WARRANTY, EITHER EXPRESS OR IMPLIED, INCLUDING, WITHOUT LIMITATION,
# THE WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
# PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY OF THE ORIGINAL
# WORK IS WITH YOU.  (See the license agreement for full details,
# including disclaimer of warranty and limitation of liability.)
#
# Under no curcumstances is this product intended to be used where the
# safety of any person, animal, or property depends upon, or is at
# risk of any kind from, the correct operation of this software.
#

class PageOrientationViolationError (Exception):
    "You can't change the direction of a page after setting it the other way already."

class DuplicatePageError (Exception):
    "We already have one of those, thanks."

PORTRAIT  = 0
LANDSCAPE = 1

class MapPage (object):
    '''Describes a single magic map page.  Attributes:

        page:   page number (an integer)
        realm:  None or page title
        orient: PORTRAIT or LANDSCAPE (module constant values)
        bg:     background image element list
        creators: list of names of realm owners (or other similar text)
        rooms:  Dictionary mapping room ID to MapRoom objects for this page
        source_modified_date: datetime the page's source code was changed
        source_compiled_date: datetime the page's data was compiled from source.

        "Source" in this case is the collective set of .map files which describe
        the room(s) on this page.

        The orient attribute will read PORTRAIT until explicitly set
        by direct assignment or by loading a room which explcitly 
        specifies page orientation, then it will read as that 
        orientation and any further attempt to change it to 
        something different will throw an exception.
    '''

    def __init__(self, page, realm=None, orient=None, creators=None, bg=None, source_modified_date=None, source_compiled_date=None):
        if orient not in (PORTRAIT, LANDSCAPE, None):
            raise ValueError('Page orientation must be MapPage.PORTRAIT or MapPage.LANDSCAPE')

        if creators is None:
            self.creators = []
        elif isinstance(creators, (list, tuple)):
            self.creators = list(creators)
        else:
            self.creators = [creators]

        self.creators = creators or []
        self.page = int(page)
        self.realm = realm
        self.bg = bg or []
        self.rooms = {}
        self.source_modified_date = source_modified_date
        self.source_compiled_date = source_compiled_date
        object.__setattr__(self, 'orient', orient or None)

    def add_room(self, room):
        "Add a MapRoom object to this page of the map."
        if room.id in self.rooms:
            raise DuplicateRoomError('Room '+room.id+' already defined on page '+`self.page`)

        self.rooms[room.id] = room

    def __getattribute__(self, name):
        #
        # the .orient attribute appears PORTRAIT unless explicitly
        # assigned a direction; then it refuses to be set to anything
        # else.
        #
        if name == 'orient':
            true_value = object.__getattribute__(self, 'orient')
            return true_value if true_value is not None else PORTRAIT

        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == 'orient':
            true_value = object.__getattribute__(self, 'orient')
            if true_value is None:
                if value not in (PORTRAIT, LANDSCAPE):
                    raise ValueError('Page orientation must be PORTRAIT or LANDSCAPE.')

                object.__setattr__(self, 'orient', value)
            elif true_value != value:
                raise PageOrientationViolationError('Page %d orientation already set; cannot be changed to other direction now.' % self.page)
        else:
            object.__setattr__(self, name, value)
