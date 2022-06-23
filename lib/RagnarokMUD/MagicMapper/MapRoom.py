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
# RAGNAROK MAGIC MAPPER SOURCE CODE: A single map location on a page
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
