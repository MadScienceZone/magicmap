#
import sys
sys.path.append('/users/steve/desktop/magicmapper/lib')
# vi:set ai sm nu ts=4 sw=4 expandtab:
# XXX CORRECTIONS:
# XXX  box - stroke box outline in current color
# XXX  shadebox - fill box area in specified shade of grey ->bk
# XXX  colorbox - fill box area in specified color ->bk
# XXX  Fb (bold) is missing
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: MUD-side map source file handling
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
#
#  ***ADDITIONAL SUPPORTED PS COMMANDS***
#  x pop -> 
#
#  ***CHANGED COMMANDS***
# <w> <h> <bps> <Sx> <Sy> <x> <y> Draw[Color]Image
# -> <x> <y> <Sx> <Sy> (<base64-gif-data) DrawGIFImage
#              0    0  (no scaling)
# 
# The raw data stored in the system is a text block which
# describes one or more rooms (the room field starts a new
# room record).  Fields are of the form:
#   <tag> : <data>
# and the <data> may be continued on subsequent lines if those
# lines are indented by at least one space or tab.
# Lines beginning with a # are comments and are ignored.
#
# Supported fields:
# room: full pathname of room 
# name: room's title
# page: page ID
# realm: page title
# orient: anything with "land" is landscape; else portrait
# map: map-drawing commands (see below)
# also: pathname [ID?] of rooms to print anytime this one is present
# bg: map-drawing commands "under" all rooms
#
# What we see when we query the map service /magicmap/room/<id>
# R6 <id> <page> urlencode(<name>) [<also>,...]
# <mapdata...>
#
# page data from /magicmap/page/<page>
# P6 <page> (p|l)[b] urlencode(realm)
# <bgdata...>
#
# <map/bgdata> ::=
# R[opd] x y w h urlencode(name1[\nname2]) {[n|s][e|w][IOSPLD][len]}*
#    "   " " R r   "     "                 "
# M[waopd] [x y]*
# > x y x y
# B x y w h r g b
# N x y urlencode(text)
# C r g b
# F f s
# L 
#
#
#
# map-drawing commands (separated by whitespace unless punctuation makes
# that separation already apparent; % starts a comment to end of line):
#
# <text> <text> <x> <y> <w> <h> [<room-opts>] room [<passages>] [<doors>]
# <text> <text> <x> <y>   std   [<room-opts>] room [<passages>] [<doors>]
# <text> <text> <x> <y>   <r>   [<room-opts>] round-room [<passages>] [<doors>]
# <text> <text> <x> <y>  stdr   [<room-opts>] round-room [<passages>] [<doors>] (30pt rad)
# '[' <x> <y> ... ']' [<room-opts>] maze(room|area|wall)
#| np <drawing-cmd>* [cp] (stroke|fill)
# <x1> <y1> <x2> <y2> arrow
# <x> <y> <w> <h> box
# <x> <y> <w> <h> <shade> shadebox
# <x> <y> <w> <h> <r> <g> <b> colorbox
# <text> <x> <y> boxnum
# bk | gr | wh | <shade> sg | <r> <g> <b> color   (set line drawing/filling color)
# txtf | rmnf | <n> (ss|tt|it|sl)     (set font)
# <x> <y> mv <text> show
# <x> <y> <r> dotmark
# <w> lw
# '[' <dashlen> <gaplen> ... ']' <offset> sd
# <x> <y> Tree(1|2)
# <x> <y> Clump(1|2)
# <w> <h> <bps> <Sx> <Sy> <x> <y> Draw[Color]Image

#
# <x>, <y>, <w>, <h> ::= <float> for coordinates and sizes
# <r>                ::= <float> for radius
#
# <shade>     ::= <float>   (0=black, 1=white)
# <r>, <g>, <b> :: <float>  (0=black, 1=full color)
# <room-opts> ::= ( outdoor | proto | dark )*
# <passages> ::= ([<w> passageLength] <dir> [in|out|special|offpage]* passage)*
# <doors>    ::= ( <dir> [locked] door )*
# <drawing-cmd> ::= <x> <y> mv|moveto
#                 | <x> <y> ln|lineto
#                 | <dx> <dy> rmv|rmoveto
#                 | <dx> <dy> rln|rlineto
#                 | <x> <y> <r> <start> <end> arc
#
# these get mapped to a sequence of display objects:
# np begins drawing-mode
# fill|stroke ends it and emits the objects collected
#   mv updates the current location      
#
# <dir>       ::= north | south | east | west | northeast | northwest
#                       | southeast | southwest
# <digit>     ::= '0' .. '9'
# <int>       ::= <digit>+
# <float>     ::= <int> | [<int>] '.' <int>
# <text>      ::= '(' <chars> ')'
# <chars>     ::= text with special backslash codes for \(, \), \\, plus:
#	\320 em dash
#	\261 en dash
#	\242 cents sign
#	\262 dagger
#	\263 double dagger
#	\252 Open double quotes
#	\272 Close double quotes
#	\267 Bullet
#	\341 AE ligature
#	\361 ae ligature
#	\247 Section sign
#	\266 Paragraph sign
#	\253 Open << quotes
#	\273 Close >> quotes

import re
from RagnarokMUD.MagicMapper.MapRoom import MapRoom
from RagnarokMUD.MagicMapper.MapPage import MapPage, LANDSCAPE, PORTRAIT, PageOrientationViolationError

DEFAULT_EXIT_LENGTH = 20    # units for exit passages (unless overridden)

class MapFileFormatError (Exception): 
    '''The map source file contains a syntax or other formatting error
    and cannot be processed further.'''

class DuplicateRoomError (Exception):
    "A room ID was defined more than once in the map."

class InternalError (Exception):
    '''We don't know what just happened, but it wasn't supposed to.'''

class RoomAttributes (object):
    "Get and then clear pending room flag bits, pass to function"
    def __init__(self, f):
        self.f = f
    def __call__(self, f_self, *args):
        returnval = self.f(f_self, ''.join(sorted(f_self.room_flags)), *args)
        f_self.room_flags.clear()
        f_self.exit_flags.clear()
        f_self.exit_direction = None
        f_self.exit_length = DEFAULT_EXIT_LENGTH
        return returnval

class ExitAttributes (object):
    "Get and then clear pending room exit flag bits, pass to function"
    def __init__(self, f):
        self.f = f
    def __call__(self, f_self, *args):
        if f_self.exit_direction is None:
            raise MapFileFormatError('No direction specified for room exit!')

        returnval = self.f(f_self, f_self.exit_direction, ''.join(sorted(f_self.exit_flags)), *args)
        f_self.exit_flags.clear()
        f_self.exit_direction = None
        f_self.exit_length= DEFAULT_EXIT_LENGTH
        return returnval

class RequireArgs (object):
    "Require a number and type of arguments on the stack."
    def __init__(self, f_name, prototype):
        self.f_name = f_name
        self.prototype = prototype

    def __call__(self, f):
        # Create wrapper function for future calls to f
        def wrapper(f_self, *args):
            if len(f_self.stack) < len(self.prototype):
                raise MapFileFormatError('map definition command "'+self.f_name+'" given insufficient parameters.')
            for idx, check in enumerate(zip(self.prototype, f_self.stack[-len(self.prototype):])):
                if check[0] == 'c': #coordinate value
                    if not isinstance(check[1], (float, int)):
                        raise MapFileFormatError('map definition command "%s", parameter #%d, coordinate value expected (got "%s")' %
                                (self.f_name, idx+1, check[1]))
                    if not 0 <= check[1] <= 700:
                        raise ValueError('map definition command "%s", parameter #%d, coordinate value %f out of valid range [0,700]' %
                                (self.f_name, idx+1, check[1]))

                elif check[0] == 'd': #dimension value
                    if not isinstance(check[1], (float, int)):
                        raise MapFileFormatError('map definition command "%s", parameter #%d, dimension value expected (got "%s")' %
                                (self.f_name, idx+1, check[1]))
                    if not 0 <= check[1] <= 700:
                        raise ValueError('map definition command "%s", parameter #%d, dimension value %f out of valid range [0,700]' %
                                (self.f_name, idx+1, check[1]))

                elif check[0] == 'o': #offset value
                    if not isinstance(check[1], (float, int)):
                        raise MapFileFormatError('map definition command "%s", parameter #%d, offset value expected (got "%s")' %
                                (self.f_name, idx+1, check[1]))
                    if not -700 <= check[1] <= 700:
                        raise ValueError('map definition command "%s", parameter #%d, offset value %f out of valid range [-700,700]' %
                                (self.f_name, idx+1, check[1]))

                elif check[0] == 'k': #color value (0-1)
                    if not isinstance(check[1], (float, int)):
                        raise MapFileFormatError('map definition command "%s", parameter #%d, color value expected (got "%s")' %
                                (self.f_name, idx+1, check[1]))
                    if not 0 <= check[1] <= 1:
                        raise ValueError('map definition command "%s", parameter #%d, color value %f out of valid range [0,1]' %
                                (self.f_name, idx+1, check[1]))

                elif check[0] == 'p': #array of coordinate pairs
                    if not isinstance(check[1], (list,tuple)):
                        raise MapFileFormatError('map definition command "%s", parameter #%d, coordinate-pair-list value expected (got "%s")' %
                                (self.f_name, idx+1, check[1]))
                    if len(check[1]) % 2 != 0:
                        raise MapFileFormatError('map definition command "%s", parameter #%d, coordinate-pair-list value "%s" has odd number of elements)' %
                                (self.f_name, idx+1, check[1]))
                    if not all([0 <= i <= 700 for i in check[1]]):
                        raise ValueError('map definition command "%s", parameter #%d, coordinate(s) in list out of range [0,700]: %s' %
                                (self.f_name, idx+1, check[1]))

                elif check[0] == 's': #string value
                    if not isinstance(check[1], str):
                        raise MapFileFormatError('map definition command "%s", parameter #%d, string value expected (got "%s")' %
                                (self.f_name, idx+1, check[1]))

                else:
                    raise InternalError('BUG: PS function "%s" prototype "%s" invalid (what is "%s" supposed to mean?)' %
                            (self.f_name, self.prototype, check[0]))
            return f(f_self, *args)
        return wrapper

class MapSource (object):
    '''The Ragnarok Magic Map as described in RRFC42 and RRFC46.
    This object class understands the map file format and can
    render images of the map.'''

    _IGNORE_LINE= re.compile(r'^#|^\s*$')
    _FIELD_CONT = re.compile(r'^\s+(?P<moretext>\S.*?)\s*$')
    _FIELD_DECL = re.compile(r'^(?P<tag>\w+)\s*:\s*(?P<value>.*?)\s*$')

    def __init__(self, file=None):
        "Create map source file manager, optionally reading map in from file."

        self.pages = {}
        self.room_page = {}
        if file is not None:
            self.add_from_file(file)

    def _each_record(self, input_file):
        "Scan file for record blocks, generating record dictionaries for each found."

        current_record = {}
        current_tag = None

        for line in input_file:
            #
            # Strip comments and blank lines
            #
            if MapSource._IGNORE_LINE.match(line):
                continue
            #
            # Recognize beginning of a field (possibly
            # a new record block)
            #
            decl = MapSource._FIELD_DECL.match(line)
            if decl:
                current_tag = decl.group('tag')
                if current_tag == 'room':
                    if current_record:
                        yield current_record
                        current_record = {}
                    
                if current_tag in current_record:
                    raise MapFileFormatError('Map record for '
                            +current_record.get('room', decl.group('value') 
                                    if current_tag=='room' else 'unknown room')
                            +' contains multiple '+current_tag+' fields.')

                current_record[current_tag] = decl.group('value')
            else:
                #
                # recognize the continuation of the previous field
                #
                cont = MapSource._FIELD_CONT.match(line)
                if cont:
                    if current_tag is None:
                        raise MapFileFormatError("Continuation line in map file outside containing record block: "+cont.group('moretext'))
                    if current_tag not in ('map', 'also', 'bg'):
                        raise MapFileFormatError('"'+current_tag+'" fields cannot have multiple lines; only "map", "also" and "bg" can do that.')

                    current_record[current_tag] += '\n' + cont.group('moretext')
                else:
                    #
                    # We're not sure WHAT we just read...
                    #
                    raise MapFileFormatError("Unrecognizable line in map file at "
                            + current_record.get('room', 'unknown room')
                            + ': ' + line.strip())
        #
        # yield last read block, if any
        #
        if current_record:
            yield current_record


    def add_from_file(self, input_file):
        "Add rooms and places to this file from a map source file."

        for record in self._each_record(input_file):
            for required_field in 'room', 'page':
                if required_field not in record:
                    raise MapFileFormatError('Map source file record does not contain a "'
                            +required_field+'" field: ' + repr(record))
            #
            # set up containing page first
            #
            page = self.get_page(record['page'])

            if 'bg' in record:
                if page.bg:
                    # XXX warn that multiple rooms contribute to this page bg
                    pass
                page.bg.extend(self.compile(record['bg']))

            if 'realm' in record:
                if page.realm and record['realm'] != page.realm:
                    # XXX warn that room overrides page realm name
                    pass
                page.realm = record['realm']

            if 'orient' in record:
                page.orient = LANDSCAPE if 'land' in record['orient'] else PORTRAIT

            if record['room'] in self.room_page:
                raise DuplicateRoomError('Room '+record['room']+' was already defined (on page '+repr(self.room_page[record['room']])+')')

            self.room_page[record['room']] = page.page
            page.add_room(MapRoom(record['room'], page, record.get('name'), 
                self.compile(record['map']) if 'map' in record else None,
                record.get('also','').split('\n')))

    def get_page(self, page_id):
        "Get page by id (coerced to integer) and return it (creating one if needed)"

        i = int(page_id)
        if i not in self.pages:
            self.pages[i] = MapPage(i)
        return self.pages[i]

    def compile(self, source):
        "Compile source string -> list of encoded element definitions"
        object = []
        self.stack = []
        self.room_flags = set()
        self.exit_flags = set()
        self.exit_direction = None
        self.exit_length= DEFAULT_EXIT_LENGTH
        self.current_room_exits = None
        self.x = 0
        self.y = 0
        self.drawing_mode_list = None

        #
        # The source used to be PostScript commands.  We keep the same
        # general format but proscribe a small list of commands which
        # are available and forbid random PS.  We'll interpret these
        # commands in the source string and emit a list of individual
        # graphic object definitions we can more quickly parse later.
        #
        # This has the main benefit of revealing syntax errors before the
        # end user tries to see their map.
        #
        # (...) push string value, interpreting \ escapes.
        # otherwise, space-delimited strings are interpreted:
        # if it looks like a numeric constant, push it.
        # some other symbols are pushed, others are executed (which may
        # pop their arguments)
        #
        ps_command_dispatch = {
            'arrow':    self._ps_arrow,
            'bk':       self._ps_bk,
            'box':      self._ps_box,
            'boxnum':   self._ps_boxnum,
            'Clump1':   self._ps_clump1,
            'Clump2':   self._ps_clump2,
            'color':    self._ps_color,
            'colorbox': self._ps_colorbox,
            'dotmark':  self._ps_dotmark,
            'DrawGIFImage': self._ps_image,
            'gr':       self._ps_gr,
            'it':       self._ps_it,
            'lw':       self._ps_linewidth,
            'mazearea': self._ps_mazearea,
            'mazeroom': self._ps_mazeroom,
            'mazewall': self._ps_mazewall,
            'rmnf':     self._ps_rmnf,
            'room':     self._ps_room,
            'round-room': self._ps_round_room,
            'sd':       self._ps_setdash,
            'sg':       self._ps_sg,
            'sl':       self._ps_sl,
            'ss':       self._ps_ss,
            'shadebox': self._ps_shadebox,
            'show':     self._ps_show_text,
            'Tree1':    self._ps_tree1,
            'Tree2':    self._ps_tree2,
            'tt':       self._ps_tt,
            'txtf':     self._ps_txtf,
            'wh':       self._ps_wh,
        }
        ps_room_flags = {
            'dark':     'd',
            'proto':    'p',
            'outdoor':  'o',
        }
        ps_exit_directions = {
            'north':    'n',
            'south':    's',
            'east':     'e',
            'west':     'w',
            'northeast':'a',
            'southeast':'b',
            'northwest':'c',
            'southwest':'d',
        }
        ps_exit_flags = {   # door is also 'D'
            'in':       'i',
            'out':      'o',
            'offpage':  'x',
            'special':  '!',
            'locked':   'L',
        }
        for ps_token in self._each_ps_token(source):
            if isinstance(ps_token, (int, float)):
                self.stack.append(ps_token)
            elif ps_token in ps_command_dispatch:
                object.append(ps_command_dispatch[ps_token]())
            elif ps_token in ps_room_flags:
                self.room_flags.add(ps_room_flags[ps_token])
            elif ps_token in ps_exit_flags:
                self.exit_flags.add(ps_exit_flags[ps_token])
            elif ps_token in ps_exit_directions:
                if self.exit_direction is not None:
                    if ps_exit_directions[ps_token] != self.exit_direction:
                        raise MapFileFormatError('Exit declared to be going multiple directions!')
                else:
                    self.exit_direction = ps_exit_directions[ps_token]
            elif ps_token == 'passageLength':
                self._ps_passage_length()
            elif ps_token == 'door':
                self._ps_door()
            elif ps_token == 'passage':
                self._ps_passage()
            elif ps_token == 'std':
                self.stack.append(50)
                self.stack.append(20)
            elif ps_token == 'stdr':
                self.stack.append(30)
            elif ps_token == 'mv' or ps_token == 'moveto':
                self._ps_moveto()
            elif ps_token == 'rmv' or ps_token == 'rmoveto':
                self._ps_rmoveto()
            elif ps_token == 'pop':
                try:
                    self.stack.pop()
                except IndexError:
                    raise MapFileFormatError('pop command encountered with no corresponding value to pop')
            elif ps_token == '[':
                self.stack.append(None)
            elif ps_token == ']':
                list_obj = []
                while self.stack:
                    i = self.stack.pop()
                    if i is None:
                        break
                    list_obj.insert(0,i)
                else:
                    raiseMapFileFormatError('"]" without corresponding "[" in map definition.')
                self.stack.append(list_obj)
                
            elif ps_token.startswith('(') and ps_token.endswith(')'):
                self.stack.append(re.sub(r'\\([0-7]{1,3})', lambda m: chr(int(m.group(1), 8)), ps_token)[1:-1])

            elif ps_token == 'np' or ps_token == 'newpath':
                if self.drawing_mode_list is not None:
                    raise MapFileFormatError('newpath command encountered before previous path completed.')
                self.drawing_mode_list = [[(self.x, self.y)]]
            elif ps_token == 'curveto': # XXX fix!
                self.stack.pop()
                self.stack.pop()
                self.stack.pop()
                self.stack.pop()
                self._ps_lineto()
            elif ps_token == 'ln' or ps_token == 'lineto':
                self._ps_lineto()
            elif ps_token== 'rln' or ps_token == 'rlineto':
                self._ps_rlineto()
            elif ps_token == 'stroke' or ps_token == 'fill': # XXX fix fill!
                if self.drawing_mode_list is None:
                    raise MapFileFormatError('stroke command encountered outside drawing mode (need "newpath" first)')
                for line_path in self.drawing_mode_list:
                    if len(line_path) < 2:
                        continue

                    coords = []
                    for x, y in line_path:
                        coords.append(x)
                        coords.append(y)
                    object.append(['P', coords])
                self.drawing_mode_list = None
            else:
                raise MapFileFormatError('Unrecognized map drawing command "'+ ps_token + '".')

        if self.stack:
            raise MapFileFormatError('Extra values in map definition with nowhere to go: ' + repr(self.stack))
        if self.drawing_mode_list is not None:
            raise MapFileFormatError('Drawing path not completed (missing "stroke" or "fill"?)')
        return object

    @RequireArgs('arrow', 'cccc')
    def _ps_arrow(self):
        return ['>']+list(reversed([self.stack.pop() for i in range(4)]))

    #
    # trivial stuff
    #
    def _ps_txtf(self): return ['Ft', 8]
    def _ps_rmnf(self): return ['Fr', 6]
    def _ps_bk(self):   return ['C', 0, 0, 0]
    def _ps_gr(self):   return ['C', .5, .5, .5]
    def _ps_wh(self):   return ['C', 1, 1, 1]

    @RequireArgs('moveto', 'cc')
    def _ps_moveto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        self._do_moveto(x, y)

    @RequireArgs('rmoveto', 'oo')
    def _ps_rmoveto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        self._do_moveto(self.x + x, self.y + y)

    def _do_moveto(self, x, y):
        self.x = x
        self.y = y
        if self.drawing_mode_list is not None:
            if len(self.drawing_mode_list[-1]) < 2:
                # if we hadn't really drawn anything yet, just replace old location
                self.drawing_mode_list[-1] = [(self.x, self.y)]
            else:
                # otherwise, push previous set of coordinates and start a new set from here...
                self.drawing_mode_list.append([(self.x, self.y)])

    @RequireArgs('lineto', 'cc')
    def _ps_lineto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        self._do_lineto(x, y)

    @RequireArgs('rlineto', 'oo')
    def _ps_rlineto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        self._do_lineto(self.x + x, self.y + y)

    def _do_lineto(self, x, y):
        self.x = x
        self.y = y
        if self.drawing_mode_list is None:
            raise MapFileFormatError('[r]lineto command encountered outside drawing mode (need "newpath" first)')
        self.drawing_mode_list[-1].append((self.x, self.y))



    @RequireArgs('ss', 'd')
    def _ps_ss(self):   return ['Fs', self.stack.pop()]

    @RequireArgs('tt', 'd')
    def _ps_tt(self):   return ['FT', self.stack.pop()]

    @RequireArgs('it', 'd')
    def _ps_it(self):   return ['Fi', self.stack.pop()]

    @RequireArgs('sl', 'd')
    def _ps_sl(self):   return ['Fo', self.stack.pop()]

    @RequireArgs('sg', 'k')
    def _ps_sg(self):
        v = self.stack.pop()
        return ['C', v, v, v]

    @RequireArgs('color', 'kkk')
    def _ps_color(self):
        return ['C'] + list(reversed([self.stack.pop() for i in range(3)]))

    @RequireArgs('box', 'ccdd')
    def _ps_box(self):
        return ['B']+list(reversed([self.stack.pop() for i in range(4)]))+[0,0,0]

    @RequireArgs('boxnum', 'scc')
    def _ps_boxnum(self):
        return ['#']+list(reversed([self.stack.pop() for i in range(2)]))+[self.stack.pop()]

    @RequireArgs('Clump1', 'cc')
    def _ps_clump1(self):
        return ['Tc']+list(reversed([self.stack.pop() for i in range(2)]))

    @RequireArgs('Clump2', 'cc')
    def _ps_clump2(self):
        return ['Tc2']+list(reversed([self.stack.pop() for i in range(2)]))

    @RequireArgs('colorbox', 'ccddkkk')
    def _ps_colorbox(self):
        return ['B']+list(reversed([self.stack.pop() for i in range(7)]))

    @RequireArgs('dotmark', 'ccd')
    def _ps_dotmark(self):
        return ['*']+list(reversed([self.stack.pop() for i in range(3)]))

    @RequireArgs('DrawGIFImage', 'ccdds')
    def _ps_image(self):
        return ['G'] + list(reversed([self.stack.pop() for i in range(5)]))

    @RequireArgs('lw', 'd')
    def _ps_linewidth(self):
        return ['L', self.stack.pop()]

    @RequireArgs('mazearea', 'p')
    @RoomAttributes
    def _ps_mazearea(self, flagbits):
        return ['Ma'+flagbits, self.stack.pop()]

    @RequireArgs('mazeroom', 'p')
    @RoomAttributes
    def _ps_mazeroom(self, flagbits):
        return ['Maw'+flagbits, self.stack.pop()]

    @RequireArgs('mazewall', 'p')
    @RoomAttributes
    def _ps_mazewall(self, flagbits):
        return ['Mw'+flagbits, self.stack.pop()]

    @RequireArgs('door', '')
    @ExitAttributes
    def _ps_door(self, direction, flagbits):
        if self.current_room_exits is None:
            raise MapFileFormatError('door declaration requires a room first!')
        if direction not in self.current_room_exits:
            # no passage there; create the exit now for the door
            new_exit = [direction+'D'+flagbits, 0]
            self.current_room_exits[direction] = new_exit
            self.current_room_exits['__list__'].append(new_exit)
        else:
            # add "door" to existing exit
            if 'D' in self.current_room_exits[direction][0]:
                raise MapFileFormatError('Exit has multiple doors defined for it!')
            self.current_room_exits[direction][0] += 'D'+flagbits

    @RequireArgs('passage', '')
    @ExitAttributes
    def _ps_passage(self, direction, flagbits):
        # This is tricky, because it modifies the most recent room definition.
        # so we need a reference to that object from before.
        if self.current_room_exits is None:
            raise MapFileFormatError('passage declaration requires a room first!')
        if direction not in self.current_room_exits:
            new_exit = [direction+flagbits, self.exit_length]
            self.current_room_exits['__list__'].append(new_exit)
            self.current_room_exits[direction] = new_exit
        else:
            raise MapFileFormatError('passage declared multiple times for same room (or door defined before its passage)!')

    @RequireArgs('passageLength', 'd')
    def _ps_passage_length(self):
        self.exit_length = self.stack.pop()

    @RequireArgs('room', 'ssccdd')
    @RoomAttributes
    def _ps_room(self, flagbits):
        self.current_room_exits = { '__list__': [] }
        return ['R'+flagbits] \
                + list(reversed([self.stack.pop() for i in range(4)])) \
                + list(reversed([self.stack.pop() for i in range(2)])) \
                + [self.current_room_exits['__list__']]

    @RequireArgs('round-room', 'ssccd')
    @RoomAttributes
    def _ps_round_room(self, flagbits):
        self.current_room_exits = { '__list__': [] }
        r = self.stack.pop()
        return ['R'+flagbits] \
                + list(reversed([self.stack.pop() for i in range(2)])) \
                + ['R', r] \
                + list(reversed([self.stack.pop() for i in range(2)])) \
                + [self.current_room_exits['__list__']]

    @RequireArgs('sd', 'pd')
    def _ps_setdash(self):
        return ['D']+list(reversed([self.stack.pop() for i in range(2)]))

    @RequireArgs('shadebox', 'ccddk')
    def _ps_shadebox(self):
        color = self.stack.pop()
        return ['B']+list(reversed([self.stack.pop() for i in range(4)]))+[color]*3

    @RequireArgs('show', 's')
    def _ps_show_text(self):
        return ['S', self.x, self.y, self.stack.pop()]

    @RequireArgs('Tree1', 'cc')
    def _ps_tree1(self):
        return ['T']+list(reversed([self.stack.pop() for i in range(2)]))

    @RequireArgs('Tree2', 'cc')
    def _ps_tree2(self):
        return ['T2']+list(reversed([self.stack.pop() for i in range(2)]))


    def _each_ps_token(self, source):
        '''Generate a list of PostScript-style code tokens from input source string.

        Strings are one token: '(...)' with \ooo for octal character codes (we force
        \(, \), and \\ to \ooo equivalents).

        otherwise each token is returned as a separate string value.  For example,
        _each_ps_token('(hello \(Hi!\))(world) 1 2 3 [1.0 2.0] foo bar') yields the sequence:
        ['(hello \050Hi!\051)', '(world)', 1, 2, 3, '[', 1.0, 2.0, ']', 'foo', 'bar']'''
        
        source = source.replace(r'\\', r'\134').replace(r'\(', r'\050').replace(r'\)', r'\051')
        ignoring_comment = False
        for token in re.split(r'(\n|[ \t]+|[][]|\(.*?\))', source):
            if token.startswith('%'):
                ignoring_comment=True
                continue

            if ignoring_comment:
                if token == '\n':
                    ignoring_comment=False
                continue

            if token.strip() == '':
                continue
            try:
                yield int(token)        # try converting to integer if we can
            except:
                try:
                    yield float(token)  # try converting to float if we can
                except:
                    yield token         # punt

#
# Output format:
# Marshaling:
#   space-separated tokens (newline==space)
#   numeric value printed as digits
#   string printed as /<chars>, but:
#       urlencode (+ for space, slash may be omitted if it's obviously a string)
#       so:  'hello' => 'hello'
#            'hello world' => 'hello+world'
#            '123' => '/123'
#            ''    => '/'
#     
#   :n n elements following are elements in a list object (recursion ok)
#
#   Source:
#       (Heimdall's) (Path) 395 335 std proto outdoor room
#       450 341 moveto (\(See p. 3\)) show
#       (Museum) (Entrance) 325 335 std outdoor room
#           east passage west passage
#       (Museum) (Rodunda) 275 345 stdr round-room
#           north passage
#           east passage
#           west passage
#           south passage
#           southeast passage
#       301 320 moveto (Dn) show
#
#   Object:
#       [
#           ['Rop', 395, 335, 50, 20, "Heimdall's", 'Path', []],
#           ['S', 450, 341, '(See p. 3)'],
#           ['Ro', 325, 335, 50, 20, 'Museum', 'Entrance', [['e',20],['w',20]]],
#           ['R', 275, 345, 'R', 30, 'Museum', 'Rotunda', [['n',20],['e',20],['w',20],['s',20],['b',20]]],
#           ['S', 301, 320, 'Dn']
#       ]
#
#   Text:
#       :5 :8 Rop 395 332 50 20 Heimdall's Path :0 :4 S 450 341 (See+p.+3) 
#       :8 Ro 325 335 50 20 Museum Entrance :2 :2 e 20 :2 w 20
#       :8 R 275 345 R 30 Museum Rotunda :5 :2 n 20 :2 e 20 :2 w 20 :2 s 20 :2 b 20 
#       :4 S 301 320 Dn
#  
# maps are lists of elements; elements are lists:
#   first element is type (char 0) + flag characters
#
# # x y label                   boxnum
# * x y r                       dotmark
# > x1 y1 x2 y2                 arrow
# B x y h w                     box
# C r g b                       color/bk/gr/wh/sg
# D [...] offset                sd
# F[iorstrtT] pts                 txtf/rmnf/ss/tt/it/sl
# G x y Sx|0 Sy|0 data          DrawGIFImage
# L w                           lw
# M[awdop] [x1 y1 ... xn yn]    maze*
# P[cf] [x1 y1 x2 y2 ... xn yn] draw polygon (from np...stroke) [f=fill, c=closed]
# R[] x y h|R w|r lbl1 lbl2 [...] [round-]room
# S x y text                    show
# T[c2] x y                     tree/clump
if __name__ == '__main__':
    import glob
    ms = MapSource()
    page_bg = {}
    page_rooms = {}
    page_attrs = {}

    for input_pat in sys.argv[1:]:
      for input_file in glob.glob(input_pat):
        with open(input_file, 'r') as source:
            for record in ms._each_record(source):
                pg = record['page']
                if pg not in page_bg:
                    page_bg[pg] = []
                    page_rooms[pg] = []
                    page_attrs[pg] = {}
                if 'bg' in record:
                    page_bg[pg].append(record['bg'])
                if 'realm' in record:
                    page_attrs[pg]['realm'] = record['realm']
                if 'orient' in record:
                    page_attrs[pg]['orient'] = record['orient']
                if 'map' in record:
                    page_rooms[pg].append(record['map'])
        print("%s: pg=%s %d rooms" % (
                input_file, sorted(page_bg.keys()), 
                sum([len(page_rooms[i]) for i in page_rooms])))
    for page in page_bg:
        with open("Page_"+page+".ps", "w") as dest:
            dest.write("% Page " + page + "\n")
            dest.write(str(page_attrs[pg]))
            dest.write("% bg\n")
            dest.write('\n'.join(page_bg[page]))
            dest.write('\n\n% rooms\n\n')
            dest.write('\n'.join(page_rooms[page]))





    
