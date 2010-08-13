# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Utility Program: giantmap
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

#import shutil
#import os.path
#import os
#import hashlib
#import base64
#import datetime
import sys
sys.path.append('../lib')
import datetime
import re
import os
from RagnarokMUD.MagicMapper.MapSource import PostScriptMapSource, MapFileFormatError
from RagnarokMUD.MagicMapper.MapPage   import PORTRAIT, LANDSCAPE

LAYOUT = (
        (                               # sheet
            (1,2,3,4),       # top row
#            (page,page,page,...),       # next row
#            (page,page,page,...),       # page = (page#[,voff[,hoff]])
        ),
#        (                               
#            (page,page,page,...),
#            (page,page,page,...),
#            (page,page,page,...),
#        ),
)

source_tree='.'
magic_map = PostScriptMapSource()
compile_dtm = datetime.datetime.now()
creator_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+r'(\w+)')
core_re    = re.compile(re.escape(os.path.sep)+r'room\b')

def PS(str):
    if str is None:
        return '()'

    return '(' + str.replace('\\','\\\\').replace('(','\\(').replace(')','\\)') + ')'

for root, dirnames, filenames in os.walk(source_tree):
    for each_dir in os.path.split(root):
        creator_name = None
        creator_m = creator_re.search(root)
        if creator_m:
            creator_name = creator_m.group(1)
        elif core_re.search(root):
            creator_name = 'Base World Map'

    for filename in filenames:
        if filename.endswith('.map'):
            try:
                magic_map.add_from_file(open(os.path.join(root, filename)), creator=creator_name)
            except Exception as e:
                raise MapFileFormatError('Error in %s: %s' % (os.path.join(root, filename), e))

TARGET_SIZE = (44,34)
all_maps = magic_map.pages.keys()
LAYOUT = [
        [
            all_maps[:]
        ]
]

with open('giant-map.ps', 'w') as output_ps:
    for ps_header in 'mmap.preamble', 'mmap.rag.block':
        with open(ps_header, 'r') as preamble:
            for line in preamble:
                output_ps.write(line)

    for sheet in LAYOUT:
        output_ps.write("%" * 80 + '\n')
        output_ps.write("%" * 80 + '\n')
        for row in sheet:
            output_ps.write("%\n% --ROW--\n%\n")
            for page in row:
                if page not in all_maps:
                    raise KeyError("Page %d is not loaded!" % page)
                all_maps.remove(page)
                the_page = magic_map.pages[page]
                print "p.%d %d" % (the_page.page, len(the_page.rooms))
                output_ps.write("%%%% PAGE #%d\n" % page)
                output_ps.write("%% compiled %s\n" % compile_dtm.strftime('%d-%b-%Y %H:%M:%S.%f'))
                if the_page.source_modified_date is None:
                    output_ps.write('% modification date unknown\n')
                else:
                    output_ps.write("%% modified %s\n" % the_page.source_modified_date.strftime('%d-%b-%Y %H:%M:%S.%f'))
                if the_page.orient == LANDSCAPE:
                    output_ps.write("LandscapeMap ")
                output_ps.write("%s (%d) %s %s %s NewPage\n" % (
                        PS(the_page.realm),
                        the_page.page,
                        PS(', '.join(the_page.creators)),
                        PS(compile_dtm.strftime('%d-%b-%Y %H:%M:%S')),
                        PS("Magic Map of Ragnarok")
                    )
                )
                output_ps.write("%\n% background\n%\n")
                output_ps.write('\n'.join(the_page.bg))
                for the_room in the_page.rooms.values():
                    output_ps.write("\n%%\n%% room: %s (%s)\n%%\n" % (
                            the_room.id, the_room.name
                        )
                    )
                    output_ps.write("%% compiled %s\n" % compile_dtm.strftime('%d-%b-%Y %H:%M:%S.%f'))
                    if the_room.source_modified_date is None:
                        output_ps.write('% modification date unknown\n')
                    else:
                        output_ps.write("%% modified %s\n" % the_room.source_modified_date.strftime('%d-%b-%Y %H:%M:%S.%f'))
                    if the_room.map is not None:
                        output_ps.write('\n'.join(the_room.map))
                    output_ps.write('\n')
                output_ps.write("EndPage\n")
            output_ps.write("%% --END ROW-- %%\n")
            # [LandscapeMap] 
            # realm page creator date title NewPage
            # [MM_PortGrid][MM_LandGrid]
            # ...
            # EndPage
        output_ps.write("% END SHEET\n")
        #print "Page %3d %s %s" % (page.page, ('P' if page.orient==PORTRAIT else ('L' if page.orient==LANDSCAPE else '?')), page.realm)
if len(all_maps):
    print "Layout did not specify:", all_maps
