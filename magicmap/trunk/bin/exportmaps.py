#!/usr/local/bin/python
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: mud-side map exporter
# On some systems, e.g., Microsoft Windows, we need to have a file 
# with a ".py" suffix so the system can associate it with the Python
# interpreter which needs to run it.  On other systems, e.g., Linux,
# Unix, Macintosh OSX, etc., the command is executed without the need 
# for that suffix, so the extra ".py" is just a distraction and seems
# weird to have to type.  
#
# So this file is just an alternative way to start the tool for the
# benefit of systems which need it.
# 
# $Header$
#
# Copyright (c) 2010, 2011 by Steven L. Willoughby, Aloha, Oregon, USA.
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

import imp
import os.path
import sys

#@@REL@@sys.tracebacklimit=0
exportmaps_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exportmaps')

try:
	mod = open(exportmaps_full_path, 'U')
	imp.load_module('exportmaps', mod, '', ('', 'U', 1))
finally:
	mod.close()
