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
# RAGNAROK MAGIC MAPPER SOURCE CODE: Data Transfer for map objects
#

from RagnarokMUD.MagicMapper.MapPage import MapPage, LANDSCAPE, PORTRAIT
from RagnarokMUD.MagicMapper.MapRoom import MapRoom
from RagnarokMUD.MagicMapper.Local   import gen_public_room_id
import urllib.request, urllib.parse, urllib.error, hashlib, base64, textwrap, datetime

DATA_FORMAT_VERSION = 6

class MagicMapDataFormatError (Exception):              
    '''We can't understand the data sent to us in a map or page file.
    This exception is a general "file is invalid" kind of case which
    can be caught by calling code.  More specific exception sub-classes
    are also defined if more granularity is needed.'''

class InvalidPageHeader (MagicMapDataFormatError):      "Data format error: page header can't be understood or malformed."
class InvalidRoomHeader (MagicMapDataFormatError):      "Data format error: room header can't be understood or malformed."
class UnsupportedPageVersion (MagicMapDataFormatError): "Page file format number not supported."
class UnsupportedRoomVersion (MagicMapDataFormatError): "Room file format number not supported."
class ElementListLengthError (MagicMapDataFormatError): "A map element list lengh is wrong vs. the file's actual contents."
class ElementListFormatError (MagicMapDataFormatError): "Malformed element list encoding."
class DataAfterElementList (MagicMapDataFormatError):   "Map drawing elements exist past end of encoded list"
class MapDataChecksumError (MagicMapDataFormatError):   "Map data does not match the checksum - maybe invalid file"
class MapDataLengthError   (MagicMapDataFormatError):   "Map data does not match expected length"
class InvalidMapDataFooter (MagicMapDataFormatError):   "Room or Page file footer was malformed"
class MissingRoomReferencePoint (MagicMapDataFormatError): "No ref: field and no reference point could be inferred."



class MapDataHandler (object):
    '''Translates the data representing map objects between 
    our internal format and what's served out to clients over
    the network.'''

    def dump_page(self, page, mtime=None, gentime=None, version=DATA_FORMAT_VERSION):
        '''given a MapPage object, emit multi-line ASCII string representing that page's data.
        If mtime and/or gentime are not given, the dates in the page object are used,
        or the current date and time if there's nothing in the page object either.'''

        if version != 6:
            raise NotImplementedError('Only version 6 magic map format is understood.')

        bgdata = self.encode_map_elements(page.bg)
        preamble = 'P6 %d %s %s %s %d' % (
            page.page,
            'L' if page.orient==LANDSCAPE else 'P',
            self.encode_text(page.realm),
            self.encode_text_list([_f for _f in page.creators if _f]),
            len(bgdata)
        )

        return '\n'.join([preamble]+bgdata+[
            '%'+base64.b64encode(hashlib.sha1(('\n'.join([preamble]+bgdata)+'\n').encode('utf-8')).digest()).decode('utf-8')+' '+
            (gentime or page.source_compiled_date or datetime.datetime.now()).strftime('%Y-%m-%dT%H:%M:%S.%f')+' '+
            (mtime   or page.source_modified_date or datetime.datetime.now()).strftime('%Y-%m-%dT%H:%M:%S.%f')
        ])

    def dump_room(self, room, public_id_filter=None, mtime=None, gentime=None, version=DATA_FORMAT_VERSION):
        '''given a MapRoom object, emit multi-line ASCII string representing that room's data.
        If mtime and/or gentime are not given, the dates in the room object are used,
        or the current date and time if there's nothing in the room object either.
        
        public_id_filter is a callable which takes the internal name of a room and returns
        the public ID we should use for these data files.  If not specified, no translation
        will be done.'''

        if version != 6:
            raise NotImplementedError('Only version 6 magic map format is understood.')

        if public_id_filter is None:
            public_id_filter = lambda i: i

        mapdata = self.encode_map_elements(room.map)
        print("Room {0} ({1}):".format(room.id, public_id_filter(room.id)))
        if room.also is not None:
            for a in [_f for _f in room.also if _f]:
                print("  -- also {0} ({1})".format(a, public_id_filter(a)))
        preamble = 'R6 %s %d %s %s %d %d %d' % (
            self.encode_text(public_id_filter(room.id)),
            room.page.page,
            self.encode_text(room.name),
            self.encode_text_list([public_id_filter(i) for i in room.also if i]
                if room.also is not None else []),
            room.reference_point[0] if room.reference_point is not None else 0,
            room.reference_point[1] if room.reference_point is not None else 0,
            len(mapdata)
        )

        return '\n'.join([preamble] + mapdata + [
            '%'+base64.b64encode(hashlib.sha1(('\n'.join([preamble]+mapdata)+'\n').encode('utf-8')).digest()).decode('utf-8')+' '+
            (gentime or room.source_compiled_date or datetime.datetime.now()).strftime('%Y-%m-%dT%H:%M:%S.%f')+' '+
            (mtime   or room.source_modified_date or datetime.datetime.now()).strftime('%Y-%m-%dT%H:%M:%S.%f')
        ])

    def encode_map_elements(self, element_list, width=78):
        "Take internal-format display element list and return multi-line ASCII representation of it as a list of lines."
        #
        # The format is a space-separated (including newlines as "spaces") list of
        # values which represent a list structure:
        #  :n      following n values are actually elements in a single list object
        #  /abc    string value 'abc'; the / is optional if the string cannot be confused with a number
        #  /       ...so this is a 0-length string value (we change None to an empty string too)
        #  num     an integer or float value as decimal digits, possibly with decimal point/exponent
        #
        if element_list is None:
            element_list = []

        def _element_list_encoder(input_list):
            output_list = []
            for element in input_list:
                if isinstance(element, (list, tuple)):
                    output_list.append(':%d' % len(element))
                    output_list.extend(_element_list_encoder(element))
                elif isinstance(element, int):
                    output_list.append(str(element))
                elif isinstance(element, float):
                    output_list.append(str(round(element, 5)))
                elif not isinstance(element, str):
                    raise TypeError("Can't encode "+repr(element)+" (unsupported data type)")
                else:
                    output_list.append(self.encode_text(element))

            return output_list

        return textwrap.TextWrapper(width=width, expand_tabs=False,
            replace_whitespace=True, drop_whitespace=True, initial_indent='',
            subsequent_indent='', fix_sentence_endings=False, break_long_words=False,
            break_on_hyphens=False).wrap(' '.join(_element_list_encoder([element_list])))

    def encode_text(self, text):
        "Take text string and return marshalled version which has no spaces inside it."
        if text is None or len(text) == 0:
            return '/'

        if text[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_':
            return urllib.parse.quote_plus(text, '/', encoding='utf-8')
        else:
            return '/'+urllib.parse.quote_plus(text, '/', encoding='utf-8')

    def encode_text_list(self, list):
        "Take list of strings and return marshalled version which has no spaces inside it."
        #
        # specifically, the string data is string-encoded, joined with commas, then @-prefixed
        # as with strings.  @ by itself is a zero-element list, while @/ is a one-element list
        # of an empty string, and @/,/ is ['',''], etc.
        #
        if list is None:
            return '@'

        return '@' + ','.join(map(self.encode_text, list))

    def _parse_header(self, header):
        "Parse out the encoded fields of a header line and return them as a list of values."
        return list(map(self.decode_value, header.split()))

    def decode_value(self, encoded_value):
        "Given an encoded value, return the actual data value, or None if no value given"

        encoded_value = encoded_value.strip()
        if not encoded_value:
            return None

        sentinel = encoded_value[0]
        #
        # [/]text...   String value
        #              %xx codes for all but A-Za-z0-9_.-/
        #              space is +
        #              leading / optional if first character is A-Za-z_
        #
        if encoded_value == '/':
            return ''
        if sentinel == '/' or 'A' <= sentinel <= 'Z' or 'a' <= sentinel <= 'z' or sentinel == '_':
            if sentinel == '/':
                return urllib.parse.unquote_plus(encoded_value[1:], encoding='utf-8')
            return urllib.parse.unquote_plus(encoded_value, encoding='utf-8')
        #
        # @[str[,...]]  String list
        #
        if encoded_value == '@':
            return []
        if sentinel == '@':
            output = []
            for element in encoded_value[1:].split(','):
                if not element:
                    # be forgiving: allow ,, to be an empty element string
                    # even though the spec demands it to be ,/,
                    output.append('')
                elif element[0] == '/':
                    output.append(urllib.parse.unquote_plus(element[1:], encoding='utf-8'))
                else:
                    output.append(urllib.parse.unquote_plus(element, encoding='utf-8'))
            return output
        #
        # Integer or float values
        #
        try:
            return int(encoded_value)
        except ValueError:
            try:
                return float(encoded_value)
            except:
                raise ValueError('Encoded value "%s" in map data field not understood' % encoded_value)

    def decode_object_list(self, encoded_data):
        "Read encoded object list from encoded string and return it as a list object."

        self._encoded_list = encoded_data.split()
        if not self._encoded_list:
            return None

        obj_list = self._decode_object_list_next_layer()
        
        if self._encoded_list:
            raise DataAfterElementList('Extra data after last list element at "'+' '.join(self._encoded_list)+'".')

        return obj_list

    def _decode_object_list_next_layer(self):
        "Internal function called recursively to decode each level of nested list elements."

        v = []
        if not self._encoded_list:
            raise ElementListLengthError('Unexpected end of object list reached')
        if self._encoded_list[0][:1] != ':':
            raise ElementListFormatError('Start-of-list marker expected at "'+' '.join(self._encoded_list)+'".')
        try:
            marker = self._encoded_list.pop(0)
            count = int(marker[1:])
        except:
            raise ElementListFormatError('Unrecognizable start-of-list marker "'+marker+'".')

        while count > 0:
            if not self._encoded_list:
                raise ElementListLengthError('Ran out of data early (%d more elements expected at current level)' % count)

            if self._encoded_list[0][:1] == ':':
                v.append(self._decode_object_list_next_layer())
            else:
                try:
                    v.append(self.decode_value(self._encoded_list.pop(0)))
                except ValueError:
                    raise ElementListFormatError('Error decoding value "'+v+'".')

            count -= 1

        return v
    
    def parse_page_header(self, header):
        "Read page header line, return dictionary of page attributes"

        try:
            fields = [self.decode_value(v) for v in header.split()]
        except:
            raise InvalidPageHeader('Unable to parse page header line: "'+header+'"')

        if not fields:
            raise InvalidPageHeader('Truncated page header line: "'+header+'"')

        if fields[0] != 'P6':
            raise UnsupportedPageVersion('Page data claims to be in "'+fields[0]+'" format which is not supported.')

        if len(fields) != 6:
            raise InvalidPageHeader('Page header contains %d fields (6 expected)' % len(fields))

        for idx,tp in enumerate((str, int, str, str, list, int)):
            if not isinstance(fields[idx], tp):
                raise InvalidPageHeader('Page header field #%d (%s) type mismatch' % (idx, repr(fields[idx])))

        if fields[2] not in ('L','P'):
            raise InvalidPageHeader('Page orientation "'+fields[2]+'" not recognized.')

        return dict(
                format=fields[0],
                page=fields[1],
                orient=(LANDSCAPE if fields[2]=='L' else PORTRAIT),
                realm=fields[3],
                creators=fields[4],
                bglines=fields[5]
        )

    def parse_room_header(self, header):
        "Read room header line, return dictionary of room attributes"

        try:
            fields = [self.decode_value(v) for v in header.split()]
        except:
            raise InvalidRoomHeader('Unable to parse room header line: "'+header+'"')

        if not fields:
            raise InvalidRoomHeader('Truncated room header line: "'+header+'"')

        if fields[0] != 'R6':
            raise UnsupportedRoomVersion('Room data claims to be in "'+fields[0]+'" format which is not supported.')

        if len(fields) != 8:
            raise InvalidRoomHeader('Room header contains %d fields (8 expected)' % len(fields))

        for idx,tp in enumerate((str, str, int, str, list, (int,float), (int,float), int)):
            if not isinstance(fields[idx], tp):
                raise InvalidRoomHeader('Room header field #%d (%s) type mismatch' % (idx, repr(fields[idx])))

        if fields[5] == 0 and fields[6] == 0:
            ref = None
        else:
            ref = (fields[5], fields[6])

        return dict(
                format=fields[0],
                id=fields[1],
                page=fields[2],
                name=fields[3],
                also=fields[4],
                ref=ref,
                objlines=fields[7],
        )

    def parse_footer(self, footer):
        "decode room or page footer line and return dictionary of its fields."

        fields = footer.split()
        if len(fields) != 3:
            raise InvalidMapDataFooter('Footer line should have three fields (%d found instead)' % len(fields))

        if fields[0][0] != '%':
            raise InvalidMapDataFooter('Invalid footer format at "'+fields[0]+'".')

        try:
            return dict(
                    checksum = base64.b64decode(fields[0][1:]),
                    compiled = datetime.datetime.strptime(fields[1], '%Y-%m-%dT%H:%M:%S.%f'),
                    modified = datetime.datetime.strptime(fields[2], '%Y-%m-%dT%H:%M:%S.%f'),
            )
        except Exception as e:
            raise InvalidMapDataFooter('Unable to understand footer line: "%s" (%s)' % (footer, e))

    def load_page_file(self, fileobj):
        "Load a page (returning a new MapPage object) from an encoded file, given a file object to read."
        return self.load_page_list(fileobj.readlines())

    def load_page(self, filedata):
        return self.load_page_list(filedata.splitlines(True))

    def load_page_list(self, lines):
        lines = [s.replace('\r\n', '\n') for s in lines]

        if len(lines) < 2:
            raise MapDataLengthError('Truncated or corrupt page data (only %d line%s)' % (
                len(lines), 's' if len(lines) != 1 else ''))

        header = self.parse_page_header(lines[0])
        if len(lines) < header['bglines'] + 2:
            raise MapDataLengthError('Truncated or corrupt page data (only %d of %d lines)' % (
                len(lines), header['bglines'] + 2))
        footer = self.parse_footer(lines[header['bglines']+1])

        for extra_line in lines[header['bglines']+2:]:
            if extra_line.strip():
                raise MapDataLengthError('Extra line(s) after end of data: ' + extra_line)

        s1 = hashlib.sha1((''.join(lines[:header['bglines']+1])).encode('utf-8')).digest()
        if s1 != footer['checksum']:
            raise MapDataChecksumError('Page data checksum error (was %s, expected %s).' % (
                base64.b64encode(s1), base64.b64encode(footer['checksum'])))

        return MapPage(header['page'], realm=header['realm'], orient=header['orient'], creators=header['creators'],
                bg=self.decode_object_list(' '.join(lines[1:header['bglines']+1])),
                source_compiled_date=footer['compiled'], source_modified_date=footer['modified'])

    def load_room_file(self, fileobj):
        "Load a room (returning a new MapRoom object) from an encoded file, given a file object to read."
        return self.load_room_list(fileobj.readlines())

    def load_room(self, roomdata):
        return self.load_room_list(roomdata.splitlines(True))

    def load_room_list(self, lines):
        lines = [s.replace('\r\n', '\n') for s in lines]

        if len(lines) < 2:
            raise MapDataLengthError('Truncated or corrupt room data (only %d line%s)' % (
                len(lines), 's' if len(lines) != 1 else ''))

        header = self.parse_room_header(lines[0])
        if len(lines) < header['objlines'] + 2:
            raise MapDataLengthError('Truncated or corrupt room data (only %d of %d lines)' % (
                len(lines), header['objlines'] + 2))
        footer = self.parse_footer(lines[header['objlines']+1])

        for extra_line in lines[header['objlines']+2:]:
            if extra_line.strip():
                raise MapDataLengthError('Extra line(s) after end of data: ' + extra_line)

        s1 = hashlib.sha1((''.join(lines[:header['objlines']+1])).encode('utf-8')).digest()
        if s1 != footer['checksum']:
            raise MapDataChecksumError('Room data checksum error (was %s, expected %s).' % (
                base64.b64encode(s1), base64.b64encode(footer['checksum'])))

        return header['page'], MapRoom(header['id'], None, name=header['name'], also=header['also'],
                map=self.decode_object_list(' '.join(lines[1:header['objlines']+1])),
                source_modified_date=footer['modified'], source_compiled_date=footer['compiled'],
                reference_point=header['ref']
        )
#@[00]@| Ragnarok MagicMapper 6.1.0-alpha.0
#@[01]@|
#@[10]@| Copyright ?? 2010, 2018, 2020, 2021, 2022 by Steven L. Willoughby, Aloha, Oregon, USA.
#@[11]@| All Rights Reserved. Licensed under the terms and conditions of the BSD-3-Clause
#@[12]@| License as described in the accompanying LICENSE file distributed with MagicMapper.
#@[13]@|
#@[20]@| Based on earlier code from the Ragnarok MudShell (MSH) client,
#@[21]@| Copyright ?? 1993, 2000-2003 by Steven L. Willoughby, Aloha, Oregon, USA.
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
#@[44]@| CONTRIBUTORS ???AS IS??? AND ANY EXPRESS OR IMPLIED WARRANTIES,
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
