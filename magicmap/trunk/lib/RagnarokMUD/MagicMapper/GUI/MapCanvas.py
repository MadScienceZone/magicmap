# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: GUI: Map Canvas
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
import math
import itertools
import RagnarokMUD.MagicMapper.MapPage
from   RagnarokMUD.MagicMapper.Bezier   import make_bezier

class MapDataFormatError (Exception):
    "Problem with internal data representation of the map locations."

class InvalidDrawingElement (MapDataFormatError):
    "The specification of a map-drawing object was incorrect."

class MapDataProcessingError (Exception):
    "Problem encountered trying to handle a location."

class MapCanvas (wx.Panel):
    FontCodeTranslation = {
            'b':    (wx.FONTFAMILY_SWISS,    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
            'i':    (wx.FONTFAMILY_ROMAN,    wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL),
            'o':    (wx.FONTFAMILY_SWISS,    wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL),
            'r':    (wx.FONTFAMILY_ROMAN,    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
            's':    (wx.FONTFAMILY_SWISS,    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
            't':    (wx.FONTFAMILY_SWISS,    wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
            'T':    (wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
    }

    def __init__(self, parent, page_obj=None, config=None, *a, **k):
        wx.Panel.__init__(self, parent, *a, **k)

        self.config = config
        self.canvas_left_margin = self.config.getfloat('rendering', 'canvas_left_margin')
        self.canvas_top_margin = self.config.getfloat('rendering', 'canvas_top_margin')
        self.font_magnification = self.config.getfloat('rendering', 'font_magnification')
        self.page_number_font = self.config.get('rendering', 'page_number_font')
        self.page_number_size = self.config.getint('rendering', 'page_number_size')
        self.page_number_x = self.config.getint('rendering', 'page_number_x')
        self.page_number_y = self.config.getint('rendering', 'page_number_y')
        self.page_title_font = self.config.get('rendering', 'page_title_font')
        self.page_title_size = self.config.getint('rendering', 'page_title_size')
        self.page_title_x = self.config.getint('rendering', 'page_title_x')
        self.page_title_y = self.config.getint('rendering', 'page_title_y')
        self.page_title2_x = self.config.getint('rendering', 'page_title2_x')
        self.page_title2_y = self.config.getint('rendering', 'page_title2_y')
        N = self.config.getint('rendering', 'bezier_points')
        self.Bezier_range = [i/(N-1.0) for i in range(N)]
        self.image_cache = {}
        self.bg_tile = wx.Bitmap(self.config.get('rendering', 'background_tile'))
        self.logo_image = wx.Bitmap(self.config.get('rendering', 'logo_image'))
        self.bg_w, self.bg_h = self.bg_tile.GetWidth(), self.bg_tile.GetHeight()
        self.page_obj = page_obj
        self.current_location = None
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.DrawingElementDispatchTable = {
            #cmd: drawing method,         args, include flags?
            'A': (self.DrawMapAreaFill,      7, False),
            'B': (self.DrawMapBox,           4, False),
            'C': (self.SetMapColour,         3, False),
            'D': (self.SetMapDashPattern,    2, False),
            'F': (self.SetMapFont,           1, True),
            'G': (self.DrawMapBitmap,        5, False),
            'L': (self.SetMapLineWidth,      1, False),
            'M': (self.DrawMapMazeCorridors, 1, True),
            'N': (self.DrawMapNumberBox,     3, False),
            'O': (self.DrawMapDotMark,       3, True),
            'P': (self.DrawMapPolygon,       1, True),
            'Q': (self.DrawMapArc,           1, True),
            'R': (self.DrawMapRoom,          7, True),
            'S': (self.DrawMapText,          3, False),
            'T': (self.DrawMapTree,          2, True),
            'V': (self.DrawMapVector,        4, False),
        }

    def _pos_map2wx(self, x, y):
        "Convert map (x,y) position (lower-left origin) to wx (upper-lefe) as (x,y) tuple"
        return (x+self.canvas_left_margin, (610 if self.MMap_LandscapePage else 730) - y + self.canvas_top_margin)

    def _colour_map2wx(self, r, g, b):
        "Convert map colour values (0.0-1.0) to wx values (0-255) as RGB tuple"
        return (r * 255, g * 255, b * 255)

    def DrawGraphPaper(self, dc):
        for width, skip in ((1,5), (2,30)):
            dc.SetPen(wx.Pen((30,144,255), width))
            for x in range(30, (700 if self.MMap_LandscapePage else 580)+1, skip):
                dc.DrawLine(x+self.canvas_left_margin, 30+self.canvas_top_margin, 
                        x+self.canvas_left_margin, (580 if self.MMap_LandscapePage else 700)+self.canvas_top_margin)
            for y in range((580 if self.MMap_LandscapePage else 700), 30-1, -skip):
                dc.DrawLine(30+self.canvas_left_margin, y+self.canvas_top_margin, 
                        (700 if self.MMap_LandscapePage else 580)+self.canvas_left_margin, y+self.canvas_top_margin)

        self.SetMapFont(dc, 't',8)
        for x in range(30, (700 if self.MMap_LandscapePage else 580)+1, 30):
            self.DrawMapText(dc, x, (580 if self.MMap_LandscapePage else 700)+8, str(x), center_on_xy=True)
        for y in range(30, (580 if self.MMap_LandscapePage else 700)+1, 30):
            self.DrawMapText(dc, 22, y, str(y), center_on_xy=True)

    def SetCurrentLocation(self, room_id=None):
        "Make the specified room the current location (default or None = no current location)"
        # XXX flip to page?  or is that a higher-level management layer?
        if self.current_location != room_id:
            self.current_location = room_id
            self.Refresh()

    def DrawMapAreaFill(self, dc, x, y, w, h, r, g, b):
        "[A,x,y,w,h,r,g,b] -> rectangular area at (x,y) by (w,h) filled in specified color"
        x, y = self._pos_map2wx(x, y)
        colour = self._colour_map2wx(r, g, b)
        dc.SetPen(wx.Pen(colour))
        dc.SetBrush(wx.Brush(colour))
        dc.DrawPolygon([(x,y), (x+w,y), (x+w,y-h), (x,y-h)])

    def DrawMapBox(self, dc, x, y, w, h):
        "[B, x, y, w, h] -> unfilled rectangle at (x,y) by (w,h) in current color, current line width"
        x, y = self._pos_map2wx(x, y)
        dc.SetPen(self.MMap_CurrentPen)
        dc.DrawLines([(x,y), (x+w,y), (x+w,y-h), (x,y-h), (x,y)])

    def DrawMapBitmap(self, dc, x, y, w, h, image_id):
        "[G, x, y, w, h, id] -> draw image at (x,y) scaled to (w,h)"

        if (image_id,w,h) not in self.image_cache:
            if w == 0 and h == 0:
                self.image_cache[(image_id,w,h)] = wx.BitmapFromImage(wx.Image(os.path.join(self.config.get('rendering', 'XXX_image_test_area'), image_id[0], image_id), wx.BITMAP_TYPE_PNG))
            else:
                self.image_cache[(image_id,w,h)] = wx.BitmapFromImage(wx.Image(os.path.join(self.config.get('rendering', 'XXX_image_test_area'), image_id[0], image_id), wx.BITMAP_TYPE_PNG).Rescale(w, h))
        dc.DrawBitmap(self.image_cache[(image_id,w,h)], x, y, True)

    def _standard_colour(self, flags):
        '''Given set of flags, return appropriate pen and brush:
              FLAG  EFFECT
                @    use color set for current location
                o    use outdoor pen
                d    use dark brush
        '''
        if '@' in flags:
            brush_colour = self.MMap_HereDarkColour if 'd' in flags else self.MMap_HereLightColour
            pen_colour = self.MMap_HereOutdoorColour if 'o' in flags else self.MMap_HereIndoorColour
        else:
            brush_colour = self.MMap_DarkColour if 'd' in flags else self.MMap_LightColour
            pen_colour = self.MMap_OutdoorColour if 'o' in flags else self.MMap_IndoorColour

        pen_width = self.MMap_OutdoorWidth if 'o' in flags else self.MMap_IndoorWidth

        return pen_colour, pen_width, brush_colour

    def DrawMapMazeCorridors(self, dc, flags, coord_list):
        "[Mflags, [x0, y0, x1, y1, ..., xn, yn]] -> draw a maze of twisty passages"
        stdpen, stdwidth, stdbrush = self._standard_colour(flags)
        if 'a' in flags:
            # fill in area specified by coordinates
            fill_colour = self._colour_map2wx(*stdbrush)
            dc.SetPen(wx.Pen(fill_colour))
            dc.SetBrush(wx.Brush(fill_colour))
            dc.DrawPolygon([self._pos_map2wx(x,y) for x,y in zip(*[coord_list[i::2] for i in range(2)])])
        if 'w' in flags:
            # stroke path around area, may not necessarily be closed
            self.SetMapLineWidth(dc, stdwidth)
            self.SetMapColour(dc, *stdpen)
            self.SetMapDashPattern(dc, [4,3] if 'p' in flags else None, 0)
            dc.SetPen(self.MMap_CurrentPen)
            if 'c' in flags:
                dc.DrawSpline([self._pos_map2wx(x,y) for x,y in zip(*[coord_list[i::2] for i in range(2)])])
            else:
                dc.DrawLines([self._pos_map2wx(x,y) for x,y in zip(*[coord_list[i::2] for i in range(2)])])
            self.SetMapLineWidth(dc, 1)
            self.SetMapDashPattern(dc)

    def DrawMapNumberBox(self, dc, x, y, text):
        "[N, x, y, text] -> draw text in an unfilled 20x20 box at (x,y) in the current color and font"
        self.DrawMapBox(dc, x, y, 20, 20)
        self.DrawMapText(dc, x+10, y+10, text, center_on_xy=True)

    def DrawMapDotMark(self, dc, flags, x, y, radius):
        "[O, x, y, radius] -> draw filled dot centered at (x,y) in current color"
        dc.SetPen(self.MMap_CurrentPen)
        dc.SetBrush(self.MMap_CurrentBrush if 'f' in flags else wx.TRANSPARENT_BRUSH)
        x, y = self._pos_map2wx(x, y)
        dc.DrawCircle(x, y, radius)

    def DrawMapArc(self, dc, flags, vlist):
        "[Qflags, x, y, radius, start, end] -> draw (maybe fill) an arc"
        if len(vlist) != 5:
            raise InvalidDrawingElement('Arc object should specify 5 data elements; {0} given'.format(len(vlist)))
        x, y, r, s, e = vlist
        dc.SetPen(self.MMap_CurrentPen)
        dc.SetBrush(self.MMap_CurrentBrush if 'f' in flags else wx.TRANSPARENT_BRUSH)
        x, y = self._pos_map2wx(x, y)
        dc.DrawEllipticArc(x - r, y - r, r*2.0, r*2.0, s, e)

    def DrawMapPolygon(self, dc, flags, coord_list):
        "[Pflags, [x0, y0, x1, y1, ..., xn, yn]] -> draw (maybe fill) polygon through points"
        dc.SetPen(self.MMap_CurrentPen)
        dc.SetBrush(self.MMap_CurrentBrush)

        if 'b' in flags:
            # convert point list to Bezier curve points
            coord_list = (make_bezier([(x,y) for x, y in zip(*[coord_list[i::2] for i in range(2)])]))(self.Bezier_range)
            coord_list = [pt for pt in itertools.chain(*coord_list)]

        if 'f' in flags:
            dc.DrawPolygon([self._pos_map2wx(x,y) for x,y in zip(*[coord_list[i::2] for i in range(2)])])
        elif 's' in flags:
            dc.DrawSpline([self._pos_map2wx(x,y) for x,y in zip(*[coord_list[i::2] for i in range(2)])])
        else:
            #if 'c' in flags:
            #    coord_list.extend(coord_list[0:2])
            dc.DrawLines([self._pos_map2wx(x,y) for x,y in zip(*[coord_list[i::2] for i in range(2)])])

    def DrawMapRoom(self, dc, flags, x, y, w, h, t1, t2, exits):
        "[Rflags, x, y, w, h, title1, title2, [[dir,len]...]] -> room"
        if w == 'R' or w == 'r':
            return self.DrawMapRoundRoom(dc, flags, x, y, h, t1, t2, exits)

        stdpen, stdwidth, stdbrush = self._standard_colour(flags)
        self.SetMapDashPattern(dc)
        self.DrawMapAreaFill(dc, x, y, w, h, *(stdbrush))
        self.SetMapColour(dc, *stdpen)
        self.SetMapLineWidth(dc, stdwidth)
        if 'p' in flags: self.SetMapDashPattern(dc, [4,3], 0)
        self.DrawMapBox(dc, x, y, w, h)
        if 'p' in flags: self.SetMapDashPattern(dc)
        #
        # titles
        #
        self.SetMapColour(dc, 0,0,0)
        self.SetMapFont(dc, 't',8)
        cx = x + w/2.0
        cy = y + h/2.0
        if t2:
            self.DrawMapText(dc, cx, cy + max(4, h/8.0), t1, center_on_xy=True)
            self.DrawMapText(dc, cx, cy - max(4, h/8.0), t2, center_on_xy=True)
        else:
            self.DrawMapText(dc, cx, cy, t1, center_on_xy=True)

        self._handle_exits(dc, exits, cx, cy, w/2.0, h/2.0, w/2.0, h/2.0)

    def _handle_exits(self, dc, exits, Cx, Cy, Rx, Ry, RRx, RRy, use_tilting=False):
        vectors = { 
                'n':    (  +0,  +Ry, +0, +1, False),
                's':    (  +0,  -Ry, +0, -1, False),
                'e':    ( +Rx,   +0, +1, +0, False),
                'w':    ( -Rx,   +0, -1, +0, False),
                'a':    (+RRx, +RRy, +1, +1, True ),
                'b':    (+RRx, -RRy, +1, -1, True ),
                'c':    (-RRx, +RRy, -1, +1, True ),
                'd':    (-RRx, -RRy, -1, -1, True ),
        }

        def extended(x, y, xlen, ylen, code):
            if 'x' in code:
                maxX, maxY = (700,580) if self.MMap_LandscapePage else (580,700)
                minX, minY = (30,30)
                return max(min(x + (xlen*100000), maxX), minX), max(min(y + (ylen*100000), maxY), minY)
            return x+xlen, y+ylen

        for direction_code, corridor_length in exits:
            Vx, Vy, Lx, Ly, tilted = vectors[direction_code[0]]
            if not use_tilting:
                tilted = False
            Xx, Xy = Cx+Vx, Cy+Vy                # exit point in map coords
            XXx, XXy = self._pos_map2wx(Xx, Xy)  # exit point in screen coords
            if corridor_length > 0:
                self.SetMapLineWidth(dc, 1)
                self.SetMapColour(dc, *self.MMap_IndoorColour)
                self.SetMapDashPattern(dc, [4,3] if '!' in direction_code else None, 0)
                endX, endY = extended(Xx, Xy, corridor_length*Lx, corridor_length*Ly, direction_code)
                XendX, XendY = self._pos_map2wx(endX, endY)
                if 'i' in direction_code:
                    self.DrawMapVector(dc, endX, endY, Xx, Xy)
                elif 'o' in direction_code:
                    self.DrawMapVector(dc, Xx, Xy, endX, endY)
                else:
                    dc.SetPen(self.MMap_CurrentPen)
                    dc.DrawLine(XXx, XXy, XendX, XendY)

            if 'D' in direction_code:
                dc.SetPen(wx.BLACK_PEN)
                dc.SetBrush(wx.WHITE_BRUSH)
                if tilted:
                    dc.DrawPolygon([(XXx,XXy-6), (XXx+6,XXy), (XXx,XXy+6), (XXx-6,XXy)])
                else:
                    dc.DrawPolygon([(XXx-4,XXy-4), (XXx-4,XXy+4), (XXx+4,XXy+4), (XXx+4,XXy-4)])
            if 'L' in direction_code:
                dc.SetPen(wx.BLACK_PEN)
                dc.SetBrush(wx.BLACK_BRUSH)
                dc.DrawCircle(XXx, XXy, 2)

    def DrawMapRoundRoom(self, dc, flags, x, y, radius, t1, t2, exits):
        stdpen, stdwidth, stdbrush = self._standard_colour(flags)
        dc.SetPen(wx.Pen(self._colour_map2wx(*stdbrush)))
        dc.SetBrush(wx.Brush(self._colour_map2wx(*stdbrush)))
        xx, yy = self._pos_map2wx(x, y)
        dc.DrawCircle(xx, yy, radius)

        self.SetMapColour(dc, *stdpen)
        self.SetMapLineWidth(dc, stdwidth)
        self.SetMapDashPattern(dc, [4,3] if 'p' in flags else None, None)
        dc.SetPen(self.MMap_CurrentPen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawCircle(xx, yy, radius)
        if 'p' in flags: self.SetMapDashPattern(dc)
        self.SetMapLineWidth(dc, self.MMap_IndoorWidth)
        self.SetMapColour(dc, 0,0,0)
        #
        # titles
        #
        self.SetMapFont(dc, 't',8)
        if t2:
            self.DrawMapText(dc, x, y + max(4, radius/6.0), t1, center_on_xy=True)
            self.DrawMapText(dc, x, y - max(4, radius/6.0), t2, center_on_xy=True)
        else:
            self.DrawMapText(dc, x, y, t1, center_on_xy=True)

        self._handle_exits(dc, exits, x, y, radius, radius, radius*.7071, radius*.7071, True)

    def DrawMapText(self, dc, x, y, text, center_on_xy=False):
        "[S, x, y, text] -> text drawn at (x,y) in current font/color"
        utext = unicode()
        translation_table = {
                '\320': unichr(0x2014),  # em dash ---
                '\261': unichr(0x2013),  # en dash --
                '\242': unichr(0x00a2),  # cent sign
                '\262': unichr(0x2020),  # dagger
                '\263': unichr(0x2021),  # double dagger
                '\252': unichr(0x201c),  # open quotes  ``
                '\272': unichr(0x201d),  # close quotes ''
                '\267': unichr(0x2022),  # bullet
                '\341': unichr(0x01fc),  # AE
                '\361': unichr(0x00e6),  # ae
                '\247': unichr(0x00a7),  # section
                '\266': unichr(0x00b6),  # paragraph
                '\253': unichr(0x00ab),  # <<
                '\273': unichr(0x00bb),  # >>
        }
        for ch in text:
            if ch in translation_table:
                utext += translation_table[ch]
            else:
                utext += ch

        if self.MMap_CurrentFont[0] not in self.FontCodeTranslation:
            raise InvalidDrawingElement('Font code {0} not understood.'.format(self.MMap_CurrentFont[0]))

        dc.SetFont(wx.Font(self.MMap_CurrentFont[1] * self.font_magnification, *self.FontCodeTranslation[self.MMap_CurrentFont[0]]))
        dc.SetTextForeground(self.MMap_CurrentColour)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        xw, xh = dc.GetTextExtent(utext)
        x, y = self._pos_map2wx(x, y)
        if center_on_xy:
            # adjust x,y so that the text ends up being centered on that point
            x -= xw/2
            y -= xh/2
        else:
            # adjust y so it uses the top left corner, not the bottom left.
            y -= xh
        dc.DrawText(utext, x, y)

    def DrawMapTree(self, dc, flags, Ox, Oy):
        "[Tflags, x, y] -> tree sort-of-at (x,y)"

        if 'c' in flags:
            if '2' in flags:
                self._DrawMapTree(dc, Ox-15, Oy-5, scale=.5)
                self._DrawMapTree(dc, Ox, Oy+12, scale=.5)
                self._DrawMapTree(dc, Ox+14, Oy+2, scale=.5)
            else:
                self._DrawMapTree(dc, Ox+12, Oy+12, scale=.5)
                self._DrawMapTree(dc, Ox, Oy+12, scale=.5)
                self._DrawMapTree(dc, Ox+12, Oy, scale=.5)
        elif '2' in flags:
            self._DrawMapTree(dc, Ox, Oy, scale=.5, alt=True)
        else:
            self._DrawMapTree(dc, Ox, Oy, scale=.5)

    def _DrawMapTree(self, dc, Ox, Oy, scale=3, alt=False):
        fill = wx.Brush((34,139,34))
        no_fill = wx.TRANSPARENT_BRUSH
        black = wx.Pen((0,0,0), 1)

        dc.SetBrush(wx.Brush((34,139,34)))
        for x, y, r, a1, a2, pen, brush in (
                (16, 16, 11,  0,   0, wx.TRANSPARENT_PEN, fill),
                (20, 22, 7, -20, 120, black,              fill),
                (12, 25, 6,  20, 200, black,              fill),
                ( 6, 19, 4,  60, 260, black,              fill),
                (12, 12, 8, 150, 280, black,              fill),
                (16,  6, 3,-180,  10, black,              fill),
                (22, 10, 5,-140,  80, black,              fill),
                (27, 17, 4,-130, 120, black,              fill),
                (15, 18, 3,  40, 200, black,           no_fill),
                (20, 13, 3,  60,-120, black,           no_fill)
        ):
            if alt:
                xx, yy = self._pos_map2wx(Ox+(x*scale)-(r*scale)-(35*scale), Oy+(y*scale)+(r*scale))
            else:
                xx, yy = self._pos_map2wx(Ox+(x*scale)-(r*scale), Oy+(y*scale)+(r*scale))
            dc.SetPen(pen)
            dc.DrawEllipticArc(xx, yy, 2*r*scale, 2*r*scale, a1, a2)

    def DrawMapVector(self, dc, x1, y1, x2, y2, L=5, spread=120):
        "[V, x1, y1, x2, y2] -> arrow from (x1,y1) to (x2,y2) pointing to (x2,y2) in current color; L=arrowhead length; spread=degrees from terminal point to fin points"
        #
        # Given a vector from point 1 to 2 (x1,y1)-(x2,y2),
        # we need to draw an arrow head of size L, with fins 
        # pointing back L (so really the total size is 2L),
        # with the arrow tip at point 2 (x2, y2).
        #
        # The easiest way to picture this (to me, anyway) is
        # to have the arrow points 120 degrees around a circle
        # which circumscribes the arrow head.  So we need to
        # determine the center point (C) of that circle.  To do
        # that, we need to know the vector's length (r) and angle
        # from the x axis (theta).
        #
        dy = y2 - y1
        dx = x2 - x1
        r = math.sqrt(dx**2 + dy**2)
        theta = math.atan2(dy, dx)
        Cx = (r-L) * math.cos(theta) + x1
        Cy = (r-L) * math.sin(theta) + y1
        #
        # Now we know the point of arrow is tangent to the circle
        # centered at point C with radius L, at angle theta.  The 
        # other two points of the arrowhead (A and B) are +/-
        # <spread> degrees from there.
        #
        sr = math.radians(spread)

        Ax = L * math.cos(theta + sr) + Cx
        Ay = L * math.sin(theta + sr) + Cy

        Bx = L * math.cos(theta - sr) + Cx
        By = L * math.sin(theta - sr) + Cy
        #
        # Now we have the coordinates of all the bits of the arrow
        # we need, just draw the thing!
        #
        dc.SetPen(self.MMap_CurrentPen)
        dc.SetBrush(self.MMap_CurrentBrush)
        A = self._pos_map2wx(Ax, Ay)
        B = self._pos_map2wx(Bx, By)
        C = self._pos_map2wx(Cx, Cy)
        P1 = self._pos_map2wx(x1, y1)
        P2 = self._pos_map2wx(x2, y2)
        dc.DrawLines([P1, P2])
        dc.DrawPolygon([C, A, P2, B])

    def SetMapColour(self, dc, r, g, b):
        "[C, r, g, b] -> current drawing colour changed"
        self.MMap_CurrentColour = self._colour_map2wx(r, g, b)
        self.MMap_CurrentBrush = wx.Brush(self.MMap_CurrentColour)
        self._update_current_pen()

    def SetMapDashPattern(self, dc, mslist=None, offset=None):
        "[D, [mark, space, ...], offset] -> current drawing dash pattern changed"
        if mslist:
            self.MMap_CurrentDashes = (mslist, offset)
        else:
            self.MMap_CurrentDashes = None
        self._update_current_pen()

    def SetMapLineWidth(self, dc, width):
        "[L, width] -> current line drawing width changed"
        self.MMap_CurrentWidth = width
        self._update_current_pen()

    def _update_current_pen(self):
        if self.MMap_CurrentDashes is None:
            self.MMap_CurrentPen = wx.Pen(self.MMap_CurrentColour, self.MMap_CurrentWidth, wx.SOLID)
        else:
            self.MMap_CurrentPen = wx.Pen(self.MMap_CurrentColour, self.MMap_CurrentWidth, wx.USER_DASH)
            self.MMap_CurrentPen.SetDashes(self.MMap_CurrentDashes[0])
            # XXX not using offset yet

    def SetMapFont(self, dc, font_code, size):
        "[Ffont, size] -> current font changed"
        if '@' in font_code:
            font_code = font_code.replace('@','')  # we don't recognize this flag
        self.MMap_CurrentFont = (font_code, size)

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.SetMapMode(wx.MM_POINTS)
        self.MMap_DarkColour = (.7,.7,.7)
        self.MMap_LightColour = (1,1,1)
        self.MMap_OutdoorColour = (.5,.5,.5)
        self.MMap_IndoorColour  = (0,0,0)
        self.MMap_OutdoorWidth = 2
        self.MMap_IndoorWidth = 1

        self.MMap_HereDarkColour = (.7,.7,.0)
        self.MMap_HereLightColour = (1,1,0)
        self.MMap_HereOutdoorColour = (.5,.5,.0)
        self.MMap_HereIndoorColour  = (1,0,0)

        self.MMap_LandscapePage=False
        self.MMap_CurrentColour = (0,0,0)
        self.MMap_CurrentWidth = 1
        self.MMap_CurrentDashes = None
        #
        # tile image
        #
        fr_w, fr_h = self.GetClientSizeTuple()
        for x in range(0, fr_w, self.bg_w):
            for y in range(0, fr_h, self.bg_h):
                dc.DrawBitmap(self.bg_tile, x, y, True)
        #
        # logo
        #
        dc.DrawBitmap(self.logo_image, 0, 0, True)
        if self.page_obj:
            #
            # annotations
            #
            self.SetMapFont(dc, self.page_number_font, self.page_number_size)
            self.SetMapColour(dc, 0,0,0)
            self.DrawMapText(dc, self.page_number_x, self.page_number_y, '{{{0}}}'.format(self.page_obj.page))
            self.SetMapFont(dc, self.page_title_font, self.page_title_size)
            if self.page_obj.realm is not None:
                self.DrawMapText(dc, self.page_title_x, self.page_title_y, self.page_obj.realm)
            if self.page_obj.creators:
                self.DrawMapText(dc, self.page_title2_x, self.page_title2_y, '[{0}]'.format(', '.join(self.page_obj.creators)))
            else:
                self.DrawMapText(dc, self.page_title2_x, self.page_title2_y, '[Base world map]')
            #page, realm [creators]

            self.MMap_LandscapePage = self.page_obj.orient == RagnarokMUD.MagicMapper.MapPage.LANDSCAPE
            page_context = 'Magic Map Page {0}{1}'.format(
                self.page_obj.page,
                ' ('+self.page_obj.realm+')' if self.page_obj.realm else ''
            )
            self._render_map_element_list(dc, '{0}, Background'.format(page_context), self.page_obj.bg)

            for room in self.page_obj.rooms.values():
                self._render_map_element_list(
                        dc, 
                        '{0}, Room {1}{2}'.format(
                            page_context,
                            room.id,
                            ' ('+room.name+')' if room.name else ''
                        ), 
                        room.map,
                        room.id == self.current_location
                )

            if self.current_location is not None:
                if self.current_location in self.page_obj.rooms:
                    this_room = self.page_obj.rooms[self.current_location]
                    if this_room.reference_point is not None:
                        self.SetMapColour(dc, 1,0,0)
                        self.SetMapLineWidth(dc, 1)
                        self.SetMapDashPattern(dc, [4,3], 0)
                        dc.SetPen(self.MMap_CurrentPen)
                        dc.CrossHair(*self._pos_map2wx(*this_room.reference_point))
                        self.SetMapDashPattern(dc)


    def _render_map_element_list(self, dc, context, element_list, is_current_location=False):
        for drawing_object in element_list:
            try:
                drawing_code = drawing_object[0][0]
                if drawing_code in self.DrawingElementDispatchTable:
                    drawing_method, args_expected, include_flags = self.DrawingElementDispatchTable[drawing_code]
                    if len(drawing_object) != args_expected+1:
                        raise InvalidDrawingElement(
                                '{0}: Object {1} has {2} element{3} ({4} expected)'.format(
                                    context, drawing_object, 
                                    len(drawing_object), '' if len(drawing_object)==1 else 's',
                                    args_expected+1
                                )
                        )
                    if include_flags:
                        drawing_method(dc, drawing_object[0][1:]+('@' if is_current_location else ''), *drawing_object[1:])
                    else:
                        drawing_method(dc, *drawing_object[1:])
                else:
                    raise InvalidDrawingElement('{0}: Object {1} has unknown type "{2}"'.format(
                                context, drawing_object, drawing_object[0]))
            except MapDataFormatError:
                raise
            except Exception as problem:
                raise MapDataProcessingError('{0}: Error processing object {1}: {2}'.format(
                            context, drawing_object, problem))

class TestPanel (MapCanvas):
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.SetMapMode(wx.MM_POINTS)

        self.MMap_DarkColour = (.7,.7,.7)
        self.MMap_LightColour = (1,1,1)
        self.MMap_OutdoorColour = (.5,.5,.5)
        self.MMap_IndoorColour  = (0,0,0)
        self.MMap_OutdoorWidth = 2
        self.MMap_IndoorWidth = 1
        self.MMap_LandscapePage=False
        self.MMap_CurrentColour = (0,0,0)
        self.MMap_CurrentWidth = 1
        self.MMap_CurrentDashes = None

        self.DrawGraphPaper(dc)
        self.SetMapColour(dc, 1,0,0)
        self.SetMapLineWidth(dc, 1)
        self.SetMapDashPattern(dc, [4,3], 0)
        dc.SetPen(self.MMap_CurrentPen)
        dc.CrossHair(500,600)
        self.SetMapDashPattern(dc)

        self.SetMapFont(dc, 't', 8)
        self.SetMapLineWidth(dc, 1)
        self.SetMapColour(dc, 0,0,0)

        self.DrawMapAreaFill(dc, 100.5, 100.5, 50.5, 20.5, 1, 0, 0)
        self.DrawMapAreaFill(dc, 100, 200, 50, 20, 0, 1, 0)
        self.DrawMapAreaFill(dc, 100, 300, 50, 20, 0, 0, 1)
        self.DrawMapAreaFill(dc, 100, 400, 50, 20, .5, .5, 0)
        self.DrawMapBox(dc, 50, 50, 200, 150)
        self.SetMapColour(dc, 1,0,0)
        self.DrawMapBox(dc, 60, 60, 200, 150)
        self.SetMapColour(dc, 0,1,0)
        self.DrawMapBox(dc, 70, 70, 200, 150)
        self.DrawMapMazeCorridors(dc, 'aw', [30, 30, 45, 30, 45, 45, 40, 45, 40, 35, 30, 35])
        self.DrawMapDotMark(dc, 'g', 300, 300, 50)
        self.DrawMapPolygon(dc, 'f', [20, 20, 40, 20, 30, 35])

        self.DrawMapText(dc, 600, 400, 'HELLO')
        self.SetMapFont(dc, 'i',20)
        self.SetMapColour(dc, 0,0,0)
        self.DrawMapText(dc, 400, 400, '\252Hi There\272')

        self.DrawMapRoom(dc, 'dp', 100, 600, 'R', 30, 'FCD', '#2', [['n',20],['s',30],['e',10],['wDL',40]])
        self.DrawMapRoom(dc, 'op', 200, 600, 50, 30, 'FCD', '(Future)', [])
        self.DrawMapNumberBox(dc, 450, 450, 'p12')
        self.SetMapLineWidth(dc, 1)
        self.SetMapDashPattern(dc, [4,3],0)
        #self.DrawMapVector(dc, 300,600, 300,700)
        #self.DrawMapVector(dc, 400,630, 300,630)
        self.DrawMapTree(dc, 'c2', 300,600)
        #self.DrawMapTree(dc, '2', 300,600)

        dc.SetPen(wx.BLACK_PEN)
        dc.SetBrush(wx.Brush('green'))

        self.DrawMapBitmap(dc, 100,200, 0, 0, 'aaaaa.png')

        #try:
            #gc = wx.GraphicsContext.Create(dc)
        #except NotImplementedError:
            #dc.DrawText("Sorry, your wxPython package does not support GraphicsContext classes.  We can't go on from here.", 25, 25)
            #return

        #font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        #font.SetWeight(wx.BOLD)
        #gc.SetFont(font)
#
        #path = gc.CreatePath()
        #path.AddCircle(0,0,BASE2)
        #path.MoveToPoint(0,-BASE2)
        #path.AddLineToPoint(0,BASE2)
        #path.MoveToPoint(-BASE2,0)
        #path.AddLineToPoint(BASE2,0)
        #path.CloseSubpath()
        #path.AddRectangle(-BASE4, -BASE4/2, BASE2, BASE4)
#
        #gc.PushState()
        #gc.Translate(60, 75)
        #gc.SetPen(wx.Pen('navy', 1))
        #gc.SetBrush(wx.Brush('pink'))
#
        #w,h = gc.GetTextExtent('StrokePath')
        #gc.DrawText('StrokePath', -w/2, -BASE2-h-4)
        #gc.StrokePath(path)
        #gc.PopState()

#class MapCanvas (wx.Panel):
#    'Experimenting...'
#
#    def __init__(self, parent, *args, **kwargs):
#        wx.Panel.__init__(self, parent, *args, **kwargs)
#        self.parent = parent
#
#        # from demo
#        NothingBtn = wx.Button(self, label="Do nothing with a long label")
#        NothingBtn.Bind(wx.EVT_BUTTON, self.DoNothing)
#
#        MsgBtn = wx.Button(self, label="Send Message")
#        MsgBtn.Bind(wx.EVT_BUTTON, self.OnMsgBtn)
#
#        Sizer = wx.BoxSizer(wx.VERTICAL)
#        Sizer.Add(NothingBtn, 0, wx.ALIGN_CENTER|wx.ALL, 5)
#        Sizer.Add(MsgBtn,     0, wx.ALIGN_CENTER|wx.ALL, 5)
#
#        self.SetSizerAndFit(Sizer)
#
#    def DoNothing(self, event=None):
#        pass
#
#    def OnMsgBtn(self, event=None):
#        dlg = wx.MessageDialog(self, message='A completely useless message',
#                caption='A message box', style=wx.OK|wx.ICON_INFORMATION)
#        dlg.ShowModal()
#        dlg.Destroy()
#
if __name__ == '__main__':
    import RagnarokMUD.MagicMapper.ConfigurationManager
    config = RagnarokMUD.MagicMapper.ConfigurationManager.ConfigurationManager()
    class MagicMapperApp (wx.App):
        def OnInit(self):
            f = wx.Frame(None, title='Magic Map')
            m = TestPanel(f, config=config)
            m.Fit()
            f.Show()
            return True
#class DemoFrame (wx.Frame):
#    def __init__(self, *args, **kwargs):
#        wx.Frame.__init__(self, *args, **kwargs)
#        MenuBar = wx.MenuBar()
#        FileMenu = wx.Menu()
#        self.Bind(wx.EVT_MENU, self.OnQuit, FileMenu.Append(wx.ID_EXIT, text='&Quit'))
#        MenuBar.Append(FileMenu, '&File')
#        self.SetMenuBar(MenuBar)
#        self.Panel = MapCanvas(self)
#        self.Fit()
#
#    def OnQuit(self, event=None):
#        self.Close()
#
if __name__ == '__main__':

    MagicMapperApp(redirect=False).MainLoop()
