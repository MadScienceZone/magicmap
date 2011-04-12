# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Map Compiler
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

from RagnarokMUD.MagicMapper.MapSource      import MapSource, MapFileFormatError
from RagnarokMUD.MagicMapper.MapPage        import MapPage
from RagnarokMUD.MagicMapper.MapRoom        import MapRoom
from RagnarokMUD.MagicMapper.MapDataHandler import MapDataHandler
from RagnarokMUD.MagicMapper.Local          import gen_public_room_id
import os, os.path, datetime, re, sys

def make_world(source_tree, dest_tree, creator_from_path=False, ignore_errors=False):
    '''Perform the work of compiling MUD-side files to our digested format.

    If the optional creator_from_path parameter is True, then the creator
    list for a page is the list of wizard names whose files are included in
    the page, where the incoming filename is assumed to be of the form:
      .../players/<creator_name>/...
    or they are base world maps.  IT IS CRITICAL that all user-generated
    content have ".../players/<creator_name>/..." up front in the path
    pattern or identity checks will fail.

    THIS ALSO IMPLIES that creator_from_path MUST be set True in order
    for permissions to be enforced.  In practice, this should ALWAYS
    be set in production use.

    It is assumed that the directory structure under <dest_tree> is the
    same as the usual web root for the map (e.g., .../magicmap):
      <dest_tree>/page/###
      <dest_tree>/room/a/ab/abfile

    If ignore_errors is set, exceptions raised during operations will be
    reported but not allowed to stop execution of the overall map (although
    the realms where errors occurred may be incomplete).
    '''

    magic_map = MapSource()
    translator = MapDataHandler()
    compile_dtm = datetime.datetime.now()
    #
    # This regex is a bit naive, but it will work as long
    # as your system uses a single path separator string
    # (sorry VMS)
    #

    creator_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+r'(\w+)')
    rootdir_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+'\w+$')
    map_dir_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+'\w+'+re.escape(os.path.sep)+'map('+re.escape(os.path.sep)+'.*)?$')
    #core_re    = re.compile(re.escape(os.path.sep)+r'room\b')

    for root, dirnames, filenames in os.walk(source_tree):
        #for each_dir in os.path.split(root):
        # prune to include only ~/realm.map and ~/map/...*.map
        # and the base "realm.map" (anywhere outside player files)
        creator_name = None
        if creator_from_path:
            creator_m = creator_re.search(root)
            if creator_m:
                creator_name = creator_m.group(1)
                if rootdir_re.search(root):
                    if 'realm.map' in filenames:
                        filenames = ['realm.map']
                    else:
                        continue
                elif not map_dir_re.search(root):
                    continue
            else:
                creator_name = 'Base World Map'

        for filename in filenames:
            if filename.endswith('.map'):
                try:
                    src_filename = os.path.join(root, filename)
                    magic_map.add_from_file(open(src_filename), 
                            creator=creator_name, enforce_creator=True, 
                            source_date=datetime.utcfromtimestamp(os.stat(src_filename).st_mtime))
                except Exception, e:
                    if ignore_errors:
                        sys.stderr.write('%s: parser error: %s\n' % (src_filename, e))
                    else:
                        raise MapFileFormatError('Error in %s: %s' % (src_filename, e))
#
# At this point, we have the whole known world map in magic_map.
# Export this out in the client-readable format to our output
# directory structure...
#
    if not os.path.exists(os.path.join(dest_tree, 'page')):
        os.makedirs(os.path.join(dest_tree, 'page'))

    for page in magic_map.pages.values():
        with open(os.path.join(dest_tree, 'page', str(page.page)), 'w') as p:
            p.write(translator.dump_page(page, gentime=compile_dtm) + '\n')
        # XXX suppress if didn't change since last run XXX
        
        for room in page.rooms.values():
            public_room_id = gen_public_room_id(room.id)
            if not public_room_id:
                raise ValueError('public room ID generated from %s was empty!' % room.id)
            target_dir = os.path.join(dest_tree, 'room', public_room_id[:1], public_room_id[:2])
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            target_name = os.path.join(target_dir, public_room_id)
            if os.path.exists(target_name) and room.source_modified_date:
                # don't overwrite if we have nothing new to do
                if datetime.utcfromtimestamp(os.stat(target_name).st_mtime) >= room.source_modified_date:
                    continue

            with open(target_name, 'w') as rm:
                rm.write(translator.dump_room(room, public_id_filter=gen_public_room_id, gentime=compile_dtm) + '\n')
            if room.source_modified_date:
                #match the source's timestamp
                os.utime(target_name, 
                        (time.time(), time.mktime(room.source_modified_date.utctimetuple())))
