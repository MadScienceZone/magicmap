# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: GUI: Map Viewer Frame
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
import sys
import os.path
import wx
import itertools

from glob    import glob
from fnmatch import fnmatch

from wx.lib.wordwrap import wordwrap

from RagnarokMUD.MagicMapper.GUI.MapCanvas import MapCanvas
from RagnarokMUD.MagicMapper.MapSource     import MapSource, MapFileFormatError, DuplicateRoomError
from RagnarokMUD.MagicMapper.MapManager    import MapManager

class MapViewerFrame (wx.Frame):
    def __init__(self, parent=None, image_dir=None, config=None, prog_name=None, about_text=None, help_text=None, verbose=False, **k):
        wx.Frame.__init__(self, parent, **k)
        self.verbose = verbose

        if prog_name is None:
            self.prog_name = sys.argv[0]
        else:
            self.prog_name = prog_name

        self.about_text = about_text
        self.help_text = help_text
        self.config = config
        self.image_dir = image_dir

        self.CreateStatusBar()
        self.canvas = MapCanvas(self, config=config, image_dir=image_dir)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.canvas, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()

        #self.canvas.Fit()

    def _setup_menus(self, menu_list):
        menu_bar = wx.MenuBar()
        for menu, item_list in menu_list:
            the_menu = wx.Menu()
            for title, description, binding, id in item_list:
                if title:
                    self.Bind(wx.EVT_MENU, binding, the_menu.Append(id, title, description))
                else:
                    the_menu.AppendSeparator()
            menu_bar.Append(the_menu, menu)
        self.SetMenuBar(menu_bar)

    def OnZoom100(self, event): self._not_yet()
    def OnZoomIn(self, event): self._not_yet()
    def OnZoomOut(self, event): self._not_yet()
    def OnEditPreferences(self, event): self._not_yet()

    def OnCloseWindow(self, event):
        self.Close(True)

    def Alert(self, text, title, flags):
        dlg = wx.MessageDialog(self, text, title, flags)
        dlg.ShowModal()
        dlg.Destroy()

    def _not_yet(self):
        self.Alert("Not yet implemented", "Error", wx.OK | wx.ICON_ERROR)

    def OnAbout(self, event):
        about = wx.AboutDialogInfo()
        about.Name = self.prog_name
        about.Version = '%MAGICMAP_RELEASE%'
        about.Copyright = 'Ragnarok Magic Mapper (c) 1993, 2000, 2001, 2002, 2003, 2010, 2012, 2018.  All Rights Reserved.'
        about.Description = wordwrap(self.about_text, 500, wx.ClientDC(self))
        about.WebSite = "http://www.rag.com/tech/tools/{0}".format(self.prog_name), "Program information and documentation"
        about.Developers = ['Written by Steve Willoughby',
                            'Based on some original ideas by Ron Lunde']
        about.License = wordwrap('''
Licensed under the Open Software License version 3.0.

In brief, Licensor grants You a worldwide, royalty-free, non-exclusive, sublicensable license, for the duration of the copyright, to reproduce the Original Work in copies, either alone or as part of a collective work; to translate, adapt, alter, transform, modify, or arrange the Original Work, thereby creating derivative works ("Derivative Works") based upon the Original Work; to distribute or communicate copies of the Original Work and Derivative Works to the public, with the proviso that copies of Original Work or Derivative Works that You distribute or communicate shall be licensed under this Open Software License; to perform the Original Work publicly; and to display the Original Work publicly.

This is not the full text of the license agreement.  See the accompanying LICENSE file (or view it at http://www.opensource.org/licenses/osl-3.0.php) for the complete list of terms and conditions.
                ''', 500, wx.ClientDC(self))
        wx.AboutBox(about)

        #self.Alert(self.about_text, "About {0}".format(self.prog_name), wx.OK | wx.ICON_INFORMATION)

    def OnHelp(self, event):
        self.Alert(self.help_text, "Documentation for {0}".format(self.prog_name), wx.OK | wx.ICON_INFORMATION)


class MapPreviewFrame (MapViewerFrame):
    def __init__(self, recursive=False, expand_globs=False, pattern="*.map", ignore_errors=False, verbose=False, file_list=None, **k):
        MapViewerFrame.__init__(self, **k)
        self.recursive = recursive
        self.expand_globs = expand_globs
        self.file_list = file_list or []
        self.pattern = pattern
        self.ignore_errors = ignore_errors

        self._setup_menus((
            ('&File', (
                ('&Open Map File(s)...\tCtrl+O', 'Open map file(s) to display', self.OnOpenFiles, wx.ID_OPEN),
                ('Open Map &Folder...', 'Recursively open maps in folder', self.OnOpenDirs, -1),
                (None, None, None, None),
                ('E&xit\tCtrl+Q', 'Terminate the program', self.OnCloseWindow, wx.ID_EXIT),
            )),
            ('&Edit', (
                ('&Preferences...', 'Change configuration settings', self.OnEditPreferences, wx.ID_PREFERENCES),
            )),
            ('&View', (
                ('&Next page\tPgDn', 'Display next page (wraps around to start)', self.OnNextPage, wx.ID_FORWARD),
                ('&Previous page\tPgUp', 'Display previous page (wraps around to end)', self.OnPrevPage, wx.ID_BACKWARD),
                ('&Refresh', 'Re-display current page image', self.OnRefresh, wx.ID_REFRESH),
                (None, None, None, None),
                ('Normal &size\tCtrl+0', 'Change magnification to 100%', self.OnZoom100, wx.ID_ZOOM_100),
                ('&Zoom in\tCtrl++', 'Increase magnification +10%', self.OnZoomIn, wx.ID_ZOOM_IN),
                ('Zoom &out\tCtrl+-', 'Decrease magnification -10%', self.OnZoomOut, wx.ID_ZOOM_OUT),
                (None, None, None, None),
                ('&Reload\tCtrl+R', 'Reload all map pages from source files', self.OnReload, wx.ID_REFRESH),
                ('&Location Test', 'Cycle through all locations on this page', self.OnLocationTest, -1),
            )),
            ('&Help', (
                ('&Documentation...', 'Where to get program documentation online', self.OnHelp, wx.ID_HELP),
                ('&About {0}...'.format(self.prog_name), 'At-a-glance info about {0}'.format(self.prog_name), self.OnAbout, wx.ID_ABOUT),
            )),
        ))
        self.OnReload(None)

    def OnOpenFiles(self, event): 
        dlg = wx.FileDialog(self, 'Open Map File(s)', 
            wildcard=('Custom Pattern ({0})|{0}|'.format(self.pattern) if self.pattern != '*.map' else '')+
                'Magic Map files (*.map)|*.map|All Files (*.*)|*.*', 
            style=wx.OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.file_list = dlg.GetPaths()
            self.recursive = False
            self.OnReload(None)
        dlg.Destroy()

    def OnOpenDirs(self, event):
        dlg = wx.DirDialog(self, 'Open Maps ({0}) in Folder and all Subfolders'.format(self.pattern),
               style=wx.DD_CHANGE_DIR | wx.DD_DEFAULT_STYLE) 
        if dlg.ShowModal() == wx.ID_OK:
            self.file_list = [dlg.GetPath()]
            self.recursive = True
            self.OnReload(None)
        dlg.Destroy()

    def OnRefresh(self, event):
        self.canvas.Refresh()

    def OnReload(self, event): 
        "Read the files the user wants to display into our map collection."
        self.SetStatusText("Loading Magic Map...")
        #
        # Get list of map files to preview
        #
        if self.verbose > 1: print "OnReload(): file_list=", self.file_list, "recursive=", self.recursive

        if self.expand_globs:
            map_file_list = list(itertools.chain(*[glob(pattern) for pattern in self.file_list]))
        else:
            map_file_list = self.file_list

        if self.verbose > 1: print "OnReload(): map_file_list=", map_file_list

        if self.recursive:
            root_list, map_file_list = map_file_list, []
            for root in root_list:
                if self.verbose > 1: print "OnReload(): recursing:", root
                for dirpath, dirnames, filenames in os.walk(root):
                    if self.verbose > 1: print "OnReload(): recursing:", root, "--(", dirpath, dirnames, filenames, ")--"
                    map_file_list.extend([os.path.join(dirpath, f) for f in filenames if fnmatch(f, self.pattern)])
            if self.verbose > 1: print "OnReload(): map_file_list=", map_file_list
        #
        # Load and compile them into memory
        #
        self.world_map = MapSource()

        for map_file in map_file_list:
            if self.verbose: print "*** Loading {0} ***".format(map_file)

            try:
                self.world_map.add_from_file(open(map_file))
            except (MapFileFormatError, DuplicateRoomError) as problem:
                print "ERROR in {0}: {1}".format(map_file, problem)
                if not self.ignore_errors:
                    print "Processing stopped on fatal map error (use --ignore-errors to avoid this)."
                    raise

        if self.verbose:
            print "\n*** Loaded {0} page{1} ({2} room{3}) from {4} map source file{5}. ***".format(
                len(self.world_map.pages), '' if len(self.world_map.pages)==1 else 's',
                len(self.world_map.room_page), '' if len(self.world_map.room_page)==1 else 's',
                len(map_file_list), '' if len(map_file_list)==1 else 's'
            )
            print "Map page list:", sorted(self.world_map.pages)

        self.SetStatusText("")
        #
        # Display first page
        #
        if self.world_map.pages:
            self.page_list = sorted(self.world_map.pages)
            self._set_page_idx(0)

    def _set_page_idx(self, new_idx):
        if 0 <= new_idx < len(self.page_list):
            self.page_idx = new_idx
            page_no = self.page_list[self.page_idx]
            self.canvas.display_page(self.world_map.pages[page_no])
            self.SetStatusText("Displaying Page {0}.".format(page_no))

    def OnNextPage(self, event): self._set_page_idx((self.page_idx + 1) % len(self.page_list))
    def OnPrevPage(self, event): self._set_page_idx((self.page_idx - 1) % len(self.page_list))

    def OnLocationTest(self, event): 
        wx.FutureCall(1, self.NextLocationTest, sorted([room.id for room in self.canvas.page_obj.rooms.values()]))

    def NextLocationTest(self, room_id_list):
        if len(room_id_list) > 0:
            wx.FutureCall(self.config.getfloat('preview', 'location_delay')*1000.0, self.NextLocationTest, room_id_list[1:])
            self.SetStatusText("Showing location {0} ({1} more).".format(room_id_list[0], len(room_id_list)-1))
            self.canvas.SetCurrentLocation(room_id_list[0])
        else:
            self.canvas.SetCurrentLocation(None)
            self.SetStatusText("Done.")




class MapClientFrame (MapViewerFrame):
    def __init__(self, **k):
        MapViewerFrame.__init__(self, **k)

        self._setup_menus((
            ('&File', (
#                ('&Open Map File(s)...\tCtrl+O', 'Open map file(s) to display', self.OnOpenFiles, wx.ID_OPEN),
#                ('Open Map &Folder...', 'Recursively open maps in folder', self.OnOpenDirs, -1),
#                (None, None, None, None),
                ('E&xit\tCtrl+Q', 'Terminate the program', self.OnCloseWindow, wx.ID_EXIT),
            )),
            ('&Edit', (
                ('&Preferences...', 'Change configuration settings', self.OnEditPreferences, wx.ID_PREFERENCES),
            )),
            ('&View', (
                ('&Next page\tPgDn', 'Display next page (wraps around to start)', self.OnNextPage, wx.ID_FORWARD),
                ('&Previous page\tPgUp', 'Display previous page (wraps around to end)', self.OnPrevPage, wx.ID_BACKWARD),
                ('&Refresh', 'Re-display current page image', self.OnRefresh, wx.ID_REFRESH),
                (None, None, None, None),
                ('Normal &size\tCtrl+0', 'Change magnification to 100%', self.OnZoom100, wx.ID_ZOOM_100),
                ('&Zoom in\tCtrl++', 'Increase magnification +10%', self.OnZoomIn, wx.ID_ZOOM_IN),
                ('Zoom &out\tCtrl+-', 'Decrease magnification -10%', self.OnZoomOut, wx.ID_ZOOM_OUT),
                (None, None, None, None),
#                ('&Reload\tCtrl+R', 'Reload all map pages from source files', self.OnReload, wx.ID_REFRESH),
#                ('&Location Test', 'Cycle through all locations on this page', self.OnLocationTest, -1),
            )),
            ('&Help', (
                ('&Documentation...', 'Where to get program documentation online', self.OnHelp, wx.ID_HELP),
                ('&About {0}...'.format(self.prog_name), 'At-a-glance info about {0}'.format(self.prog_name), self.OnAbout, wx.ID_ABOUT),
            )),
        ))

        self.world_map = MapManager(config=self.config)
        #self.OnReload(None)

    def tracking_start(self, player_id):
        self.world_map.open(player_id)

    def tracking_stop(self):
        self.world_map.close()

    def tracking_position(self, room_id=None):
        if room_id is None:
            print "XXX you are now off the map"
            return

        print 'XXX tracking_position({})'.format(room_id)
        current_location = self.world_map.move_to(room_id)
        if current_location is None:
            print "XXX you are now off the map (not expected: {})".format(room_id)
        else:
            print "XXX you are now in room {}, page {}".format(
                    current_location.id, current_location.page.page)

    def tracking_sync(self, i, total, modtime, checksum, room_id):
        print "XXX update", i, "of", total, "mod", modtime, "chk", checksum, "id", room_id
        self.world_map.load(room_id, modtime, checksum)

#    def OnOpenFiles(self, event): 
#        dlg = wx.FileDialog(self, 'Open Map File(s)', 
#            wildcard=('Custom Pattern ({0})|{0}|'.format(self.pattern) if self.pattern != '*.map' else '')+
#                'Magic Map files (*.map)|*.map|All Files (*.*)|*.*', 
#            style=wx.OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
#        if dlg.ShowModal() == wx.ID_OK:
#            self.file_list = dlg.GetPaths()
#            self.recursive = False
#            self.OnReload(None)
#        dlg.Destroy()
#
#    def OnOpenDirs(self, event):
#        dlg = wx.DirDialog(self, 'Open Maps ({0}) in Folder and all Subfolders'.format(self.pattern),
#               style=wx.DD_CHANGE_DIR | wx.DD_DEFAULT_STYLE) 
#        if dlg.ShowModal() == wx.ID_OK:
#            self.file_list = [dlg.GetPath()]
#            self.recursive = True
#            self.OnReload(None)
#        dlg.Destroy()

    def OnRefresh(self, event):
        self.canvas.Refresh()

#    def OnReload(self, event): 
#        "Read the files the user wants to display into our map collection."
#        self.SetStatusText("Loading Magic Map...")
        #
        # Get list of map files to preview
        #
#        if self.verbose > 1: print "OnReload(): file_list=", self.file_list, "recursive=", self.recursive
#
#        if self.expand_globs:
#            map_file_list = list(itertools.chain(*[glob(pattern) for pattern in self.file_list]))
#        else:
#            map_file_list = self.file_list
#
#        if self.verbose > 1: print "OnReload(): map_file_list=", map_file_list
#
#        if self.recursive:
#            root_list, map_file_list = map_file_list, []
#            for root in root_list:
#                if self.verbose > 1: print "OnReload(): recursing:", root
#                for dirpath, dirnames, filenames in os.walk(root):
#                    if self.verbose > 1: print "OnReload(): recursing:", root, "--(", dirpath, dirnames, filenames, ")--"
#                    map_file_list.extend([os.path.join(dirpath, f) for f in filenames if fnmatch(f, self.pattern)])
#            if self.verbose > 1: print "OnReload(): map_file_list=", map_file_list
#        #
        # Load and compile them into memory
        #
#        self.world_map = MapSource()
#
#        for map_file in map_file_list:
#            if self.verbose: print "*** Loading {0} ***".format(map_file)
#
#            try:
#                self.world_map.add_from_file(open(map_file))
#            except (MapFileFormatError, DuplicateRoomError) as problem:
#                print "ERROR in {0}: {1}".format(map_file, problem)
#                if not self.ignore_errors:
#                    print "Processing stopped on fatal map error (use --ignore-errors to avoid this)."
#                    raise
#
#        if self.verbose:
#            print "\n*** Loaded {0} page{1} ({2} room{3}) from {4} map source file{5}. ***".format(
#                len(self.world_map.pages), '' if len(self.world_map.pages)==1 else 's',
#                len(self.world_map.room_page), '' if len(self.world_map.room_page)==1 else 's',
#                len(map_file_list), '' if len(map_file_list)==1 else 's'
#            )
#            print "Map page list:", sorted(self.world_map.pages)
#
#        self.SetStatusText("")
        #
        # Display first page
        #
#        if self.world_map.pages:
#            self.page_list = sorted(self.world_map.pages)
#            self._set_page_idx(0)

    def _set_page_idx(self, new_idx):
        if 0 <= new_idx < len(self.page_list):
            self.page_idx = new_idx
            page_no = self.page_list[self.page_idx]
            self.canvas.display_page(self.world_map.pages[page_no])
            self.SetStatusText("Displaying Page {0}.".format(page_no))

    def OnNextPage(self, event): self._set_page_idx((self.page_idx + 1) % len(self.page_list))
    def OnPrevPage(self, event): self._set_page_idx((self.page_idx - 1) % len(self.page_list))

#    def OnLocationTest(self, event): 
#        wx.FutureCall(1, self.NextLocationTest, sorted([room.id for room in self.canvas.page_obj.rooms.values()]))
#
#    def NextLocationTest(self, room_id_list):
#        if len(room_id_list) > 0:
#            wx.FutureCall(self.config.getfloat('preview', 'location_delay')*1000.0, self.NextLocationTest, room_id_list[1:])
#            self.SetStatusText("Showing location {0} ({1} more).".format(room_id_list[0], len(room_id_list)-1))
#            self.canvas.SetCurrentLocation(room_id_list[0])
#        else:
#            self.canvas.SetCurrentLocation(None)
##            self.SetStatusText("Done.")
