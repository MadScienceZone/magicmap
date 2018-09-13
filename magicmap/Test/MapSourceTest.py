# vi:set ai sm nu ts=4 sw=4 expandtab fileencoding=utf-8:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: Magic Map Source Files
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

import unittest
import io

import RagnarokMUD.MagicMapper.MapPage
from RagnarokMUD.MagicMapper.MapSource import MapSource, MapFileFormatError, DuplicateRoomError, InfiniteLoopError, InvalidRoomPath, IllegalCreatorReference, MapDefSymbol

class MapSourceTest (unittest.TestCase):
    def test_ps_tokenizer(self):
        self._test_tokenizer((
                ('(hello)(world)', ['(hello)', '(world)']),
                (r'(This string \(yes, THIS one\) has embedded parens)',
                    [r'(This string \050yes, THIS one\051 has embedded parens)']),
                ('(a) (b) 1 2 3', ['(a)', '(b)', 1.0, 2.0, 3.0]),
                ('(a)(b)1 2 3',   ['(a)', '(b)', 1.0, 2.0, 3.0]),
                ('[1 2 3 4][5 6]x y z', 
                    ['[', 1.0, 2.0, 3.0, 4.0, ']', '[', 5.0, 6.0, ']', 'x', 'y', 'z']),
                ('1 2 4.5 1.123', [1.0, 2.0, 4.5, 1.123]),
        ))

    def _test_tokenizer(self, se_list):
        for source, expected in se_list:
            self.ms._start_tokenizer()
            self.assertEqual([i for i in self.ms._each_ps_token(source)], expected)
            self.ms._stop_tokenizer()

    def test_ps_tokenizer_with_embedded_delims(self):
        self._test_tokenizer((
            ('(this string [has brackets])1(inside {and braces})5', ['(this string [has brackets])', 1, '(inside {and braces})', 5]),
            ('(this string [starts)(but this ends] brackets)', ['(this string [starts)', '(but this ends] brackets)']),
        ))

    def test_ps_function_errors_in_tokenizer(self):
        def run_tok(source):
            self.ms._start_tokenizer()
            l = [i for i in self.ms._each_ps_token(source)]
            self.ms._stop_tokenizer()

        for ex, source in (
            (MapFileFormatError, '1{2{3 4}'),
            (MapFileFormatError, '1{2{3{4}}5}6}'),
        ):
            self.assertRaises(ex, run_tok, source)


    def test_ps_function_tokenizer(self):
        self._test_tokenizer((
                ('(hello)(world){(embedded string)}1 2 3', ['(hello)', '(world)', ['(embedded string)'], 1, 2, 3]),
                ('1 2 {3 4 5} 6 {7 {8{9} 10} 11 12}', [1, 2, [3, 4, 5], 6, [7, [8, [9], 10], 11, 12]]),
        ))
    
    def setUp(self):
        self.ms = MapSource()

    def tearDown(self):
        self.ms = None

    def _test_compiler(self, se_list):
        "Given a list of (source, expected_result_list) tuples, try compiling each one and comparing the resulting list from the compiler with the expected value."
        for source, expected in se_list:
            self.assertEqual(self.ms.compile(source, allow_test=True), expected)

    def _test_compiler_symbols(self, se_list, persistent=False):
        "Given a list of (source, expected_result_list, locals, globals) tuples, try compiling each one and comparing the resulting list from the compiler, as well as testing the resulting dictionaries of local and global symbols."
        myglobs = {}
        for source, expected, localdict, globaldict in se_list:
            if not persistent:
                myglobs = {}
            res = self.ms.compile(source, allow_test=True, global_symbols=myglobs)
            self.assertEqual(res, expected, msg="result of {0} was {1}, expected {2}".format(
                source, res, expected))
            self.assertEqual(self.ms._local_symbols, localdict, msg="{0}: locals {1}, expected {2}".format(
                source, self.ms._local_symbols, localdict))
            self.assertEqual(myglobs, globaldict, msg="{0}: globals {1}, expected {2}".format(
                source, myglobs, globaldict))

    def _test_float_lists(self, a, x, msg):
        "Recursively test float values"
        if isinstance(x, (list,tuple)):
            self.assertEqual(len(x), len(a), "Length of lists unequal: actual={0} expected={1} in {2}".format(a, x, msg))
            for aa, xx in zip(a,x):
                self._test_float_lists(aa, xx, msg+'>')
        elif isinstance(x, float):
            self.assertAlmostEqual(a, x, 5, "{0} != {1} (float compare) in {2}".format(a, x, msg))
        else:
            self.assertEqual(a, x, "{0} != {1} in {2}".format(a, x, msg))

    def _test_compiler_float_values(self, se_list):
        '''Like _test_compiler(), but each value is interpreted separately rather than comparing the list.  
        Floats are compared for near-equality.  Note, however, that this is a SHALLOW scan.  In the
        result list [1, 2, [3, 4]], comparisons are made for the numeric values 1 and 2, and object
        "list of [3, 4]" against the actual value returned.'''

        for source, expected_list in se_list:
            actual_list = self.ms.compile(source, allow_test=True)
            self._test_float_lists(actual_list, expected_list, "{0}->{2} vs {1}".format(source, expected_list, actual_list))
#            self.failUnlessEqual(len(actual_list), len(expected_list), 'bad result size {0} vs. {1}'.format(
#                actual_list, expected_list))
#            for actual, expected in zip(actual_list, expected_list):
#                for r, ex in zip(actual, expected):
#                    if isinstance(ex, float):
#                        self.failUnlessAlmostEqual(r, ex, 6, "{0} != {1} in result set {2}->{3}".format(r, ex, source, actual_list))
#                    else:
#                        self.failUnlessEqual(r, ex, "{0} != {1} in result set {2}->{3}".format(r, ex, source, actual_list))

    def _test_compiler_floats(self, se_list):
        '''Like _test_compiler(), but only looks at first returned object.  Floating-point results are compared for near-equality, however.
        This MUST be used with the __test__ directive; the result list is expected to be [['_T', <return-values-here>]].  The type of the
        expected value (float or not) determines whether exact or near matching is done for that value.'''

        for source, expected in se_list:
            test_result = self.ms.compile(source, allow_test=True)[0]
            self.assertEqual(test_result[0], '_T')
            self.assertEqual(len(test_result)-1, len(expected), 'bad result size {0} vs. {1}'.format(
                test_result, expected))
            for r, ex in zip(test_result[1:], expected):
                if isinstance(ex, float):
                    self.assertAlmostEqual(r, ex, 6, "{0} != {1} in result set {2}->{3}".format(r, ex, source, test_result))
                else:
                    self.assertEqual(r,ex, "{0} != {1} in result set {2}->{3}".format(r, ex, source, test_result))

    def test_compile_vectors(self):
        self._test_compiler((
                ('100 200 230 444 arrow',            [['V', 100, 200, 230, 444]]),
                ('1 2 3 pop 4 5 arrow',              [['V', 1, 2, 4, 5]]),
        ))

    def test_compile_box(self):
        self._test_compiler((
                ('50 60 std box',                    [['B', 50, 60, 50, 20]]),
        ))

    def test_compile_area(self):
        self._test_compiler((
                ('11.2 22.3 33.4 44.5 .25 shadebox', [['A', 11.2, 22.3, 33.4, 44.5, .25, .25, .25]]),
                ('11 22 33 44 1 .5 0 colorbox',      [['A', 11, 22, 33, 44, 1, .5, 0]]),
        ))

    def test_compile_boxnum(self):
        self._test_compiler((
                ('(#27)20 700 boxnum',               [['N', 20, 700, '#27']]),
                (r'(M\2613) 15 20 boxnum',           [['N', 15, 20, 'M–3']]),
                (r'(f\(x\)) 11 22 boxnum',           [['N', 11, 22, 'f(x)']]),
        ))

    def test_compile_maze(self):
        self._test_compiler((
                ('[1 2 3 4 5 6 7 8]mazewall',        [['Mw', [1,2, 3,4, 5,6, 7,8]]]),
                ('[1 2 3 4] dark mazewall',          [['Mwd', [1,2,3,4]]]),
                ('[1 2 3 4] proto mazewall',         [['Mwp', [1,2,3,4]]]),
                ('[1 2 3 4] outdoor mazewall',       [['Mwo', [1,2,3,4]]]),
                ('[1 2 3 4] dark proto mazewall',    [['Mwdp', [1,2,3,4]]]),
                ('[1 2 3 4] proto dark mazewall',    [['Mwdp', [1,2,3,4]]]),
                ('[1 2 3 4] outdoor proto mazewall', [['Mwop', [1,2,3,4]]]),
                ('[1 2 3 4] outdoor dark proto mazewall', 
                                                     [['Mwdop', [1,2,3,4]]]),
                ('[1 2 3 4] proto outdoor dark proto mazewall[5 6]mazewall', 
                                                     [['Mwdop', [1,2,3,4]], ['Mw', [5,6]]]),
                ('[1 2 3 4] outdoor proto mazearea', [['Maop', [1,2,3,4]]]),
                ('[1 2 3 4] outdoor mazeroom',       [['Mawo', [1,2,3,4]]]),
                ('[1 2 3 4] outdoor curved mazeroom', [['Mawco', [1,2,3,4]]]),
        ))

    def test_compile_dotmark(self):
        self._test_compiler((
                ('50 60 2 dotmark',                  [['Of', 50, 60, 2]]),
        ))

    def test_compile_trees(self):
        self._test_compiler((
                ('50 60 Tree1',                      [['T', 50, 60]]),
                ('50 60 Tree2',                      [['T2', 50, 60]]),
                ('50 60 Clump1',                     [['Tc', 50, 60]]),
                ('50 60 Clump2',                     [['Tc2', 50, 60]]),
        ))

    def test_compile_image(self):
        self._test_compiler((
                #('10 20 0 0 (R0lGODlhFAAUAKU7AAAAAAICAgUFBQoKChkZGSkpKTIyMkFBQUJCQrc1RLg1RFJSUldXV7o8S7s/TVtbW7o9hbk+hbo+hV5awIZPvYZPvrxFiohRv2ZmZrdGu7dGvLdHu2hoaLlKvcBPkHNzc8ppaX9/f8trbMVpyM51dc93d9B7e62G0piYmKel3ee5v8bF6dnH6s/Pz+HMzOvL7O3O4O/S1fDW5ebm5unp6ebr9vfr+Pry8vn3/P7+/////199wV99wV99wV99wV99wSH+EUNyZWF0ZWQgd2l0aCBHSU1QACwAAAAAFAAUAAAGpUAG4OAylY5IEWhJuj0GD4CUo2ooEoosVuGIoaSBgxQQknkgkogEErHAQuMCjTMO2UaZzEbTecGlCC06On9kOCcUFRcshRgzg4OFITkpEyuSkJmNMzWYmZpjCx91n6WFpKWlKAFjH6mppwuPr5CFrACytIR1KAJSubCovb+zoFIhmcO4xTMYqMm+yzozC8+fyrLOx7rKGAQAAii6g8MEKAbi4+ToQQA7) DrawGIFImage',                [['G', 10, 20, 0, 0, 'R0lGODlhFAAUAKU7AAAAAAICAgUFBQoKChkZGSkpKTIyMkFBQUJCQrc1RLg1RFJSUldXV7o8S7s/TVtbW7o9hbk+hbo+hV5awIZPvYZPvrxFiohRv2ZmZrdGu7dGvLdHu2hoaLlKvcBPkHNzc8ppaX9/f8trbMVpyM51dc93d9B7e62G0piYmKel3ee5v8bF6dnH6s/Pz+HMzOvL7O3O4O/S1fDW5ebm5unp6ebr9vfr+Pry8vn3/P7+/////199wV99wV99wV99wV99wSH+EUNyZWF0ZWQgd2l0aCBHSU1QACwAAAAAFAAUAAAGpUAG4OAylY5IEWhJuj0GD4CUo2ooEoosVuGIoaSBgxQQknkgkogEErHAQuMCjTMO2UaZzEbTecGlCC06On9kOCcUFRcshRgzg4OFITkpEyuSkJmNMzWYmZpjCx91n6WFpKWlKAFjH6mppwuPr5CFrACytIR1KAJSubCovb+zoFIhmcO4xTMYqMm+yzozC8+fyrLOx7rKGAQAAii6g8MEKAbi4+ToQQA7']]),
                ('10 20 50 40 (TestImageID12345) graphic', [['G', 10, 20, 50, 40, 'TestImageID12345']]),
        ))

    def test_compile_linewidth(self):
        self._test_compiler((
                ('13.6 lw',                          [['L', 13.6]]),
        ))

    def test_compile_dash(self):
        self._test_compiler((
                ('[15 10.5 3 2] 1.5 sd',             [['D', [15, 10.5, 3, 2], 1.5]]),
        ))

    def test_compile_show(self):
        self._test_compiler((
                ('222 333 mv(stuff at \(222,333\))show', [['S', 222, 333, 'stuff at (222,333)']]),
                ))

    def test_bad_compile_show(self):
        self.assertRaises(MapFileFormatError, self.ms.compile, '(some text) show')

    def test_compile_round_room(self):
        self._test_compiler((
                ('(a)(circle)10 20 50 round-room',          [['R', 10, 20, 'R', 50, 'a', 'circle', []]]),
                ('(a)(well)10 20 stdr dark round-room',     [['Rd', 10, 20, 'R', 30, 'a', 'well', []]]),
                ))

    def test_compile_room(self):
        self._test_compiler((
                ('(a)(room)10 20 std dark room',            [['Rd', 10, 20, 50, 20, 'a', 'room', []]]),
                ('(another)(one)30 40 31 32 outdoor room',  [['Ro', 30, 40, 31, 32, 'another', 'one', []]]),
                ('()() 11 22 std proto room',               [['Rp', 11, 22, 50, 20, '', '', []]]),
                ('()() 11 22 std proto outdoor room',       [['Rop', 11, 22, 50, 20, '', '', []]]),
                ('()() 11 22 std outdoor proto room',       [['Rop', 11, 22, 50, 20, '', '', []]]),
                ('()() 11 22 std outdoor dark proto room',  [['Rdop', 11, 22, 50, 20, '', '', []]]),
                ))

    def test_compile_passages(self):
        self._test_compiler((
                ('(aa)\t(bb)\t\t1 2 3 4 outdoor room north passage',
                                                            [['Ro', 1, 2, 3, 4, 'aa', 'bb', [['n', 20]]]]),
                ('(x)() 5 5 5 5 room northeast passage ()()1 1 1 1 room',
                                                            [['R',5,5,5,5,'x','', [['a', 20]]], ['R',1,1,1,1,'','',[]]]),
                ('()()0 0 0 0 proto room north passage south passage east passage',
                                                            [['Rp',0,0,0,0,'','', [['n', 20], ['s', 20], ['e', 20]]]]),
                ('(a)(a)1 2 3 4 dark room south (b)(b) 5 6 7 8 room north passage',
                                                            [['Rd',1,2,3,4,'a','a', []], ['R',5,6,7,8,'b','b', [['n',20]]]]),
                ('(gorilla)(gorilla) 6 6 6 6 outdoor dark room 37 passagelength north passage',
                                                            [['Rdo',6,6,6,6,'gorilla','gorilla', [['n',37]]]]),
                ('(gorilla)(gorilla) 6 6 6 6 outdoor dark room east passage 37 passageLength north passage south passage',
                                                            [['Rdo',6,6,6,6,'gorilla','gorilla', [['e', 20], ['n',37], ['s', 20]]]]),
                ('(a)(a)1 2 3 4 dark room south in passage (b)(b) 5 6 7 8 room out north passage special northwest passage south special offpage passage',
                                                            [['Rd',1,2,3,4,'a','a',[['si',20]]],['R',5,6,7,8,'b','b',[['no',20],['c!',20],['s!x',20]]]]),
                ))

    def test_compile_doors(self):
        self._test_compiler((
                ('(a)(b)6 5 4 3 room south passage south door', [['R',6,5,4,3,'a','b',[['sD', 20]]]]),
                ('(a)(b)6 5 4 3 room south door',           [['R',6,5,4,3,'a','b',[['sD', 0]]]]),
                ('(a)()100 100 100 100 room northeast passage south special passage northeast locked door',
                                                            [['R',100,100,100,100,'a','',[['aDL',20],['s!',20]]]]),
                ))

    def test_compile_colors(self):
        self._test_compiler((
                ('bk gr wh',                                [['C',0,0,0],['C',.5,.5,.5],['C',1,1,1]]),
                ('0 sg .25 sg .77 sg .1 .2 .3 color',       [['C',0,0,0],['C',.25,.25,.25],['C',.77,.77,.77],['C',.1,.2,.3]]),
                ))

    def test_compile_fonts(self):
        self._test_compiler((
                ('txtf rmnf 12 ss 13 tt 14 it 15 sl',       [['Ft',8],['Fr',6],['Fs',12],['FT',13],['Fi',14],['Fo',15]]),
                ('15.5 bf',                                 [['Fb', 15.5]]),
                ))

    def test_compile_rmove(self):
        self._test_compiler((
                ('12 34 moveto 10 20 rmoveto(at 22,54)show',[['S', 22, 54, 'at 22,54']]),
                ))

    def test_compile_polygon(self):
        self._test_compiler((
                ('np 0 0 mv 10 10 ln stroke',               [['P', [0, 0, 10, 10]]]),
                ('np 0 0 mv 0 10 ln 20 20 ln cp stroke',    [['Pc', [0,0,0,10,20,20]], ['Pc', [20,20,0,0]]]),
                ('np 0 0 mv 0 10 ln 20 20 ln cp fill',      [['Pcf', [0,0,0,10,20,20]], ['Pcf', [20,20,0,0]]]),
                ('np 0 0 moveto 0 10 ln 20 20 ln stroke',   [['P', [0,0,0,10,20,20]]]),
                ('np 10 12 mv 0 10 rln -5 15 rln stroke',   [['P', [10,12,10,22,5,37]]]),
                ))

    def test_compile_(self):
        self._test_compiler((
                ('np 11 22 mv 33 44 ln 50 50 rmv 10 10 rln stroke', [['P', [11,22, 33,44]], ['P', [83,94, 93,104]]]),
                ('np 11 22 mv 33 44 ln 50 50 rmv 10 10 rln fill', [['Pf', [11,22, 33,44]], ['Pf', [83,94, 93,104]]]),
                ))

    def test_ps_comments(self):
        self._test_compiler((('''
% This is a test
0 0 moveto %home
(hello)%greeting
show
100 100 mv (End) %stroke
show
''', [
    ['S', 0, 0, 'hello'],
    ['S', 100, 100, 'End']
]),))

            # GIF89a
    def test_bad_params(self):
        for exc, source in (
                (MapFileFormatError, '1 2 arrow'),
                (MapFileFormatError, '1 3 4 x arrow'),
                (ValueError,         '5000 1 1 1 arrow'),
                (MapFileFormatError, '1 4 5 5 gray50 shadebox'),
                (ValueError,         '1 3 4 4 12 shadebox'),
                (MapFileFormatError, '1 2 3 4 5 6 box'),
                (MapFileFormatError, '[1 2 3 4 5 6 7] mazewall'),
                (ValueError,         '[100 2000 3 4 5 6] mazewall'),
                (ValueError,         '-57.2 lw'),
                (MapFileFormatError, '(a)(a)1 2 3 4 dark room passage'),
                (MapFileFormatError, '(a)(a)1 2 3 4 dark room (b)(b) 5 6 7 8 room north east passage'),
                (MapFileFormatError, 'east passage'),
                (MapFileFormatError, '()()0 0 0 0 room north door south passage north passage'),
                (MapFileFormatError, '()()0 0 0 0 room north passage south passage north passage'),
        ):
            self.assertRaises(exc, self.ms.compile, source)

    def test_bad_ps_commands(self):
        for exc, source in (
                (MapFileFormatError, '1 2 3 sesame-street pop pop pop pop'),
                (MapFileFormatError, 'pop'),
                (MapFileFormatError, 'np 0 0 mv np 1 1 mv 2 2 ln stroke'),
                (MapFileFormatError, '1 1 ln'),
                (MapFileFormatError, 'np 0 0 mv 1 1 ln'),
                (MapFileFormatError, 'stroke'),
        ):
            self.assertRaises(exc, self.ms.compile, source)

    def test_record_parser(self):
        f = io.StringIO('''
#
# A test input source
#
room: /a/room/here
room: /another/room
page:12
room: /full/room
name: Full Room
page: 37
realm: Beeker's Test Factory
ref:   123 456
orient: portrait
map:   a b c d e
       f g h i j
       % a comment
       x y z z z
also: /a/b/c
      /d/e/f
bg:   x1 x2 x3 x4
''')
        for expected, actual in zip([
            {'room':'/a/room/here'},
            {'room':'/another/room', 'page':'12'},
            {'room':'/full/room', 'page':'37', 'realm':"Beeker's Test Factory",
                'orient':'portrait','map':'a b c d e\nf g h i j\n% a comment\nx y z z z',
                'ref':(123, 456),
                'also':'/a/b/c\n/d/e/f', 'bg':'x1 x2 x3 x4', 'name':'Full Room'}
        ], self.ms._each_record(f)):
            self.assertEqual(sorted(expected.keys()), sorted(actual.keys()))
            for k in expected:
                self.assertEqual(expected[k], actual[k])
        f.close()

    def test_inappropriate_continuation(self):
        for dupfield in 'room', 'name', 'page', 'realm', 'orient':
            f = io.StringIO('room: /a/b/c\n' + dupfield + ': first\n   second\n  third\n')
            def ff():
                list(self.ms._each_record(f))
            self.assertRaises(MapFileFormatError, ff)
            f.close()

    def test_incorrect_format(self):
        f = io.StringIO('room: whatever\nfoo bar\n')
        def ff():
            list(self.ms._each_record(f))
        self.assertRaises(MapFileFormatError,  ff)

    def test_duplicated_fields(self):
        f = io.StringIO('room: whatever\npage: 12\npage:13\n')
        def ff():
            list(self.ms._each_record(f))
        self.assertRaises(MapFileFormatError,  ff)

    def test_missing_required_field(self):
        f = io.StringIO('''
page: 12
room: outofplace
''')
        self.assertRaises(MapFileFormatError, MapSource, f)

        f = io.StringIO('''
room: another
realm: note no page number
''')
        self.assertRaises(MapFileFormatError, MapSource, f)

    def test_relative_path_with_no_creator(self):
        for name in 'relative-name', 'relative/path', '~/twiddle_path':
            self.assertRaises(InvalidRoomPath, MapSource, io.StringIO('''
room: '''+name+'''
page: 1
'''))

    def test_normalized_paths(self):
        for a,b in (
            ('/foo//bar//baz', 'foo/bar/baz'),
            ('/players/x/../a/b/c/../d', 'players/a/b/d')
        ):
            ms = MapSource(io.StringIO('''
room: '''+a+'''
page: 12
'''))
            self.assertTrue(b in ms.room_page, msg="{0} translated to {1} not {2}".format(
                a, list(ms.room_page.keys()), b))

    def test_relative_path_with_creator(self):
        for a,b in (
            ('relative-name', 'players/me/relative-name'),
            ('relative/path', 'players/me/relative/path'),
            ('~/twiddle_path','players/me/twiddle_path'),
            ('~me/twiddle_path','players/me/twiddle_path'),
            ('~them/twiddle_path','players/them/twiddle_path'),
            ('/absolute/path/to/file','absolute/path/to/file'),
        ):
            ms = MapSource()
            ms.add_from_file(io.StringIO('''
room: '''+a+'''
page: 1
'''), creator='me', enforce_creator=False)
            self.assertTrue(b in ms.pages[1].rooms, msg="{0} didn't translate to {1}, got {2}".format(a,b,list(ms.pages[1].rooms.keys())))
            
    def test_cross_realm_definition(self):
        for name in (
            '/players/aaa/path',
            '~aaa/path',
            '/room/base/path',
        ):
            ms = MapSource()
            self.assertRaises(IllegalCreatorReference, ms.add_from_file, io.StringIO('''
room: '''+name+'''
page: 2
'''), creator='bbb', enforce_creator=True)

    def test_base_realm_definition(self):
        for name in (
            '/players/aaa/path',
            '~aaa/path',
        ):
            ms = MapSource()
            self.assertRaises(IllegalCreatorReference, ms.add_from_file, io.StringIO('''
room: '''+name+'''
page: 2
'''), creator=None, enforce_creator=True)

    def test_realm_creator(self):
        for name, cname in (
            ('/players/aaa/path', 'aaa'),
            ('/players/bbb/path', 'bbb'),
            ('~ccc/path', 'ccc'),
            ('/room/foo/bar', 'Base World Map'),
        ):
            ms = MapSource(io.StringIO('''
room: '''+name+'''
page: 34
'''))
            self.assertEqual(ms.pages[34].creators[0], cname,
                msg="{0} creator(s) {1}, expected {2}".format(
                    name, ms.pages[34].creators, cname))


    def test_duplicate_room(self):
        self.assertRaises(DuplicateRoomError, MapSource, io.StringIO('''
room: ~x/one
page: 1

room: ~x/one
page: 2
'''))

    def test_reference_point_explicit(self):
        self.assertEqual(MapSource(io.StringIO('''
room: ~x/one
page: 1
ref:  123 456
map:  (foo)(bar)111 222 std room
''')).pages[1].rooms['players/x/one'].reference_point, (123, 456))

    def test_reference_point_room(self):
        self.assertEqual(MapSource(io.StringIO('''
room: ~x/one
page: 1
map:  (foo)(bar)100 200 std room
      (aaa)(bbb)333 444 std room
      555 666 2 dotmark
''')).pages[1].rooms['players/x/one'].reference_point, (125, 210))

    def test_reference_point_round(self):
        self.assertEqual(MapSource(io.StringIO('''
room: ~x/one
page: 1
map:  (foo)(bar)100 200 stdr round-room
      (aaa)(bbb)333 444 std room
      555 666 2 dotmark
''')).pages[1].rooms['players/x/one'].reference_point, (100, 200))

    def test_reference_point_dot(self):
        self.assertEqual(MapSource(io.StringIO('''
room: ~x/one
page: 1
map:  [1 2 3 4 5 6 7 8] mazeroom
      555 666 2 dotmark
''')).pages[1].rooms['players/x/one'].reference_point, (555,666))

    def test_get_page(self):
        ms = MapSource()
        p12 = ms.get_page(12)
        self.assertEqual(sorted(ms.pages.keys()), [12])
        self.assertTrue(ms.get_page(12) is p12)
        self.assertEqual(sorted(ms.pages.keys()), [12])
        self.assertEqual(p12.page, 12)
        p13 = ms.get_page('13')
        self.assertEqual(sorted(ms.pages.keys()), [12, 13])
        self.assertEqual(p13.page, 13)

    def test_get_page_bad_number(self):
        ms = MapSource()
        self.assertRaises(ValueError, ms.get_page, 'z')
        self.assertRaises(ValueError, ms.get_page, '10z')
        self.assertRaises(TypeError, ms.get_page, None)

    def test_load_file(self):
        with open('data/museum.map', 'r') as f:
            ms = MapSource(file=f)
        self.assertEqual(sorted(ms.pages.keys()), [5, 20])
        self.assertEqual(ms.pages[5].page, 5)
        self.assertEqual(ms.pages[20].page, 20)
        self.assertEqual(ms.pages[5].bg, [])
        self.assertEqual(ms.pages[20].bg, [
            ['Fi', 36],
            ['S', 0, 0, 'Museum Quest']
        ])
        self.assertEqual(ms.pages[20].orient, RagnarokMUD.MagicMapper.MapPage.PORTRAIT)
        self.assertEqual(ms.pages[5].orient, RagnarokMUD.MagicMapper.MapPage.LANDSCAPE)
        self.assertEqual(ms.pages[20].realm, "Aardvark's Museum--Gateway to Adventureland")
        self.assertEqual(ms.pages[5].realm, None)

        self.assertEqual(sorted(ms.pages[5].rooms.keys()), ['players/fizban/aardvark/entrance'])
        self.assertEqual(sorted(ms.pages[20].rooms.keys()), [
            'players/fizban/aardvark/china',
            'players/fizban/aardvark/egypt',
            'players/fizban/aardvark/india',
            'players/fizban/aardvark/prehistory',
            'players/fizban/aardvark/proto-south',
            'players/fizban/aardvark/rotunda',
            ])

        self.assertEqual(ms.room_page['players/fizban/aardvark/entrance'], 5)
        self.assertEqual(ms.room_page['players/fizban/aardvark/egypt'], 20)
        entrance = ms.pages[5].rooms['players/fizban/aardvark/entrance']
        self.assertEqual(entrance.map, [
            ['Rp', 380, 430, 50, 20, 'Museum', 'Entrance', [['e', 20]]],
            ['S', 385, 420, '(See p. 20)']
        ])
        self.assertEqual(entrance.page.page, 5)

        rotunda = ms.pages[20].rooms['players/fizban/aardvark/rotunda']
        self.assertEqual(rotunda.page.page, 20)
        self.assertEqual(rotunda.page.realm, "Aardvark's Museum--Gateway to Adventureland")
        self.assertEqual(rotunda.map, [
            ['Rop', 395, 335, 50, 20, "Heimdall's", "Path", []],
            ['S', 450, 341, '(See p. 3)'],
            ['Ro', 325, 335, 50, 20, "Museum", "Entrance", [['e', 20], ['w', 20]]],
            ['R', 275, 345, 'R', 30, 'Museum', 'Rotunda', [
                ['n', 20],
                ['e', 20],
                ['w', 20],
                ['s', 20],
                ['b', 20]
            ]],
            ['S', 301, 320, 'Dn']
        ])
        
    def test_math_expressions(self):
        self._test_compiler_floats((
            ('1 2 add 13.4 57.2 add -1 1.5 add -10 -2 add 4 __test__', (3,(13.4+57.2),0.5,-12)),
            ('1 2 sub 13.4 57.2 sub -1 1.5 sub -10 -2 sub 4 __test__', (-1,(13.4-57.2),-2.5,-8)),
            ('1 2 mul 13.4 57.2 mul -1 1.5 mul -10 -2 mul 4 __test__', (2,(13.4*57.2),-1.5,20)),
            ('1 2 div 13.4 57.2 div -1 1.5 div -10 -2 div 4 __test__', (0.5,(13.4/57.2),-1/1.5,5)),
            ('1 2 idiv 13.4 57.2 idiv -1 1.5 idiv -10 -2 idiv 4 __test__', (0,(13.4//57.2),-1,5)),
            ('1 neg -2.5 neg 2 __test__', (-1, 2.5)),
            ('1 5 mod 2 5 mod 4 5 mod 5 5 mod 6 5 mod 5 __test__', (1,2,4,0,1)),
            ('2 3 exch (x) (y) exch 1.2 (x) exch 6 __test__', (3,2,'y','x','x',1.2)),
            ('1 2 3 pop 2 __test__', (1,2)),
            ('true false 2 __test__', (-1,0)),
            ('1 abs 1.5 abs -2 abs -2.17 abs 4 __test__', (1, 1.5, 2, 2.17)),
            ('1 0 eq 17 17 eq 1 0 ne 17 17 ne 4 __test__', (0,-1,-1,0)),
            ('1 0 le 17 17 le 1.0 0.1 le 17.1 17.2 le 4 __test__', (0,-1,0,-1)),
            ('1 0 lt 17 17 lt 1.0 0.1 lt 17.1 17.2 lt 4 __test__', (0,0,0,-1)),
            ('1 0 gt 17 17 gt 1.0 0.1 gt 17.1 17.2 gt 4 __test__', (-1,0,-1,0)),
            ('1 0 ge 17 17 ge 1.0 0.1 ge 17.1 17.2 ge 4 __test__', (-1,-1,-1,0)),
            # 101 <<3 =101000 1100 >>2 = 11
            ('5 3 bitshift 12 -2 bitshift 7.2 0 bitshift 3 __test__', (0x28,0x03,0x07)),
            ('5 dup 1.23 dup (abc) dup dup 7 __test__', (5, 5, 1.23, 1.23, 'abc', 'abc', 'abc')),
            ('1 4 3 (abc) 17 count 6 __test__', (1, 4, 3, 'abc', 17, 5)),
            ('1 (hello) 12 3 3 2 count 7 __test__', (1, 'hello', 12, 3, 3, 2, 6)),
            ('1 (hello) 12 3 3 2 clear count 1 __test__', (0,)),
            ('1.23 (xyz) 5 6.2 3 copy 7 __test__', (1.23, 'xyz', 5, 6.2, 'xyz', 5, 6.2)),
            ('1.23 (xyz) 5 0 index 4 __test__', (1.23, 'xyz', 5, 5)),
            ('1.23 (xyz) 5 1 index 4 __test__', (1.23, 'xyz', 5, 'xyz')),
            ('1.23 (xyz) 5 2 index 4 __test__', (1.23, 'xyz', 5, 1.23)),
            ('3 (a) (b) (c) 12 4 3 roll 5 __test__', (3, 'b', 'c', 12, 'a')),
            ('(x) 20 30 40 50 4 -1 roll 5 __test__', ('x', 30, 40, 50, 20)),
        ))

    def test_bad_math_expressions(self):
        for source, ex in (
            ('2 add', MapFileFormatError), ('add', MapFileFormatError),
            ('2 sub', MapFileFormatError), ('sub', MapFileFormatError),
            ('2 div', MapFileFormatError), ('div', MapFileFormatError),
            ('2 mul', MapFileFormatError), ('mul', MapFileFormatError),
            ('2 idiv', MapFileFormatError), ('idiv', MapFileFormatError),
            ('2 0 div', ZeroDivisionError),
            ('2 0 idiv', ZeroDivisionError),
            ('neg', MapFileFormatError),
            ('5 mod', MapFileFormatError), ('mod', MapFileFormatError),
            ('exch', MapFileFormatError), ('2 exch', MapFileFormatError),
            ('pop', MapFileFormatError),
            ('abs', MapFileFormatError),
            ('eq', MapFileFormatError), ('0 eq', MapFileFormatError),
            ('ne', MapFileFormatError), ('0 ne', MapFileFormatError),
            ('lt', MapFileFormatError), ('0 lt', MapFileFormatError),
            ('gt', MapFileFormatError), ('0 gt', MapFileFormatError),
            ('ge', MapFileFormatError), ('0 ge', MapFileFormatError),
            ('le', MapFileFormatError), ('0 le', MapFileFormatError),
            ('1 bitshift', MapFileFormatError), ('bitshift', MapFileFormatError),
            ('1 bitshift', MapFileFormatError), ('bitshift', MapFileFormatError),
            ('1 (2) bitshift', MapFileFormatError), ('(2) 1 bitshift', MapFileFormatError),
            ('dup', MapFileFormatError),
            ('copy', MapFileFormatError),
            ('2 copy', MapFileFormatError),
            ('1 2 copy', MapFileFormatError),
            ('index', MapFileFormatError),
            ('2 index', MapFileFormatError),
            ('1 2 index', MapFileFormatError),
            ('1 1 index', MapFileFormatError),
            ('roll', MapFileFormatError), ('5 roll', MapFileFormatError),
            ('2 5 roll', MapFileFormatError), ('1 2 3 4 5 roll', MapFileFormatError),
        ):
            try:
                self.ms.compile(source, allow_test=True)
            except ex:
                pass
            else:
                self.fail("expression {0} failed to make the compiler raise {1}".format(source, ex))

    def test_conditional(self):
        self._test_compiler((
            ('1 2 {3 4 5} if 4 __test__', [['_T', 1, 3, 4, 5]]),
            ('1 0 {3 4 5} if 1 __test__', [['_T', 1]]),
            ('1 2 {3 4}{5 6} ifelse 3 __test__', [['_T', 1,3,4]]),
            ('1 0 {3 4}{5 6} ifelse 3 __test__', [['_T', 1,5,6]]),
        ))

    def test_repeat_loop(self):
        self._test_compiler((
            ('0 {1 2 3} repeat count 1 __test__ clear', [['_T', 0]]),
            ('1 {1 2 3} repeat count 1 __test__ clear', [['_T', 3]]),
            ('2 {1 2 3} repeat count 1 __test__ clear', [['_T', 6]]),
            ('10 {1 2 3} repeat count 1 __test__ clear', [['_T', 30]]),
            ('1 {1 2 3} repeat 3 __test__ clear', [['_T', 1, 2, 3]]),
            ('2 {1 2 3} repeat 6 __test__ clear', [['_T', 1, 2, 3, 1, 2, 3]]),
        ))

    def test_loop_and_exit(self):
        self._test_compiler((
            ('20 30 mv (foo) 1 2 3 4 { 1 eq { exit } if (xx) show } loop 1 __test__',
                [['S', 20, 30, 'xx'], ['S', 20, 30, 'xx'], ['S', 20, 30, 'xx'], ['_T', 'foo']]),
        ))
                
    def test_infinite_loop(self):
        self.assertRaises(InfiniteLoopError, self.ms.compile, '{ clear } loop')

    def test_for_loop(self):
        self._test_compiler((
            ('5 2 20 { dup } for 16 __test__', [['_T', 5, 5, 7, 7, 9, 9, 11, 11, 13, 13, 15, 15, 17, 17, 19, 19 ]]),
            ('10 1 1 4 { add } for 1 __test__', [['_T', 20]]),
            ('10 -2 4 { dup } for 8 __test__', [['_T', 10, 10, 8, 8, 6, 6, 4, 4]]),
        ))

    def test_bit_ops(self):
        self._test_compiler((
            ('() 7 8 or 2 __test__', [['_T', '', 15]]),
            ('() 7 8 and 2 __test__', [['_T', '', 0]]),
            ('() 7 8 xor 2 __test__', [['_T', '', 15]]),
            ('() 15 5 xor 2 __test__', [['_T', '', 10]]),
            ('() -1 not 2 __test__', [['_T', '', 0]]),
        ))

    def test_trig_opts(self):
        self._test_compiler_floats((
            ('() 0 1 atan 1 0 atan -100 0 atan 4 4 atan 5 __test__', ('', 0.0, 90.0, 270.0, 45.0)),
            ('() 0 cos 90 cos 3 __test__', ('', 1.0, 0.0)),
            ('() 0 sin 90 sin 3 __test__', ('', 0.0, 1.0)),
        ))

    def test_misc_math(self):
        self._test_compiler_floats((
            ('() 3.2 ceiling -4.8 ceiling 99 ceiling 4 __test__',    ('', 4.0, -4.0, 99.0)),
            ('() 3.2 floor -4.8 floor 99 floor 4 __test__',          ('', 3.0, -5.0, 99.0)),
            ('() 3.2 truncate -4.8 truncate 99 truncate 4 __test__', ('', 3.0, -4.0, 99.0)),
            ('() 9 sqrt 15 sqrt 167.5 sqrt 0 sqrt 5 __test__',       ('', 3.0, 3.8729833462, 12.9421791, 0.0)),
            ('() 10 logn 100 logn 3 __test__',                       ('', 2.3025850929940459, 4.60517)),
            ('() 10 log 100 log 3 __test__',                         ('', 1.0, 2.0)),
            ('() 10 2 exp 10 3 exp 9 0.5 exp -9 -1 exp 5 __test__',  ('', 100.0, 1000.0, 3.0, -0.111111)),
        ))

    def test_math_errors(self):
        for ex, src in (
            (ValueError, '-167.5 sqrt'),
        ):
            self.assertRaises(ex, self.ms.compile, src)

    def test_current_point(self):
        self._test_compiler((
            ('() 1 2 mv 4 5 currentpoint 5 __test__', [['_T', '', 4, 5, 1, 2]]),
        ))

    def test_symbolic_string_names(self):
        deprecated_codes = [ 0o320, 0o252, 0o247, 0o261, 0o272, 0o266, 0o242, 0o267, 0o253,
                             0o262, 0o341, 0o273, 0o263, 0o361, 0o261 ]
        legal_glyphs = {
            '—': '[--]', '–': '[-]',  '¢': '[/c]', '†': '[+]',  '‡': '[++]',
            '“': '[``]', '”': "['']", '•': '[*]',  'Æ': '[AE]', 'æ': '[ae]',
            '§': '[S]',  '¶': '[P]',  '«': '[<<]', '»': '[>>]', '‒': '-',

            '—': '320',  '–': '261',  '¢': '242',  '†': '262',  '‡': '263',
            '“': '252',  '”': "272",  '•': '267',  'Æ': '341',  'æ': '361',
            '§': '247',  '¶': '266',  '«': '253',  '»': '273', 

            '—': '[#2014]',  '–': '[#2013]', '¢': '[#0a2]', '†': '[#2020]', '‡': '[#2021]',
            '“': '[#201c]',  '”': "[#201D]", '•': '[#2022]','Æ': '[#00C6]', 'æ': '[#0e6]',
            '§': '[#0000A7]','¶': '[#b6]',   '«': '[#ab]',  '»': '[#bb]',   'X': '[#58]',
            'ö': '[#f6]',    '⺝': '[#2e9d]','㒳':'[#34b3]',

            '\\': '\\',   '(':  '(',    ')':  ')',   
        }
        for ch in range(256):
            if ch in deprecated_codes:
                continue
            if 32 <= ch < 127:
                self._test_compiler((('(x\\%03oy) 1 __test__' % ch, [['_T', 'x'+chr(ch)+'y']]),))
            else:
                try:
                    self.ms.compile('(x\\%03oy) pop' % ch)
                except MapFileFormatError:
                    pass
                else:
                    self.fail("special character code '\\%03o' failed to raise MapFileFormatError exception" % ch)

        for ch in legal_glyphs:
            self._test_compiler((('(x\\'+legal_glyphs[ch]+'y) 1 __test__', [['_T', 'x'+ch+'y']]),))

    def test_int_bases(self):
        self._test_compiler((
            ('(dec) 1 10 20 10#30 10#40 6 __test__', [['_T', 'dec', 1, 10, 20, 30, 40]]),
            ('(oct) 1 10 20 8#30 8#40   6 __test__', [['_T', 'oct', 1, 10, 20, 0o30, 0o40]]),
            ('(hex) 1 10 20 16#30 16#4e 6 __test__', [['_T', 'hex', 1, 10, 20, 0x30, 0x4e]]),
            ('(bin) 1 2#1000 2#0101     4 __test__', [['_T', 'bin', 1, 8, 5]]),
            ('0#000 1 __test__', [['_T', 0]]),
            ('36#000 36#Z 2 __test__', [['_T', 0, 35]]),
        ))
        for src in ('37#000', '1#000'):
            self.assertRaises(MapFileFormatError, self.ms.compile, src)

    def test_numbers(self):
        self._test_compiler_floats((
            ('(a) 123 -98 43445 0 +17 6 __test__', ('a', 123, -98, 43445, 0, 17)),
            ('(a) -.002 34.5 -3.62 123.6e10 1.0E-5 1E6 -1. 0.0 9 __test__', 
                ('a', -0.002, 34.5, -3.62, 1236000000000., .00001, 1000000, -1., 0.)),
        ))

    def test_lastpath_err(self):
        for src in (
                'lastpath stroke',
                'np 1 2 mv 3 4 ln lastpath stroke',
                'np 1 2 mv 3 4 ln stroke np lastpath stroke',
        ):
            self.assertRaises(MapFileFormatError, self.ms.compile, src)

    def test_curveto(self):
        self._test_compiler((
            ('newpath 11 22 moveto 3 4 5 6 7 8 curveto stroke', [['Pb', [11, 22, 3, 4, 5, 6, 7, 8]]]),
            ('np 1 2 mv 3 4 ln 5 6 ln 7 8 9 0 1 2 curveto 3 4 ln 5 6 ln stroke',
                [['P', [1,2,3,4,5,6]], ['Pb', [5,6,7,8,9,0,1,2]], ['P', [1,2,3,4,5,6]]]),
            ('np 1 2 mv 3 4 5 6 7 8 curveto 9 0 1 2 3 4 curveto 5 6 7 8 9 0 curveto 1 2 lineto fill',
                [['Pbf', [1,2,3,4,5,6,7,8]], ['Pbf', [7,8,9,0,1,2,3,4]], ['Pbf', [3,4,5,6,7,8,9,0]], ['Pf', [9,0,1,2]]]),
            ('newpath 1 2 moveto 3 4 5 6 7 8 curveto stroke lastpath fill', [['Pb', [1, 2, 3, 4, 5, 6, 7, 8]], ['Pbf', [1, 2, 3, 4, 5, 6, 7, 8]]]),
            ('newpath 10 20 moveto [9 8 7 6 5 4 3 2 1 0] acurveto stroke', [['Pb', [10, 20, 9,8,7,6,5,4,3,2,1,0]]]),
            ('newpath 10 20 moveto [1 2 3 4 5 6 7 8] scurveto stroke', [['Ps', [10, 20, 1, 2, 3, 4, 5, 6, 7, 8]]]),
            ('newpath 4 5 moveto 6 7 lineto 8 9 lineto 15 16 17 18 19 20 curveto 21 22 lineto closepath stroke lastpath fill', [
                ['Pc', [4, 5, 6, 7, 8, 9]],
                ['Pbc', [8, 9, 15, 16, 17, 18, 19, 20]],
                ['Pc', [19, 20, 21, 22]],
                ['Pc', [21, 22, 4, 5]],
                ['Pcf', [4, 5, 6, 7, 8, 9]],
                ['Pbcf', [8, 9, 15, 16, 17, 18, 19, 20]],
                ['Pcf', [19, 20, 21, 22]],
                ['Pcf', [21, 22, 4, 5]],
            ]),
        ))

    def test_graphic_state(self):
        self._test_compiler((
            ('.42 sg .1 .2 .3 color', [['C', .42, .42, .42], ['C', .1, .2, .3]]),
            ('.42 sg gsave .1 .2 .3 color grestore', 
                [['C', .42, .42, .42], ['C', .1, .2, .3], ['C', .42, .42, .42]]),
            ('gsave .1 .2 .3 color grestore', 
                [['C', .1, .2, .3], ['C', 0, 0, 0]]),
            ('gsave txtf grestore', [['Ft',8]]),
            ('gsave rmnf grestore', [['Fr',6],['Ft',8]]),
            ('27 bf gsave 10 bf grestore', [['Fb', 27], ['Fb', 10], ['Fb', 27]]),
            ('27 bf gsave 10 it grestore', [['Fb', 27], ['Fi', 10], ['Fb', 27]]),
            ('gsave 66 it gsave txtf grestore', [['Fi', 66], ['Ft', 8], ['Fi', 66]]),
            ('44 tt gsave rmnf txtf grestore', [['FT', 44], ['Fr', 6], ['Ft', 8], ['FT', 44]]),
            ('44 sf gsave rmnf txtf grestore', [['Ff', 44], ['Fr', 6], ['Ft', 8], ['Ff', 44]]),
            ('44 sl gsave rmnf txtf grestore', [['Fo', 44], ['Fr', 6], ['Ft', 8], ['Fo', 44]]),
            ('44 ss gsave rmnf txtf grestore', [['Fs', 44], ['Fr', 6], ['Ft', 8], ['Fs', 44]]),
            ('gsave 5 lw grestore', [['L', 5], ['L', 1]]),
            ('''2 3 scale 
                (one)(two)5 6 7 8 room 9 passagelength east passage west passage
                (x) (y) 10 11 12 round-room 9 passagelength east passage west passage
             ''', [
                ['Z', 2, 3],
                ['R', 5, 6, 7, 8, 'one', 'two', [['e', 9], ['w', 20]]],
                ['R', 10, 11, 'R', 12, 'x', 'y',[['e', 9], ['w', 20]]],
             ]),
            ('5 6 scale gsave 7 8 scale grestore', [['Z',5,6],['Z',35,48],['Z',5,6]]),
            ('gsave 7 8 scale grestore', [['Z',7,8],['Z',1,1]]),
            ('10 -20 translate', [['X',10,-20]]),
            ('10 -20 translate gsave -1.5 6.6 translate grestore', [['X',10,-20],['X',8.5,-13.4],['X',10,-20]]),
            ('gsave -1.5 6.6 translate grestore', [['X',-1.5,6.6],['X',0,0]]),
            ('3 4 scale 2 2 scale', [['Z',3,4],['Z',6,8]]),
            ('3 4 scale gsave 2 2 scale grestore', [['Z',3,4],['Z',6,8],['Z',3,4]]),
            ('gsave 3 4 scale gsave 2 2 scale grestore grestore', [['Z',3,4],['Z',6,8],['Z',3,4],['Z',1,1]]),
            ('2 3 scale 20 30 translate', [['Z',2,3],['X',40,90]]),
        ))

    def test_bad_graphic_state(self):
        for src in (
            'grestore',
            'gsave grestore grestore'
        ):
            self.assertRaises(MapFileFormatError, self.ms.compile, src)

    def test_arc_paths(self):
        self._test_compiler_float_values((
            ('np 10 15 mv 10 15 2 45 300 arc stroke currentpoint 2 __test__', [
                ['P', [10, 15, 11.41421356, 16.41421356]],
                ['Q', [10, 15, 2, 45, 300]],
                ['_T', 11, 13.267949192],
            ]),
            ('np 0 0 mv 0 0 1 0 45 arc cp fill currentpoint 2 __test__', [
                ['Pcf', [0, 0, 1, 0]],
                ['Qcf', [0, 0, 1, 0, 45]],
                ['Pcf', [.707106, .707106, 0, 0]],
                ['_T', 0, 0],
            ]),
            ('np 10 15 mv 10 15 2 45 660 arc stroke currentpoint 2 __test__', [
                ['P', [10, 15, 11.41421356, 16.41421356]],
                ['O', 10, 15, 2],
                ['_T', 11.0, 13.267949192],
            ]),
            ('np 10 15 mv 10 15 2 45 -60 arc stroke currentpoint 2 __test__', [
                ['P', [10, 15, 11.41421356, 16.41421356]],
                ['Q', [10, 15, 2, 45, 300]],
                ['_T', 11.0, 13.267949192],
            ]),
        ))

    def test_arcn_paths(self):
        self._test_compiler_float_values((
            ('np 10 15 2 300 45 arcn 10 15 ln stroke currentpoint 2 __test__', [
                ['Q', [10, 15, 2, 45, 300]],
                ['P', [11.41421356, 16.41421356, 10, 15]],
                ['_T', 10, 15],
            ]),
        ))

    def test_arcn_wipe(self):
        self._test_compiler_float_values((
            ('np 0 0 2 0 90 arc 0 0 1 90 0 arcn cp stroke currentpoint 2 __test__', [
                ['Qc', [0, 0, 2, 0, 90]],
                ['Pc', [0.0, 2.0, 0.0, 1.0]],
                ['Qc', [0, 0, 1, 0, 90]],
                ['Pc', [1.0, 0.0, 2.0, 0.0]],
                ['_T', 2.0, 0.0],
            ]),
        ))

    def test_no_currrent_point(self):
        for src in ('np 4 3 lineto stroke', 'np 4 3 rlineto stroke'):
            self.assertRaises(MapFileFormatError, self.ms.compile, src)

    def test_symbol_name(self):
        self._test_compiler((
            ('/foo { 1 2 3 add sub } 2 __test__', [['_T', MapDefSymbol('foo'), [1, 2, 3, 'add', 'sub']]]),
            ('/$bar { /i 1 ndef } 2 __test__',    [['_T', MapDefSymbol('$bar'), ['/i', 1, 'ndef']]]),
        ))

    def test_def_proc(self):
        self._test_compiler_symbols((
            ('/foo { 1 2 3 add add } def', [], {'foo': [1,2,3,'add','add']}, {}),
            ('/i 10 ndef i 1 __test__', [['_T', 10]], {'i': 10}, {}),
            ('/$i 20 ndef /i 1 ndef $i i add 1 __test__', [['_T', 21]], {'i': 1}, {'$i': 20}),
        ))

    def test_persistent_globals(self):
        self._test_compiler_symbols((
            ('/foo { 1 2 3 add add } def', [], {'foo': [1,2,3,'add','add']}, {}),
            ('/i 10 ndef i 1 __test__', [['_T', 10]], {'i': 10}, {}),
            ('/$i 20 ndef /i 1 ndef $i i add 1 __test__', [['_T', 21]], {'i': 1}, {'$i': 20}),
            ('/$j 30 ndef /i 1 ndef $i i add 1 __test__', [['_T', 21]], {'i': 1}, {'$i': 20, '$j': 30}),
            ('/$j (xxx) sdef /k 1 ndef $i k add 1 __test__', [['_T', 21]], {'k': 1}, {'$i': 20, '$j': 'xxx'}),
            ('/$SQUARE { dup mul } def', [], {}, {'$i': 20, '$j': 'xxx', '$SQUARE': ['dup', 'mul']}),
            ('15 $SQUARE 6 $SQUARE 2 __test__', [['_T', 15**2, 36]], {}, {'$i': 20, '$j': 'xxx', '$SQUARE': ['dup', 'mul']}),
        ), persistent=True)

    def test_def_type_mismatch(self):
        for src in (
            '/$eric (half a string) def',
            '/$eric 42 def',
            '/$eric {1 2 3} ndef',
            '/$eric (hello) ndef',
            '/$eric {1 2 3} sdef',
            '/$eric 444 sdef',
            '/eric (half a string) def',
            '/eric 42 def',
            '/eric {1 2 3} ndef',
            '/eric (hello) ndef',
            '/eric {1 2 3} sdef',
            '/eric 444 sdef',
            '$undefined',
        ):
            self.assertRaises(MapFileFormatError, self.ms.compile, src)

# TODO
#   arc[n]
#   effects of start>end and end more than a full circle away from start
