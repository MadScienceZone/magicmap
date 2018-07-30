#!/usr/bin/python
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: mud-side map exporter
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

import sys
import os, os.path
import optparse
import platform
import glob
import itertools

#@@REL@@sys.tracebacklimit=0

#@@BEGIN-DEV:
#XXX FIXME XXX development hack
sys.path.append(os.path.join('..','lib'))
#:END-DEV@@

from RagnarokMUD.MagicMapper.ConfigurationManager import ConfigurationManager
import RagnarokMUD.MagicMapper.MagicMapCompiler

config = ConfigurationManager()

op = optparse.OptionParser(usage='%prog [-ghIrv] [-i imgdir] [-p pattern] mapfiles...', version='6.0')
if platform.system() == 'Windows':
    op.set_defaults(expand_globs=True, pattern='*.map', dest_dir="maproot")
else:
    op.set_defaults(pattern='*.map', dest_dir="maproot")

op.add_option('-g', '--expand-globs', action='store_true', help='Expand wildcard patterns in filename list [%default]')
op.add_option('-I', '--ignore-errors',action='store_true', help='Keep trying to finish even if some errors were found')
#op.add_option('-i', '--image-dir',    metavar='DIR',       help='Top-level embedded image directory')
#op.add_option('-p', '--pattern',      metavar='PAT',       help='Limit recursion to filenames matching wildcard pattern [%default]')
#op.add_option('-r', '--recursive',    action='store_true', help='Recurse into subdirectories looking for map files')
op.add_option('-d', '--dest-dir',     metavar='DIR',       help="Output directory root [%default]")
op.add_option('-v', '--verbose',      action='count',      help='Increase verbosity (cumulative)')

opt, cmd_map_file_list = op.parse_args()

if opt.expand_globs:
    cmd_map_file_list = list(itertools.chain(*[glob.glob(pattern) for pattern in cmd_map_file_list]))

for dir_name in cmd_map_file_list:
    RagnarokMUD.MagicMapper.MagicMapCompiler.make_world(dir_name, opt.dest_dir, True, opt.ignore_errors, enforce_creator=True, verbosity=opt.verbose)