#!/usr/bin/env python3
# vi:set ai sm nu ts=4 sw=4 fileencoding=utf-8 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: mapping client
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

import sys
import os, os.path
import optparse
import platform
import tkinter as tk
from tkinter import ttk

#@@REL@@sys.tracebacklimit=0

#@@BEGIN-DEV:
sys.path.append(os.path.join('..','lib'))
#:END-DEV@@

from RagnarokMUD.MagicMapper.ConfigurationManager import ConfigurationManager
config = ConfigurationManager()
config.save_first()

from RagnarokMUD.MagicMapper.GUI.BasicDialogs     import display_splash_screen
from RagnarokMUD.MagicMapper.GUI.MapViewerFrame   import MapPreviewFrame

op = optparse.OptionParser(usage='%prog [-bghIrv] [-C creator] [-i imgdir] [-p pattern] mapfiles...', version='6.1')
if platform.system() == 'Windows':
    op.set_defaults(expand_globs=True, pattern='*.map')
else:
    op.set_defaults(pattern='*.map')

op.add_option('-b', '--enforce-boundaries', action='store_true', help='Enforce creator/realm boundaries')
op.add_option('-C', '--creator',      help='Specify realm creator name (rather than deducing it from pathnames)')
op.add_option('-g', '--expand-globs', action='store_true', help='Expand wildcard patterns in filename list [%default]')
op.add_option('-I', '--ignore-errors',action='store_true', help='Keep trying to finish even if some errors were found')
op.add_option('-i', '--image-dir',    metavar='DIR',       help='Top-level embedded image directory')
op.add_option('-p', '--pattern',      metavar='PAT',       help='Limit recursion to filenames matching wildcard pattern [%default]')
op.add_option('-r', '--recursive',    action='store_true', help='Recurse into subdirectories looking for map files')
op.add_option('-v', '--verbose',      action='count',      help='Increase verbosity (cumulative)')

opt, cmd_map_file_list = op.parse_args()

print("""
             Ragnarok Magic Map 6.1 Preview Tool (viewmap)
                  *** PRE-RELEASE PREVIEW VERSION ***

Thank you for helping us test this program prior to releasing it as ready
for full production use.  In this version, this window will show some 
debugging information which you may or may not find useful in the testing
process.

Error messages about your map pages will show up here as well.  Eventually
they will be put in a GUI window for you.
""")

icon = None

class MapPreviewApp (tk.Tk):
    def __init__(self, *args, **kwargs):
        global icon

        tk.Tk.__init__(self, *args, **kwargs)


        w = MapPreviewFrame(master=self, title="Ragnarok Map Preview", config=config, prog_name="viewmap",
            expand_globs = opt.expand_globs,
            recursive = opt.recursive,
            pattern = opt.pattern,
            ignore_errors = opt.ignore_errors,
            verbose = opt.verbose or 0,
            file_list = cmd_map_file_list,
            creator_name = opt.creator,
            enforce_creator = bool(opt.enforce_boundaries),
            image_dir = opt.image_dir,
            about_text = '''
This application allows wizards to preview what their maps will look like by loading the raw "source" form of the map pages into this viewer.

Run with the --help option for more details, or see the documentation online.  (Link below)''',
            help_text = '''The official documentation for this program can be found
online at the following URL:

http://www.rag.com/tech/tools/viewmap

A brief synopsis of viewmap's usage may be displayed by
running it with the --help option.''')
        w.pack(fill=tk.BOTH, expand=True)
        display_splash_screen(self, 'viewmaplogo.gif')

        if sys.platform != 'win32':
            icon = tk.PhotoImage(file=os.path.join(config.image_path,'mapper.gif'))
            self.call('wm', 'iconphoto', self, icon)
        else:
            try:
                self.iconbitmap(bitmap=os.path.join(config.image_path,'mapper.ico'),
                             default=os.path.join(config.image_path,'mapper.ico'))
            except Exception:
                pass

Application = MapPreviewApp()
Application.mainloop()
