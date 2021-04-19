#!/usr/bin/env python3
# vi:set ai sm nu ts=4 sw=4 expandtab:
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
import queue
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
from RagnarokMUD.MagicMapper.GUI.MapViewerFrame   import MapClientFrame
from RagnarokMUD.MagicMapper.NetworkIO            import ProxyService

op = argparse.ArgumentParser(usage='%(prog)s [-ChlVv] [-H hostname] [-P port] [-p proxyport] [-S [user[:password]@][version:]host:port] [-w url]')

op.add_argument('-C', '--copyright', action='store_true', help='Print copyright and licensing information and exit.')
op.add_argument('-H', '--host', metavar='NAME', help='Connect to MUD host by name', default='rag.com')
op.add_argument('-l', '--local', action='store_true', help='Use built-in MUD interface instead of proxying for an external client.')
op.add_argument('-P', '--port', metavar='PORT', help='Connect to MUD port', default='2222')
op.add_argument('-p', '--proxy', metavar='PORT', help='External MUD client connectst to localhost port', default='2222')
op.add_argument('-S', '--socks', metavar='PROXY', help='Specify SOCKS proxy parameters')
op.add_argument('-V', '--version', action='store_true', help='Print program version number and exit.')
op.add_argument('-v', '--verbose', action='count', default=0, help='Increase output verbosity.')
op.add_argument('-w', '--web-base', metavar='URL', help='Base URL for stored image content.')

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
             Ragnarok Magic Map 6.1 Client (magicmapper)
                  *** PRE-RELEASE PREVIEW VERSION ***

Thank you for helping us test this program prior to releasing it as ready
for full production use.  In this version, this window will show some 
debugging information which you may or may not find useful in the testing
process.

Error messages about your map pages will show up here as well.  Eventually
they will be put in a GUI window for you.
""")

icon = None

class MagicMapperApp (tk.Tk):
    def __init__(self, *a, **kwargs):
        """Main application window for the magic mapper. Everything is launched
        from here."""
        tk.Tk.__init__(self, *a, **kwargs)
        self.proxy = None

        w = MapClientFrame(master=self, title="Ragnarok Magic Mapper",
            config=config, prog_name="magicmapper",
            verbose = args.verbose,
#            host=(args.host, args.port),
#            local_mode=args.local,
#            proxy_port=args.proxy,
#            socks_proxy=args.socks,
#            web_base=args.web_base,
            about_text = '''
This client displays your location on the MUD game's magic map as you explore.
            ''',
            help_text = '''
The official documentation for this program can be found online at the following URL:

https://www.rag.com/tech/tools/magicmapper

A brief synopsis of magicmapper's usage may be displayed by running it with the --help option.
            ''',
        )

        w.pack(fill=tk.BOTH, expand=True)
        display_splash_screen(self, 'magicmapperlogo.gif')


        if sys.platform != 'win32':
            icon = tk.PhotoImage(file=os.path.join(config.image_path,'mapper.gif'))
            self.call('wm', 'iconphoto', self, icon)
        else:
            try:
                self.iconbitmap(bitmap=os.path.join(config.image_path,'mapper.ico'),
                             default=os.path.join(config.image_path,'mapper.ico'))
            except Exception:
                pass

        if args.local:
            tk.messagebox.showerror(title="Not Implemented", 
                message="The local MUD client feature has not yet been implemented.")
            sys.exit(1)
        else:
            #
            # set up proxy service for external MUD client
            #
            self.proxy = ProxyService(
                remote_hostname=args.host,
                remote_port=args.port,
                local_hostname='localhost',
                local_port=args.proxy,
                event_queue = w.event_queue,
            )
            if args.socks:
                #
                # socks proxy string is [user[:password]@][version:]host:port
                #
                m = re.match(r'^(?:(.*?)(?::(.*))?@)?(?:(.*?):)?(.*):(.*)$', args.socks)
                if m:
                    socks_username = m.group(1)
                    socks_password = m.group(2)
                    socks_version = m.group(3) or '5'
                    socks_host = m.group(4)
                    socks_port = m.group(5)
                    proxy.set_socks_proxy(socks_version, socks_host, socks_port, socks_username, socks_password)
                else:
                    op.error('Invalid --socks value')
                    sys.exit(1)
            self.proxy.run()
            w.start_queue_runner()

    def stop(self):
        if self.proxy:
            print("Stopping communication threads...")
            self.proxy.stop()
            print("Done.")

Application = MagicMapperApp()
Application.mainloop()
Application.stop()