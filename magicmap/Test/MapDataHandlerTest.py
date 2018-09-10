# vi:set ai sm nu ts=4 sw=4 expandtab fileencoding=UTF-8:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: Magic Map Data Marshalling
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
import datetime
from RagnarokMUD.MagicMapper.MapPage import MapPage, PORTRAIT, LANDSCAPE
from RagnarokMUD.MagicMapper.MapRoom import MapRoom
from RagnarokMUD.MagicMapper.MapDataHandler import MapDataHandler, MagicMapDataFormatError, InvalidPageHeader,  InvalidRoomHeader,\
        UnsupportedRoomVersion, UnsupportedPageVersion, ElementListLengthError, ElementListFormatError, DataAfterElementList,\
        MapDataChecksumError, MapDataLengthError, InvalidMapDataFooter, MissingRoomReferencePoint

class MapDataHandlerTest (unittest.TestCase):
    def test_dump_page(self):
        dh=MapDataHandler()
        p=MapPage(1, realm="Kubla Khan's Xanadu", orient=LANDSCAPE, creators=['SamuelTC'], bg=[
            ['Fi', 36],
            ['S', 0, 0, 'Museum Quest']
        ])
        self.assertEqual(dh.dump_page(p,
            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991000)
        ), '''P6 1 L Kubla+Khan%27s+Xanadu @SamuelTC 1
:2 :2 Fi 36 :4 S 0 0 Museum+Quest
%wVHC3hQEwHTa1+vynC6115ccqSA= 2010-03-30T23:31:24.000000 2010-03-30T23:16:40.000000''')

    def test_dump_page_timestamps(self):
        p=MapPage(1, realm="Kubla Khan's Xanadu", orient=LANDSCAPE, creators=['SamuelTC'], bg=[
            ['Fi', 36],
            ['S', 0, 0, 'Museum Quest']
        ], source_modified_date = datetime.datetime(2009, 10, 31, 0, 0, 0, 0),
           source_compiled_date = datetime.datetime(2010, 0o1, 12, 1, 2, 3, 4))
        self.assertEqual(MapDataHandler().dump_page(p), '''P6 1 L Kubla+Khan%27s+Xanadu @SamuelTC 1
:2 :2 Fi 36 :4 S 0 0 Museum+Quest
%wVHC3hQEwHTa1+vynC6115ccqSA= 2010-01-12T01:02:03.000004 2009-10-31T00:00:00.000000''')

    def test_parse_header(self):
        dh = MapDataHandler()
        self.assertEqual(dh._parse_header('F77 126 Kubla%27s+Xanadu @Larry,Curly,Moe 12'),
                ['F77', 126, "Kubla's Xanadu", ['Larry', 'Curly', 'Moe'], 12])

    def test_decode_integer(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('37'), 37)

    def test_decode_float(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('18.57'), 18.57)

    def test_decode_string(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('/18.57'), '18.57')
        self.assertEqual(dh.decode_value('/Hello+World'), 'Hello World')
        self.assertEqual(dh.decode_value('Hello+World'), 'Hello World')
        self.assertEqual(dh.decode_value('Hello%2C+World'), 'Hello, World')

    def test_decode_string_list_empty(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@/'), [''])

    def test_decode_empty_string_list(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@'), [])

    def test_decode_string_list(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@spam'), ['spam'])

    def test_decode_string_list2(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@spam,eggs'), ['spam', 'eggs'])

    def test_decode_string_list3(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@spam,eggs,,sausage'), ['spam', 'eggs', '', 'sausage'])

    def test_decode_string_list3a(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@spam,eggs,/,sausage'), ['spam', 'eggs', '', 'sausage'])

    def test_decode_string_list3a(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@spam,42,/,sau%2Csage'), ['spam', '42', '', 'sau,sage'])

    def test_decode_string_list4(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_value('@spam,42,@,@/,/14'), ['spam', '42', '@', '@/', '14'])

    def test_decode_errors(self):
        dh = MapDataHandler()
        self.assertRaises(ValueError, dh.decode_value, '7..7325')

    def test_parse_page_header(self):
        dh=MapDataHandler()
        self.assertEqual(dh.parse_page_header('P6 672 L /69+Ways+to+Skin+a+Gargoyle @Larry,Moe 15'), {
            'format': 'P6', 
            'page': 672, 
            'orient': LANDSCAPE,
            'realm': '69 Ways to Skin a Gargoyle',
            'creators': ['Larry', 'Moe'],
            'bglines': 15
        })

    def test_parse_page_header2(self):
        dh=MapDataHandler()
        self.assertEqual(dh.parse_page_header('P6 672 P /69+Ways+to+Skin+a+Gargoyle @Larry,Moe 15'), {
            'format': 'P6', 
            'page': 672, 
            'orient': PORTRAIT,
            'realm': '69 Ways to Skin a Gargoyle',
            'creators': ['Larry', 'Moe'],
            'bglines': 15
        })

    def test_page_header_error(self):
        dh = MapDataHandler()
        self.assertRaises(InvalidPageHeader, dh.parse_page_header, 'P6 672 Q /69 @ 15')
        self.assertRaises(InvalidPageHeader, dh.parse_page_header, 'P6 6..72')
        self.assertRaises(InvalidPageHeader, dh.parse_page_header, 'P7 6..72')
        self.assertRaises(InvalidPageHeader, dh.parse_page_header, '')
        self.assertRaises(InvalidPageHeader, dh.parse_page_header, 'P6 x x x x x x')
        self.assertRaises(InvalidPageHeader, dh.parse_page_header, 'P6 x x x x')
        self.assertRaises(InvalidPageHeader, dh.parse_page_header, 'P6 1 Q / @ 0')
        self.assertRaises(UnsupportedPageVersion, dh.parse_page_header, 'P7 1 2 3')

    def test_parse_object_list(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_object_list(':2 :1 AAA 127'), [['AAA'], 127])

    def test_parse_object_list2(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_object_list(':7 /55.17 /662 17 238.3 Testing+Testing :3 1 2 3 @a,b,q'), 
                ['55.17', '662', 17, 238.3, 'Testing Testing', [1,2,3], ['a','b','q']])

    def test_parse_object_list3(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_object_list(':7 /55.17 :3 x :5 4 3 2 1 0 z 17 238.3 Testing+Testing :3 1 2 3 @a,b,q'), 
            ['55.17', ['x',[4,3,2,1,0],'z'],17,238.3,'Testing Testing',[1,2,3],['a','b','q']])

    def test_parse_null_object_list(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_object_list('  '), None)

    def test_parse_empty_object_list(self):
        dh = MapDataHandler()
        self.assertEqual(dh.decode_object_list(':0'), [])

    def test_parse_object_list_errors(self):
        dh = MapDataHandler()
        self.assertRaises(ElementListLengthError, dh.decode_object_list, ':3 xxx yyy')
        self.assertRaises(DataAfterElementList, dh.decode_object_list, ':2 xxx yyy zzz')
        self.assertRaises(ElementListFormatError, dh.decode_object_list, '/hello :2 a b')
       

    def test_load_page(self):
        p = MapDataHandler().load_page_file(io.StringIO('''P6 17 P Sample+Realm @Fizban 1
:0
%gkkgGh6Vw93E3Dj7sXqOWT7ggJ8= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33
'''))
        self.assertEqual(p.page, 17)
        self.assertEqual(p.orient, PORTRAIT)
        self.assertEqual(p.realm, "Sample Realm")
        self.assertEqual(p.creators, ['Fizban'])
        self.assertEqual(p.bg, [])

    def test_load_page_with_bg(self):
        p = MapDataHandler().load_page_file(io.StringIO('''P6 1767 L Sample+Realm @Fizban,Galadriel 3
:3
:4 S 100 200 Here+there+be+dragons%21 :8 R 500 500 50 20 Room / :1 :2 nD 20
:5 V 50 60 70 80
%3Q5iHvcZrl585Q0kTPeIcMmo+ts= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33
'''))
        self.assertEqual(p.page, 1767)
        self.assertEqual(p.orient, LANDSCAPE)
        self.assertEqual(p.realm, "Sample Realm")
        self.assertEqual(p.creators, ['Fizban','Galadriel'])
        self.assertEqual(p.bg, [
            ['S', 100, 200, 'Here there be dragons!'],
            ['R', 500, 500, 50, 20, 'Room', '', [['nD', 20]]],
            ['V', 50, 60, 70, 80]
        ])
        self.assertEqual(p.source_modified_date, datetime.datetime(2010, 0o2, 0o3, 00, 00, 12, 330000))
        self.assertEqual(p.source_compiled_date, datetime.datetime(2010, 0o1, 0o2, 12, 34, 56, 789000))

    def test_load_page_bad_checksum(self):
        self.assertRaises(MapDataChecksumError, MapDataHandler().load_page_file, io.StringIO('''P6 17 P Sample+Realm @Fizban 1
:0
%Rf5yqfoGRDAXCrIaITEzsByw4gd= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33
'''))

    def test_load_page_length_error(self):
        self.assertRaises(MapDataLengthError, MapDataHandler().load_page_file, io.StringIO('''P6 17 P Sample @ 27
:0
stuff
more stuff
'''))

    def test_load_page_header_error(self):
        dh=MapDataHandler()
        self.assertRaises(UnsupportedPageVersion, dh.load_page_file, io.StringIO('''P4 17 P Sample+Realm @Fizban 1
:0
%0000 0 0
'''))
    def test_load_page_header_error2(self):
        dh=MapDataHandler()
        self.assertRaises(InvalidPageHeader, dh.load_page_file, io.StringIO('''P6 / Sample+Realm @Fizban 1
:0
%0000 0 0
'''))
    def test_load_page_header_error3(self):
        dh=MapDataHandler()
        self.assertRaises(MapDataLengthError, dh.load_page_file, io.StringIO('''P6 27 L Sample+Realm @Fizban 1
:0
%0000 2010-01-01T00:00:00.0 2010-01-01T00:00:00.0

foo
'''))
    def test_load_page_line_error(self):
        dh=MapDataHandler()
        self.assertRaises(MapDataLengthError, dh.load_page_file, io.StringIO('''P6 17 P Sample+Realm @Fizban 1
'''))

    def test_parse_footer(self):
        dh=MapDataHandler()
        self.assertEqual(dh.parse_footer('%MTIzNDU2Nzg5MA== 2010-01-02T12:34:56.789000 2010-04-22T23:14:57.0'), {
            'checksum': b'1234567890',
            'compiled': datetime.datetime(2010,0o1,0o2,12,34,56,789000),
            'modified': datetime.datetime(2010,0o4,22,23,14,57,0),
        })


    def test_parse_footer_errors(self):
        dh=MapDataHandler()
        self.assertRaises(InvalidMapDataFooter, dh.parse_footer, '')
        self.assertRaises(InvalidMapDataFooter, dh.parse_footer, 'x x x')
        self.assertRaises(InvalidMapDataFooter, dh.parse_footer, '%x x x')
        self.assertRaises(InvalidMapDataFooter, dh.parse_footer, '%MTIzNDU2Nzg5MA== x x')

    def test_dump_room(self):
        dh=MapDataHandler()
        p=MapPage(10, realm="Kubla Khan's Xanadu", orient=LANDSCAPE, bg=[
            ['Fi', 36],
            ['S', 0, 0, 'Museum Quest']
        ])
        r0=MapRoom('/players/fizban/aardvark/prehistory', p, 'Prehistory Exhibit')
        r1=MapRoom('/players/fizban/aardvark/prehistory', p, 'Prehistory Exhibit', reference_point=(1,2))
        r2=MapRoom('/players/fizban/aardvark/prehistory', p, 'Prehistory Exhibit', [
            ['R', 345, 285, 50, 20, 'Hall of', 'Prehistory', [['w', 20]]],
            ['S', 332, 297, 'Up']
        ])
        r3=MapRoom('/players/fizban/aardvark/prehistory', p, 'Prehistory Exhibit', [
            ['R', 345, 285, 50, 20, 'Hall of', 'Prehistory', [['w', 20]]],
            ['S', 332, 297, 'Up']
        ], ['/players/fizban/also1','/players/fizban/also2'])

        #self.assertRaises(MissingRoomReferencePoint, dh.dump_room, r0)  # no reference point!
        self.assertEqual(dh.dump_room(r0,
            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991000)
        ), '''R6 //players/fizban/aardvark/prehistory 10 Prehistory+Exhibit @ 0 0 1
:0
%bh8WXJx8xBNLGBrpaudjjS6Avfs= 2010-03-30T23:31:24.000000 2010-03-30T23:16:40.000000''')

        self.assertEqual(dh.dump_room(r1,

            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991000)
        ), '''R6 //players/fizban/aardvark/prehistory 10 Prehistory+Exhibit @ 1 2 1
:0
%TwIHcXoO8mXxRV4wccq2ncHPLFI= 2010-03-30T23:31:24.000000 2010-03-30T23:16:40.000000''')
        self.assertEqual(dh.dump_room(r2,
            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991884)
        ), '''R6 //players/fizban/aardvark/prehistory 10 Prehistory+Exhibit @ 370 295 1
:2 :8 R 345 285 50 20 Hall+of Prehistory :1 :2 w 20 :4 S 332 297 Up
%kExYp+f/XR/WbO0jgP5OkcsM8xY= 2010-03-30T23:31:24.000000 2010-03-30T23:31:24.000000''')
        self.assertEqual(dh.dump_room(r3,
            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991000)
        ), '''R6 //players/fizban/aardvark/prehistory 10 Prehistory+Exhibit @//players/fizban/also1,//players/fizban/also2 370 295 1
:2 :8 R 345 285 50 20 Hall+of Prehistory :1 :2 w 20 :4 S 332 297 Up
%7wVnPJrlDOhUr2lguUftNQxeZo4= 2010-03-30T23:31:24.000000 2010-03-30T23:16:40.000000''')

    def test_dump_room_timestamps(self):
        dh=MapDataHandler()
        p=MapPage(10, realm="Kubla Khan's Xanadu", orient=LANDSCAPE, bg=[
            ['Fi', 36],
            ['S', 0, 0, 'Museum Quest']
        ])
        r1=MapRoom('/players/fizban/aardvark/prehistory', p, 'Prehistory Exhibit',
                source_modified_date = datetime.datetime(2009, 6, 12, 5,55,12,345678),
                source_compiled_date = datetime.datetime(2009, 7, 14, 2,22,22,222222),
                reference_point = (0,0))
        r2=MapRoom('/players/fizban/aardvark/prehistory', p, 'Prehistory Exhibit', [
            ['R', 345, 285, 50, 20, 'Hall of', 'Prehistory', [['w', 20]]],
            ['S', 332, 297, 'Up']
        ],
            source_modified_date = datetime.datetime(2009, 6, 12, 5,55,12,0),
            source_compiled_date = datetime.datetime(2009, 7, 14, 2,22,22,0)
        )
        r3=MapRoom('/players/fizban/aardvark/prehistory', p, 'Prehistory Exhibit', [
            ['R', 345, 285, 50, 20, 'Hall of', 'Prehistory', [['w', 20]]],
            ['S', 332, 297, 'Up']
        ], ['/players/fizban/also1','/players/fizban/also2'],
            source_modified_date = datetime.datetime(2009, 6, 12, 5,55,12,1),
            source_compiled_date = datetime.datetime(2009, 7, 14, 2,22,22,2)
        )

        self.assertEqual(dh.dump_room(r1,
            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991000)
        ), '''R6 //players/fizban/aardvark/prehistory 10 Prehistory+Exhibit @ 0 0 1
:0
%bh8WXJx8xBNLGBrpaudjjS6Avfs= 2010-03-30T23:31:24.000000 2010-03-30T23:16:40.000000''')

        self.assertEqual(dh.dump_room(r2), '''R6 //players/fizban/aardvark/prehistory 10 Prehistory+Exhibit @ 370 295 1
:2 :8 R 345 285 50 20 Hall+of Prehistory :1 :2 w 20 :4 S 332 297 Up
%kExYp+f/XR/WbO0jgP5OkcsM8xY= 2009-07-14T02:22:22.000000 2009-06-12T05:55:12.000000''')
        self.assertEqual(dh.dump_room(r3), '''R6 //players/fizban/aardvark/prehistory 10 Prehistory+Exhibit @//players/fizban/also1,//players/fizban/also2 370 295 1
:2 :8 R 345 285 50 20 Hall+of Prehistory :1 :2 w 20 :4 S 332 297 Up
%7wVnPJrlDOhUr2lguUftNQxeZo4= 2009-07-14T02:22:22.000002 2009-06-12T05:55:12.000001''')

    def test_dump_long_map(self):
        dh = MapDataHandler()
        p = MapPage(123, realm="...Somewhere“REALLY different!", bg=[
            ['S', 12, 34, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 22, 44, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 32, 54, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 42, 64, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
        ])
        r = MapRoom('asafsdfjjf8a7f0fds7f8a7ds0f870d9', p, 'Abandoned Mine Chamber', [
            ['R', 20, 20, 50, 50, '50x50 room', '', [['n',20],['si', 30]]],
            ['S', 12, 34, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 22, 44, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 32, 54, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 42, 64, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 12, 34, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 22, 44, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 32, 54, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 42, 64, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 12, 34, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 22, 44, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 32, 54, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
            ['S', 42, 64, 'fjasldkjfds fj;aslkfjd;slfkjas;dljfd;slafj ds;jfa;sj'],
        ], reference_point=(45,30))
        self.assertEqual(dh.dump_page(p,
            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991884)),
'''P6 123 P /...Somewhere%E2%80%9CREALLY+different%21 @ 4
:4 :4 S 12 34 fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj
:4 S 22 44 fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4
S 32 54 fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S
42 64 fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj
%LiMXZlALPZ86eTUQ1BgiFcFHwhY= 2010-03-30T23:31:24.000000 2010-03-30T23:31:24.000000''')
        self.assertEqual(dh.dump_room(r,
            gentime=datetime.datetime.utcfromtimestamp(1269991884),
            mtime=datetime.datetime.utcfromtimestamp(1269991884)),

'''R6 asafsdfjjf8a7f0fds7f8a7ds0f870d9 123 Abandoned+Mine+Chamber @ 45 30 13
:13 :8 R 20 20 50 50 /50x50+room / :2 :2 n 20 :2 si 30 :4 S 12 34
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 22 44
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 32 54
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 42 64
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 12 34
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 22 44
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 32 54
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 42 64
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 12 34
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 22 44
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 32 54
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj :4 S 42 64
fjasldkjfds+fj%3Baslkfjd%3Bslfkjas%3Bdljfd%3Bslafj+ds%3Bjfa%3Bsj
%R05DLf9rgr9YmThAQAHmP2R9WAk= 2010-03-30T23:31:24.000000 2010-03-30T23:31:24.000000''')

    def test_load_room_checksum(self):
        self.assertRaises(MapDataChecksumError, MapDataHandler().load_room_file, io.StringIO('''R6 abc123fff 17 Sample+Room @Fizban 0 0 1
:0
%aFn7s85I0K2dyFrX6rp1E/i/f4g= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33
'''))

    def test_extra_crud_in_room(self):
        self.assertRaises(MapDataLengthError, MapDataHandler().load_room_file, io.StringIO('''R6 abc123fff 17 Sample+Room @Fizban 0 0 1
:0
%D6du1sDkekTO6HLCsj5zoouv1RM= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33
more text
should not
be here!
'''))

    def test_load_room(self):
        p, r = MapDataHandler().load_room_file(io.StringIO('''R6 abc123fff 17 Sample+Room @Fizban 0 0 1
:0
%6f66rmTCbhKzO0KpGEwcYV1ZBKg= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33
'''))
        self.assertEqual(r.id, 'abc123fff')
        self.assertEqual(r.page, None)
        self.assertEqual(r.name, "Sample Room")
        self.assertEqual(r.also, ['Fizban'])
        self.assertEqual(r.map, [])
        self.assertEqual(p, 17)

    def test_load_room_with_map(self):
        p, r = MapDataHandler().load_room_file(io.StringIO('''R6 abcxyzzy_ 573282 Odd+Room @abc5732,abc93423 1 2 3
:3
:4 S 100 200 Here+there+be+dragons%21 :8 R 500 500 50 20 Room / :1 :2 nD 20
:5 V 50 60 70 80
%JcUwESYu+kPXSj5W5Cm6F7RpWMg= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33
'''))
        self.assertEqual(p, 573282)
        self.assertEqual(r.page, None)
        self.assertEqual(r.id, 'abcxyzzy_')
        self.assertEqual(r.name, "Odd Room")
        self.assertEqual(r.also, ['abc5732','abc93423'])
        self.assertEqual(r.reference_point, (1,2))
        self.assertEqual(r.map, [
            ['S', 100, 200, 'Here there be dragons!'],
            ['R', 500, 500, 50, 20, 'Room', '', [['nD', 20]]],
            ['V', 50, 60, 70, 80]
        ])
        self.assertEqual(r.source_modified_date, datetime.datetime(2010, 0o2, 0o3, 00, 00, 12, 330000))
        self.assertEqual(r.source_compiled_date, datetime.datetime(2010, 0o1, 0o2, 12, 34, 56, 789000))

    def test_load_room_length_error(self):
        self.assertRaises(MapDataLengthError, MapDataHandler().load_room_file, io.StringIO('''R6 abc 17 Sample @ 0 0 27
:0
stuff
more stuff
'''))

    def test_load_room_header_error(self):
        dh=MapDataHandler()
        self.assertRaises(UnsupportedRoomVersion, dh.load_room_file, io.StringIO('''R4 aaa 17 A+room @ 1
:0
%0000 0 0
'''))
    def test_load_room_header_error2(self):
        dh=MapDataHandler()
        self.assertRaises(InvalidMapDataFooter, dh.load_room_file, io.StringIO('''R6 aaa 17 Sample @Fizban 0 0 1
:0
%0000 0 0
'''))
    def test_load_room_header_error3(self):
        dh=MapDataHandler()
        self.assertRaises(MapDataLengthError, dh.load_room_file, io.StringIO('''R6 a 27 Sample @Fizban 0 0 1
:0
%0000 2010-01-01T00:00:00.0 2010-01-01T00:00:00.0

foo
'''))
    def test_load_room_line_error(self):
        dh=MapDataHandler()
        self.assertRaises(MapDataLengthError, dh.load_room_file, io.StringIO('''R6 aaaaa 17 A+room @ 0 0 1
'''))
    def test_parse_room_header(self):
        dh=MapDataHandler()
        self.assertEqual(dh.parse_room_header('R6 abc123 17 A+room @ 5 6 2'), {
            'format':  'R6', 
            'page':     17, 
            'id':       'abc123',
            'name':     'A room',
            'also':     [],
            'ref':      (5,6),
            'objlines': 2
        })

    def test_parse_room_header2(self):
        dh=MapDataHandler()
        self.assertEqual(dh.parse_room_header('R6 abc 17 /69+Ways+to+Skin+a+Gargoyle @def,ghi,jkl 11 22 15'), {
            'format': 'R6', 
            'id':     'abc',
            'page':    17, 
            'name':    '69 Ways to Skin a Gargoyle',
            'also':    ['def', 'ghi', 'jkl'],
            'ref':     (11,22),
            'objlines':15
        })

    def test_room_header_error(self):
        dh = MapDataHandler()
        self.assertRaises(InvalidRoomHeader, dh.parse_room_header, 'R6 / 6..72')
        self.assertRaises(UnsupportedRoomVersion, dh.parse_room_header, 'R7 / 6.72')
        self.assertRaises(InvalidRoomHeader, dh.parse_room_header, '')
        self.assertRaises(InvalidRoomHeader, dh.parse_room_header, 'R6 x x x x x x')
        self.assertRaises(InvalidRoomHeader, dh.parse_room_header, 'R6 x x x x')
        self.assertRaises(InvalidRoomHeader, dh.parse_room_header, 'R6 x x x x x x x x')

    def test_newline_variations(self):
        for name, text in (
                ('newlines', 'R6 abcxyzzy_ 573282 Odd+Room @abc5732,abc93423 44 55 3\n:3\n:4 S 100 200 Here+there+be+dragons%21 :8 R 500 500 50 20 Room / :1 :2 nD 20\n:5 V 50 60 70 80\n%CZX+6Ad15/Kp38rBrkUDXlMHUHU= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33\n'),
                ('CRLF', 'R6 abcxyzzy_ 573282 Odd+Room @abc5732,abc93423 44 55 3\r\n:3\r\n:4 S 100 200 Here+there+be+dragons%21 :8 R 500 500 50 20 Room / :1 :2 nD 20\r\n:5 V 50 60 70 80\r\n%CZX+6Ad15/Kp38rBrkUDXlMHUHU= 2010-01-02T12:34:56.789000 2010-02-03T00:00:12.33\r\n'),
        ):
            p, r = MapDataHandler().load_room_file(io.StringIO(text))
            self.assertEqual(p, 573282, name)
            self.assertEqual(r.page, None, name)
            self.assertEqual(r.id, 'abcxyzzy_', name)
            self.assertEqual(r.name, "Odd Room", name)
            self.assertEqual(r.reference_point, (44, 55))
            self.assertEqual(r.also, ['abc5732','abc93423'], name)
            self.assertEqual(r.map, [
                ['S', 100, 200, 'Here there be dragons!'],
                ['R', 500, 500, 50, 20, 'Room', '', [['nD', 20]]],
                ['V', 50, 60, 70, 80]
            ], name)
            self.assertEqual(r.source_modified_date, datetime.datetime(2010, 0o2, 0o3, 00, 00, 12, 330000), name)
            self.assertEqual(r.source_compiled_date, datetime.datetime(2010, 0o1, 0o2, 12, 34, 56, 789000), name)
