########################################################################################
#  _______  _______  _______ _________ _______  _______  _______  _______              #
# (       )(  ___  )(  ____ \\__   __/(  ____ \(       )(  ___  )(  ____ ) Ragnarok    #
# | () () || (   ) || (    \/   ) (   | (    \/| () () || (   ) || (    )| MUD         #
# | || || || (___) || |         | |   | |      | || || || (___) || (____)| Magic       #
# | |(_)| ||  ___  || | ____    | |   | |      | |(_)| ||  ___  ||  _____) Mapper      #
# | |   | || (   ) || | \_  )   | |   | |      | |   | || (   ) || (       Client      #
# | )   ( || )   ( || (___) |___) (___| (____/\| )   ( || )   ( || )       (rag.com)   #
# |/     \||/     \|(_______)\_______/(_______/|/     \||/     \||/                    #
#   ______    __       _______         _______  _        _______           _______     #
#  / ____ \  /  \     (  __   )       (  ___  )( \      (  ____ )|\     /|(  ___  )    #
# ( (    \/  \/) )    | (  )  |       | (   ) || (      | (    )|| )   ( || (   ) |    #
# | (____      | |    | | /   | _____ | (___) || |      | (____)|| (___) || (___) |    #
# |  ___ \     | |    | (/ /) |(_____)|  ___  || |      |  _____)|  ___  ||  ___  |    #
# | (   ) )    | |    |   / | |       | (   ) || |      | (      | (   ) || (   ) |    #
# ( (___) )_ __) (_ _ |  (__) |       | )   ( || (____/\| )      | )   ( || )   ( | _  #
#  \_____/(_)\____/(_)(_______)       |/     \|(_______/|/       |/     \||/     \|(_) #
#                                                                                      #
########################################################################################
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: A single map page
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
            raise DuplicateRoomError('Room '+room.id+' already defined on page '+repr(self.page))

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
#@[00]@| Ragnarok MagicMapper 6.1.0-alpha.0
#@[01]@|
#@[10]@| Copyright © 2010, 2018, 2020, 2021, 2022 by Steven L. Willoughby, Aloha, Oregon, USA.
#@[11]@| All Rights Reserved. Licensed under the terms and conditions of the BSD-3-Clause
#@[12]@| License as described in the accompanying LICENSE file distributed with MagicMapper.
#@[13]@|
#@[20]@| Based on earlier code from the Ragnarok MudShell (MSH) client,
#@[21]@| Copyright © 1993, 2000-2003 by Steven L. Willoughby, Aloha, Oregon, USA.
#@[22]@| MSH is licensed under the terms and conditions of the BSD-3-Clause
#@[23]@|
#@[30]@| Redistribution and use in source and binary forms, with or without
#@[31]@| modification, are permitted provided that the following conditions
#@[32]@| are met:
#@[33]@| 1. Redistributions of source code must retain the above copyright
#@[34]@|    notice, this list of conditions and the following disclaimer.
#@[35]@| 2. Redistributions in binary form must reproduce the above copy-
#@[36]@|    right notice, this list of conditions and the following dis-
#@[37]@|    claimer in the documentation and/or other materials provided
#@[38]@|    with the distribution.
#@[39]@| 3. Neither the name of the copyright holder nor the names of its
#@[40]@|    contributors may be used to endorse or promote products derived
#@[41]@|    from this software without specific prior written permission.
#@[42]@|
#@[43]@| THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
#@[44]@| CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES,
#@[45]@| INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
#@[46]@| MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#@[47]@| DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
#@[48]@| BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
#@[49]@| OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#@[50]@| PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#@[51]@| PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#@[52]@| THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
#@[53]@| TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
#@[54]@| THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#@[55]@| SUCH DAMAGE.
#@[56]@|
#@[60]@| This software is not intended for any use or application in which
#@[61]@| the safety of lives or property would be at risk due to failure or
#@[62]@| defect of the software.
