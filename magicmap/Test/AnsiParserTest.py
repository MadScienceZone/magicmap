# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: ANSI Sequence Parser
# $Header$
#
# Copyright (c) 2012, 2018 by Steven L. Willoughby, Aloha, Oregon, USA.
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
#import datetime
#import threading
#import SimpleHTTPServer, BaseHTTPServer
#import urllib
#import posixpath
#import os, os.path
#import urllib2
#import time
#import shutil
#import email.utils

import unittest
from RagnarokMUD.MagicMapper.AnsiParser import *

class AnsiParserHarness (AnsiParser):
    def __init__(self, *a, **k):
        AnsiParser.__init__(self, *a, **k)
        self.stack = []

    def handle_tracking_stop(self, player_name):
        self.stack.append("stop")

    def handle_tracking_start(self, player_name):
        self.stack.append(["start", player_name])

    def handle_tracking_position(self, id):
        self.stack.append(["location", id])

    def handle_debug(self, a):
        self.stack.append(["debug"] + a)

    def handle_gauge_create(self, id, name, fmt):
        self.stack.append(['gauge create', id, name, fmt])

    def handle_gauge_update(self, id, value, maxvalue):
        self.stack.append(['gauge update', id, value, maxvalue])

    def handle_gauge_destroy(self, id):
        self.stack.append(['gauge destroy', id])

    def handle_image(self, id):
        self.stack.append(['image', id])

class AnsiParserTest (unittest.TestCase):
    def setUp(self):
        self.ap = AnsiParser()
        self.ah = AnsiParserHarness()

    def tearDown(self):
        self.ap = None
        self.ah = None

    def test_suppression(self):
        self.assertEqual(self.ap.filter('hello\33[>1tworld\n'), 'hello')

    def test_suppress_cancel(self):
        self.assertEqual(self.ap.filter('hello\33[>1tworld\33[>0there\n'), 'hellohere\n')

    def test_suppress_eol(self):
        self.assertEqual(self.ap.filter('hello\33[>1tworld\nvisible\n'), 'hellovisible\n')
        self.assertEqual(self.ap.filter('hello\33[>1tworld\nvisible'), 'hellovisible')
        self.assertEqual(self.ap.filter('\33[>1tworld\nvisible'), 'visible')
        self.assertEqual(self.ap.filter('\33[>1tworld\nvisible\33[>0t'), 'visible')
        self.assertEqual(self.ap.filter('\33[>1tworld\nvisible\33[K'), 'visible\33[K')

    def test_suppress_image(self):
        self.ap.inline_images_enabled = False
        self.assertEqual(self.ap.filter('hello\33[>2tworld\nvisible\n'), 'helloworld\nvisible\n')
        self.assertEqual(self.ap.filter('hello\33[>2tworld\nvisible'), 'helloworld\nvisible')
        self.assertEqual(self.ap.filter('\33[>2tworld\nvisible'), 'world\nvisible')
        self.assertEqual(self.ap.filter('\33[>2tworld\nvisible\33[>0t'), 'world\nvisible')
        self.assertEqual(self.ap.filter('\33[>2tworld\nvisible\33[K'), 'world\nvisible\33[K')

        self.ap.inline_images_enabled = True
        self.assertEqual(self.ap.filter('hello\33[>2tworld\nvisible\n'), 'hellovisible\n')
        self.assertEqual(self.ap.filter('hello\33[>2tworld\nvisible'), 'hellovisible')
        self.assertEqual(self.ap.filter('\33[>2tworld\nvisible'), 'visible')
        self.assertEqual(self.ap.filter('\33[>2tworld\nvisible\33[>0t'), 'visible')
        self.assertEqual(self.ap.filter('\33[>2tworld\nvisible\33[K'), 'visible\33[K')

    def test_passthrough(self):
        self.assertEqual(self.ap.filter('hello, world'), 'hello, world')

    def test_start(self):
        self.assertEqual(self.ah.filter('a\33[>1;"jon"pb'), 'ab')
        self.assertEqual(self.ah.stack, [['start','jon']])

    def test_start_null_name(self):
        self.assertEqual(self.ah.filter('aa\33[>1;pbb'), 'aabb')
        self.assertEqual(self.ah.stack, [['start',None]])

    def test_start_null_name2(self):
        self.assertEqual(self.ah.filter('aa\33[>1pbb'), 'aabb')
        self.assertEqual(self.ah.stack, [['start',None]])

    def test_start_null_name_no_semi(self):
        self.assertEqual(self.ah.filter('aa\33[>1"jon"pbb'), 'aabb')
        self.assertEqual(self.ah.stack, [['start','jon']])

    def test_invalid_private(self):
        self.assertEqual(self.ap.filter('a\33[>134abc'), 'abc')    # filtered out

    def test_not_our_sequence(self):
        self.assertEqual(self.ap.filter('a\33[Aabc'), 'a\33[Aabc') # passed

    def test_embedded_digits_in_string(self):
        self.assertEqual(self.ah.filter('a\33[>1;"abc123def"q'), 'a')
        self.assertEqual(self.ah.stack, [['debug', 1, 'abc123def']])

    def test_juxtapositions(self):
        self.assertEqual(self.ah.filter('a\33[>"xxx"5;6"qq";"ab"3"de""jk"q'), 'a')
        self.assertEqual(self.ah.stack, [['debug', 'xxx', 5, 6, 'qq', 'ab', 3, 'de', 'jk']])

    def test_juxtapositions2(self):
        self.assertEqual(self.ah.filter('a\33[>"xxx"5;6"qq";"ab"3"de""jk"2q'), 'a')
        self.assertEqual(self.ah.stack, [['debug', 'xxx', 5, 6, 'qq', 'ab', 3, 'de', 'jk', 2]])

    def test_invalid_private(self):
        self.assertEqual(self.ap.filter('aa\33[>1;2;"34"56abc'), 'aa\33[>1;2;"34";56abc')

    def test_unterminated(self):
        self.assertRaises(IncompleteSequence, self.ap.filter, 'aa\33[>17')

    def test_gauge(self):
        self.assertEqual(self.ah.filter('q\33[>12;"foo";"{}"wq'), 'qq')
        self.assertEqual(self.ah.stack, [['gauge create', 12, 'foo', '{}']])

        self.assertEqual(self.ah.filter('\33[>3;"HP";"{v}/{max} HP"wx\33[>3;27;123u\33[>3x'), 'x')
        self.assertEqual(self.ah.stack, [['gauge create', 12, 'foo', '{}'],
                                          ['gauge create', 3, "HP", "{v}/{max} HP"],
                                          ['gauge update', 3, 27, 123],
                                          ['gauge destroy', 3]])

    def test_location(self):
        self.assertEqual(self.ah.filter('1\33[>"aa"~2\33[>"bb"~\33[>~\33[>""~3'), '123')
        self.assertEqual(self.ah.stack, [
            ['location', 'aa'],
            ['location', 'bb'],
            ['location', None],
            ['location', None]
            ])

    def test_image(self):
        self.assertEqual(self.ah.filter('1\33[>"aa"v2\33[>"bb"v\33[>v\33[>""v3'), '123')
        self.assertEqual(self.ah.stack, [
            ['image', 'aa'],
            ['image', 'bb'],
            ])

    def test_disabled_image(self):
        self.ah.inline_images_enabled = False
        self.assertEqual(self.ah.filter('1\33[>"aa"v2\33[>"bb"v\33[>v\33[>""v3'), '123')
        self.assertEqual(self.ah.stack, [])
