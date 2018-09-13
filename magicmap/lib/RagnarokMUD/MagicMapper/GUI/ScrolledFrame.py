# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: GUI: Scrolled Frame class
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

import tkinter as tk
from tkinter import ttk

class ScrolledCanvas (ttk.Frame):
    '''Creates a frame with a canvas and horizontal and vertical scrollbars attached.
    The canvas widget inside the frame is referenced by the object's canvas attribute.'''

    def __init__(self, master=None, scrollregion=None, *args, **kwargs):
        ttk.Frame.__init__(self, master, *args, **kwargs)

        self.canvas = tk.Canvas(self, scrollregion=scrollregion)
        self.x_scroll = ttk.Scrollbar(self, command=self.canvas.xview, orient=tk.HORIZONTAL)
        self.y_scroll = ttk.Scrollbar(self, command=self.canvas.yview, orient=tk.VERTICAL)
        self.canvas['xscrollcommand'] = self.x_scroll.set
        self.canvas['yscrollcommand'] = self.y_scroll.set

        self.canvas.grid(column=0, row=0, sticky=tk.N+tk.S+tk.W+tk.E)
        self.x_scroll.grid(column=0, row=1, sticky=tk.W+tk.E)
        self.y_scroll.grid(column=1, row=0, sticky=tk.N+tk.S)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
