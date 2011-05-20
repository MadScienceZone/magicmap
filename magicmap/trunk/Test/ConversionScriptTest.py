# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: Magic Map Conversion
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

import unittest
import shutil
import os.path
import os
import hashlib
import base64
import datetime
from RagnarokMUD.MagicMapper.MagicMapCompiler import make_world

SRC=os.path.join('data','world')           # map source files (*.map)
DST=os.path.join('data','compiled')        # compiled output for clients (built here)
DSTC=os.path.join('data','compiled_creators') # compiled output for clients including realm creators (built here)
CMP=os.path.join('data','compiled_good')   # known-good output for clients (compared)
CMPC=os.path.join('data','compiled_good_creators')   # known-good output for clients (compared)

class DataFormatError (Exception):
    "We encountered something evil when trying to grok the map files we obtained."

class ConversionScriptTest (unittest.TestCase):
    def test_map_conversion_process(self):
        if os.path.exists(DST):
            shutil.rmtree(DST)

        os.mkdir(DST, 0755)
        make_world(source_tree=SRC, dest_tree=DST, enforce_creator=False)
        self.assertTreesEqual(DST, CMP)

    def test_map_conversion_with_creators(self):
        if os.path.exists(DSTC):
            shutil.rmtree(DSTC)

        os.mkdir(DSTC, 0755)
        make_world(source_tree=SRC, dest_tree=DSTC, creator_from_path=True, verbosity=5)
        self.assertTreesEqual(DSTC, CMPC)

    def assertTreesEqual(self, actual, expected):
        "Descend directory trees and see if the files are the same"
        #
        # We need to validate that the file contents match
        # XXX timestamps inside files
        # XXX mtime matches source too
        # XXX creator's name
        #
        class FileInfo (object):
            "Track info about files we care about and compare"
            #
            # This understands that files have the internal format:
            # <header line of a bunch of stuff....> <number of lines>
            # <that many more lines of stuff...>
            # %<SHA1 checksum of data above> <generation datetime> <mtime datetime>
            #
            # We want to know that:
            # XXX the ORIGINAL file's checksum is correct, 
            # XXX AND collect the datestamps from the bottom
            #
            # In verification, we want to know that another file has:
            # XXX the same computed checksum, AND 
            # XXX its footer checksum matches AND 
            # XXX the dates are as expected AND
            # XXX the file's mtime matches the timestamp inside.
            #
            def __init__(self, path):
                self.path = path

                with open(path, 'r') as f:
                    file_contents = [s.replace('\r\n', '\n') for s in f.readlines()]

                if len(file_contents) < 2:
                    raise DataFormatError('Truncated or corrupt file (%s) (%d lines)' %
                            (path, len(file_contents)))

                try:
                    datalen = int(file_contents[0].strip().split()[-1])
                except:
                    raise DataFormatError('Malformed preamble in '+path)

                if len(file_contents) != datalen+2:
                    raise DataFormatError('Incorrect file line count (was %d, expected %d) in %s' %
                            (len(file_contents), datalen+2, path))

                self.checksum = hashlib.sha1(''.join(file_contents[:-1])).digest()

                if file_contents[-1][0] != '%':
                    raise DataFormatError('Corrupt file (%s): unexpected final line: %s' %
                            (path, file_contents[-1]))
                try:
                    claimed_checksum, gentime, mtime = file_contents[-1][1:].split()
                    self.claimed_checksum = base64.b64decode(claimed_checksum)
                    self.gentime = datetime.datetime.strptime(gentime, '%Y-%m-%dT%H:%M:%S.%f')
                    self.mtime   = datetime.datetime.strptime(mtime,   '%Y-%m-%dT%H:%M:%S.%f')
                except Exception, e:
                    raise DataFormatError('Corrupt file (%s): Cannot parse final line: %s (%s)' %
                            (path, file_contents[-1], e))

                if self.claimed_checksum != self.checksum:
                    raise DataFormatError('Corrupt file (%s): Data checksum %s but claims to be %s' %
                            (path, base64.b64encode(self.checksum), base64.b64encode(self.claimed_checksum)))


        expected_file_info = {}
        root = expected
        for dirpath, dirnames, filenames in os.walk(root):

            if dirpath.startswith(root):
                relative_dir = dirpath[len(root):]
            else:
                raise ValueError("Unexpected path "+dirpath+' encountered (should start with "'+root+'")')

            for hidden_dir_name in [d for d in dirnames if d.startswith('.')]:
                dirnames.remove(hidden_dir_name)

            for filename in filenames:
                expected_file_info[os.path.join(relative_dir,filename)] = FileInfo(os.path.join(dirpath,filename))

        root = actual
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.startswith(root):
                relative_dir = dirpath[len(root):]
            else:
                raise ValueError("Unexpected path "+dirpath+' encountered (should start with "'+root+'")')

            for hidden_dir_name in [d for d in dirnames if d.startswith('.')]:
                dirnames.remove(hidden_dir_name)

            for filename in filenames:
                path_key = os.path.join(relative_dir,filename)
                self.assert_(path_key in expected_file_info, 'Generated file "'+os.path.join(dirpath,filename)+'" not found in known-good directory.')
                actual_file_info = FileInfo(os.path.join(dirpath,filename))
                self.assertEquals(actual_file_info.checksum, expected_file_info[path_key].checksum, 'File checksum mismatch: key={0},file={1}'.format(path_key,os.path.join(dirpath,filename)))
                del expected_file_info[path_key]
            
        self.assertEquals(len(expected_file_info), 0, 'Failed to generate all files: %s\n%d unmatched files total' % (
            '\n'.join(expected_file_info.keys()),
            len(expected_file_info)))

# XXX only update new files

