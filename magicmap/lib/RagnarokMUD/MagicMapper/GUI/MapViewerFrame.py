# vi:set ai sm nu ts=4 sw=4 expandtab fileencoding=utf-8:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: GUI: Map Viewer Frame
# $Header$
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
import os.path
import itertools
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
import tkinter.messagebox
import traceback
import re

from glob    import glob
from fnmatch import fnmatch

from RagnarokMUD.MagicMapper.GUI.MapCanvas import MapCanvas
from RagnarokMUD.MagicMapper.MapSource     import MapSource, MapFileFormatError, DuplicateRoomError
from RagnarokMUD.MagicMapper.MapManager    import MapManager

class KeyBindingDef:
    def __init__(self, label, keycode):
        self.label = label
        self.keycode = keycode

def GUI_call(f):
    def _wrapper(*a, **k):
        try:
            f(*a, **k)
        except Exception as problem:
            i = sys.exc_info()
            tk.messagebox.showerror(
                title="Error (This may be a bug)",
                message="Something's wrong with the fabric of reality here.\n{0}".format(problem)
            )
            traceback.print_tb(i[2])
    return _wrapper

class MapViewerFrame (ttk.Frame):
    def __init__(self, master=None, title=None, image_dir=None, config=None, prog_name=None, about_text=None, help_text=None, verbose=0, **k):
        ttk.Frame.__init__(self, master, **k)
        self.verbose = verbose

        if prog_name is None:
            self.prog_name = sys.argv[0]
        else:
            self.prog_name = prog_name

        if title:
            master.wm_title(title)

        self.about_text = about_text
        self.help_text = help_text
        self.config = config
        self.image_dir = image_dir

        self.canvas = MapCanvas(self, config=config, image_dir=image_dir)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.status_w = ttk.Label(self, text='')
        self.status_w.pack(fill=tk.X, expand=False)

    def _setup_menus(self, menu_list):
        top = self.winfo_toplevel()
        self.menu_bar = tk.Menu(top)

        keymaps = {
            # code       MacOS, [Other]
           'Alt+C':      (KeyBindingDef('Alt+C', '<Option-c>'),
                          KeyBindingDef('Alt+C', '<Alt-c>')),
           'Alt+G':      (KeyBindingDef('Alt+G', '<Option-g>'),
                          KeyBindingDef('Alt+G', '<Alt-g>')),
           'Alt+R':      (KeyBindingDef('Alt+R', '<Option-r>'),
                          KeyBindingDef('Alt+R', '<Alt-r>')),
           'Cmd++':      (KeyBindingDef('Cmd++', '<Command-equal>'),
                          KeyBindingDef('Ctrl++', '<Control-equal>')),
           'Cmd+-':      (KeyBindingDef('Cmd+-', '<Command-minus>'),
                          KeyBindingDef('Ctrl+-', '<Control-minus>')),
           'Cmd+.':      (KeyBindingDef('Cmd+.', '<Command-period>'),
                          KeyBindingDef('Alt+P', '<Alt-p>')),
           'Cmd+0':      (KeyBindingDef('Cmd+0', '<Command-0>'),
                          KeyBindingDef('Ctrl+0', '<Control-0>')),
           'Cmd+L':      (KeyBindingDef('Cmd+L', '<Command-l>'),
                          KeyBindingDef('Ctrl+L', '<Control-l>')),
           'Cmd+O':      (KeyBindingDef('Cmd+O', '<Command-o>'),
                          KeyBindingDef('Ctrl+O', '<Control-o>')),
           'Cmd+R':      (KeyBindingDef('Cmd+R', '<Command-r>'),
                          KeyBindingDef('Ctrl+R', '<Control-r>')),
           'Alt+Cmd+O':  (KeyBindingDef('Alt+Cmd+O', '<Option-Command-o>'),
                          KeyBindingDef('Alt+Ctrl+O', '<Control-Alt-o>')),
           'Ctrl+Q':     (KeyBindingDef('Ctrl+Q', '<Control-q>'),
                          KeyBindingDef('Ctrl+Q', '<Control-q>')),
           'PageDown':   (KeyBindingDef('PageDown', '<Next>'),
                          KeyBindingDef('PgDn', '<Next>')),
           'PageUp':     (KeyBindingDef('PageUp', '<Prior>'),
                          KeyBindingDef('PgUp', '<Prior>')),
        }

        for menu, item_list in menu_list:
            the_menu = tk.Menu(self.menu_bar)
            for title, accel, cmd, variable in item_list:
                if title:
                    if accel in keymaps:
                        if sys.platform == 'darwin':
                            k = keymaps[accel][0]
                            if variable is not None:
                                the_menu.add_checkbutton(label=title, accelerator=k.label,
                                    command=cmd, variable=variable)
                            else:
                                the_menu.add_command(label=title, accelerator=k.label, command=cmd)
                            self.bind_all(k.keycode, cmd)
                        else:
                            k = keymaps[accel][1]
                            if variable is not None:
                                the_menu.add_checkbutton(label=title, accelerator=k.label,
                                    command=cmd, variable=variable)
                            else:
                                the_menu.add_command(label=title, accelerator=k.label, command=cmd)
                            self.bind_all(k.keycode, cmd)
                    else:
                        if variable is not None:
                            the_menu.add_checkbutton(label=title, command=cmd, variable=variable)
                        else:
                            the_menu.add_command(label=title, command=cmd)
                else:
                    the_menu.add_separator()
            self.menu_bar.add_cascade(label=menu, menu=the_menu)
        top['menu'] = self.menu_bar


    def _not_yet(self, *a):
        tk.messagebox.showerror(title="Not Implemented Yet", message='''You wander into a sudden, unexplained dense fog, where only the vaguest outlines of some future construction are visible in the distance. It is not possible to proceed any farther this direction.
There is a small sign posted here, which simply reads, "This section has not been implemented yet. Please try again with a future version."''')
        
    def set_status_text(self, text=''):
        self.status_w['text'] = text

    def close_window(self, *a):
        self.destroy()
        sys.exit(0)

#    def OnCloseWindow(self, event):
#        self.Close(True)
#
#    def Alert(self, text, title, flags):
#        dlg = wx.MessageDialog(self, text, title, flags)
#        dlg.ShowModal()
#        dlg.Destroy()
#
#    def _not_yet(self):
#        self.Alert("Not yet implemented", "Error", wx.OK | wx.ICON_ERROR)
#
    def help(self, *a): 
        tk.messagebox.showinfo(title="Help", message='''
The documentation for {0} is currently online. Please see https://www.rag.com/tech/tools/{0} for full information about this program.'''.format(self.prog_name))

    def about(self, *a):
        tk.messagebox.showinfo(title="About {}".format(self.prog_name), message='''
Ragnarök Magic Mapper %MAGICMAP_RELEASE%
Written by Steve Willoughby, based on some original ideas by Ron Lunde.
©1993, 2000, 2001, 2002, 2003, 2010, 2012, 2018 Steven L. Willoughby, Aloha, Oregon, USA. All Rights Reserved.

{}'''.format(self.about_text))

class MapPreviewFrame (MapViewerFrame):
    def __init__(self, master=None, recursive=False, expand_globs=False, pattern="*.map", ignore_errors=False, verbose=0, file_list=None, creator_name=None, enforce_creator=False, **k):
        MapViewerFrame.__init__(self, master=master, verbose=verbose, **k)
        self.recursive = recursive
        self.creator_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+r'(\w+)')
        self.expand_globs = expand_globs
        self.file_list = file_list or []
        self.zoom_idx = 0
        self.zoom_factors = (1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0)
        self.pattern = pattern
        self.page_idx = None
        self.ignore_errors = ignore_errors
        self._enforce_creator = tk.IntVar(master=self, value=(1 if enforce_creator else 0))
        self._set_creator = tk.IntVar(master=self, value=(1 if creator_name else 0))
        self._creator_name = tk.StringVar(master=self, value=creator_name or '')
        self.about_text = '''This tool is intended for game implementors (“wizards”) to test out their magic map designs during the development and maintenance of their realms within the MUD. It takes local map and image files and displays them on this map viewer, just as they will be in the production map.

For more information, see https://www.rag.com/tech/tools/viewmap.'''

        self.grids_active = tk.IntVar(value=0)
        self._setup_menus((
            ('File', (
                ('Open Map File(s)...', 'Cmd+O',      self.open_files,   None),
                ('Open Map Folder...',  'Alt+Cmd+O',  self.open_dirs,    None),
                (None,                  None,         None,              None),
                ('Quit '+self.prog_name,'Ctrl+Q',     self.close_window, None),
            )),
            ('Edit', (
                ('Preferences...',      'Cmd+.',      self.edit_preferences, None),
            )),
            ('View', (
                ('Next page',           'PageDown',   self.next_page,   None),
                ('Previous page',       'PageUp',     self.prev_page,   None),
                ('Refresh',             'Cmd+R',      self.refresh,     None),
                (None, None, None, None),
                ('Normal size',         'Cmd+0',      self.zoom_100,    None),
                ('Zoom in',             'Cmd++',      self.zoom_in,     None),
                ('Zoom out',            'Cmd+-',      self.zoom_out,    None),
                (None, None, None, None),
                ('Reload',              'Alt+R',      self.reload,      None),
            )),
            ('Tools', (
                ('Show Grid',           'Alt+G',      self.toggle_grids, self.grids_active),
                ('Location Test',       'Cmd+L',      self.test_location, None),
                ('Manage Creator Options...', 'Alt+C', self.manage_creators, None),
            )),
            ('Help', (
                ('Documentation...',    None,         self.help,        None),
                ('About '+self.prog_name, None,       self.about,       None),
            )),
        ))
        self.reload()

    @GUI_call
    def open_files(self, *a):
        name = tk.filedialog.askopenfilenames(
            defaultextension='.map',
            filetypes=[
                ('Magic Map files', '*.map'),
                ('All files',       '*'),
            ],
            parent=self,
            title="Open Magic Map File(s)...")
        if name:
            self.file_list = name
            self.recursive = False
            self.reload()

    @GUI_call
    def open_dirs(self, *a):
        print("open_dirs({}, {})", self, a)
        dialog = tk.filedialog.Directory(self)
        print("dialog {}".format(dialog))
        name = dialog.show(title="Open Magic Map Directory...")
        print("name {}".format(name))

        if name:
            self.file_list = [name]
            self.recursive = True
            self.reload()

    @GUI_call
    def refresh(self, *a): 
        self.canvas.refresh(graph_paper=self.grids_active.get())

    @GUI_call
    def toggle_grids(self, *a):
        if a:
            self.grids_active.set(not self.grids_active.get())
        self.refresh()

    @GUI_call
    def reload(self, *a): 
        "Read the files the user wants to display into our map collection."

        self.set_status_text("Loading Magic Map...")
        #
        # Get list of map files to preview
        #
        if self.verbose > 1: print("reload(): file_list=", self.file_list, "recursive=", self.recursive)

        if self.expand_globs:
            map_file_list = list(itertools.chain(*[glob(pattern) for pattern in self.file_list]))
        else:
            map_file_list = self.file_list

        if self.verbose > 1: print("reload(): map_file_list=", map_file_list)

        if self.recursive:
            root_list, map_file_list = map_file_list, []
            if self.verbose > 1:
                print("starting recursion with root_list={}, map_file_list={}".format(root_list, map_file_list))
            for root in root_list:
                if self.verbose > 1: print("reload(): recursing:", root)
                for dirpath, dirnames, filenames in os.walk(root):
                    if self.verbose > 1: print("reload(): recursing:", root, "--(", dirpath, dirnames, filenames, ")--")
                    map_file_list.extend([os.path.join(dirpath, f) for f in filenames if fnmatch(f, self.pattern)])
            if self.verbose > 1: print("reload(): map_file_list=", map_file_list)
        #
        # Load and compile them into memory
        #
        self.world_map = MapSource()

        for map_file in map_file_list:
            if self.verbose: print("*** Loading {0} ***".format(map_file))
            self.set_status_text("Loading Magic Map... {0}".format(map_file))
            self.update()

            try:
                if not self._set_creator.get():
                    # determine creator from file pathname
                    creator_m = self.creator_re.search(os.path.splitdrive(map_file)[1])
                    room_creator = creator_m.group(1) if creator_m else None
                    if self.verbose > 1: print("creator is {} based on pathname {}".format(room_creator, map_file))
                else:
                    room_creator = self._creator_name.get() or None
                    if self.verbose > 1: print("creator is {} based on user settings".format(room_creator))

                self.world_map.add_from_file(open(map_file), creator=room_creator, enforce_creator=bool(self._enforce_creator.get()))
            except (MapFileFormatError, DuplicateRoomError) as problem:
                print("ERROR in {0}: {1}".format(map_file, problem))
                if not self.ignore_errors:
                    print("Processing stopped on fatal map error (use --ignore-errors to avoid this).")
                    tk.messagebox.showerror(title="Compilation Error", message='Error in {}:\n{}'.format( map_file, problem))
                    return

        if self.verbose:
            print("\n*** Loaded {0} page{1} ({2} room{3}) from {4} map source file{5}. ***".format(
                len(self.world_map.pages), '' if len(self.world_map.pages)==1 else 's',
                len(self.world_map.room_page), '' if len(self.world_map.room_page)==1 else 's',
                len(map_file_list), '' if len(map_file_list)==1 else 's'
            ))
            print("Map page list:", sorted(self.world_map.pages))

        #
        # Display first page
        #
        if self.world_map.pages:
            self.page_list = sorted(self.world_map.pages)
            self._set_page_idx(0)
            if len(self.world_map.pages) > 10:
                self.set_status_text("Loaded pages {0}, (+{1} more)".format(
                    ', '.join([str(s) for s in sorted(self.world_map.pages)][:10]), len(self.world_map.pages)-10))
            else:
                self.set_status_text("Loaded Page{1} {0}".format(
                    ', '.join([str(s) for s in sorted(self.world_map.pages)]),
                    ('' if len(self.world_map.pages) == 1 else 's')))
        else:
            self.set_status_text("No pages loaded.")
            self.page_list = []

    def _set_page_idx(self, new_idx):
        if 0 <= new_idx < len(self.page_list):
            self.page_idx = new_idx
            page_no = self.page_list[self.page_idx]
            self.canvas.display_page(self.world_map.pages[page_no])
            self.set_status_text("Displaying Page {0}.".format(page_no))

    @GUI_call
    def next_page(self, *a): 
        if self.page_idx is not None:
            self._set_page_idx((self.page_idx + 1) % len(self.page_list))

    @GUI_call
    def prev_page(self, *a): 
        if self.page_idx is not None:
            self._set_page_idx((self.page_idx - 1) % len(self.page_list))

    @GUI_call
    def zoom_100(self, *a): 
        self.zoom_idx = 0
        self.canvas.set_zoom(self.zoom_factors[self.zoom_idx])
        self.refresh()
        self.set_status_text("Zoom set to 100%")

    @GUI_call
    def zoom_in(self, *a):
        self.zoom_idx = min(self.zoom_idx + 1, len(self.zoom_factors)-1)
        self.canvas.set_zoom(self.zoom_factors[self.zoom_idx])
        self.refresh()
        self.set_status_text("Zoom set to {:d}%".format(int(self.zoom_factors[self.zoom_idx]*100)))

    @GUI_call
    def zoom_out(self, *a):
        self.zoom_idx = max(0, self.zoom_idx - 1)
        self.canvas.set_zoom(self.zoom_factors[self.zoom_idx])
        self.refresh()
        self.set_status_text("Zoom set to {:d}%".format(int(self.zoom_factors[self.zoom_idx]*100)))

    @GUI_call
    def edit_preferences(self, *a): self._not_yet()

    @GUI_call
    def test_location(self, *e):
        self.after(1000, self._test_next_location, sorted([room.id for room in self.canvas.page_obj.rooms.values()]))

    def _test_next_location(self, room_id_list):
        if room_id_list:
            self.after(int(self.config.getfloat('preview', 'location_delay')*1000), self._test_next_location, room_id_list[1:])

            self.set_status_text("Showing location {} ({} more).".format(room_id_list[0],
                len(room_id_list)-1))
            self.canvas.set_current_location(room_id_list[0])
        else:
            self.canvas.set_current_location(None)
            self.set_status_text("Done.")

    @GUI_call
    def manage_creators(self, *a):
        "Allow user to set creator settings"

        #  _______________________________________________
        # |  _                                            |
        # | (_) Set all creators to __________________    |
        # | (_) Deduce creator from directory structure   |
        # |  _                                            |
        # | [_] Enforce creator boundaries                |
        # |                              ________   ____  |
        # |                             |_Cancel_| |_OK_| |
        # |_______________________________________________|
        #

        dialog = tk.Toplevel(self)
        dialog.title('Manage Creator Options')
        dialog.transient(self)
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        dialog.resizable(False,False)

        f = ttk.Frame(dialog)
        f.grid(sticky=tk.N+tk.S+tk.E+tk.W)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)

        ttk.Radiobutton(f, text='Set all creators to:', variable=self._set_creator, value=1, command=self._flip_creator).grid(
            column=0, row=0, sticky=tk.W, padx=3, pady=2)
        self._creator_w = ttk.Entry(f, textvariable=self._creator_name)
        self._creator_w.grid(column=1, row=0, sticky=tk.W, padx=3, pady=2)

        ttk.Radiobutton(f, text='Deduce creator from directory structure.', variable=self._set_creator, value=0, command=self._flip_creator).grid(
            column=0, row=1, columnspan=2, sticky=tk.W, padx=3, pady=2)
            
        ttk.Checkbutton(f, text='Enforce creator boundaries', variable=self._enforce_creator).grid(
            column=0, row=2, columnspan=2, sticky=tk.W, padx=3, pady=8)
        ttk.Button(f, text='OK', command=dialog.destroy).grid(
            column=1, row=3, sticky=tk.E, padx=3, pady=10)
        self._flip_creator()

    def _flip_creator(self, *a):
        self._creator_w.state(['!disabled'] if self._set_creator.get() else ['disabled'])
        

#class MapClientFrame (MapViewerFrame):
#    def __init__(self, **k):
#        MapViewerFrame.__init__(self, **k)
#
#        self._setup_menus((
#            ('&File', (
##                ('&Open Map File(s)...\tCtrl+O', 'Open map file(s) to display', self.OnOpenFiles, wx.ID_OPEN),
##                ('Open Map &Folder...', 'Recursively open maps in folder', self.OnOpenDirs, -1),
##                (None, None, None, None),
#                ('E&xit\tCtrl+Q', 'Terminate the program', self.OnCloseWindow, wx.ID_EXIT),
#            )),
#            ('&Edit', (
#                ('&Preferences...', 'Change configuration settings', self.OnEditPreferences, wx.ID_PREFERENCES),
#            )),
#            ('&View', (
#                ('&Next page\tPgDn', 'Display next page (wraps around to start)', self.OnNextPage, wx.ID_FORWARD),
#                ('&Previous page\tPgUp', 'Display previous page (wraps around to end)', self.OnPrevPage, wx.ID_BACKWARD),
#                ('&Refresh', 'Re-display current page image', self.OnRefresh, wx.ID_REFRESH),
#                (None, None, None, None),
#                ('Normal &size\tCtrl+0', 'Change magnification to 100%', self.OnZoom100, wx.ID_ZOOM_100),
#                ('&Zoom in\tCtrl++', 'Increase magnification +10%', self.OnZoomIn, wx.ID_ZOOM_IN),
#                ('Zoom &out\tCtrl+-', 'Decrease magnification -10%', self.OnZoomOut, wx.ID_ZOOM_OUT),
#                (None, None, None, None),
##                ('&Reload\tCtrl+R', 'Reload all map pages from source files', self.OnReload, wx.ID_REFRESH),
##                ('&Location Test', 'Cycle through all locations on this page', self.OnLocationTest, -1),
#            )),
#            ('&Help', (
#                ('&Documentation...', 'Where to get program documentation online', self.OnHelp, wx.ID_HELP),
#                ('&About {0}...'.format(self.prog_name), 'At-a-glance info about {0}'.format(self.prog_name), self.OnAbout, wx.ID_ABOUT),
#            )),
#        ))
#
#        self.world_map = MapManager(config=self.config)
#        #self.OnReload(None)
#
#    def tracking_start(self, player_id):
#        self.world_map.open(player_id)
#
#    def tracking_stop(self):
#        self.world_map.close()
#
#    def tracking_position(self, room_id=None):
#        if room_id is None:
#            print("XXX you are now off the map")
#            return
#
#        print('XXX tracking_position({})'.format(room_id))
#        current_location = self.world_map.move_to(room_id)
#        if current_location is None:
#            print("XXX you are now off the map (not expected: {})".format(room_id))
#        else:
#            print("XXX you are now in room {}, page {}".format(
#                    current_location.id, current_location.page.page))
#
#    def tracking_sync(self, i, total, modtime, checksum, room_id):
#        print("XXX update", i, "of", total, "mod", modtime, "chk", checksum, "id", room_id)
#        self.world_map.load(room_id, modtime, checksum)
#
##    def OnOpenFiles(self, event): 
##        dlg = wx.FileDialog(self, 'Open Map File(s)', 
##            wildcard=('Custom Pattern ({0})|{0}|'.format(self.pattern) if self.pattern != '*.map' else '')+
##                'Magic Map files (*.map)|*.map|All Files (*.*)|*.*', 
##            style=wx.OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
##        if dlg.ShowModal() == wx.ID_OK:
##            self.file_list = dlg.GetPaths()
##            self.recursive = False
##            self.OnReload(None)
##        dlg.Destroy()
##
##    def OnOpenDirs(self, event):
##        dlg = wx.DirDialog(self, 'Open Maps ({0}) in Folder and all Subfolders'.format(self.pattern),
##               style=wx.DD_CHANGE_DIR | wx.DD_DEFAULT_STYLE) 
##        if dlg.ShowModal() == wx.ID_OK:
##            self.file_list = [dlg.GetPath()]
##            self.recursive = True
##            self.OnReload(None)
##        dlg.Destroy()
#
#    def OnRefresh(self, event):
#        self.canvas.Refresh()
#
##    def OnReload(self, event): 
##        "Read the files the user wants to display into our map collection."
##        self.SetStatusText("Loading Magic Map...")
#        #
#        # Get list of map files to preview
#        #
##        if self.verbose > 1: print "OnReload(): file_list=", self.file_list, "recursive=", self.recursive
##
##        if self.expand_globs:
##            map_file_list = list(itertools.chain(*[glob(pattern) for pattern in self.file_list]))
##        else:
##            map_file_list = self.file_list
##
##        if self.verbose > 1: print "OnReload(): map_file_list=", map_file_list
##
##        if self.recursive:
##            root_list, map_file_list = map_file_list, []
##            for root in root_list:
##                if self.verbose > 1: print "OnReload(): recursing:", root
##                for dirpath, dirnames, filenames in os.walk(root):
##                    if self.verbose > 1: print "OnReload(): recursing:", root, "--(", dirpath, dirnames, filenames, ")--"
##                    map_file_list.extend([os.path.join(dirpath, f) for f in filenames if fnmatch(f, self.pattern)])
##            if self.verbose > 1: print "OnReload(): map_file_list=", map_file_list
##        #
#        # Load and compile them into memory
#        #
##        self.world_map = MapSource()
##
##        for map_file in map_file_list:
##            if self.verbose: print "*** Loading {0} ***".format(map_file)
##
##            try:
##                self.world_map.add_from_file(open(map_file))
##            except (MapFileFormatError, DuplicateRoomError) as problem:
##                print "ERROR in {0}: {1}".format(map_file, problem)
##                if not self.ignore_errors:
##                    print "Processing stopped on fatal map error (use --ignore-errors to avoid this)."
##                    raise
##
##        if self.verbose:
##            print "\n*** Loaded {0} page{1} ({2} room{3}) from {4} map source file{5}. ***".format(
##                len(self.world_map.pages), '' if len(self.world_map.pages)==1 else 's',
##                len(self.world_map.room_page), '' if len(self.world_map.room_page)==1 else 's',
##                len(map_file_list), '' if len(map_file_list)==1 else 's'
##            )
##            print "Map page list:", sorted(self.world_map.pages)
##
##        self.SetStatusText("")
#        #
#        # Display first page
#        #
##        if self.world_map.pages:
##            self.page_list = sorted(self.world_map.pages)
##            self._set_page_idx(0)
#
#    def _set_page_idx(self, new_idx):
#        if 0 <= new_idx < len(self.page_list):
#            self.page_idx = new_idx
#            page_no = self.page_list[self.page_idx]
#            self.canvas.display_page(self.world_map.pages[page_no])
#            self.SetStatusText("Displaying Page {0}.".format(page_no))
#
#    def OnNextPage(self, event): self._set_page_idx((self.page_idx + 1) % len(self.page_list))
#    def OnPrevPage(self, event): self._set_page_idx((self.page_idx - 1) % len(self.page_list))
#
##    def OnLocationTest(self, event): 
##        wx.FutureCall(1, self.NextLocationTest, sorted([room.id for room in self.canvas.page_obj.rooms.values()]))
##
##    def NextLocationTest(self, room_id_list):
##        if len(room_id_list) > 0:
##            wx.FutureCall(self.config.getfloat('preview', 'location_delay')*1000.0, self.NextLocationTest, room_id_list[1:])
##            self.SetStatusText("Showing location {0} ({1} more).".format(room_id_list[0], len(room_id_list)-1))
##            self.canvas.SetCurrentLocation(room_id_list[0])
##        else:
##            self.canvas.SetCurrentLocation(None)
###            self.SetStatusText("Done.")
