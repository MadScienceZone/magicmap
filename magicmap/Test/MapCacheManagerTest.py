# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: Magic Map Data Caching
# $Header$
#
# Copyright (c) 2010, 2018 by Steven L. Willoughby, Aloha, Oregon, USA.
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

import unittest
import os, os.path
from RagnarokMUD.MagicMapper.MapCacheManager import MapCacheManager, CacheManagerError
import datetime
import shutil
import io
import time

CACHEDIR = os.path.join('data','testcache')

class MapCacheManagerTest (unittest.TestCase):
    def setUp(self):
        if os.path.exists(CACHEDIR):
            shutil.rmtree(CACHEDIR)

        self.cm = MapCacheManager(CACHEDIR)
        self.assertTrue(os.path.exists(CACHEDIR), "Can't find "+CACHEDIR+" after opening it.")
        self.assertTrue(os.path.isdir(CACHEDIR), CACHEDIR+" is not a directory.")

    def tearDown(self):
        self.cm.close()
        del self.cm

    def test_fn_1(self):
        self.assertEqual(self.cm._encode_filename('rmO_aPzcZbw4g_HlzLxk8k'), ('_R', '_R_M', '_R_MO_5F_AP_Z_CZ_B_W4_G_5FH_L_ZL_X_K8_K.MMC'))
    def test_fn_2(self):
        self.assertEqual(self.cm._encode_filename('-cRDWjIFbaTKhi4IEUIr6F'), ('_2D', '_2D_C', '_2D_CRDW_JIF_B_ATK_H_I4IEUI_R6F.MMC'))
    def test_fn_3(self):
        self.assertEqual(self.cm._encode_filename('5B7r7QXftBdRNJEBK0YFPV'), ('5', '5B', '5B7_R7QX_F_TB_DRNJEBK0YFPV.MMC'))

    def test_store(self):
        self.cm.store('Test', io.StringIO('''This is a test file.

This is only a test.'''))
        self.assertEqual(self.cm.retrieve('Test')[0].read(), '''This is a test file.

This is only a test.''')
        
    def test_not_found(self):
        self.assertTrue(self.cm.retrieve('NotThere') is None, "Didn't flag NotThere as being... well... not thre!")

    def test_invalid_dir(self):
        open(os.path.join('data','testcache','F'), 'w').close()
        self.assertRaises(CacheManagerError, self.cm.store, 'Fail', io.StringIO(''))

    def test_cache_expired(self):
        self.cm.store('TimeTest', io.StringIO('''Has this timed out?'''))
        old_age = self.cm.retrieve('TimeTest')[1]
        time.sleep(2)
        new_age = self.cm.retrieve('TimeTest')[1]
        self.assertTrue(1 <= new_age <= 3, "new age was %d" % new_age)
        time.sleep(1)
        self.cm.touch('TimeTest')
        newer_age = self.cm.retrieve('TimeTest')[1]
        self.assertTrue(0 <= newer_age <= 1, "newer age was %d after touch() call" % newer_age)

    def test_invalid_cache(self):
        open(os.path.join('data','ThisIsNotACacheDir'),'w').close()
        self.assertRaises(CacheManagerError, MapCacheManager, os.path.join('data','ThisIsNotACacheDir'))
