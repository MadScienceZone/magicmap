#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Local Caching of Map Objects

from RagnarokMUD.MagicMapper.MapPage import MapPage, LANDSCAPE, PORTRAIT
from RagnarokMUD.MagicMapper.MapRoom import MapRoom
import os, os.path
import time
import sqlite3

class CacheManagerError (Exception):
    "Error encountered while trying to work with the cache"

#
# We store cached copies of the data files in the same format
# we receive them from the website, in <DIRNAME>/a/ab/abcdef for room abcdef
# and <DIRNAME>/page/number for pages.
#
# Some filesystems don't allow mixed case filenames (or maybe they
# allow them but don't consider files distinct if their names are
# the same modulo case differences) which will cause a problem for
# us.  Also, room IDs may contain characters illegal to some file-
# systems.  So we will make the following transformations in the 
# hopes that they will work on the least common denominator system:
#
# upper-case letters and digits:    passed as-is
# lower-case letters:               replaced with _(upper-case)
# everything else:                  replaced with _xx (hex code xx)
#
# The encoding of _(letter) shouldn't collide with _(hexcode)
# because our names are always 7-bit ASCII and so would always be
# less than hex code _7F so _Ax - _Fx would be out of the way.
#
# Examples:
#
# rmO_aPzcZbw4g_HlzLxk8k --> _R/_R_M/_R_MO_5F_AP_Z_CZ_B_W4_GH_L_ZL_X_K8_K
# -cRDWjIFbaTKhi4IEUIr6F --> _2D/_2D_C/_2D_CRDW_JIF_B_ATK_H_I4IEUI_R6F
# 5B7r7QXftBdRNJEBK0YFPV --> 5/5B/5B7_R7QX_F_TB_DRNJEBK0YFPV
#
# Since Rag uses 22-character room IDs, the worst case scenario
# is something like:
# ...................... --> _2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E
#
# So as long as a filename *could* be 66 characters long and still be allowable, we're ok.
#
#import re

class DbMapCacheManager:
    def __init__(self, dbname):
        self.dbname = dbname
        self.db = None

        if not os.path.exists(dbname):
            self.create_new_db()

        self.open()

    def close(self):
        if self.db:
            self.db.close()
            self.db = None

    def open(self):
        self.close()
        self.db = sqlite3.connect(self.dbname)

    def create_new_db(self):
        db = sqlite3.connect(self.dbname)
        c = db.cursor()
        c.executescript('''
            drop table if exists visited;
            drop table if exists rooms;
            drop table if exists pages;
            drop table if exists characters;
            create table characters (
                character_id integer primary key,
                name         string
            );
            create table visited (
                character_id integer,
                room_id      integer,
                foreign key (character_id) references characters (character_id)
                    on delete cascade,
                foreign key (room_id) references rooms (room_id)
                    on delete cascade
            );
            create table pages (
                page_id      integer primary_key,
                page_number  integer,
                orientation  string,
                realm        string,
                creators     string,
                background   blob,
                modtime      datetime,
                cachetime    datetime
            );
            create table rooms (
                room_id      integer primary_key,
                page_id      integer,
                location_id  string,
                name         string,
                see_also     string,
                x            integer,
                y            integer,
                data         blob,
                modtime      datetime,
                cachetime    datetime,
                foreign key (page_id) references pages (page_id)
                    on delete restrict
            );
        ''')
        db.commit()
        db.close()

    def expire_cache(self, character_name=None):
        "force all cache update times to 0 so the next freshen_cache() will reload everything."

        c = self.db.cursor()
        if character_name is None:
            c.executescript('''
                update rooms set cachetime=0;
                update pages set cachetime=0;
            ''')
        else:
            c.executescript('''
                update rooms
                  set cachetime=0
                  where room_id in (
                    select room_id from visited
                      inner join characters
                        on characters.character_id = visited.character_id
                          and characters.name =:name
                  );
                update pages
                  set cachetime=0
                  where page_id in (
                    select page_id from visited
                      inner join characters
                        on characters.character_id = visited.character_id
                          and characters.name =:name
                  );
            ''', {'name': character_name})
        self.db.commit()

    def purge_cache(self, character_name=None):
        "delete all map content from the database, as if the player never visited anything."

        c = self.db.cursor()
        if character_name is None:
            # delete the entire database (all content for all characters)
            c.executescript('''
                delete from visited;
                delete from rooms;
                delete from pages;
                delete from characters;
            ''')
        else:
            # limit to removing information for one character
            data = c.execute('select character_id from characters where name = ?', (character_name,)).fetchone()
            if not data:
                raise KeyError(f'Cache has no record of a character named {character_name}')
            character_id = int(data[0])

            c.executescript('''
                delete from visited 
                  where character_id = ?;
                delete from rooms 
                  where room_id not in (
                    select room_id from visited
                  );
                delete from pages
                  where page_id not in (
                    select page_id from rooms
                  );
            ''', (character_id,))

        self.db.commit()

    def freshen_cache(self, age=7, progress=self.progress_meter):
        "Check for newer versions of map data that's older than <age> days, updating as necessary."
        mapdata = MapDataHandler()
        status_msg = 'Checking for newer map content... Updated {}'
        target_time = time.time() - (age * 86400)
        c = self.db.cursor()

        progress(status_msg.format(0), 0, 0)
        target_pages = c.execute('''
            select page_id, page_number, cachetime
                from pages
                where cachetime < ?
        ''', (target_time,)).fetchall()
        target_rooms = c.execute('''
            select room_id, page_id, location_id, cachetime
                from rooms
                where cachetime < ?
        ''', (target_time,)).fetchall()

        n = len(target_pages) + len(target_rooms)
        i = 0
        hits = 0
        progress(status_msg.format(hits), i, n)
        page_no_by_id = {}
        for page_id, page_no, cachetime in target_pages:
            i += 1
            page_no_by_id[page_id] = page_no
            # ask if a more current copy is there (200) or not (304)
            # If-Modified-Since: dayname, day month year hour:minute:second GMT
            # note that our cachetime is always in GMT
            modsince = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(cachetime))
            response = requests.get(f'https://www.rag.com/magicmap/page/{page_no}', headers={
                'If-Modified-Since': modsince
            })

            if response.status_code == 304:
                # Our cached copy is still current.
                c.execute('update pages set cachetime = ? where page_id = ?', (int(time.time()), page_id))
            elif response.status_code == 200:
                # We have a new version available.
                # r.content has the payload
                hits += 1
                try:
                    map_page = mapdata.load_page(r.content.decode())
                    c.execute('''
                        update pages set 
                            orientation = ?,
                            realm = ?,
                            creators = ?,
                            background = ?,
                            modtime = ?,
                            cachetime = ?
                        where page_id = ?
                    ''', (
                        'L' if map_page.orient == LANDSCAPE else 'P',
                        map_page.realm or '',
                        ', '.join(map_page.creators),
                        json.dumps(map_page.bg),
                        map_page.source_modified_date,
                        int(time.time()),
                        page_id
                    ))
                except Exception as err:
                    print(f'XXX ERROR {err} loading data for page {page_no} from server')
            else:
                print(f'XXX ERROR HTTP STATUS {response.status_code} for page {page_no} from server')
            progress(status_msg.format(hits), i, n)
        self.db.commit()

        for room_id, page_id, location_id, cachetime in target_rooms:
            i += 1
            progress(status_msg.format(hits), i, n)
            # ask if a more current copy is there (200) or not (304)
            # If-Modified-Since: dayname, day month year hour:minute:second GMT
            # note that our cachetime is always in GMT
            modsince = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(cachetime))
            response = requests.get(f'https://www.rag.com/magicmap/room/{location_id[0:1]}/{location_id[0:2]}/{location_id}', headers={
                'If-Modified-Since': modsince
            })

            if response.status_code == 304:
                # Our cached copy is still current.
                c.execute('update rooms set cachetime = ? where room_id = ?', (int(time.time()), room_id))
            elif response.status_code == 200:
                # We have a new version available.
                # r.content has the payload
                hits += 1
                try:
                    map_room = mapdata.load_room(r.content.decode())
                    # XXX look for page_number changing
                    # XXX if page_id not in our hash, we need to get that page too, and add to our cache
                    c.execute('''
                        update rooms set 
                            page_id



                            realm = ?,
                            creators = ?,
                            background = ?,
                            modtime = ?,
                            cachetime = ?
                        where page_id = ?
                    ''', (
                        'L' if map_page.orient == LANDSCAPE else 'P',
                        map_page.realm or '',
                        ', '.join(map_page.creators),
                        json.dumps(map_page.bg),
                        map_page.source_modified_date,
                        int(time.time()),
                        page_id
                    ))
                except Exception as err:
                    print(f'XXX ERROR {err} loading data for page {page_no} from server')
            else:
                print(f'XXX ERROR HTTP STATUS {response.status_code} for page {page_no} from server')
        self.db.commit()


        


    def progress_meter(self, message, value, maxvalue):
        if message is None:
            print('[========================================] Done.')
        else:
            if maxvalue <= 0:
                stars = '[*****.....*****.....*****.....*****.....]'
            else:
                nstars = min(int((value / maxvalue) * 40), 40)
                stars = '[' + (nstars * '*') + (40-nstars) * '.' + ']'

            print(f'{stars} {message}\r', end='', flush=True)

class MapCacheManager:
    def __init__(self, dirname):
        "Open (creating if necessary) a cache at the given dirname, and prepare to manage it."

        self.cache_dir = dirname
        if not os.path.isdir(dirname):
            if os.path.exists(dirname):
                raise CacheManagerError('MapCacheManager canot create directory '+dirname+'; there appears to be another file in the way.')
            os.mkdir(dirname, 0o755)

    def close(self):
        pass

    def retrieve(self, key):
        "Find the given key in the cache -> None (not found) or (fileobj, age in seconds)"
        d1, d2, cache_name = self._encode_filename(key)
        cache_entry_path = os.path.join(self.cache_dir, d1, d2, cache_name)

        if os.path.exists(cache_entry_path):
            return open(cache_entry_path, 'r'), (time.time() - os.path.getmtime(cache_entry_path))

        return None

    def store(self, key, fileobj):
        "Store data from fileobj into the cache under the given key"
        self.store_str(key, fileobj.read())

    def store_str(self, key, data):
        "Store string data into the cache under the given key"
        d1, d2, cache_name = self._encode_filename(key)
        entry_dir = os.path.join(self.cache_dir, d1, d2)

        if not os.path.isdir(entry_dir):
            if os.path.exists(entry_dir):
                raise CacheManagerError('MapCacheManager cannot create directory '+entry_dir+'; there appears to be another file in the way.')
            try:
                os.makedirs(entry_dir)
            except Exception as err:
                raise CacheManagerError('System error creating {0}: {1}'.format(entry_dir, err))

        with open(os.path.join(entry_dir, cache_name), 'w') as cached_copy:
            cached_copy.write(data)

    def remove(self, key):
        "Remove the data from the cache"
        d1, d2, cache_name = self._encode_filename(key)
        entry_path = os.path.join(self.cache_dir, d1, d2, cache_name)
        if os.path.exists(entry_path):
            os.unlink(entry_path)

    def touch(self, key):
        "Touch the cached file, updating its timestamp."
        #
        # Silently ignores the request if there is no such
        # cache file; should it?
        #
        d1, d2, cache_name = self._encode_filename(key)
        cache_entry_path = os.path.join(self.cache_dir, d1, d2, cache_name)
        if os.path.exists(cache_entry_path):
#            with open(cache_entry_path, 'r+b') as cached_file:
#                first_byte = cached_file.read(1)
#                cached_file.seek(0, os.SEEK_SET)
#                cached_file.write(first_byte)
            os.utime(cache_entry_path, None)

    def _encode_file_char(self, char):
        "Transform id character to sequence of 'safe' filename characters"

        if char.isupper() or char.isdigit():
            return char

        if char.islower():
            return '_' + char.upper()

        return '_%02X' % ord(char)

    def _encode_filename(self, id):
        "Encode an ID (assumed to be printable 7-bit ASCII) into a usable filename -> (dir, dir, filename)"

        if not id:
            return ('_00','_00', '_00.MMC')

        return (self._encode_file_char(id[0]), 
            ''.join([self._encode_file_char(i) for i in id[:2]]),
            ''.join([self._encode_file_char(i) for i in id]) + '.MMC')
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
