#!/usr/local/bin/python
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: mapping client
# $Header$
#
# Copyright (c) 2010, 2012 by Steven L. Willoughby, Aloha, Oregon, USA.
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
import wx
import optparse

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

op = optparse.OptionParser(usage='%prog [-hv] [-H hostname] [-P port] [-L localhost] [-p localport]', version='6.0')
op.set_defaults(
        hostname=config.get('connection', 'remote_hostname'),
        local_hostname=config.get('connection', 'local_hostname'),
        local_port=config.get('connection', 'local_port'),
        port=config.get('connection', 'remote_port'),
)

op.add_option('-H', '--hostname', action='store', metavar='NAME', help='game host [%default]')
op.add_option('-L', '--local-hostname', action='store', metavar='NAME', help='local proxy host [%default]')
op.add_option('-p', '--local-port', type='int', action='store', metavar='N', help='local proxy port [%default]')
op.add_option('-P', '--port', action='store', type='int', metavar='N', help='TCP port [%default]')
op.add_option('-v', '--verbose',      action='count',      help='Increase verbosity (cumulative)')

opt, extra_args = op.parse_args()

if extra_args:
    op.error("Extra non-option arguments")

print """
                  Ragnarok Magic Map 6.0b1 (magicmap)
                  *** PRE-RELEASE PREVIEW VERSION ***

Thank you for helping us test this program prior to releasing it as ready
for full production use.  In this version, this window will show some 
debugging information which you may or may not find useful in the testing
process.

Error messages about your map pages will show up here as well.  Eventually
they will be put in a GUI window for you.
"""
#
# ConfigurationManager
# MapClientApp
#   MapClientFrame (menus)
#      MapManager (live data + database)
#         NetworkIO (fetch more data)
#   ProxyService
#      AnsiParser
#
#

class MapClientApp(wx.App):
    def OnInit(self):
        self.scheduled_comms = False

        display_splash_screen('magicmaplogo.png')
        frame = MapClientFrame(title="Magic Mapper", config=config, prog_name="magicmap",
#            hostname = opt.hostname,
#            port = opt.port,
            verbose = opt.verbose,
            about_text = '''
This application draws your magic map in real time as you explore the MUD.

Run with the --help option for more details, or see the documentation online.  (Link below)''',
            help_text = '''The official documentation for this program can be found
online at the following URL:

http://www.rag.com/tech/tools/magicmap

A brief synopsis of magicmap's usage may be displayed by
running it with the --help option.''')
        frame.Show()
        self.SetTopWindow(frame)

        # start communications proxy
        self.proxy = ProxyService(
            local_hostname = opt.local_hostname,
            local_port = opt.local_port,
            remote_hostname = opt.hostname,
            remote_port = opt.port,
            target_viewer = frame
        )
        if config.has_section('proxy'):
            try:
                if config.getbool('proxy', 'mud_proxy_on'):
                    self.proxy.set_socks_proxy(config.get('proxy', 'mud_proxy_type'),
                            config.get('proxy', 'mud_proxy_server'),
                            config.getint('proxy', 'mud_proxy_port'))
            except Exception as err:
                print "XXX Unable to set proxy: {}".format(err)

        self.Bind(wx.EVT_IDLE, self.OnIdle)
        return True

    def OnIdle(self, event):
        # throttle polls to 100mS intervals
        if not self.scheduled_comms:
            wx.CallLater(100, self.DoComms)
            self.scheduled_comms = True

    def DoComms(self):
        self.proxy.poll()
        self.scheduled_comms = False

#    def OnExit(self):

Application = MapClientApp(redirect=False)
Application.MainLoop()
#@@BEGIN-DEV:
#
# Style notes:
#  1. import wx (not * or wxPython.wx stuff)
#  2. constructors should use kw args
#  3. Don't use IDs; wx.ID_ANY if needed
#     But use standard IDs like wx.ID_EXIT
#  4. Use Bind() for events
#  5. sizers, not absolute positions
#  6. wx.App, not wx.PySimpleApp
#  7. separate classes, not nested panels in one
#  8. native preferred over wx: size=(500,400) not size=wx.Size(500,400)
#  9. docstrings
# 10. StdDialogButtonSizer adapts to platform look and feel
# 
#:END-DEV@@
