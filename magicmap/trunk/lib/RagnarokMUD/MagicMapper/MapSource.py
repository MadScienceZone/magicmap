#
# vi:set ai sm nu ts=4 sw=4 expandtab:
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
# TODO: update the list of supported commands here
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
# <room-opts> ::= ( outdoor | proto | dark | <shade> shaded )*
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

import re, math
from RagnarokMUD.MagicMapper.MapRoom import MapRoom
from RagnarokMUD.MagicMapper.MapPage import MapPage, LANDSCAPE, PORTRAIT, PageOrientationViolationError

DEFAULT_EXIT_LENGTH = 20    # units for exit passages (unless overridden)

class IllegalCreatorReference (Exception): pass
class InvalidRoomPath (Exception): pass
class MapFileFormatError (Exception): 
    '''The map source file contains a syntax or other formatting error
    and cannot be processed further.'''

class DuplicateRoomError (Exception):
    "A room ID was defined more than once in the map."

class InternalError (Exception):
    '''We don't know what just happened, but it wasn't supposed to.'''

class NoProcedureRunning (Exception):
    "Tried to stop something we weren't doing."

class InfiniteLoopError (Exception):
    "The road goes on and on and on and on and on and on and..."

class RoomAttributes (object):
    "Get and then clear pending room flag bits, pass to function"
    def __init__(self, f):
        self.f = f
    def __call__(self, f_self, *args):
        if f_self.room_shade is None:
            shade = ''
        else:
            shade = '$%02d' % max(min(int(f_self.room_shade*100), 0), 99)
        returnval = self.f(f_self, ''.join(sorted(f_self.room_flags)) + shade, *args)
        f_self.room_flags.clear()
        f_self.exit_flags.clear()
        f_self.exit_direction = None
        f_self.exit_length = DEFAULT_EXIT_LENGTH
        f_self.room_shade = None
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
        f_self.room_shade = None
        return returnval

class RequireArgs (object):
    '''Require a number and type of arguments on the stack.

    This is applied as a function decorator in the compiler's methods which
    handle individual commands, as:

    @RequireArgs(cmdname, prototype)
    def handler_method(self, ...):

    The prototype is one of two things:
      (a) an integer value, indicating that there must be at least that many
          elements of any type on the stack, or
      (b) a string of single-letter descriptors indicating the number (implicitly)
          and types (explicitly) of the elements which should be on the stack,
          in order from deepest to top-most.  So 'abc' means the stack should
          contain a type a, b, and c object with c being at the top of the stack.

    The prototype values are:
      'b' boolean value (int for now)
      'c' coordinate value (int/float in range 0 <= x <= 700)
      'd' dimension value (int/float in range 0 <= x <= 700)
      'f' float value (float or something able to be coerced into one)
      'i' int value (integer or something able to be coerced into one)
      'k' color value (float in range 0 <= x <= 1)
      'o' offset value (int/float in range -700 <= x <= 700)
      'p' array of coordinate pairs (list/tuple of even number of 'c' values)
      's' string value (string object)
      'x' executable block of code (list of tokens to be re-scanned by compiler)
      '''

    def __init__(self, f_name, prototype):
        self.f_name = f_name
        self.prototype = prototype

    def __call__(self, f):
        # Create wrapper function for future calls to f
        def wrapper(f_self, *args):
            if isinstance(self.prototype, int):
                # Just care about quantity of args, not types
                if len(f_self.stack) < self.prototype:
                    raise MapFileFormatError('map definition command "{0}" needs {1} parameter{2}, but found {3}'.format(
                        self.f_name, self.prototype, ('' if self.prototype==1 else 's'), len(f_self.stack)))
            else:
                # check quantity AND type of args
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

                    elif check[0] == 'x': #executable block
                        if not isinstance(check[1], (list,tuple)):
                            raise MapFileFormatError('map definition command "%s", parameter #%d, procedure block expected (got "%s")' %
                                    (self.f_name, idx+1, check[1]))

                    elif check[0] == 's': #string value
                        if not isinstance(check[1], str):
                            raise MapFileFormatError('map definition command "%s", parameter #%d, string value expected (got "%s")' %
                                    (self.f_name, idx+1, check[1]))

                    elif check[0] == 'f': #float value
                        try:
                            v = float(check[1])
                        except:
                            raise MapFileFormatError('map definition command "{0}", parameter #{1:d}, should be numeric, was "{2}"'.format(
                                self.f_name, idx+1, check[1]))

                    elif check[0] == 'i': #int value
                        try:
                            v = int(check[1])
                        except:
                            raise MapFileFormatError('map definition command "{0}", parameter #{1:d}, should be integral, was "{2}"'.format(
                                self.f_name, idx+1, check[1]))

                    elif check[0] == 'b': # boolean
                        try:
                            v = int(check[1])
                        except:
                            raise MapFileFormatError('map definition command "{0}", parameter #{1:d}, should be boolean, was "{2}"'.format(
                                self.f_name, idx+1, check[1]))

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
    _INT_BASE   = re.compile(r'^\s*(?P<base>\d+)#(?P<value>[0-9A-Za-z]+)\s*$')
    
    _LOOP_MAX = 10000   # too many iterations (emergency stop)

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

                if current_tag == 'ref':
                    try:
                        current_record[current_tag] = tuple([float(i) for i in decl.group('value').split()])
                    except:
                        raise MapFileFormatError('"ref" field could not be understood: {0}'.format(line))
                    if len(current_record[current_tag]) != 2:
                        raise MapFileFormatError('"ref" field must have two values: {0}'.format(line))
                else:
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


    def add_from_file(self, input_file, creator=None, enforce_creator=False):
        "Add rooms and places to this file from a map source file."

        for record in self._each_record(input_file):
            for required_field in 'room', 'page':
                if required_field not in record:
                    raise MapFileFormatError('Map source file record does not contain a "'
                            +required_field+'" field: ' + `record`)
            #
            # set up containing page first
            #
            page = self.get_page(record['page'])

            if 'bg' in record:
                if page.bg:
                    # XXX warn that multiple rooms contribute to this page bg
                    pass
                page.bg.extend(self.compile(record['bg']))

            if creator is not None and creator not in page.creators:
                page.creators.append(creator)

            if 'realm' in record:
                if page.realm and record['realm'] != page.realm:
                    # XXX warn that room overrides page realm name
                    pass
                page.realm = record['realm']

            if 'orient' in record:
                page.orient = LANDSCAPE if 'land' in record['orient'] else PORTRAIT


            # Sanitize room pathname to /players/<name>/... with no /../
            # Allowed input forms (all referring to ~<name>/dir/room.c):
            #   /players/<name>/dir/room    -> players/<name>/dir/room
            #   ~<name>/dir/room            -> players/<name>/dir/room
            #   ~/dir/room                  -> players/<name>/dir/room
            #   dir/room                    -> players/<name>/dir/room
            # Base map forms (everything else):
            #   /room/foo                   -> room/foo
            #    
            room_name = os.path.normpath(record['room'])
            room_creator = None
            #
            # expand ~ syntax and convert to relative path from mudlib root
            #
            m_tilde = re.match(r'~(\w*)/(.*)', room_name)
            if m_tilde:
                # ~/...
                # ~<name>/...
                if not m_tilde.group(1):
                    if creator is None:
                        raise(InvalidRoomPath('Cannot determine creator name to expand path {0}'.format(room_name))
                    room_creator = creator
                else:
                    room_creator = m_tilde.group(1)
                    
                room_name = 'players/'+room_creator+'/'+m_tilde.group(2)

            else:
                m_player= re.match(r'/players/(\w+)/', room_name)
                if m_player:
                    # /players/<name>/...
                    room_creator = m_player.group(1)
                    room_name = room_name[1:]
                elif room_name.startswith('/'):
                    # /something-other-than-players/...
                    room_creator = None
                    room_name = room_name[1:]
                else:
                    # relative path in creator's realm
                    if creator is None:
                        raise InvalidRoomPath('Cannot determine creator name to expand path {0}'.format(room_name))
                    room_creator = creator
                    room_name = 'players/'+room_creator+'/'+room_name

            record['room'] = room_name
            if room_name in self.room_page:
                raise DuplicateRoomError('Room '+room_name+' was already defined (on page '+`self.room_page[record['room']]`+')')

            if enforce_creator:
                # Ensure that we don't have user A defining room maps in user B's
                # realm.
                # (if path does not match that pattern then it's a base map with
                # NO creator, which means the creator param must be undefined here)
                if room_creator != creator:
                    if creator is None:
                        raise IllegalCreatorReference('Base maps cannot define rooms inside wizard realms: {0}'.format(room_name))
                    else:
                        raise IllegalCreatorReference("Map in {0}'s realm cannot define rooms for {1}'s realm: {2}".format(creator, room_creator, room_name))


            self.room_page[record['room']] = page.page
            page.add_room(MapRoom(record['room'], page, record.get('name'), 
                self.compile(record['map']) if 'map' in record else None,
                record.get('also','').split('\n'),
                reference_point=record.get('ref')))

    def get_page(self, page_id):
        "Get page by id (coerced to integer) and return it (creating one if needed)"

        i = int(page_id)
        if i not in self.pages:
            self.pages[i] = MapPage(i)
        return self.pages[i]

    def compile(self, source, allow_test=False):
        "Compile source string -> list of encoded element definitions"
        object = []
        self.stack = []
        self.room_flags = set()
        self.exit_flags = set()
        self.drawing_flags = set()
        self.exit_direction = None
        self.exit_length= DEFAULT_EXIT_LENGTH
        self.room_shade = None
        self.current_room_exits = None
        self.current_point = None
        self.drawing_mode_list = None
        self.last_drawing_mode_list = None
        self.last_drawing_flags = set()
        self._start_tokenizer()

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

        #
        # drawing_mode_list handles the newpath...stroke|fill
        # sequence.  If this is None, we're NOT in drawing
        # mode.  Otherwise, it is a list of lines/polygons
        # where each element is a dictionary holding the 
        # type of object being rendered and a list of 
        # points, where each point is a 2-tuple (x,y).
        #
        # (x0,y0) is the current point
        # newpath:  create empty list (toplevel type None, None|[(x0,y0)])
        # stroke|fill:
        # moveto:   set current point, and if in drawing mode:
        #               replace toplevel if None or single point
        #               otherwise push previous set and start new type None, [(x,y)]
        # acurveto: _a ty=b [(x1,y1)...] isolate
        # scurveto: _a ty=s [(x1,y1)...] isolate
        # curveto:  _a ty=b [(x1,y1), (x2,y2), (x3,y3), isolate
        # lineto:   _a ty=p [(x,y)]
        # arc:
        #   if cp? _a ty=p [(x1,y1)]
        #   _a ty=a [(xc,yc), (x1,y1), (x2,y2)], isolate
        # stroke|fill:
        #   each entry on stack except ty=None/empty points/single points:
        #       ty=[bs]? add to type_flags
        #       ty=a? -> [Q, xc, yc, x1, y1, x2, y2]
        #       else: -> [P, x1, y1, ...]
        #   exit drawing mode
        #
        #
        # _a c ty [(x1,y1),...(xn,yn)]: 
        #   requires current point
        #   isolate? push (ty, [(x0,y0),(x1,y1),...(xn,yn)]), push (None, [(xn,yn)])
        #   or toplevel type different? push (ty, [(x0,y0),(x1,y1),...(xn,yn)])
        #   or: add (x1,y1)...(xn,yn) to toplevel's list
        #   and set current point to (xn,yn) or explicitly named point


        #
        # drawing_flags = c|f
        #
        #  newpath -> [[(x,y)]]
        #  lineto -> append (x,y)
        #  rlineto -> append(x,y)
        #  moveto ->
        #       replace top of list's (x,y) coords if only
        #        one set yet (nothing drawn)
        #       otherwise, push a new line starting here
        #  stroke|fill -> [P + coords] for each line
        #  
        # 
        ps_command_dispatch = {
            'arrow':    self._ps_arrow,
            'bf':       self._ps_bf,
            'bk':       self._ps_bk,
            'box':      self._ps_box,
            'boxnum':   self._ps_boxnum,
            'Clump1':   self._ps_clump1,
            'Clump2':   self._ps_clump2,
            'color':    self._ps_color,
            'colorbox': self._ps_colorbox,
            'dotmark':  self._ps_dotmark,
            'graphic':  self._ps_image,
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
        if allow_test:
            ps_command_dispatch['__test__'] = self._ps__test__
        ps_internal_commands = {
            'add':      self._do_add,
            'sub':      self._do_sub,
            'mul':      self._do_mul,
            'div':      self._do_div,
            'idiv':     self._do_idiv,
            'neg':      self._do_neg,
            'mod':      self._do_mod,
            'exch':     self._do_exch,
            'true':     self._do_true,
            'false':    self._do_false,
            'exp':      self._do_exp,
            'atan':     self._do_atan,
            'cos':      self._do_cos,
            'sin':      self._do_sin,
            'ceiling':  self._do_ceiling,
            'floor':    self._do_floor,
            'truncate': self._do_truncate,
            'logn':     self._do_logn,
            'log':      self._do_log,
            'sqrt':     self._do_sqrt,
            'abs':      self._do_abs,
            'eq':       self._do_eq,
            'ne':       self._do_ne,
            'lt':       self._do_lt,
            'gt':       self._do_gt,
            'ge':       self._do_ge,
            'le':       self._do_le,
            'bitshift': self._do_bitshift,
            'dup':      self._do_dup,
            'count':    self._do_count,
            'clear':    self._do_clear,
            'copy':     self._do_copy,
            'index':    self._do_index,
            'roll':     self._do_roll,
            'if':       self._do_if,
            'ifelse':   self._do_ifelse,
            'repeat':   self._do_repeat,
            'loop':     self._do_loop,
            'exit':     self._do_exit,
            'for':      self._do_for,
            'or':       self._do_or,
            'and':      self._do_and,
            'xor':      self._do_xor,
            'not':      self._do_not,
            'currentpoint': self._do_currentpoint,
            'curveto':  self._do_curveto,
            'acurveto': self._do_acurveto,
            'scurveto': self._do_scurveto,
            'arc':      self._do_arc,
            'arcn':     self._do_arcn,
        }
        ps_room_flags = {
            'curved':   'c',
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
        ps_drawing_flags = {  # fill is also 'f'
            'cp':       'c',
            'closepath':'c',
        }
        for ps_token in self._each_ps_token(source):
            #print "compile: stack={0}, token={1}".format(self.stack, ps_token)
            if isinstance(ps_token, (int, float, list, tuple)):
                self.stack.append(ps_token)
            elif ps_token in ps_command_dispatch:
                object.append(ps_command_dispatch[ps_token]())
            elif ps_token in ps_internal_commands:
                ps_internal_commands[ps_token]()
            elif ps_token in ps_drawing_flags:
                if self.drawing_mode_list is None:
                    raise MapFileFormatError(ps_token + ' command encountered outside drawing mode.')
                self.drawing_flags.add(ps_drawing_flags[ps_token])
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
            elif ps_token == 'shaded':
                self._ps_shaded()
            elif ps_token == 'passageLength' or ps_token == 'passagelength':
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
                self.stack.append(re.sub(r'\\([0-7]{1,3}|\[.*?\]|-)', (lambda m: string_escape_translator(m.group(1))), ps_token)[1:-1])


            elif ps_token == 'np' or ps_token == 'newpath':
                if self.drawing_mode_list is not None:
                    raise MapFileFormatError('newpath command encountered before previous path completed.')
                self.drawing_flags.clear()
                self.drawing_mode_list = [
                    {
                        'type':   None, 
                        'points': None if self.current_point is None else [self.current_point]
                    }
                ]
            elif ps_token == 'ln' or ps_token == 'lineto':
                self._ps_lineto()
            elif ps_token== 'rln' or ps_token == 'rlineto':
                self._ps_rlineto()
            elif ps_token == 'lastpath':
                if self.drawing_mode_list is not None:
                    raise MapFileFormatError('lastpath command cannot be given inside another path')
                if self.last_drawing_mode_list is None:
                    raise MapFileFormatError("can't use lastpath command if there WAS no last path to re-use!")

                self.drawing_flags = self.last_drawing_flags
                self.drawing_mode_list = self.last_drawing_mode_list
                self.last_drawing_mode = None
                self.last_drawing_flags = None

            elif ps_token == 'stroke' or ps_token == 'fill':
                if self.drawing_mode_list is None:
                    raise MapFileFormatError('stroke command encountered outside drawing mode (need "newpath" first)')

                self.last_drawing_flags = self.drawing_flags.copy()
                self.last_drawing_mode_list = self.drawing_mode_list
                starting_point = None
                end_point = None

                if ps_token == 'fill':
                    self.drawing_flags.add('f')
                for line_path in self.drawing_mode_list:
                    if line_path['type'] is None or line_path['points'] is None or len(line_path['points']) < 2:
                        continue

                    coords = []
                    for x, y in line_path['points']:
                        coords.append(x)
                        coords.append(y)
                    if   line_path['type'] == 'p': type_flags = []
                    elif line_path['type'] == 'b': type_flags = ['b']
                    elif line_path['type'] == 's': type_flags = ['s']
                    elif line_path['type'] == 'a': 
                        #
                        # the arguments we receive for arcs are not just a list of points.
                        # they are:
                        # (x0, y0), (xc, yc), (radius, None), (start, end), (x1, y1), (x2, y2)
                        #   0   1     2   3       4      5       6     7     8   9     10  11
                        # current pt, center,  radius,  ---,  angles of arc, start pt, end pt
                        #
                        type_flags = []
                        if len(coords) != 12:
                            raise InternalError('arc in drawing_mode_list has {0} value{1} (should be 12) at {2}'.format(
                                len(coords), ('' if len(coords) == 1 else 's'), line_path))
                        if coords[7]-coords[6] >= 360:
                            # full circle, use 'O' object type
                            object.append(['Of' if 'f' in self.drawing_flags else 'O', coords[2], coords[3], coords[4]])
                        else:
                            object.append(['Q'+''.join(sorted(list(self.drawing_flags))), 
                                [coords[2], coords[3], coords[4], coords[6], coords[7]]
                            ])

                        if starting_point is None:
                            starting_point = (coords[8], coords[9])
                        end_point = (coords[10], coords[11])
                        continue
                    else:
                        raise InternalError('drawing_mode_list object with invalid type "{0}" encountered in {1}'.format(line_path['type'], line_path))

                    object.append(['P'+''.join(sorted(list(self.drawing_flags) + type_flags)), coords])
                    if starting_point is None:
                        starting_point = (coords[0], coords[1])
                    end_point = (coords[-2], coords[-1])

                self.drawing_mode_list = None
                if 'c' in self.drawing_flags and starting_point is not None and end_point is not None and starting_point != end_point:
                    object.append(['P'+''.join(sorted(list(self.drawing_flags) + type_flags)), list(end_point + starting_point)])
                    self.current_point = starting_point

            else:
                raise MapFileFormatError('Unrecognized map drawing command "'+ ps_token + '".')

        self._stop_tokenizer()
        if self.stack:
            raise MapFileFormatError('Extra values in map definition with nowhere to go: ' + `self.stack`)
        if self.drawing_mode_list is not None:
            raise MapFileFormatError('Drawing path not completed (missing "stroke" or "fill"?)')
        return object

    @RequireArgs('arrow', 'cccc')
    def _ps_arrow(self):
        return ['V']+list(reversed([self.stack.pop() for i in range(4)]))

    #
    # trivial stuff
    #
    def _ps_txtf(self):  return ['Ft', 8]
    def _ps_rmnf(self):  return ['Fr', 6]
    def _ps_bk(self):    return ['C', 0, 0, 0]
    def _ps_gr(self):    return ['C', .5, .5, .5]
    def _ps_wh(self):    return ['C', 1, 1, 1]
    def _do_true(self):  self.stack.append(-1)
    def _do_false(self): self.stack.append(0)
    def _do_count(self): self.stack.append(len(self.stack))
    def _do_clear(self): self.stack = []

    def _do_currentpoint(self): 
        if self.current_point is None:
            raise MapFileFormatError('currentpoint: no current point set yet')
        self.stack.extend(self.current_point)

    @RequireArgs('and', 'ii')
    def _do_and(self):
        self.stack.append(int(self.stack.pop()) & int(self.stack.pop()))

    @RequireArgs('or', 'ii')
    def _do_or(self):
        self.stack.append(int(self.stack.pop()) | int(self.stack.pop()))

    @RequireArgs('xor', 'ii')
    def _do_xor(self):
        self.stack.append(int(self.stack.pop()) ^ int(self.stack.pop()))

    @RequireArgs('not', 'i')
    def _do_not(self):
        self.stack.append(~ int(self.stack.pop()))

    @RequireArgs('add', 'ff')
    def _do_add(self):
        self.stack.append(float(self.stack.pop()) + float(self.stack.pop()))

    @RequireArgs('sub', 'ff')
    def _do_sub(self):
        y = float(self.stack.pop())
        x = float(self.stack.pop())
        self.stack.append(x - y)

    @RequireArgs('mul', 'ff')
    def _do_mul(self):
        y = float(self.stack.pop())
        x = float(self.stack.pop())
        self.stack.append(x * y)

    @RequireArgs('div', 'ff')
    def _do_div(self):
        y = float(self.stack.pop())
        x = float(self.stack.pop())
        self.stack.append(x / y)

    @RequireArgs('idiv', 'ff')
    def _do_idiv(self):
        y = float(self.stack.pop())
        x = float(self.stack.pop())
        self.stack.append(x // y)

    @RequireArgs('neg', 'f')
    def _do_neg(self):
        x = float(self.stack.pop())
        self.stack.append(-x)

    @RequireArgs('mod', 'ff')
    def _do_mod(self):
        y = float(self.stack.pop())
        x = float(self.stack.pop())
        self.stack.append(x % y)

    @RequireArgs('abs', 'f')
    def _do_abs(self):
        self.stack[-1] = abs(float(self.stack[-1]))

    @RequireArgs('sqrt', 'f')
    def _do_sqrt(self):
        self.stack[-1] = math.sqrt(float(self.stack[-1]))

    @RequireArgs('floor', 'f')
    def _do_floor(self):
        self.stack[-1] = math.floor(float(self.stack[-1]))

    @RequireArgs('ceiling', 'f')
    def _do_ceiling(self):
        self.stack[-1] = math.ceil(float(self.stack[-1]))

    @RequireArgs('truncate', 'f')
    def _do_truncate(self):
        self.stack[-1] = int(self.stack[-1])

    @RequireArgs('log', 'f')
    def _do_log(self):
        self.stack[-1] = math.log10(self.stack[-1])

    @RequireArgs('logn', 'f')
    def _do_logn(self):
        self.stack[-1] = math.log(self.stack[-1])

    @RequireArgs('exp', 'ff')
    def _do_exp(self):
        exponent = float(self.stack.pop())
        base = float(self.stack.pop())
        self.stack.append(math.pow(base, exponent))

    @RequireArgs('atan', 'ff')
    def _do_atan(self):
        den = float(self.stack.pop())
        num = float(self.stack.pop())
        self.stack.append(math.degrees(math.atan2(num, den)) % 360)

    @RequireArgs('cos', 'f')
    def _do_cos(self):
        self.stack[-1] = math.cos(math.radians(float(self.stack[-1])))

    @RequireArgs('sin', 'f')
    def _do_sin(self):
        self.stack[-1] = math.sin(math.radians(float(self.stack[-1])))

    @RequireArgs('exch', 2)
    def _do_exch(self):
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    @RequireArgs('dup', 1)
    def _do_dup(self):
        self.stack.append(self.stack[-1])

    @RequireArgs('if', 'bx')
    def _do_if(self):
        body = self.stack.pop()
        condition = bool(self.stack.pop())
        if condition:
            self._tokenizer_push(body)

    @RequireArgs('ifelse', 'bxx')
    def _do_ifelse(self):
        body_else = self.stack.pop()
        body_if = self.stack.pop()
        condition = bool(self.stack.pop())
        if condition:
            self._tokenizer_push(body_if)
        else:
            self._tokenizer_push(body_else)

    @RequireArgs('repeat', 'ix')
    def _do_repeat(self):
        body = self.stack.pop()
        counter = int(self.stack.pop())
        self._tokenizer_push(body, counter)

    @RequireArgs('loop', 'x')
    def _do_loop(self):
        self._tokenizer_push(self.stack.pop(), self._LOOP_MAX+1) # nearly infinite! :)

    def _do_exit(self):
        try:
            self._tokenizer_pop(out_of_loop=True)
        except NoProcedureRunning:
            raise MapFileFormatError('exit command encountered outside a running loop context')

    @RequireArgs('for', 'fffx')
    def _do_for(self):
        body = self.stack.pop()
        maxv = float(self.stack.pop())
        step = float(self.stack.pop())
        minv = float(self.stack.pop())
        self._tokenizer_push(body, [minv, step, maxv])

    @RequireArgs('copy', 'i')
    def _do_copy(self):
        count = int(self.stack.pop())
        if len(self.stack) < count:
            raise MapFileFormatError('map definition command "copy" asked to copy {0} element{1} but only found {2}.'.format(
                count, ('' if count==1 else 's'), len(self.stack)))
        self.stack.extend(self.stack[-count:])

    @RequireArgs('roll', 'ii')
    def _do_roll(self):
        places = int(self.stack.pop())
        n = int(self.stack.pop())
        if n > 0:
            if len(self.stack) < n:
                raise MapFileFormatError('map definition command "roll" asked to move {0} element{1} but only found {2}.'.format(
                    n, ('' if n==1 else 's'), len(self.stack)))
            self.stack[-n:] = self.stack[-((places-1)%n)-1:] + self.stack[-n:-((places-1)%n)-1]
                    
    @RequireArgs('index', 'i')
    def _do_index(self):
        idx = int(self.stack.pop())
        if idx < 0:
            raise MapFileFormatError('map definition command "index" given negative index ({0}).'.format(idx))
        if len(self.stack) <= idx:
            raise MapFileFormatError('map definition command "index" given offset {0} in {1}-element stack'.format(
                idx, len(self.stack)))
        self.stack.append(self.stack[-(idx+1)])

    @RequireArgs('bitshift', 'ii')
    def _do_bitshift(self):
        places = int(self.stack.pop())
        bits = int(self.stack.pop())
        if   places < 0: self.stack.append(bits >> -places)
        elif places > 0: self.stack.append(bits << places)
        else:            self.stack.append(bits)

    @RequireArgs('eq', 2)
    def _do_eq(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(-1 if a == b else 0)

    @RequireArgs('ne', 2)
    def _do_ne(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(-1 if a != b else 0)

    @RequireArgs('lt', 2)
    def _do_lt(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(-1 if a < b else 0)

    @RequireArgs('gt', 2)
    def _do_gt(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(-1 if a > b else 0)

    @RequireArgs('le', 2)
    def _do_le(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(-1 if a <= b else 0)

    @RequireArgs('ge', 2)
    def _do_ge(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(-1 if a >= b else 0)

    @RequireArgs('moveto', 'cc')
    def _ps_moveto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        self._do_moveto(x, y)

    @RequireArgs('rmoveto', 'oo')
    def _ps_rmoveto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        if self.current_point is None:
            raise MapFileFormatError('rmoveto: no current point to move FROM.')

        self._do_moveto(self.current_point[0] + x, self.current_point[1] + y)

    def _do_moveto(self, x, y):
        self.current_point = (x, y)
        if self.drawing_mode_list is not None:
            if self.drawing_mode_list[-1]['points'] is None or len(self.drawing_mode_list[-1]['points']) < 2:
                # if we hadn't really drawn anything yet, just replace old location
                self.drawing_mode_list[-1]['points'] = [self.current_point]
            else:
                # otherwise, push previous set of coordinates and start a new set from here...
                self.drawing_mode_list.append({
                    'type':   None, 
                    'points': [self.current_point]
                })

    @RequireArgs('arc', 'ccdff')
    def _do_arc(self):
        end_degrees = float(self.stack.pop())
        start_degrees = float(self.stack.pop())
        radius = float(self.stack.pop())
        center_y = self.stack.pop()
        center_x = self.stack.pop()

        while start_degrees > end_degrees:
            end_degrees += 360

        x1 = radius*math.cos(math.radians(start_degrees)) + center_x
        y1 = radius*math.sin(math.radians(start_degrees)) + center_y
        x2 = radius*math.cos(math.radians(end_degrees)) + center_x
        y2 = radius*math.sin(math.radians(end_degrees)) + center_y

        # connect start of arc to current point if any
        if self.current_point is not None:
            self._append_path_coords('arc', 'p', [(x1,y1)])
        else:
            self.current_point = (x1, y1)
        self._append_path_coords('arc', 'a', [(center_x, center_y), (radius, None), (start_degrees, end_degrees), (x1, y1), (x2, y2)], isolate=True)

    @RequireArgs('arcn', 'ccdff')
    def _do_arcn(self):
        end_degrees = float(self.stack.pop())
        start_degrees = float(self.stack.pop())
        radius = float(self.stack.pop())
        center_y = self.stack.pop()
        center_x = self.stack.pop()

        while end_degrees > start_degrees:
            end_degrees -= 360

        x1 = radius*math.cos(math.radians(start_degrees)) + center_x
        y1 = radius*math.sin(math.radians(start_degrees)) + center_y
        x2 = radius*math.cos(math.radians(end_degrees)) + center_x
        y2 = radius*math.sin(math.radians(end_degrees)) + center_y

        # connect start of arc to current point if any
        if self.current_point is not None:
            self._append_path_coords('arc', 'p', [(x1,y1)])
        else:
            self.current_point = (x1, y1)
        self._append_path_coords('arc', 'a', [(center_x, center_y), (radius, None), (end_degrees, start_degrees), (x1, y1), (x2, y2)], isolate=True)


    @RequireArgs('acurveto', 'p')
    def _do_acurveto(self):
        pointlist = self.stack.pop()
        if len(pointlist) < 4:
            raise MapFileFormatError('acurveto requires at least 2 points in the list')
        self._append_path_coords('acurveto', 'b', zip(pointlist[0::2], pointlist[1::2]), isolate=True)

    @RequireArgs('scurveto', 'p')
    def _do_scurveto(self):
        pointlist = self.stack.pop()
        if len(pointlist) < 2:
            raise MapFileFormatError('scurveto requires at least 1 point in the list')
        self._append_path_coords('scurveto', 's', zip(pointlist[0::2], pointlist[1::2]), isolate=True)

    @RequireArgs('curveto', 'cccccc')
    def _do_curveto(self):
        y3 = self.stack.pop()
        x3 = self.stack.pop()
        y2 = self.stack.pop()
        x2 = self.stack.pop()
        y1 = self.stack.pop()
        x1 = self.stack.pop()
        self._append_path_coords('curveto', 'b', [(x1, y1), (x2, y2), (x3, y3)], isolate=True)

    @RequireArgs('lineto', 'cc')
    def _ps_lineto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        self._do_lineto(x, y)

    @RequireArgs('rlineto', 'oo')
    def _ps_rlineto(self):
        y = self.stack.pop()
        x = self.stack.pop()
        if self.current_point is None:
            raise MapFileFormatError('rlineto: no current point to draw FROM.')

        self._do_lineto(self.current_point[0] + x, self.current_point[1] + y)

    def _do_lineto(self, x, y):
        self._append_path_coords('[r]lineto', 'p', [(x,y)])

    def _append_path_coords(self, cmdname, dtype, pointlist, isolate=False, current=None):
        #print "_append_path_coords: {0}, {1}, {2}, {3}".format(cmdname, dtype, pointlist, isolate)
        if self.drawing_mode_list is None:
            raise MapFileFormatError('{0} command encountered outside drawing mode (need "newpath" first)'.format(cmdname))

        if self.current_point is None:
            raise MapFileFormatError('Trying to append a {0}-type point list ({1}) to the drawing path with no current point defined yet (missing a "mv" at the start of the path?)'.format(dtype, pointlist))

        if isolate:
            self.drawing_mode_list.extend([
                {
                    'type':   dtype,
                    'points': [self.current_point] + pointlist
                },
                {
                    'type':   None,
                    'points': [pointlist[-1]]
                }
            ])
        elif self.drawing_mode_list[-1]['type'] != dtype:
            self.drawing_mode_list.append({
                'type':   dtype,
                'points': [self.current_point] + pointlist
            })
        else:
            self.drawing_mode_list[-1]['points'].extend(pointlist)

        self.current_point = current if current is not None else pointlist[-1]

    @RequireArgs('ss', 'd')
    def _ps_ss(self):   return ['Fs', self.stack.pop()]

    @RequireArgs('tt', 'd')
    def _ps_tt(self):   return ['FT', self.stack.pop()]

    @RequireArgs('bf', 'd')
    def _ps_bf(self):   return ['Fb', self.stack.pop()]

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
        return ['B']+list(reversed([self.stack.pop() for i in range(4)]))

    @RequireArgs('__test__', 'd')
    def _ps__test__(self):
        count = self.stack.pop()
        return ['_T']+list(reversed([self.stack.pop() for i in range(count)]))

    @RequireArgs('boxnum', 'scc')
    def _ps_boxnum(self):
        return ['N']+list(reversed([self.stack.pop() for i in range(2)]))+[self.stack.pop()]

    @RequireArgs('Clump1', 'cc')
    def _ps_clump1(self):
        return ['Tc']+list(reversed([self.stack.pop() for i in range(2)]))

    @RequireArgs('Clump2', 'cc')
    def _ps_clump2(self):
        return ['Tc2']+list(reversed([self.stack.pop() for i in range(2)]))

    @RequireArgs('colorbox', 'ccddkkk')
    def _ps_colorbox(self):
        return ['A']+list(reversed([self.stack.pop() for i in range(7)]))

    @RequireArgs('dotmark', 'ccd')
    def _ps_dotmark(self):
        return ['Of']+list(reversed([self.stack.pop() for i in range(3)]))

    @RequireArgs('graphic', 'ccdds')
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

    @RequireArgs('passagelength', 'd')
    def _ps_passage_length(self):
        self.exit_length = self.stack.pop()

    @RequireArgs('shaded', 'k')
    def _ps_shaded(self):
        self.room_shade = self.stack.pop()

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
        return ['A']+list(reversed([self.stack.pop() for i in range(4)]))+[color]*3

    @RequireArgs('show', 's')
    def _ps_show_text(self):
        if self.current_point is None:
            raise MapFileFormatError('show: no current point defined (missing a "mv" perhaps?)')
        return ['S', self.current_point[0], self.current_point[1], self.stack.pop()]

    @RequireArgs('Tree1', 'cc')
    def _ps_tree1(self):
        return ['T']+list(reversed([self.stack.pop() for i in range(2)]))

    @RequireArgs('Tree2', 'cc')
    def _ps_tree2(self):
        return ['T2']+list(reversed([self.stack.pop() for i in range(2)]))

    #
    # PostScript input tokenizer
    #

    def _start_tokenizer(self):
        "Initialize the tokenizer and get ready to read source lines."
        self._diversion = []
        self._token_input_stack = []

    def _stop_tokenizer(self):
        "Shut down tokenizer, raise exceptions if left in an odd state."
        if len(self._diversion) != 0:
            raise MapFileFormatError('Unterminated procedure block ("{" without matching "}")')
        if len(self._token_input_stack) != 0:
            raise InternalError('Tokenizer stopped inside procedure block!')

    def _tokenizer_push(self, block, count=None):
        '''Push a code block onto the tokenizer's input stream.  Further tokens will
        come from this block until it's been popped or run all the way through.'''
        if count is None:
            # This just means "not a looping construct"
            self._token_input_stack.append([0, None, 0, block])
        elif isinstance(count, list):
            # range loop: list is [min, step, max]
            # we add current counter to that control and insert into queue
            control = count[0:3] + [count[0]]  # initialized for first pass
            if control[0] <= control[2]:
                self._token_input_stack.append([0, control, 0, block])
                self.stack.append(control[3])  # start of 1st iter: push current value
        elif count > 0:
            self._token_input_stack.append([0, count-1, 0, block])

    def _tokenizer_pop(self, out_of_loop=False):
        if len(self._token_input_stack) == 0:
            raise NoProcedureRunning('Tokenizer popped empty stack!')

        while self._token_input_stack:
            context = self._token_input_stack[-1][1]
            #print "tokenizer_pop({0}): stack={1}, ctx={2}".format(out_of_loop, self._token_input_stack, context)
            self._token_input_stack.pop()
            if not out_of_loop or context is not None:
                #print "-STOP: stack={1}, ctx={2}".format(out_of_loop, self._token_input_stack, context)
                break
        else:
            raise MapFileFormatError('Loop termination (i.e. exit) encountered outside any active loop context.')

    def _each_ps_token(self, source):
        r'''Generate a list of PostScript-style code tokens from input source string.

        Strings are one token: '(...)' with \ooo for octal character codes (we force
        \(, \), and \\ to \ooo equivalents but leave \[...] alone).

        otherwise each token is returned as a separate string value.  For example,
        _each_ps_token('(hello \(Hi!\))(world) 1 2 3 [1.0 2.0] foo bar') yields the sequence:
        ['(hello \050Hi!\051)', '(world)', 1, 2, 3, '[', 1.0, 2.0, ']', 'foo', 'bar']
        
        To support code blocks, the tokenizer batches up anything inside curly braces
        as a single item in the token list, so:
           '1 2 { 3 4 5 } 6 7'  is fed to the compiler as [1, 2, [3, 4, 5], 6, 7]
           '1 {2 3 {4 5}6}7'    is fed to the compiler as [1, [2, 3, [4, 5], 6], 7]
        '''
        
        source = source.replace(r'\\', r'\134').replace(r'\(', r'\050').replace(r'\)', r'\051')
        ignoring_comment = False
        token_list = re.split(r'(\n|[ \t]+|[][{}]|\(.*?\))', source)

        while self._token_input_stack or token_list:
            if self._token_input_stack:
                # executable content pushed back to us to re-submit to compiler
                # _token_input_stack is a list of running procedure levels, and
                # each element of that is a list of four elements: [pc, count, iter, block]
                # where block is a token list previously digested here, 
                # iter is the number of iterations taken so far,
                # count is the number of future iterations remaining for the block, and 
                # pc is the index of the next token to yield from that block.
                pc, remaining, so_far, block = self._token_input_stack[-1]
                if pc >= len(block):
                    # the procedure has run off the end.  stop it now.
                    if so_far >= self._LOOP_MAX:
                        raise InfiniteLoopError('Loop executed terminated after {0} iterations'.format(so_far))

                    if isinstance(remaining, list):             # ranged loop: check parameters
                        remaining[3] += remaining[1]            #   increment loop counter
                        if remaining[3] > remaining[2]:         #   exceeded max value? stop
                            self._tokenizer_pop()
                            continue

                        self.stack.append(remaining[3])         #   push current value
                        pc = self._token_input_stack[-1][0] = 0     #   rewind PC to start of block again
                        self._token_input_stack[-1][2] += 1         #   increment iteration count for this block

                    elif remaining is not None and remaining > 0:   # IF we can continue again...
                        pc = self._token_input_stack[-1][0] = 0     #   rewind PC to start of block again
                        self._token_input_stack[-1][2] += 1         #   increment iteration count for this block
                        self._token_input_stack[-1][1] -= 1         #   decrement number of iterations remaining
                    else:                                           # ELSE...
                        self._tokenizer_pop()                       #   dequeue block and uplevel
                        continue

                self._token_input_stack[-1][0] += 1     # bump PC for next pass
                yield block[pc]
                continue

            # nothing on the stack, so grab the next source code token
            token = token_list.pop(0)

            if token.startswith('%'):
                ignoring_comment=True
                continue

            if ignoring_comment:
                if token == '\n':
                    ignoring_comment=False
                continue

            # maybe it's an int of an explicit base?
            m = self._INT_BASE.match(token)
            if m:
                try:
                    result = int(m.group('value'), int(m.group('base')))
                except ValueError as err:
                    raise MapFileFormatError('Invalid numeric constant "{0}": {1}'.format(token, err))
            else:
                if token.strip() == '':
                    continue
                try:
                    result =  int(token)        # try converting to integer if we can
                except:
                    try:
                        result = float(token)  # try converting to float if we can
                    except:
                        result = token         # punt

            if token == '{':
                self._diversion.append([])
                continue

            elif token == '}':
                if len(self._diversion) == 0:
                    raise MapFileFormatError('too many } braces in map definition')
                result = self._diversion.pop()

            if len(self._diversion) > 0:
                self._diversion[-1].append(result)
            else:
                yield result

class PostScriptMapSource (MapSource):
    '''Variation of map representation where the room and page data
    are raw PostScript strings instead of token lists'''

    def compile(self, source):
        "Compile source string -> PostScript string"
        return [source]


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
# A x y h w r g b               colorbox/shadebox
# B x y h w                     box
# C r g b                       color/bk/gr/wh/sg
# D [...] offset                sd
# F[biorstrtT] pts              bf/txtf/rmnf/ss/tt/it/sl
# G x y Sx|0 Sy|0 data          DrawGIFImage
# L w                           lw
# M[awdop] [x1 y1 ... xn yn]    maze*
# P[cf] [x1 y1 x2 y2 ... xn yn] draw polygon (from np...stroke) [f=fill, c=closed]
# R[] x y h|R w|r lbl1 lbl2 [...] [round-]room
# S x y text                    show
# T[c2] x y                     tree/clump


def string_escape_translator(code):
    r"given a special character code (e.g., the 'n' or '123' part of '\n' or '\123'), return the character it represents."

    special_codes = {
                        '[/c]': 0242,   # cents
                        '[S]':  0247,   # section
                        '[``]': 0252,   # open " quotes
                        '[<<]': 0253,   # open << quotes
                        '[-]':  0261,   # en-dash
                        '-':    0261,   # minus
                        '[+]':  0262,   # dagger
                        '[++]': 0263,   # double dagger
                        '[P]':  0266,   # paragraph (pilcrow)
                        '[*]':  0267,   # bullet
                        "['']": 0272,   # close " quotes
                        '[>>]': 0273,   # close >> quotes
                        '[--]': 0320,   # em-dash
                        '[AE]': 0341,   # AE ligature
                        '[ae]': 0361,   # ae ligature
    }

    if code in special_codes:
        return chr(special_codes[code])

    try:
        ch = int(code, 8)
    except:
        raise MapFileFormatError(r'Invalid string escape code "\{0}".'.format(code))

    if 32 <= ch < 127 or ch in special_codes.values():
        return chr(ch)

    raise MapFileFormatError(r'Invalid string escape code "\{0}" (out of allowed range of character codes).'.format(code))

# state includes everything -- line width, scale, rotation, translation...
