#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: ANSI Sequence Parser
# $Header$
#
# Copyright (c) 2012, 2018 by Steven L. Willoughby, Aloha, Oregon, USA.
# All Rights Reserved.  Licensed under the Open Software License
# version 3.0.  See http://www.opensource.org/licenses/osl-3.0.php
# for details.
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

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        "point addition"
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Point(self.x * other.x, self.y * other.y)

    def scale(self, factor):
        self.x *= factor
        self.y *= factor

    def clone(self):
        return Point(self.x, self.y)

class Color:
    def __init__(self, r, g, b):
        self.red = r
        self.green = g
        self.blue = b
        self.rgb = '#{0:02x}{1:02x}{2:02x}'.format(
            max(0,min(255,int(self.red * 255))),
            max(0,min(255,int(self.green * 255))),
            max(0,min(255,int(self.blue * 255)))
        )

    def __eq__(self, other):
        return self.red == other.red and self.green == other.green and self.blue == other.blue

    def __ne__(self, other):
        return not self.__eq__(other)

class GreyLevel (Color):
    def __init__(self, v):
        Color.__init__(self, v, v, v)

class FontSelection:
    def __init__(self, name, size):
        self.name = name
        self.size = size

    def __eq__(self, other):
        return self.name == other.name and self.size == other.size

    def __ne__(self, other):
        return not self.__eq__(other)

class GraphicsState:
    def __init__(self, clone_from=None):
        if clone_from is None:
            self.color = GreyLevel(0)
            self.translate = Point(0,0)
            self.scale = Point(1,1)
            self.font = FontSelection('Ft', 8)
            self.line_width = 1
        else:
            self.clone(clone_from)

    def clone(self, other_state):
        self.color = other_state.color
        self.translate = other_state.translate
        self.scale = other_state.scale
        self.font = other_state.font
        self.line_width = other_state.line_width

    def __eq__(self, other):
        return self.color == other.color and self.translate == other.translate and self.scale == other.scale and self.font == other.font and self.line_width == other.line_width

    def __ne__(self, other):
        return not self.__eq__(other)

class DashPattern:
    def __init__(self, pattern, offset):
        self.pattern = pattern
        self.offset = offset
