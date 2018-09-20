# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: GUI: Common Dialogs
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

import tkinter as tk
from tkinter import ttk
import os.path
import time

splash_images = {}

def display_splash_screen(main_window, image_file_name):
    w = tk.Toplevel(None)
    if image_file_name not in splash_images:
        splash_images[image_file_name] = tk.PhotoImage(file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'images', image_file_name))

    tk.Label(w, image=splash_images[image_file_name]).pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    w.lift()
    main_window.withdraw()
    w.update_idletasks()
    w.overrideredirect(True)
    w.after(3000, (lambda: dismiss_splash_screen(main_window, w)))

def dismiss_splash_screen(main_window, splash_window):
    main_window.deiconify()
    main_window.lift()
    splash_window.destroy()
