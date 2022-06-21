#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: A single map location on a page
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

class MapRoom (object):
    '''Describes a single magic map location.  Attributes:

        id:     room id
        page:   page object where the room is located.
        name:   name of this room as (potentially) seen by player
        map:    None or image element list
        also:   None or list of room IDs to draw whenever this is visible

        source_modified_date: datetime when the room's source file was changed
        source_compiled_date: datetime when the room's source file was compiled to what we're using here
        reference_point: None or tuple (x,y) for reference point on map

        page may be None temporarily while getting maps, but once it's valid
        and ready to use, it should refer to the room's MapPage object.
    '''

    def __init__(self, id, page, name=None, map=None, also=None, source_modified_date=None, source_compiled_date=None, reference_point=None):
        self.id = id
        self.page = page
        self.name = name
        self.map = map
        self.also = also
        self.reference_point = reference_point
        self.source_modified_date = source_modified_date
        self.source_compiled_date = source_compiled_date

        if self.reference_point is None:
            #
            # try to figure it out based on first room or dotmark
            #
            if self.map is not None:
                for element in self.map:
                    if element[0][0] == 'R':
                        if element[3] == 'R':
                            self.reference_point = (element[1], element[2])
                        else:
                            self.reference_point = (
                                    element[1] + element[3]/2.0, 
                                    element[2] + element[4]/2.0
                            )
                        break
                    if element[0][0] == 'O':
                        self.reference_point = (element[1], element[2])
                        break
                else:
                    # XXX Warning: no reference point
                    pass
