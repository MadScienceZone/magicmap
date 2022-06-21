# vi:set ai sm nu ts=4 sw=4 expandtab fileencoding=utf-8:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: GUI: Map Canvas
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
import re
import traceback

import tkinter as tk
from   tkinter import font
from   tkinter import ttk
import math
import itertools
import RagnarokMUD.MagicMapper.MapPage
from   RagnarokMUD.MagicMapper.GUI.ScrolledCanvas import ScrolledCanvas
from   RagnarokMUD.MagicMapper.BasicUnits         import Point, Color, GreyLevel, FontSelection, DashPattern
from   RagnarokMUD.MagicMapper.Bezier             import make_bezier

class MapDataFormatError (Exception):
    "Problem with internal data representation of the map locations."

class InvalidDrawingElement (MapDataFormatError):
    "The specification of a map-drawing object was incorrect."

class InvalidRoomFlag (InvalidDrawingElement):
    "The flags for a room are wrong"

class MapDataProcessingError (Exception):
    "Problem encountered trying to handle a location."

class FontDetail:
    def __init__(self, family, size, weight, slant, zoom):
        self.family = family
        self.size = size
        self.weight = weight
        self.slant = slant
        self.object = None
        self.zoom = zoom
        if size:
            self.setfont(size, zoom)

    def setfont(self, size, zoom):
        self.size = size
        self.zoom = zoom
        self.object = font.Font(family=self.family, size=-(int(self.size * self.zoom)), weight=self.weight, slant=self.slant)

    def copy(self):
        return FontDetail(self.family, self.size, self.weight, self.slant, self.zoom)

class MapCanvas (ScrolledCanvas):
    # scroll region for 1000 units * max zoom 300%
    def __init__(self, master, scrollregion=(0, 0, 3000, 3000), page_obj=None, config=None, image_dir=None, *args, **kwargs):
        ScrolledCanvas.__init__(self, master, scrollregion=scrollregion, *args, **kwargs)

        self.graph_paper_mode = False
        self._shade_pattern = re.compile(r'\$(\d\d)')
        self._color_pattern = re.compile(r'\#([0-9a-fA-F]{6})')
        self._xcolor_pattern = re.compile(r'\*([0-9a-fA-F]{6})')
        self._exit_pattern = re.compile(r'[MDgpTCSt]')
        self._gap_pattern = re.compile(r'[MgpT]')
        self.config = config
        self.zoom_factor = 1.0
        self.image_dir = image_dir
        self.canvas_left_margin = self.config.getfloat('rendering', 'canvas_left_margin')
        self.canvas_top_margin = self.config.getfloat('rendering', 'canvas_top_margin')
        self.font_magnification = self.config.getfloat('rendering', 'font_magnification')
        self.page_number_font = self.config.get('rendering', 'page_number_font')
        self.page_number_size = self.config.getint('rendering', 'page_number_size')
        self.page_number_location = Point(self.config.getint('rendering', 'page_number_x'),
                                          self.config.getint('rendering', 'page_number_y'))
        self.page_title_font = self.config.get('rendering', 'page_title_font')
        self.page_title_size = self.config.getint('rendering', 'page_title_size')
        self.page_title_location = Point(self.config.getint('rendering', 'page_title_x'),
                                         self.config.getint('rendering', 'page_title_y'))
        self.page_title2_location = Point(self.config.getint('rendering', 'page_title2_x'),
                                          self.config.getint('rendering', 'page_title2_y'))
        self.font_code_translation = {}
        for code, key in (
            ('b', 'bold'),
            ('i', 'italic'),     
            ('f', 'serif'),    
            ('o', 'slanted'),  
            ('r', 'roman'),
            ('s', 'sans'),
            ('t', 'text'),
            ('T', 'typewriter'),
        ):
            for field in 'family', 'weight', 'slant':
                if not self.config.has_option('fonts', key+"_"+field):
                    raise MapDataFormatError('Missing preferences setting for {}_{} in [fonts] section'.format(key, field))

            if self.config.has_option('fonts', key+"_size"):
                size = self.config.getint('fonts', key+"_size");
            else:
                size = None
            self.font_code_translation[code] = FontDetail(self.config.get('fonts', key+"_family"), 
                  size, self.config.get('fonts', key+"_weight"), self.config.get('fonts', key+"_slant"), self.zoom_factor)

        N = self.config.getint('rendering', 'bezier_points')
        self.Bezier_range = [i/(N-1.0) for i in range(N)]
        self.spline_points = self.config.getint('rendering', 'spline_points')
        self.image_cache = {}
        self.font_cache = {}
        self.logo_image = self._image_tk_id(file=self.config.get('rendering', 'logo_image'))
        self.bg_image = self._image_tk_id(file=self.config.get('rendering', 'background_tile'))
        self.bg_w = self.bg_image.width()
        self.bg_h = self.bg_image.height()
        self.canvas_w = scrollregion[2]
        self.canvas_h = scrollregion[3]
        self._reset_defaults()

        self.page_obj = page_obj
        self.current_location = None
        self.drawing_element_dispatch_table = {
            #cmd: drawing method,            args, include flags?
            'A': (self.draw_map_area_fill,      7, False),
            'B': (self.draw_map_box,            4, False),
            'C': (self._set_map_color,          3, False),
            'D': (self._set_map_dash_pattern,   2, False),
            'F': (self._set_map_font,           1, True),
            'G': (self.draw_map_bitmap,         5, False),
            'J': (self._fit_map_text,           5, True),
            'L': (self._set_line_width,         1, False),
            'M': (self.draw_map_maze_corridors, 1, True),
            'N': (self.draw_map_number_box,     3, False),
            'O': (self.draw_map_dot_mark,       3, True),
            'P': (self.draw_map_polygon,        1, True),
            'Q': (self.draw_map_arc,            1, True),
            'R': (self.draw_map_room,           7, True),
            'S': (self._draw_map_text,          3, False),
            'T': (self.draw_map_tree,           2, True),
            'V': (self._draw_map_vector,        4, False),
            'X': (self._set_translation,        2, False),
            'Z': (self._set_scale_factor,       2, False),
        }
        
        # enable drag-around with the mouse:
        self.canvas.bind("<ButtonPress-1>", lambda event: 
                         event.widget.scan_mark(event.x, event.y))
        self.canvas.bind("<B1-Motion>", lambda event: 
                         event.widget.scan_dragto(event.x, event.y, gain=1))

        self.refresh()

    def set_zoom(self, z):
        self.zoom_factor = z

    def _reset_defaults(self):
        self.landscape = False
        self.set_map_color(GreyLevel(0))
        self.set_map_font(FontSelection('t',8))
        self.set_translation(Point(0,0))
        self.set_scale_factor(Point(1,1))
        self.set_line_width(1)
        self.set_map_dash_pattern(DashPattern([],0))

    def display_page(self, new_page_obj):
        "Switch to displaying a new page object."
        if new_page_obj != self.page_obj:
            self.page_obj = new_page_obj
            self.refresh()

    def _width(self, width):
        return int(width * self.zoom_factor)

    def _dash(self, a):
        # Setting the dash pattern relative to zoom levels using _width 
        #   doesn't work correctly because of rounding; it can mess 
        #   catastrophically with relative lenghts of dashes and spaces. 
        #   (And dash pattern must have integers.)
        # Upd. 10/10 - after some thought and experimentation, going with this,
        #   as it preserves the ratio(s) of dashes and spaces and looks okay
        #   at all zoom levels
        if a is None: return None
        a = [i * (2*int(self.zoom_factor)-1) for i in a]
        # print("Current dash pattern: {}".format(a))
        return a

    def _pos_map2tk(self, point, absolute=False):
        "Convert magic map point to canvas coordinates"

        new_point =  Point(
            point.x * self.current_scale.x + self.current_translation.x + self.canvas_left_margin,
            (610 if self.landscape else 730) - 
                (point.y * self.current_scale.y + self.current_translation.y) 
                + self.canvas_top_margin
        )
        #print(":: _pos_map2tk(({},{}) absolute={} -> ({}*{}+{}+{}={}, {}-({}*{}+{})+{}={})".format(
        #    point.x, point.y, absolute, 
        #    point.x, self.current_scale.x, self.current_translation.x, self.canvas_left_margin,
        #    new_point.x,
        #    (610 if self.landscape else 730),
        #        point.y, self.current_scale.y, self.current_translation.y, self.canvas_top_margin,
        #    new_point.y)
        #)
        new_point.scale(self.zoom_factor)
        return new_point

    def pos_mouse2map(self, point):
        "Convert mouse position to magic map coordinates (without using scale or translate)"
        new_point = Point(self.canvas.canvasx(point.x), self.canvas.canvasy(point.y)) # convert from window to canvas pos
        new_point.scale(1.0 / self.zoom_factor)
        new_point = Point(new_point.x - self.canvas_left_margin, (610 if self.landscape else 730) - (new_point.y - self.canvas_top_margin))
        # print("mouse2map returning {} {}".format(new_point.x, new_point.y))
        return new_point
        
    def draw_graph_paper(self):
        for width, skip in ((1,5), (2,30)):
            for x in range(30, (700 if self.landscape else 580)+1, skip):
                p1 = self._pos_map2tk(Point(x, 30))
                p2 = self._pos_map2tk(Point(x, (580 if self.landscape else 700)))
                self.canvas.create_line(p1.x, p1.y, p2.x, p2.y, fill='#1e90ff', width=width)
            for y in range((580 if self.landscape else 700), 30-1, -skip):
                p1 = self._pos_map2tk(Point(30, y))
                p2 = self._pos_map2tk(Point((700 if self.landscape else 580), y))
                self.canvas.create_line(p1.x, p1.y, p2.x, p2.y, fill='#1e90ff', width=width)

        self.set_map_font(FontSelection('t',8))
        for x in range(30, (700 if self.landscape else 580)+1, 30):
            self.draw_map_text(Point(x, (580 if self.landscape else 700)+8), str(x), center_on_xy=True)
        for y in range(30, (580 if self.landscape else 700)+1, 30):
            self.draw_map_text(Point(22, y), str(y), center_on_xy=True)

    def draw_map_area_fill(self, x, y, w, h, r, g, b):
        "[A,x,y,w,h,r,g,b] -> rectangular area at (x,y) by (w,h) filled in specified color"
        point1 = self._pos_map2tk(Point(x, y))
        point2 = self._pos_map2tk(Point(x+w, y+h))
        self.canvas.create_rectangle(point1.x, point1.y, point2.x, point2.y, 
            tags=[], fill=Color(r, g, b).rgb, width=0)
        self.set_map_color(GreyLevel(0))

    def draw_map_box(self, x, y, w, h):
        "[B, x, y, w, h] -> unfilled rectangle at (x,y) by (w,h) in current color, current line width"
        point1 = self._pos_map2tk(Point(x, y))
        point2 = self._pos_map2tk(Point(x+w, y+h))
        if self.current_dash_pattern is not None:
            self.canvas.create_rectangle(point1.x, point1.y, point2.x, point2.y, 
                tags=[], outline=self.current_color.rgb, width=self._width(self.current_line_width),
                dash=self._dash(self.current_dash_pattern.pattern), dashoffset=self._width(self.current_dash_pattern.offset))
        else:
            self.canvas.create_rectangle(point1.x, point1.y, point2.x, point2.y, 
                tags=[], outline=self.current_color.rgb, width=self._width(self.current_line_width))
            
    def draw_map_bitmap(self, x, y, w, h, image_id):
        "[G, x, y, w, h, id] -> draw image at (x,y) scaled to (w,h)"
        point1=self._pos_map2tk(Point(x,y))
        self.canvas.create_image(point1.x, point1.y, anchor=tk.SW, image=self._image_tk_id(image_id))

    def _color_from_flags(self, flags):
        '''Set internal colors based on flags. The following are recognized. Additional flags
        may be present and are ignored:

        d       standard coloring for dark rooms
        o       standard coloring for outdoor rooms
        p       standard coloring for prototype rooms
        $nn     fill with grayscale level nn (00-99) as a percentage (00=black, 99=almost white)
        #rrggbb fill with RGB color where rr,gg,bb are 00-ff hex values
        *rrggbb extra color (e.g., exits, room text)
        @       change standard colors for current player location

        returns tuple (line color, line width, fill color, dash pattern, door_color, xcolor).
        Individual elements of that tuple are taken from room standard colors if not overridden
        by these flags.
        '''

        #
        # default indoor lit room: black thin lines, white fill
        #
        dash_pattern = None
        x_color = None

        line_width = 2 if 'o' in flags else 1
        if '@' in flags:
            line_color = Color(.5,.5,0) if 'o' in flags else Color(1,0,0)
            door_color = fill_color = Color(.7,.7,0) if 'd' in flags else Color(1,1,0)
        else:
            line_color = GreyLevel(.5) if 'o' in flags else GreyLevel(0)
            fill_color = GreyLevel(.7) if 'd' in flags else GreyLevel(1)      
            door_color = GreyLevel(1)

        shade = self._shade_pattern.search(flags)
        color = self._color_pattern.search(flags)
        xcolor = self._xcolor_pattern.search(flags)

        if shade:
            fill_color = GreyLevel(int(shade.group(1)) / 100.0)
        if color:
            fill_color = Color(int(color.group(1)[0:2], 16) / 255.0,
                               int(color.group(1)[2:4], 16) / 255.0,
                               int(color.group(1)[4:6], 16) / 255.0)
        if xcolor:
            x_color = Color(int(xcolor.group(1)[0:2], 16) / 255.0,
                            int(xcolor.group(1)[2:4], 16) / 255.0,
                            int(xcolor.group(1)[4:6], 16) / 255.0)

        if 'p' in flags:
            dash_pattern = DashPattern([4,3], 0)
            
        return (line_color, line_width, fill_color, dash_pattern, door_color, x_color)

    def _normalize_point_list(self, coord_list):
        if not coord_list or not isinstance(coord_list, list) or len(coord_list) % 2 != 0:
            raise MapDataFormatError('Coordinate list must have an even number of elements')

        points = []
        for x,y in zip(coord_list[0::2], coord_list[1::2]):
            p = self._pos_map2tk(Point(x,y))
            points.append(p.x)
            points.append(p.y)

        return points

    def draw_map_maze_corridors(self, flags, coord_list):
        "[Mflags, [x0, y0, x1, y1, ..., xn, yn]] -> draw a maze of twisty passages"
        line_color, line_width, fill_color, dash_pattern, door_color, x_color = self._color_from_flags(flags)
        points = self._normalize_point_list(coord_list)

        if 'a' in flags:
            self.canvas.create_polygon(*points, fill=fill_color.rgb, smooth=1 if 'c' in flags else 0,
                splinesteps=self.spline_points, width=0)
        if 'w' in flags:
            if dash_pattern is None:
                self.canvas.create_line(*points, fill=line_color.rgb, width=self._width(line_width),
                    smooth=1 if 'c' in flags else 0, splinesteps=self.spline_points)
            else:
                self.canvas.create_line(*points, dash=self._dash(dash_pattern.pattern), 
                    dashoffset=self._width(dash_pattern.offset), fill=line_color.rgb, width=self._width(line_width),
                    smooth=1 if 'c' in flags else 0, splinesteps=self.spline_points)

    def draw_map_number_box(self, x, y, text):
        "[N, x, y, text] -> draw text in an unfilled 20x20 box at (x,y) in the current color and font"
        self.draw_map_box(x, y, 20, 20)
        self.draw_map_text(Point(x+10, y+10), text, center_on_xy=True)

    def _draw_tk_dot(self, center, radius, color):
        # coordinates already in Tk units and positions
        self.canvas.create_oval(center.x-radius, center.y-radius, center.x+radius, center.y+radius,
            fill=color.rgb, width=0)

    def draw_map_dot_mark(self, flags, x, y, radius):
        "[O, x, y, radius] -> draw possibly-filled dot centered at (x,y) in current color"
        p1 = self._pos_map2tk(Point(x-radius, y+radius))
        p2 = self._pos_map2tk(Point(x+radius, y-radius))
        if self.current_dash_pattern is None:
            self.canvas.create_oval(p1.x, p1.y, p2.x, p2.y, 
                fill=self.current_color.rgb if 'f' in flags else '',
                outline=self.current_color.rgb, width=self._width(self.current_line_width))
        else:
            self.canvas.create_oval(p1.x, p1.y, p2.x, p2.y, 
                dash=self._dash(self.current_dash_pattern.pattern), dashoffset=self._width(self.current_dash_pattern.offset),
                fill=self.current_color.rgb if 'f' in flags else '',
                outline=self.current_color.rgb, width=self._width(self.current_line_width))

    def draw_map_arc(self, flags, vlist):
        "[Qflags, x, y, radius, start, end] -> draw (maybe fill) an arc"
        if len(vlist) != 5:
            raise InvalidDrawingElement('Arc object should specify 5 data elements; {0} given'.format(len(vlist)))
        x, y, r, s, e = vlist
        p1 = self._pos_map2tk(Point(x-r, y+r))
        p2 = self._pos_map2tk(Point(x+r, y-r))
        s = s % 360
        e = e % 360

        opts = {
            'outline': self.current_color.rgb,
            'width': self._width(self.current_line_width),
            'start': s,
            'extent': (e - s) % 360,
            'style': tk.ARC,
        }
        if self.current_dash_pattern is not None:
            opts['dash'] = self._dash(self.current_dash_pattern.pattern)
            opts['dashoffset'] = self._width(self.current_dash_pattern.offset)
        if 'f' in flags:
            opts['fill'] = self.current_color.rgb
            opts['style'] = tk.PIESLICE

        self.canvas.create_arc(p1.x, p1.y, p2.x, p2.y, **opts)

    def draw_map_polygon(self, flags, coord_list):
        "[Pflags, [x0, y0, x1, y1, ..., xn, yn]] -> draw (maybe fill) polygon through points"
        points = self._normalize_point_list(coord_list)

        if 'b' in flags:
            #
            # coord list are set of control points for Bézier curve; convert that to the
            # actual points now
            #
            coord_tuple_list = make_bezier([(x,y) for x,y in zip(coord_list[0::2], coord_list[1::2])])(self.Bezier_range)
            points = self._normalize_point_list([p for p in itertools.chain(*coord_tuple_list)])
        
        opts = {
            'smooth': 0,
            'width': self._width(self.current_line_width),
        }

        if 's' in flags:
            opts['smooth'] = 1
            opts['splinesteps'] = self.spline_points

        if self.current_dash_pattern is not None:
            opts['dash'] = self._dash(self.current_dash_pattern.pattern)
            opts['dashoffset'] = self._width(self.current_dash_pattern.offset)

        if 'f' in flags:
            self.canvas.create_polygon(*points, fill=self.current_color.rgb,
                outline=self.current_color.rgb, **opts)
        elif 'c' in flags:
            self.canvas.create_polygon(*points, fill='', outline=self.current_color.rgb, **opts)
        else:
            self.canvas.create_line(*points, fill=self.current_color.rgb, **opts)

    def draw_map_room(self, flags, x, y, w, h, t1, t2, exits):
        "[Rflags, x, y, w, h, title1, title2, [[dir,len]...]] -> room"
        if w == 'R' or w == 'r':
            return self.draw_map_round_room(flags, x, y, h, t1, t2, exits)

        line_color, line_width, fill_color, dash_pattern, door_color, x_color = self._color_from_flags(flags)
        #
        # Standard rectangular room
        #
        opts = {
            'fill': fill_color.rgb,
            'outline': line_color.rgb,
            'width': self._width(line_width),
        }
        if dash_pattern is not None:
            opts['dash'] = self._dash(dash_pattern.pattern)
            opts['dashoffset'] = self._width(dash_pattern.offset)

        p1 = self._pos_map2tk(Point(x, y+h))
        p2 = self._pos_map2tk(Point(x+w, y))

        if 'x' not in flags:
            self.canvas.create_rectangle(p1.x, p1.y, p2.x, p2.y, **opts)

        if x_color is not None:
            self.set_map_color(x_color)
        else:
            self.set_map_color(GreyLevel(0))

        if 'f' not in flags:
            self.set_map_font(FontSelection('t',8))

        cx = x + w/2
        cy = y + h/2
        # I think text should be allowed in phantom rooms... if you don't
        # want text, you can always put () () -P.
        # if 'x' not in flags: 
        if t2:
            self._fit_map_text('m', x,cy, w, h/2, t1)
            self._fit_map_text('m', x, y, w, h/2, t2)
        else:
            self._fit_map_text('m', x, y, w, h, t1)

        self.set_map_color(GreyLevel(0))
        self._handle_exits(exits, Point(cx, cy), Point(w/2, h/2), Point(w/2, h/2),
            (line_color, line_width, fill_color, dash_pattern, door_color, x_color))

    def _handle_exits(self, exits, center, R, RR, colors, circular=False):
        line_color, line_width, fill_color, dash_pattern, door_color, x_color = colors
        vectors = { #   V                     V2                L              Tilted?
                'n':    (Point(   +0,  +R.y), Point  (+0,+R.y), Point(+0, +1), False),
                's':    (Point(   +0,  -R.y), Point(  +0,-R.y), Point(+0, -1), False),
                'e':    (Point( +R.x,    +0), Point(+R.x,  +0), Point(+1, +0), False),
                'w':    (Point( -R.x,    +0), Point(-R.x,  +0), Point(-1, +0), False),
                'a':    (Point(+RR.x, +RR.y), Point(+R.x,+R.y), Point(+1, +1), True ),
                'b':    (Point(+RR.x, -RR.y), Point(+R.x,-R.y), Point(+1, -1), True ),
                'c':    (Point(-RR.x, +RR.y), Point(-R.x,+R.y), Point(-1, +1), True ),
                'd':    (Point(-RR.x, -RR.y), Point(-R.x,-R.y), Point(-1, -1), True ),
        }

        def extended(start, length, code):
            if 'x' in code:
                max_point = Point(700,580) if self.landscape else Point(580,700)
                min_point = Point(30,30)
                return Point(
                    max(min(start.x + length.x * self.canvas_w, max_point.x), min_point.x),
                    max(min(start.y + length.y * self.canvas_h, max_point.y), min_point.y),
                )
            return start + length

        for direction_code, corridor_length in exits:
            if direction_code[0] not in vectors:
                raise InvalidDrawingElement('Room exit direction code {} is not valid.'.format(direction_code))

            V, V2, U, tilted = vectors[direction_code[0]]
            x_color = self._color_from_flags(direction_code)[5]
            
            # U is our unit vector showing the direction from start_point
            start_point = center + V
            #
            # if there's a door here also, we need to move the corridor
            # back so it's not concealed under the door.
            #
            # Round rooms need all corridors moved a door-width out.
            # Square rooms only need it for n,s,e,w directions.
            #
            #         Rect. Round
            #     U    Adj   Adj
            # N +0,+1 +0,+4 +0,+4
            # S +0,-1 +0,-4 +0,-4
            # E +1,+0 +4,+0 +4,+0
            # W -1,+0 -4,+0 -4,+0
            #NE +1,+1   -  +√8,+√8
            #NW -1,+1   -  -√8,+√8
            #SE +1,-1   -  +√8,-√8
            #SW -1,-1   -  -√8,-√8
            #
            corridor_start_point = start_point.clone()
            if 'D' in direction_code or 'T' in direction_code:
                if not tilted:
                    corridor_start_point += U * Point(4,4) 
                elif circular:
                    corridor_start_point += U * Point(math.sqrt(8),math.sqrt(8))

            if corridor_length > 0:
                # draw line from center+V to the point length*L from there in x and y directions
                L = U.clone()
                L.scale(corridor_length)
                end_point = extended(center + V2, L, direction_code)

                opts = {
                    'width': self._width(1),
                    'fill': '#000000' if x_color is None else x_color.rgb,
                }
                if 'i' in direction_code:           # although, really, this is kind of silly...
                    if 'o' in direction_code:       # an in-only and out-only corridor is kind of 
                        opts['arrow'] = tk.BOTH     # just a corridor :)
                    else:                           
                        opts['arrow'] = tk.FIRST    

                elif 'o' in direction_code:
                    opts['arrow'] = tk.LAST

                if '!' in direction_code:
                    opts['dash'] = self._dash([4,2])
                    opts['dashoffset'] = 0

                p1 = self._pos_map2tk(corridor_start_point)
                p2 = self._pos_map2tk(end_point)

                self.canvas.create_line(p1.x, p1.y, p2.x, p2.y, **opts)

            if x_color is None:
                exit_color = GreyLevel(0)
                portal_color = Color(0,0,1)
            else:
                exit_color = portal_color = x_color

            #
            # Calculate the location of points we'll need to draw the various door
            # effects
            #                       P4      P1_P6_       P3
            #                  P6=Ps___P2___|_____|_____P1_Ps=P6
            #                   P3 | P5   P1a Ps P2      P5| P4
            #                      P1         P5 P2a       P2
            #                  P1  |                       |
            #                   +--|P1a              P1a=P1|--+
            #                 P6|  |Ps=P5    ROOM     P5=Ps|  |P6
            #                   +--|P2=P2a              P2a|--+P2
            #                      |                       |
            #                      |                       P2
            #                      P1     P1a P5         P5|
            #                   P3 |_P5____P1_Ps_P2a___P1__| P4
            #                  P6=Ps   P2   |____|         Ps=P6
            #                       P4        P6 P2      P3
            #
                
            if self._exit_pattern.search(direction_code):
                Ps = self._pos_map2tk(start_point)
                if tilted:
                    # 45 degree angled doors for diagonal exits
                    s2 = math.sqrt(2)
                    s8 = math.sqrt(8)
                    s32= math.sqrt(32)
                    _p1 = Point(start_point.x - (s32 if U.x>0 else 0), start_point.y - (U.y*s32 if U.x<0 else 0))
                    _p2 = Point(start_point.x + (s32 if U.x<0 else 0), start_point.y - (U.y*s32 if U.x>0 else 0))
                    _p3 = _p1 + U*Point(s8,s8)
                    _p4 = _p2 + U*Point(s8,s8)
                    if circular:
                        _p1 = _p3
                        _p2 = _p4
                        _p3 = _p1 + U*Point(s8,s8)
                        _p4 = _p2 + U*Point(s8,s8)
                    P1 = self._pos_map2tk(_p1)
                    P2 = self._pos_map2tk(_p2)
                    P3 = self._pos_map2tk(_p3)
                    P4 = self._pos_map2tk(_p4)
                    P5 = self._pos_map2tk(corridor_start_point - U*Point(s8,s8))
                    P6 = self._pos_map2tk(corridor_start_point)
                    P1a= P1
                    P2a= P2
                else: 
                    P1 = self._pos_map2tk(Point(start_point.x - (0 if U.x>0 else 4), start_point.y + (0 if U.y<0 else 4)))
                    P2 = self._pos_map2tk(Point(start_point.x + (0 if U.x<0 else 4), start_point.y - (0 if U.y>0 else 4)))
                    P1a= self._pos_map2tk(Point(start_point.x - (0 if U.x!=0 else 4), start_point.y + (0 if U.y!=0 else 4)))
                    P2a= self._pos_map2tk(Point(start_point.x + (0 if U.x!=0 else 4), start_point.y - (0 if U.y!=0 else 4)))
                    P5 = Ps
                    P6 = self._pos_map2tk(corridor_start_point)
                #
                # gap doorways and magical portals
                #
                if self._gap_pattern.search(direction_code):
                    if tilted:
                        # gap
                        self.canvas.create_polygon(P1.x, P1.y, P2.x, P2.y, Ps.x, Ps.y,
                            fill=fill_color.rgb, outline=fill_color.rgb, width=self._width(line_width))
                        # portal
                        if 'M' in direction_code:
                            if tilted and not circular:
                                if 'D' in direction_code:
                                    self.canvas.create_line(P1.x, P1.y, P2.x, P2.y,
                                        fill=portal_color.rgb, width=self._width(4))
                                else:
                                    self.canvas.create_polygon(P1.x, P1.y, P2.x, P2.y, P4.x, P4.y, P3.x, P3.y,
                                        fill=portal_color.rgb, width=0)
                            else:
                                self.canvas.create_line(P1.x, P1.y, P2.x, P2.y,
                                    fill=portal_color.rgb, width=self._width(4))
                    else:
                        # gap
                        self.canvas.create_line(P1a.x, P1a.y, P2a.x, P2a.y,
                            fill=fill_color.rgb, width=self._width(line_width))
                        # portal
                        if 'M' in direction_code:
                            self.canvas.create_line(P1a.x, P1a.y, P2a.x, P2a.y,
                                fill=portal_color.rgb, width=self._width(4))
                    #
                    # portcullis
                    #
                    if 'p' in direction_code:
                        self._draw_tk_dot(P1a, self._width(1.9), exit_color)
                        self._draw_tk_dot(Ps,  self._width(1.9), exit_color)
                        self._draw_tk_dot(P2a, self._width(1.9), exit_color)
                    #
                    # turnstile
                    #
                    if 'T' in direction_code:
                        r = self._width(3)
                        s3_2 = math.sqrt(3)/2
                        p = P5 if tilted and not circular else Ps
                        self.canvas.create_line(p.x-r, p.y, p.x+r, p.y, 
                            fill=exit_color.rgb, width=self._width(1))
                        self.canvas.create_line(p.x-0.5*r, p.y-s3_2*r, p.x+0.5*r, p.y+s3_2*r,
                            fill=exit_color.rgb, width=self._width(1))
                        self.canvas.create_line(p.x+0.5*r, p.y-s3_2*r, p.x-0.5*r, p.y+s3_2*r,
                            fill=exit_color.rgb, width=self._width(1))
                #
                # secret doors
                #
                elif 'S' in direction_code:
                    self.canvas.create_text(Ps.x, Ps.y, anchor=tk.CENTER, fill=exit_color.rgb,
                        font=self.font_cache[self.load_font(FontSelection('s', 10))], text="S")
                #
                # concealed doors
                #
                elif 'C' in direction_code:
                    self.canvas.create_text(Ps.x, Ps.y, anchor=tk.CENTER, fill=exit_color.rgb,
                        font=self.font_cache[self.load_font(FontSelection('s', 10))], text="C")
                #
                # normal doors
                #
                elif 'D' in direction_code:
                    if tilted:
                        self.canvas.create_polygon(P1.x, P1.y, P2.x, P2.y, P4.x, P4.y, P3.x, P3.y,
                            fill=door_color.rgb, outline=exit_color.rgb, width=self._width(1))
                    else:
                        self.canvas.create_rectangle(P1.x, P1.y, P2.x, P2.y,
                            fill=door_color.rgb, outline=exit_color.rgb, width=self._width(1))
                    if '2' in direction_code:
                        self.canvas.create_line(P5.x, P5.y, P6.x, P6.y,
                            fill=exit_color.rgb, width=self._width(1))
                #
                # locked exits
                #
                if 'L' in direction_code:
                    if tilted:
                        self.canvas.create_line(P1.x, P1.y, P4.x, P4.y, width=self._width(1), fill=exit_color.rgb)
                        self.canvas.create_line(P2.x, P2.y, P3.x, P3.y, width=self._width(1), fill=exit_color.rgb)
                    else:
                        self.canvas.create_line(P1.x, P1.y, P2.x, P2.y, width=self._width(1), fill=exit_color.rgb)
                        self.canvas.create_line(P1.x, P2.y, P2.x, P1.y, width=self._width(1), fill=exit_color.rgb)

    def draw_map_round_room(self, flags, x, y, radius, t1, t2, exits):
        line_color, line_width, fill_color, dash_pattern, door_color, x_color = self._color_from_flags(flags)

        p1 = self._pos_map2tk(Point(x-radius, y+radius))
        p2 = self._pos_map2tk(Point(x+radius, y-radius))
        cp = self._pos_map2tk(Point(x,y))

        opts = {
            'fill': fill_color.rgb,
            'outline': line_color.rgb,
            'width': self._width(line_width),
        }
        if dash_pattern is not None:
            opts['dash'] = self._dash(dash_pattern.pattern)
            opts['dashoffset'] = self._width(dash_pattern.offset)

        if 'x' not in flags:
            self.canvas.create_oval(p1.x, p1.y, p2.x, p2.y, **opts)

        #
        # titles
        #
        if x_color is None:
            self.set_map_color(GreyLevel(0))
        else:
            self.set_map_color(x_color.rgb)

        if 'f' not in flags:
            self.set_map_font(FontSelection('t',8))

        if 'x' not in flags:
            if t2:
                self._fit_map_text('s', x-radius, y, radius*2, 0, t1)
                self._fit_map_text('n', x-radius, y, radius*2, 0, t2)
            else:
                self._fit_map_text('m', x-radius, y, radius*2, 0, t1)

        self.set_map_color(GreyLevel(0))
        self._handle_exits(exits, Point(x, y), Point(radius, radius), Point(radius*.7071, radius*.7071), 
            (line_color, line_width, fill_color, dash_pattern, door_color, x_color), True)

    def _fit_map_text(self, flags, x, y, w, h, text):
        self.fit_map_text(flags, Point(x,y), Point(w,h), text)

    def fit_map_text(self, flags, point, size, text):
        "[Jflags, x, y, w, h, text] -> text drawn in bounding box with scaling and alignment"
        #
        # like draw_map_text(), but scales the current font (just for this string)
        # DOWN if necessary so that the entire text fits inside the bounding box described
        # by point and size:
        # 
        # if size.x > 0:   width of text object must be <= size.x.
        # if size.y > 0:   hieght of text object must be <= size.y.
        #
        # having found the right font size, place the text on the canvas in a box
        # anchored inside it based on the flags:
        #
        #
        # (point.x,point.y+size.y)              (point.x+size.x,point.y+size.y)
        #  ___________________________________________________________________
        # |c                                 n                               a|
        # |                                                                   |
        # |                                                                   |
        # |w                                 m                               e|
        # |                                                                   |
        # |d_________________________________s_______________________________b|
        # (point.x,point.y)                            (point.x+size.x,point.y)
        #
        the_font = self.current_font
        adjust=0

        if   'a' in flags: anchor_at=Point(point.x+size.x, point.y+size.y);    anchor=tk.NE
        elif 'b' in flags: anchor_at=Point(point.x+size.x, point.y       );    anchor=tk.SE
        elif 'c' in flags: anchor_at=Point(point.x       , point.y+size.y);    anchor=tk.NW
        elif 'd' in flags: anchor_at=Point(point.x       , point.y       );    anchor=tk.SW
        elif 'e' in flags: anchor_at=Point(point.x+size.x, point.y+size.y/2);  anchor=tk.E
        elif 'm' in flags: anchor_at=Point(point.x+size.x/2, point.y+size.y/2);anchor=tk.CENTER
        elif 'n' in flags: anchor_at=Point(point.x+size.x/2, point.y+size.y);  anchor=tk.N
        elif 's' in flags: anchor_at=Point(point.x+size.x/2, point.y       );  anchor=tk.S
        elif 'w' in flags: anchor_at=Point(point.x       , point.y+size.y/2);  anchor=tk.W
        else:
            # adjust for baseline too
            anchor_at=point
            anchor=tk.SW
            adjust=the_font.metrics('descent')

        p = self._pos_map2tk(anchor_at)
        t_id = self.canvas.create_text(p.x, p.y+adjust, anchor=anchor, fill=self.current_color.rgb,
            font=the_font, text=text)

        font_size = self.current_font_size
        while font_size > 1:
            bbox = self.canvas.bbox(t_id)
            if not ((size.x > 0 and bbox[2]-bbox[0] > self._width(size.x)) 
                 or (size.y > 0 and bbox[3]-bbox[1] > self._width(size.y))):
                break

            font_size -= 1
            key = self.load_font(FontSelection(self.current_font_code, font_size))
            the_font = self.font_cache[key]
            self.canvas.itemconfigure(t_id, font=the_font)
            if adjust > 0:
                adjust = the_font.metrics('descent')
                self.canvas.coords(t_id, p.x, p.y+adjust)
        else:
            print("** Warning: fittext: can't scale font small enough to fit text of dimensions ({0[0]},{0[1]})-({0[2]},{0[3]}) inside width {1.x} and height {1.y}".format(bbox, size))

    def _draw_map_text(self, x, y, text, center_on_xy=False):
        self.draw_map_text(Point(x,y), text, center_on_xy)

    def draw_map_text(self, point, text, center_on_xy=False):
        "[S, x, y, text] -> text drawn at (x,y) in current font/color"

        point = self._pos_map2tk(point)
        self.canvas.create_text(point.x, point.y+self.current_font.metrics('descent'), 
            anchor=tk.CENTER if center_on_xy else tk.SW,
            fill=self.current_color.rgb, font=self.current_font, text=text)

    def draw_map_tree(self, flags, Ox, Oy):
        "[Tflags, x, y] -> tree sort-of-at (x,y)"

        o = Point(Ox, Oy)

        if 'c' in flags:
            if '2' in flags:
                self._tree1(o + Point(-15, -5), rotate=True)
                self._tree1(o + Point( +0,+12), rotate=True)
                self._tree1(o + Point(+14, +2), rotate=True)
            else:
                self._tree1(o + Point( 12, 12))
                self._tree1(o + Point(  0, 12))
                self._tree1(o + Point( 12,  0))
        elif '2' in flags:
            self._tree1(o, rotate=True)
        else:
            self._tree1(o)



    def _tree1(self, o, scale=0.5, rotate=False):
        # port of the old PostScript tree1 macro which draws around (0,0)
        # we'll assume o is the point of reference that these points are all relative to.
        #
        # 20 22 7 350 120 arc      )
        # 12 25 6  40 180 arc      )
        #  6 19 4  60 210 arc      )  fill these shapes in green
        # 12 12 8 150 270 arc      )  then stroke in black as outline
        # 16  6 3 180  10 arc      )
        # 23 10 5 220  60 arc      )
        # 29 17 4 250  90 arc      )
        # closepath
        #
        # 20 13 3 200 40 arc stroke
        # 15 18 3 60 240 arc stroke
        #
        # tree2 draws tree1 rotated 90 degrees CCW
        # clump1 draws a tree1 at (12,12), (0,12), and (12,0)
        # clump2 draws a tree2 at (-15,-5), (0,12), and (14,2).
        #
        green = '#228b22'
        black = '#000000'
        polygon = []

        for outline, fill in (
            (green, green),
            (black, ''),
        ):
            for center, radius, start, end, top in (
                (Point(20,22), 7, -10, 120, False),
                (Point(12,25), 6,  40, 187, False),
                (Point( 6,19), 4,  60, 230, False),
                (Point(12,12), 8, 150, 270, False),
                (Point(16, 6), 3,-180,  10, False),
                (Point(23,10), 5,-140,  60, False),
                (Point(29,17), 4,-110, 100, False),
                (Point(20,13), 3,-160,  40, True),
                (Point(15,18), 3,  60, 240, True),
            ):
                if top and fill:
                    continue

                if rotate:
                    center = Point(-center.y, center.x)
                    start += 90
                    end += 90

                center.scale(scale)
                radius *= scale

                polygon.append(o.x + center.x + radius * math.cos(math.radians(start)))
                polygon.append(o.y + center.y + radius * math.sin(math.radians(start)))
                polygon.append(o.x + center.x)
                polygon.append(o.y + center.y)

                p1 = self._pos_map2tk(o + center + Point(-radius,+radius))
                p2 = self._pos_map2tk(o + center + Point(+radius,-radius))
                opts = {
                    'fill': fill,
                    'style': tk.PIESLICE if fill else tk.ARC,
                    'outline': outline,
                    'width': self._width(1),
                }
                self.canvas.create_arc(p1.x, p1.y, p2.x, p2.y, start=start, extent=end-start, **opts)
            if fill:
                self.canvas.create_polygon(*self._normalize_point_list(polygon), width=self._width(3), fill=fill)
                


    def _xxDrawMapTree(self, Ox, Oy, scale=3, alt=False):
        green = '#228b22'
        black = '#000000'
        for center, radius, start, end, outline, fill in (
            (Point(16, 16), 11,  0,   0, green, green),
            (Point(20, 22), 7, -20, 120, black, green),
            (Point(12, 25), 6,  20, 200, black, green),
            (Point( 6, 19), 4,  60, 260, black, green),
            (Point(12, 12), 8, 150, 280, black, green),
            (Point(16,  6), 3,-180,  10, black, green),
            (Point(22, 10), 5,-140,  80, black, green),
            (Point(27, 17), 4,-130, 120, black, green),
            (Point(15, 18), 3,  40, 200, black, ''),
            (Point(20, 13), 3,  60,-120, black, ''),
        ):
            center.scale(scale)
            if alt:
                p1 = self._pos_map2tk(center + Point(Ox-radius*scale-35*scale, Oy+radius*scale))
            else:
                p1 = self._pos_map2tk(center + Point(Ox-radius*scale, Oy+radius*scale))
            # XXX this needs to scale with the graphics state
            self.canvas.create_arc(p1.x, p1.y, p1.x+2*radius*scale, p1.y+2*radius*scale,
                style=tk.PIESLICE, fill=fill, outline=outline, start=start, extent=end-start)
                    
    def _draw_map_vector(self, x1, y1, x2, y2):
        "[V, x1, y1, x2, y2] -> arrow from (x1,y1) to (x2,y2) pointing to (x2,y2) in current color."
        self.draw_map_vector(Point(x1, y1), Point(x2, y2))

    def draw_map_vector(self, p1, p2):
        sp1 = self._pos_map2tk(p1)
        sp2 = self._pos_map2tk(p2)
        if self.current_dash_pattern is None:
            self.canvas.create_line(sp1.x, sp1.y, sp2.x, sp2.y, arrow=tk.LAST, 
                fill=self.current_color.rgb, width=self._width(self.current_line_width))
        else:
            self.canvas.create_line(sp1.x, sp1.y, sp2.x, sp2.y, arrow=tk.LAST, 
                dash=self._dash(self.current_dash_pattern.pattern),
                dashoffset=self._width(self.current_dash_pattern.offset),
                fill=self.current_color.rgb, width=self._width(self.current_line_width))
#
    def _set_map_color(self, r, g, b):  self.set_map_color(Color(r,g,b))
    def _set_map_font(self, f, size):   self.set_map_font(FontSelection(f[0], size))
    def _set_translation(self, dx, dy): self.set_translation(Point(dx, dy))
    def _set_scale_factor(self, x, y):  self.set_scale_factor(Point(x, y))
    def _set_line_width(self, lw):      self.set_line_width(lw)

    def set_map_color(self, new_color): self.current_color = new_color
    def set_map_font(self, new_font):   
        key = self.load_font(new_font)
        self.current_font = self.font_cache[key]
        self.current_font_code = new_font.name
        self.current_font_size = new_font.size

    def load_font(self, new_font):
        #
        # set_map_font(FontSelection(flag, size))
        #
        # font_code_translation[flag] = FontDetail object (size may be None)
        # font_cache[name@size@zoom] = tk.Font object
        #
        key = "{}@{}@{:.2f}".format(new_font.name,new_font.size,self.zoom_factor)
        if key not in self.font_cache:
            if new_font.name not in self.font_code_translation:
                raise MapDataFormatError('Undefined font code {} requested'.format(new_font.name))
            fd = self.font_code_translation[new_font.name]
            if fd.object and fd.size == new_font.size and fd.zoom == self.zoom_factor:
                self.font_cache[key] = fd.object
            else:
                new_desc=fd.copy()
                new_desc.setfont(new_font.size, self.zoom_factor)
                self.font_cache[key] = new_desc.object
        return key

    def set_translation(self, new_dxy): self.current_translation = new_dxy
    def set_scale_factor(self, new_sc): self.current_scale = new_sc
    def set_line_width(self, lw):       self.current_line_width = lw

    def _set_map_dash_pattern(self, pattern, offset):   
        self.set_map_dash_pattern(DashPattern(pattern, offset))

    def set_map_dash_pattern(self, dashpattern):
        "[D, [mark, space, ...], offset] -> current drawing dash pattern changed"
        if dashpattern.pattern:
            if not isinstance(dashpattern.pattern, list) or len(dashpattern.pattern) % 2 != 0:
                raise MapDataFormatError('Dash pattern must be a list with even number of elements')
            self.current_dash_pattern = dashpattern
        else:
            # if the pattern is empty, we set the default pattern (solid line)
            self.current_dash_pattern = None

    def _image_tk_id(self, image_id=None, file=None):
        if image_id is not None:
            key = '@'+image_id
            if key not in self.image_cache:
                # XXX retrieve image
                file = os.path.join(os.path.expanduser(
                    self.image_dir or self.config.get('preview', 'image_dir')), image_id + '.gif')
                self.image_cache[key] = tk.PhotoImage(file=file)
            return self.image_cache[key]

        if file is not None:
            if file not in self.image_cache:
                self.image_cache[file] = tk.PhotoImage(file=file)
            return self.image_cache[file]
        
    def refresh(self, graph_paper=None):
        if graph_paper is not None:
            self.graph_paper_mode = graph_paper
        else:
            graph_paper = self.graph_paper_mode

        self._reset_defaults()
        
        self.canvas.delete('all')

        #
        # tile background image across drawing area
        #
        for x in range(0, self.canvas_w, self.bg_w):
            for y in range(0, self.canvas_h, self.bg_h):
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.bg_image, tags=['#bg', '#sys'])
        #
        # logo
        #
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.logo_image, tags=['#logo', '#sys'])

        if self.page_obj:
            #
            # annotations
            #
            real_zoom = self.zoom_factor
            self.zoom_factor = 1.0
            self.set_map_font(FontSelection(self.page_number_font, self.page_number_size))
            self.set_map_color(GreyLevel(0))
            self.draw_map_text(self.page_number_location, '{{{0}}}'.format(self.page_obj.page))

            self.set_map_font(FontSelection(self.page_title_font, self.page_title_size))
            if self.page_obj.realm is not None:
                self.draw_map_text(self.page_title_location, self.page_obj.realm)
            if self.page_obj.creators:
                self.draw_map_text(self.page_title2_location, '[{}]'.format(', '.join(
                    map(lambda s: s.capitalize(), self.page_obj.creators))))
            else:
                self.draw_map_text(self.page_title2_location, '[Base world map]')
            self.zoom_factor = real_zoom

            self.landscape = self.page_obj.orient == RagnarokMUD.MagicMapper.MapPage.LANDSCAPE
            if graph_paper:
                self.draw_graph_paper()

            page_context = 'Magic Map Page {0}{1}'.format(
                self.page_obj.page,
                ' ('+self.page_obj.realm+')' if self.page_obj.realm else ''
            )
            #
            # Draw page background
            #
            self._render_map_element_list('{0}, Background'.format(page_context), self.page_obj.bg)

            #
            # Draw rooms
            #
            for room in list(self.page_obj.rooms.values()):
                #print(repr(room.map))
                self._render_map_element_list(
                        '{0}, Room {1}{2}'.format(
                            page_context,
                            room.id,
                            ' ('+room.name+')' if room.name else ''
                        ), 
                        room.map,
                        room.id == self.current_location
                )

            #
            # Crosshairs
            #
            if self.current_location is not None:
                if self.current_location in self.page_obj.rooms:
                    this_room = self.page_obj.rooms[self.current_location]
                    if this_room.reference_point is not None:
                        self.cross_hair(self._pos_map2tk(Point(*this_room.reference_point)))
        elif graph_paper:
            self.draw_graph_paper()

    def cross_hair(self, center):
        #print("CROSS HAIR AT {0.x},{0.y}".format(center))
        self.canvas.create_line(0, center.y, self.canvas_w, center.y, fill='#ff0000', width=1, dash='-..')
        self.canvas.create_line(center.x, 0, center.x, self.canvas_h, fill='#ff0000', width=1, dash='-..')

    def _render_map_element_list(self, context, element_list, is_current_location=False):
        if element_list is None:
            return

        for drawing_object in element_list:
            try:
                drawing_code = drawing_object[0][0]
                if drawing_code in self.drawing_element_dispatch_table:
                    drawing_method, args_expected, include_flags = self.drawing_element_dispatch_table[drawing_code]
                    if len(drawing_object) != args_expected+1:
                        raise InvalidDrawingElement(
                                '{0}: Object {1} has {2} element{3} ({4} expected)'.format(
                                    context, drawing_object, 
                                    len(drawing_object), '' if len(drawing_object)==1 else 's',
                                    args_expected+1
                                )
                        )
                    if include_flags:
                        drawing_method(drawing_object[0][1:]+('@' if is_current_location else ''), *drawing_object[1:])
                    else:
                        drawing_method(*drawing_object[1:])
                else:
                    raise InvalidDrawingElement('{0}: Object {1} has unknown type "{2}"'.format(
                                context, drawing_object, drawing_object[0]))
            except MapDataFormatError:
                raise
            except Exception as problem:
                traceback.print_tb(sys.exc_info()[2])
                print("-----")
                raise MapDataProcessingError('{0}: Error processing object {1}: {2}'.format(
                            context, drawing_object, problem))

    def set_current_location(self, room_id):
        self.current_location = room_id
        self.refresh()
