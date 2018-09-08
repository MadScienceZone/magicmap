# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: Configuration Manager
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
from RagnarokMUD.MagicMapper.ConfigurationManager import ConfigurationManager
import os.path

class ConfigurationManagerTest (unittest.TestCase):
    def test_defaults(self):
        c = ConfigurationManager()
        self.assertAlmostEqual(c.getfloat('rendering', 'font_magnification'), 0.85)

    def test_load(self):
        c = ConfigurationManager([os.path.join('data', 'test_load.ini')])
        self.assertAlmostEqual(c.getfloat('rendering', 'font_magnification'), 1.123)
