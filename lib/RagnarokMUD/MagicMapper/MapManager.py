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
# RAGNAROK MAGIC MAPPER SOURCE CODE:
#

import sqlite3
import sys
import os.path
import os
import re
from RagnarokMUD.MagicMapper.MapCacheManager import MapCacheManager
from RagnarokMUD.MagicMapper.MapDataHandler  import MapDataHandler
from RagnarokMUD.MagicMapper.NetworkIO       import NetworkIO, DataNotFound

class MapManager (object):
    '''This class manages a player's magic map by keeping track on
    the client side what rooms exist, making sure we have fresh copies
    of them, and providing their room data to the canvas as needed.'''

    #
    # Database structure:
    #
    # rooms
    # =====
    #   room_id
    #
    def __init__(self, config):
        self.pages = {}
        self.db = None
        self.parser = MapDataHandler()
        self.config = config
        self.rooms = {}
        self.io = NetworkIO(base_url=config.get('server', 'base_url'), 
                cache_dir=config.get('cache', 'location'), 
                cache_age=config.getint('cache', 'recheck_age'), 
                diag_callback=self.diag_logger,
                config=config)
    
    def diag_logger(self, level, prog, total, msg):
        print("XXX [{}] {}/{} {}".format(level, prog, total, msg))

    def open(self, player_id):
        if self.db is not None:
            self.close()

        base_dir = self.config.get('cache', 'db_base')
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        db_path = os.path.join(base_dir, 'MM_'+re.sub(r'[^a-zA-Z0-9_.]', '', player_id))
        if not os.path.exists(db_path):
            self.db = sqlite3.connect(db_path)
            self.db.execute('create table rooms (room_id string)')
            self.db.commit()
        else:
            self.db = sqlite3.connect(db_path)

        self.refresh()

    def refresh(self):
        """Check all the cached files for the known rooms on this map,
        reloading them from the server as necessary."""

        c = self.db.cursor()
        self.pages = {}
        self.rooms = {}

        for room_id in c.execute('select room_id from rooms'):
            try:
                self._load_location(room_id)
            except Exception:
                raise

    def move_to(self, room_id):
        """Get the room from the server or cache and return it.  Database is updated
        with this location if we haven't seen it yet."""

        if room_id in self.rooms:
            return self.rooms[room_id]

        try:
            room = self._load_location(room_id)
        except DataNotFound:
            return None
        except Exception:
            raise

        self.db.execute('insert into rooms values (?)', (room_id,))
        self.db.commit()
        return room

    def load(self, room_id, modtime=None, checksum=None):
        """Make sure the room is in our cache and database, updating them if
        the modtime and/or checksum mismatches the cached copy (not implemented
        yet)."""

        self.move_to(room_id)

    def _load_location(self, room_id):
        if room_id in self.rooms:
            return self.rooms[room_id]

        try:
            page_number, room = self.parser.load_room(self.io.get_room(room_id))
            if page_number in self.pages:
                page = self.pages[page_number]
            else:
                page = self.parser.load_page(self.io.get_page(page_number))
                self.pages[page_number] = page

            page.add_room(room)
            room.page = page
            self.rooms[room_id] = room
        except Exception:
            raise

        return room

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None

class FileError (Exception): pass

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
