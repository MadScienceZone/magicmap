#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Local Caching of Map Objects
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

from RagnarokMUD.MagicMapper.MapPage import MapPage, LANDSCAPE, PORTRAIT
from RagnarokMUD.MagicMapper.MapRoom import MapRoom
import os, os.path
import time

class CacheManagerError (Exception):
    "Error encountered while trying to work with the cache"

#
# We store cached copies of the data files in the same format
# we receive them from the website, in <DIRNAME>/a/abcdef for room abcdef
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
# rmO_aPzcZbw4g_HlzLxk8k --> _R/_R_MO_5F_AP_Z_CZ_B_W4_GH_L_ZL_X_K8_K
# -cRDWjIFbaTKhi4IEUIr6F --> _2D/_2D_CRDW_JIF_B_ATK_H_I4IEUI_R6F
# 5B7r7QXftBdRNJEBK0YFPV --> 5/5B7_R7QX_F_TB_DRNJEBK0YFPV
#
# Since Rag uses 22-character room IDs, the worst case scenario
# is something like:
# ...................... --> _2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E_2E
#
# So as long as a filename *could* be 66 characters long and still be allowable, we're ok.
#
#import re
class MapCacheManager (object):
    def __init__(self, dirname):
        "Open (creating if necessary) a cache at the given dirname, and prepare to manage it."

        self.cache_dir = dirname
        if not os.path.isdir(dirname):
            if os.path.exists(dirname):
                raise CacheManagerError('MapCacheManager canot create directory '+dirname+'; there appears to be another file in the way.')
            os.mkdir(dirname, 0755)

    def close(self):
        pass

    def retrieve(self, key):
        "Find the given key in the cache -> None (not found) or (fileobj, age in seconds)"
        subdir, cache_name = self._encode_filename(key)
        cache_entry_path = os.path.join(self.cache_dir, subdir, cache_name)

        if os.path.exists(cache_entry_path):
            return open(cache_entry_path, 'r'), (time.time() - os.path.getmtime(cache_entry_path))

        return None

    def store(self, key, fileobj):
        "Store data from fileobj into the cache under the given key"
        self.store_str(key, fileobj.read())

    def store_str(self, key, data):
        "Store string data into the cache under the given key"
        subdir, cache_name = self._encode_filename(key)
        entry_dir = os.path.join(self.cache_dir, subdir)

        if not os.path.isdir(entry_dir):
            if os.path.exists(entry_dir):
                raise CacheManagerError('MapCacheManager cannot create directory '+entry_dir+'; there appears to be another file in the way.')
            os.mkdir(entry_dir)

        with open(os.path.join(entry_dir, cache_name), 'w') as cached_copy:
            cached_copy.write(data)

    def remove(self, key):
        "Remove the data from the cache"
        subdir, cache_name = self._encode_filename(key)
        entry_path = os.path.join(self.cache_dir, subdir, cache_name)
        if os.path.exists(entry_path):
            os.unlink(entry_path)

    def touch(self, key):
        "Touch the cached file, updating its timestamp."
        #
        # Silently ignores the request if there is no such
        # cache file; should it?
        #
        subdir, cache_name = self._encode_filename(key)
        cache_entry_path = os.path.join(self.cache_dir, subdir, cache_name)
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
        "Encode an ID (assumed to be printable 7-bit ASCII) into a usable filename -> (dir, filename)"

        if not id:
            return ('_00','_00.MMC')

        return (self._encode_file_char(id[0]), ''.join([self._encode_file_char(i) for i in id]) + '.MMC')
