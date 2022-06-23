#!/usr/bin/env python3
# vi:set ai sm nu ts=4 sw=4 fileencoding=utf-8 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: mapping proxy
#
# Copyright (c) 2010, 2018, 2020 by Steven L. Willoughby, Aloha, Oregon, USA.
# All Rights Reserved.  Licensed under the Open Software License
# version 3.0.  See http://www.opensource.org/licenses/osl-3.0.php
# for details.
#
# Based on earlier code from the Ragnarok MudShell (MSH) client,
# Copyright (c) 1993, 2000, 2001, 2002, 2003 by Steven L. Willoughby,
# Aloha, Oregon, USA.  All Rights Reserved.  MSH is licensed under
# the terms of the BSD 3-clause license.
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
import argparse
import platform
import tkinter as tk
from tkinter import ttk

@@REL@@sys.tracebacklimit=0

#@@BEGIN-DEV:
sys.path.append(os.path.join('..','lib'))
#:END-DEV@@

from RagnarokMUD.MagicMapper.ConfigurationManager import ConfigurationManager
config = ConfigurationManager()
config.save_first()

from RagnarokMUD.MagicMapper.GUI.BasicDialogs     import display_splash_screen
from RagnarokMUD.MagicMapper.GUI.MapViewerFrame   import MapPreviewFrame

op = argparse.ArgumentParser(usage='%prog [-ChlVv] [-H hostname] [-P port] [-p proxyport] [-w url]')

op.add_argument('-C', '--copyright', action='store_true', help='Print copyright and licensing information and exit.')
op.add_argument('-H', '--host', metavar='NAME', help='Connect to MUD host by name', default='rag.com')
op.add_argument('-h', '--help', action='store_true', help='Print help and usage information and exit.')
op.add_argument('-l', '--local', action='store_true', help='Use built-in MUD interface instead of proxying for an external client.')
op.add_argument('-P', '--port', metavar='PORT', help='Connect to MUD port', default='2222')
op.add_argument('-p', '--proxy', metavar='PORT', help='External MUD client connectst to localhost port', default='2222')
op.add_argument('-V', '--version', action='store_true', help='Print program version number and exit.')
op.add_argument('-v', '--verbose', action='count', default=0, help='Increase output verbosity.')
op.add_argument('-w', '--web-base', metavar='URL', default=0, help='Increase output verbosity.')

args = op.parse_args()

if args.version:
    print("""Ragnarök Magic Map 6.1 Map Viewer Proxy (magicmapper)""")
    sys.exit(0)

if args.copyright:
    print("""Ragnarök Magic Map 6.1 Map Viewer Proxy (magicmapper)
Copyright © 2020 by Steven Willoughby, Aloha, Oregon, USA. All Rights Reserved.
Based on earlier code © 2003-2018 by Steven Willoughby and upon older code and
ideas by Ron Lunde. 

Distributed under the terms and conditions of the BSD 3-Clause License.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.""")
    sys.exit(0)

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

"""
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
"""
