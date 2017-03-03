# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: Magic Map Pages
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

import unittest
from RagnarokMUD.MagicMapper.MapPage import MapPage, PORTRAIT, LANDSCAPE, PageOrientationViolationError

class MapPageTest (unittest.TestCase):
    def test_cons(self):
        p = MapPage(27, realm='Xanadu', orient=LANDSCAPE, bg=None)
        self.assertEquals(p.page, 27)
        self.assertEquals(p.realm, 'Xanadu')
        self.assertEquals(p.orient, LANDSCAPE)
        self.assertEquals(p.bg, [])

    def test_defs(self):
        p=MapPage(88)
        self.assertEquals(p.page, 88)
        self.assert_(p.realm is None)
        self.assertEquals(p.orient, PORTRAIT)
        self.assertEquals(p.bg, [])

    def test_cons_errors(self):
        self.assertRaises(ValueError, MapPage, 'A1')
        self.assertRaises(TypeError, MapPage, None)
        self.assertRaises(ValueError, MapPage, 1, orient=27)

    def test_orient_flip(self):
        p=MapPage(1)
        self.assertEquals(p.orient, PORTRAIT)
        p.orient=PORTRAIT
        self.assertEquals(p.orient, PORTRAIT)
        p.orient=PORTRAIT
        self.assertEquals(p.orient, PORTRAIT)
        def f(v):
            p.orient=v
        self.assertRaises(PageOrientationViolationError, f, LANDSCAPE)

        p=MapPage(2)
        self.assertEquals(p.orient, PORTRAIT)
        p.orient=LANDSCAPE
        self.assertEquals(p.orient, LANDSCAPE)
        p.orient=LANDSCAPE
        self.assertEquals(p.orient, LANDSCAPE)
        def f(v):
            p.orient=v
        self.assertRaises(PageOrientationViolationError, f, PORTRAIT)
