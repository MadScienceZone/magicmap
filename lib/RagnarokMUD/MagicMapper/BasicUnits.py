########################################################################################
#  _______  _______  _______ _________ _______  _______  _______  _______              #
# (       )(  ___  )(  ____ \\__   __/(  ____ \(       )(  ___  )(  ____ ) Ragnarok    #
# | () () || (   ) || (    \/   ) (   | (    \/| () () || (   ) || (    )| MUD         #
# | || || || (___) || |         | |   | |      | || || || (___) || (____)| Magic       #
# | |(_)| ||  ___  || | ____    | |   | |      | |(_)| ||  ___  ||  _____) Mapper      #
# | |   | || (   ) || | \_  )   | |   | |      | |   | || (   ) || (       Client      #
# | )   ( || )   ( || (___) |___) (___| (____/\| )   ( || )   ( || )       (rag.com)   #
# |/     \||/     \|(_______)\_______/(_______/|/     \||/     \||/                    #
#   ______    __       _______         _______  _        _______           _______     #
#  / ____ \  /  \     (  __   )       (  ___  )( \      (  ____ )|\     /|(  ___  )    #
# ( (    \/  \/) )    | (  )  |       | (   ) || (      | (    )|| )   ( || (   ) |    #
# | (____      | |    | | /   | _____ | (___) || |      | (____)|| (___) || (___) |    #
# |  ___ \     | |    | (/ /) |(_____)|  ___  || |      |  _____)|  ___  ||  ___  |    #
# | (   ) )    | |    |   / | |       | (   ) || |      | (      | (   ) || (   ) |    #
# ( (___) )_ __) (_ _ |  (__) |       | )   ( || (____/\| )      | )   ( || )   ( | _  #
#  \_____/(_)\____/(_)(_______)       |/     \|(_______/|/       |/     \||/     \|(_) #
#                                                                                      #
########################################################################################
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Basic Units used by the Mapper
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

#@[00]@| Ragnarok MagicMapper 6.1.0-alpha.0
#@[01]@|
#@[10]@| Copyright © 2010, 2018, 2020, 2021, 2022 by Steven L. Willoughby, Aloha, Oregon, USA.
#@[11]@| All Rights Reserved. Licensed under the terms and conditions of the BSD-3-Clause
#@[12]@| License as described in the accompanying LICENSE file distributed with MagicMapper.
#@[13]@|
#@[20]@| Based on earlier code from the Ragnarok MudShell (MSH) client,
#@[21]@| Copyright © 1993, 2000-2003 by Steven L. Willoughby, Aloha, Oregon, USA.
#@[22]@| MSH is licensed under the terms and conditions of the BSD-3-Clause
#@[23]@|
#@[30]@| Redistribution and use in source and binary forms, with or without
#@[31]@| modification, are permitted provided that the following conditions
#@[32]@| are met:
#@[33]@| 1. Redistributions of source code must retain the above copyright
#@[34]@|    notice, this list of conditions and the following disclaimer.
#@[35]@| 2. Redistributions in binary form must reproduce the above copy-
#@[36]@|    right notice, this list of conditions and the following dis-
#@[37]@|    claimer in the documentation and/or other materials provided
#@[38]@|    with the distribution.
#@[39]@| 3. Neither the name of the copyright holder nor the names of its
#@[40]@|    contributors may be used to endorse or promote products derived
#@[41]@|    from this software without specific prior written permission.
#@[42]@|
#@[43]@| THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
#@[44]@| CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES,
#@[45]@| INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
#@[46]@| MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#@[47]@| DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
#@[48]@| BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
#@[49]@| OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#@[50]@| PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#@[51]@| PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#@[52]@| THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
#@[53]@| TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
#@[54]@| THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#@[55]@| SUCH DAMAGE.
#@[56]@|
#@[60]@| This software is not intended for any use or application in which
#@[61]@| the safety of lives or property would be at risk due to failure or
#@[62]@| defect of the software.
