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
# <text> <text> <x> <y>  stdr   [<room-opts>] round-room [<passages>] [<doors>]
# '[' <x> <y> ... ']' [<room-opts>] maze(room|area|wall)
# np <drawing-cmd>* [cp] (stroke|fill)
# <x1> <y1> <x2> <y2> arrow
# <x> <y> <w> <h> box
# <x> <y> <w> <h> <shade> shadebox
# <x> <y> <w> <h> <r> <g> <b> colorbox
# <text> <x> <y> Boxnum
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
# <drawing-cmd> ::= <x> <y> mv
#                 | <x> <y> ln
#                 | <dx> <dy> rmv
#                 | <dx> <dy> rln
#                 | <x> <y> <r> <start> <end> arc
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

class MapFileFormatError (Exception): 
    '''The map source file contains a syntax or other formatting error
    and cannot be processed further.'''

class MapSource (object):
    '''The Ragnarok Magic Map as described in RRFC42 and RRFC46.
    This object class understands the map file format and can
    render images of the map.'''

    _IGNORE_LINE= re.compile(r'^#|^\s*$')
    _FIELD_CONT = re.compile(r'^\s+(?P<moretext>\S.*?)\s*$')
    _FIELD_DECL = re.compile(r'^(?P<tag>\w+)\s*:\s*(?P<value>.*?)\s*')


    def _each_record(self, input_file):
        "Scan file for record blocks, generating record dictionaries for each found."

        current_record = {}
        current_tag = None

        for line in input_file:
            #
            # Strip comments and blank lines
            #
            if MagicMap._IGNORE_LINE.match(line):
                continue
            #
            # Recognize beginning of a field (possibly
            # a new record block)
            #
            decl = MagicMap._FIELD_DECL.match(line)
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
                cont = MagicMap._FIELD_CONT.match(line)
                if cont:
                    if current_tag is None:
                        raise MapFileFormatError("Continuation line in map file outside containing record block: "+cont.group('moretext'))
                    current_record[current_tag] += ' ' + cont.group('moretext')
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


#    def add_from_source(self, input_file):
#        "Add rooms and places to this file from a map source file."
#
#        for record in self._each_record(input_file):
#            for required_field in 'room', 'page':
#                if required_field not in record:
#                    raise MapFileFormatError('Map source file record does not contain a "'
#                            +required_field+'" field: ' + `record`)
#        #
#        # set up containing page first
#        #
#        page = self.get_page(record['page'])
#
#        if 'bg' in record:
#            if page.bg:
#                # XXX warn that multiple rooms contribute to this page bg
#            page.bg.append(self.compile_map(record['bg']))
#
#        if 'realm' in record:
#            if page.realm and record['realm'] != page.realm:
#                # XXX warn that room overrides page realm name
#            page.realm = record['realm']
#
#        if 'orient' in record:
#            if 'land' in record['orient']:
#                if page.orient is not None and page.orient != MapPage.LANDSCAPE:
#                    raise MapFileFormatError('Page '+page.page+' explicitly declared PORTRAIT before '+record['room']+' also declared it LANDSCAPE.')
#                    page.orient = MapPage.LANDSCAPE
#            else:
#                if page.orient is not None and page.orient != MapPage.PORTRAIT:
#                    raise MapFileFormatError('Page '+page.page+' explicitly declared LANDSCAPE before '+record['room']+' also declared it PORTRAIT.')
#                    page.orient = MapPage.PORTRAIT
#
#    def get_page(self, page_id):
#        "Get page by id (coerced to integer) and return it (creating one if needed)"
#
#        i = int(page_id)
#        if i not in self.pages:
#            self.pages[i] = MapPage(i)
#        return self.pages[i]
#
    def compile(self, source):
        pass
#    def compile_map(self, source):
#        "Compile source string -> list of encoded element definitions"
#        object = []
#
#        #
#        # The source used to be PostScript commands.  We keep the same
#        # general format but proscribe a small list of commands which
#        # are available and forbid random PS.  We'll interpret these
#        # commands in the source string and emit a list of individual
#        # graphic object definitions we can more quickly parse later.
#        #
#        # This has the main benefit of revealing syntax errors before the
#        # end user tries to see their map.
#        #
#        # (...) push string value, interpreting \ escapes.
#        # otherwise, space-delimited strings are interpreted:
#        # if it looks like a numeric constant, push it.
#        # some other symbols are pushed, others are executed (which may
#        # pop their arguments)
#        #
#        for ps_token in self._each_ps_token(source):

    def _each_ps_token(self, source):
        '''Generate a list of PostScript-style code tokens from input source string.

        Strings are one token: '(...)' with \ooo for octal character codes (we force
        \(, \), and \\ to \ooo equivalents).

        otherwise each token is returned as a separate string value.  For example,
        _each_ps_token('(hello \(Hi!\))(world) 1 2 3 [1.0 2.0] foo bar') yields the sequence:
        ['(hello \050Hi!\051)', '(world)', 1, 2, 3, '[', 1.0, 2.0, ']', 'foo', 'bar']'''
        
        source = source.replace(r'\\', r'\134').replace(r'\(', r'\050').replace(r'\)', r'\051')
        for token in re.split(r'(\s+|[][]|\(.*?\))', source):
            if token.strip() == '':
                continue
            try:
                yield float(token)  # try converting to float if we can
            except:
                yield token

#class MapPage (object):
#    PORTRAIT = 0
#    LANDSCAPE= 1
#
#    def __init__(self, id):
#        self.page = id
#        self.realm = None
#        self.orient = None
#        self.bg = []
#        self.rooms = {}
