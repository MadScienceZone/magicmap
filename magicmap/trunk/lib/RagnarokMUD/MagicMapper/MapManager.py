# vi:set ai sm nu ts=4 sw=4 expandtab:
#  _______  _______  _______ _________ _______  _______  _______  _______ 
# (       )(  ___  )(  ____ \\__   __/(  ____ \(       )(  ___  )(  ____ )
# | () () || (   ) || (    \/   ) (   | (    \/| () () || (   ) || (    )|
# | || || || (___) || |         | |   | |      | || || || (___) || (____)|
# | |(_)| ||  ___  || | ____    | |   | |      | |(_)| ||  ___  ||  _____)
# | |   | || (   ) || | \_  )   | |   | |      | |   | || (   ) || (      
# | )   ( || )   ( || (___) |___) (___| (____/\| )   ( || )   ( || )      
# |/     \||/     \|(_______)\_______/(_______/|/     \||/     \||/       
#                                                                        
#
#
# RAGNAROK MAGIC MAPPER SOURCE CODE:
# $Header$
#
# Copyright (c) 2012 by Steven L. Willoughby, Aloha, Oregon, USA.
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
        print "XXX [{}] {}/{} {}".format(level, prog, total, msg)

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

