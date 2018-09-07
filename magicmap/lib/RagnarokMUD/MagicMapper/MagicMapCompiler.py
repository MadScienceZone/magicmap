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

from RagnarokMUD.MagicMapper.MapSource      import MapSource, PostScriptMapSource, MapFileFormatError
from RagnarokMUD.MagicMapper.MapPage        import MapPage, LANDSCAPE
from RagnarokMUD.MagicMapper.MapRoom        import MapRoom
from RagnarokMUD.MagicMapper.MapDataHandler import MapDataHandler
from RagnarokMUD.MagicMapper.Local          import gen_public_room_id
import os, os.path, datetime, re, sys, time

def make_world(source_trees, dest_tree, creator_from_path=False, ignore_errors=False, enforce_creator=True, verbosity=0):
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
    if verbosity:
        sys.stderr.write("MagicMapCompiler.make_world(source_trees={0}, dest_tree={1}, creator_from_path={2}, ignore_errors={3}, verbosity={4})\n".format(`source_trees`, `dest_tree`, `creator_from_path`, `ignore_errors`, `verbosity`))
        sys.stderr.write("compile_dtm={0}\n".format(compile_dtm))

    creator_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+r'(\w+)')
    rootdir_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+'\w+$')
    map_dir_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+'\w+'+re.escape(os.path.sep)+'map('+re.escape(os.path.sep)+'.*)?$')
    rootmap_re = re.compile(re.escape(os.path.sep)+'map('+re.escape(os.path.sep)+'.*)?$')
    #core_re    = re.compile(re.escape(os.path.sep)+r'room\b')

    for source_tree in source_trees:
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
                            if verbosity > 2:
                                sys.stderr.write(root+" is player area w/o realm.map file; Skipping\n")
                            continue
                    elif not map_dir_re.search(root):
                        if verbosity > 2:
                            sys.stderr.write("Skipping non-map dir "+root+"\n")
                        continue
                elif not rootmap_re.search(root):
                    if verbosity > 2:
                        sys.stderr.write("Skipping base mudlib non-map dir "+root+"\n")
                    continue
                    
            if verbosity>1:
                sys.stderr.write("Scanning {0}, creator={1}\n".format(root, creator_name))

            # prune subdirs whose names begin with .
            for hidden_dir_name in [d for d in dirnames if d.startswith('.')]:
                dirnames.remove(hidden_dir_name)

            for filename in filenames:
                if filename.endswith('.map'):
                    if verbosity:
                        sys.stderr.write("   "+filename+"\n")
                    try:
                        src_filename = os.path.join(root, filename)
                        magic_map.add_from_file(open(src_filename), 
                                creator=creator_name, enforce_creator=enforce_creator, 
                                source_date=datetime.datetime.utcfromtimestamp(os.stat(src_filename).st_mtime),
                                verbosity=verbosity)
                    except Exception, e:
                        if ignore_errors:
                            sys.stderr.write('%s: parser error: %s\n' % (src_filename, e))
                        else:
                            raise MapFileFormatError('Error in %s: %s' % (src_filename, e))
                elif verbosity > 2:
                    sys.stderr.write("   (Skipping {0})\n".format(filename))
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
                if datetime.datetime.utcfromtimestamp(os.stat(target_name).st_mtime) >= room.source_modified_date:
                    continue

            with open(target_name, 'w') as rm:
                print "** writing", target_name,"**"
                rm.write(translator.dump_room(room, public_id_filter=gen_public_room_id, gentime=compile_dtm) + '\n')
            if room.source_modified_date:
                #match the source's timestamp
                print "** setting time stamp **"
                os.utime(target_name, 
                        (time.time(), time.mktime(room.source_modified_date.utctimetuple())))

def make_master_map(source_tree_list, dest_filename, creator_from_path=False, ignore_errors=False, enforce_creator=True, verbosity=0):
    '''Perform the work of compiling MUD-side files to an old-style PostScript file.
    This works like the make_world function other than not actually compiling the code
    and producing a single output file.'''

    magic_map = PostScriptMapSource()
    
#    translator = MapDataHandler()
#    compile_dtm = datetime.datetime.now()
    #
    # This regex is a bit naive, but it will work as long
    # as your system uses a single path separator string
    # (sorry VMS)
    #
    if verbosity:
        sys.stderr.write("MagicMapCompiler.make_master_map(source_tree={0}, dest_file={1}, creator_from_path={2}, ignore_errors={3}, verbosity={4})\n".format(`source_tree_list`, `dest_filename`, `creator_from_path`, `ignore_errors`, `verbosity`))

    creator_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+r'(\w+)')
    rootdir_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+'\w+$')
    map_dir_re = re.compile(re.escape(os.path.sep)+'players'+re.escape(os.path.sep)+'\w+'+re.escape(os.path.sep)+'map('+re.escape(os.path.sep)+'.*)?$')
    rootmap_re = re.compile(re.escape(os.path.sep)+'map('+re.escape(os.path.sep)+'.*)?$')

    for source_tree in source_tree_list:
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
                            if verbosity > 2:
                                sys.stderr.write(root+" is player area w/o realm.map file; Skipping\n")
                            continue
                    elif not map_dir_re.search(root):
                        if verbosity > 2:
                            sys.stderr.write("Skipping non-map dir "+root+"\n")
                        continue
                elif not rootmap_re.search(root):
                    if verbosity > 2:
                        sys.stderr.write("Skipping base mudlib non-map dir "+root+"\n")
                    continue
                    
            if verbosity>1:
                sys.stderr.write("Scanning {0}, creator={1}\n".format(root, creator_name))

            # prune subdirs whose names begin with .
            for hidden_dir_name in [d for d in dirnames if d.startswith('.')]:
                dirnames.remove(hidden_dir_name)

            for filename in filenames:
                if filename.endswith('.map'):
                    if verbosity:
                        sys.stderr.write("   "+filename+"\n")
                    try:
                        src_filename = os.path.join(root, filename)
                        magic_map.add_from_file(open(src_filename), 
                                creator=creator_name, enforce_creator=enforce_creator, 
                                source_date=datetime.datetime.utcfromtimestamp(os.stat(src_filename).st_mtime),
                                verbosity=verbosity)
                    except Exception, e:
                        if ignore_errors:
                            sys.stderr.write('%s: parser error: %s\n' % (src_filename, e))
                        else:
                            raise MapFileFormatError('Error in %s: %s' % (src_filename, e))
                elif verbosity > 2:
                    sys.stderr.write("   (Skipping {0})\n".format(filename))
#
# At this point, we have the whole known world map in magic_map.
# We need to output this with a compatability-adjusting PostScript preamble.
#
    with open(dest_filename, 'w') as dest_file:
        dest_file.write('''%!PS-Adobe-2.0
%%Title: Ragnarok Magic Map
%%Creator: Klive and Fizban of Ragnarok
%%EndComments
%
% Ragnarok Magic Map PostScript Preamble by Fizban (from an earlier idea
% by Klive)  $Revision: 1.11 $ $Date: 2002/11/14 08:51:56 $
%
2 setlinecap 0 setlinejoin 4 setmiterlimit /lw {setlinewidth} def
/ct {curveto} def /ln {lineto} def /mv {moveto} def /sg {setgray} def
/rln {rlineto} def /rmv {rmoveto} def
/sd {setdash} def /bk {0 sg} def /gr {.5 sg} def /wh {1 sg} def
/np {newpath} def /cp {closepath} def /fi {cp fill} def /a  {gsave} def
/z  {grestore} def /xl {translate} def /Pbuf 2 string def
/txtf {/Helvetica-Bold findfont 8 scalefont setfont} def
/rmnf {/Helvetica findfont 6 scalefont setfont} def
/it {/Times-Italic findfont exch scalefont setfont} def
/ss {/Helvetica findfont exch scalefont setfont} def
/bf {/Helvetica-Bold findfont exch scalefont setfont} def
/tt {/Courier-Bold findfont exch scalefont setfont} def
/sl {/Helvetica-Oblique findfont exch scalefont setfont} def
/std {50 20} def /stdr {30} def /proto {/Xrp true def} def
/outdoor {/Xro true def} def
/dark {/Xrd .9 def} def
/shaded {/Xrd exch def} def
/offpage {/Xpq true def} def
/in {/Xpi true def} def
/out {/Xpo true def} def
/special {[3 2] 4 sd} def
/locked {/Xpl true def} def
/roomFileName () def 
/Xro {false} def /Xrp {false} def /Xrd {1} def /Xpq {false} def
/Xpi {false} def /Xpo {false} def /Xpl {false} def
/bx { /XbH exch def /XbW exch def np mv 0 XbH rlineto XbW 0 rlineto 
0 XbH neg rlineto cp } def
/box      { bx stroke } def
/shadebox { /XXXpct exch def bx XXXpct sg fill bk } def
/room {/Xrpl 20 def /XrH exch def /XrW exch def /XrY exch def /XrX exch def
XrX XrY XrW XrH Xrd shadebox Xro {2 lw gr} {1 lw bk} ifelse 
Xrp {[4 2] 0 sd} if XrX XrY XrW XrH box 1 lw bk []0 sd txtf
dup length 0 gt {XrX 6 add XrY 2 add mv show XrX 6 add XrY 12 add mv show
} { pop XrX 6 add XrY 7 add mv show } ifelse
/XrW2 { XrW 2 div } def /XrH2 { XrH 2 div } def
/north {XrW2 XrX add dup XrY XrH add exch XrY 
XrH add Xrpl add XrW2 XrX add 720} def
/south {XrW2 XrX add dup XrY exch XrY Xrpl sub XrW2 XrX add 0} def
/east {XrX XrW add XrY XrH2 add dup XrX XrW 
add Xrpl add exch 612 XrY XrH2 add} def
/west {XrX XrH2 XrY add XrX Xrpl sub XrH2 XrY add 0 XrH2 XrY add} def
/northeast{XrX XrW add XrY XrH add XrX XrW add Xrpl add 
XrY XrH add Xrpl add 2 copy } def
/northwest{XrX XrY XrH add XrX Xrpl sub XrY XrH add Xrpl add 2 copy} def
/southeast{XrX XrW add XrY XrX XrW add Xrpl add XrY Xrpl sub 2 copy} def
/southwest{XrX XrY XrX Xrpl sub XrY Xrpl sub 2 copy} def clrm 
roomFileName length 0 gt { rmnf XrX XrY 6 sub mv roomFileName show txtf } if
/roomFileName () def } def
/passageLength { /Xrpl exch def } def
/round-room {/Xrpl 20 def /XrR exch def /XrY exch def /XrX exch def
np XrX XrY XrR 0 360 Xrd sg arc fill
Xro {2 lw gr} {1 lw bk} ifelse Xrp {[4 2] 0 sd} if
XrX XrY XrR 0 360 arc stroke 1 lw bk []0 sd txtf
dup length 0 gt {XrX 15 sub XrY 6 sub mv show XrX 15 sub XrY 4 add mv show
} { pop XrX 15 sub XrY 3 sub mv show } ifelse
/north {XrX XrY XrR add 2 copy Xrpl add XrX 720} def
/south {XrX XrY XrR sub 2 copy Xrpl sub XrX 0 } def
/east  {XrX XrR add dup XrY exch Xrpl add XrY 612 XrY } def
/west  {XrX XrR sub dup XrY exch Xrpl sub XrY 0 XrY } def
/XrA {.7070 XrR mul} def 
/northeast { XrX XrA add XrY XrA add XrX XrR add Xrpl add XrY XrR add Xrpl add 
2 copy} def
/northwest { XrX XrA sub XrY XrA add XrX XrR sub Xrpl sub XrY XrR add Xrpl add 
2 copy} def
/southeast { XrX XrA add XrY XrA sub XrX XrR add Xrpl add XrY XrR sub Xrpl sub 
2 copy} def
/southwest { XrX XrA sub XrY XrA sub XrX XrR sub Xrpl sub XrY XrR sub Xrpl sub 
2 copy} def clrm 
roomFileName length 0 gt { rmnf XrX 20 sub XrY 20 sub mv roomFileName show txtf } if
/roomFileName () def } def
/clrm { /Xro {false} def /Xrp {false} def /Xrd {1} def } def
/arrow { /Ay2 exch def /Ax2 exch def /Ay1 exch def /Ax1 exch def
/dy Ay2 Ay1 sub def /dx Ax2 Ax1 sub def
/Al dx dx mul dy dy mul add sqrt def /An dy dx atan def
/Ab Al 10 sub def a Ax1 Ay1 translate An rotate
np 0 -.5 mv Ab -.5 ln Ab -2 ln Al 0 ln Ab 2 ln Ab .5 ln 0 .5 ln fi z } def
/passage { Xpq {4 2 roll} if pop pop bk Xpi { 4 2 roll } if 
Xpi Xpo or { arrow } { np 4 2 roll mv ln stroke } ifelse
[]0 sd /Xpq {false} def /Xpi {false} def /Xpo {false} def /Xrpl 20 def } def
/door { pop pop pop pop /XpY exch 4 sub def /XpX exch 4 sub def
XpX XpY 8 8 1 shadebox bk XpX XpY 8 8 box
Xpl {XpX 4 add XpY 4 add 1.5 0 360 arc fill} if /Xpl {false} def } def
%
% the following still needs to be optimized
%
/tree_outline1 { newpath 20 22 7 350 120 arc 12 25 6 40 180 arc
6 19 4 60 210 arc 12 12 8 150 270 arc 16 6 3 180 10 arc 23 10 5 220 60 arc
29 17 4 250 90 arc closepath } def
/tree1 { .7 setgray .5 .5 scale tree_outline1 fill 0 setgray tree_outline1
stroke newpath 20 13 3 200 40 arc stroke newpath 15 18 3 60 240 arc
stroke 2 2 scale } def
/tree2 { 90 rotate tree1 -90 rotate } def
/clump1 { 12 12 translate tree1 -12 -12 translate
0 12 translate tree1 0 -12 translate 12 0 translate tree1 -12 0 translate } def
/clump2 { -15 -5 translate tree2 15 5 translate
0 12 translate tree2 0 -12 translate 14 2 translate tree2 -14 -2 translate } def
/boxnum { newpath moveto 20 0 rlineto 0 20 rlineto
-20 0 rlineto closepath stroke 5 10 translate show } def
/Tree1 { a translate tree1 z } def
/Tree2 { a translate tree2 z } def
/Clump1 { a translate clump1 z } def
/Clump2 { a translate clump2 z } def
/Boxnum { a translate boxnum z } def
% w h bps Sx Sy x y DrawImage hexdata(w*h*bps bits of greyscale)
/DrawImage { gsave translate scale 3 copy mul mul 8 div ceiling cvi 
/_DI_buffer exch string def 3 copy pop dup neg 0 3 -1 roll 4 -1 roll 
0 0 6 -3 roll 6 array astore {currentfile _DI_buffer readhexstring pop} 
image grestore } def
% w h bps Sx Sy x y DrawColorImage hexdata(w*h*bps bits*3 (r,g,b))
/DrawColorImage { gsave translate scale 3 copy mul mul 3 mul 8 div ceiling 
cvi /_DI_buffer exch string def 3 copy pop dup neg 0 3 -1 roll 4 -1 roll 
0 0 6 -3 roll 6 array astore {currentfile _DI_buffer readhexstring pop}
false 3 colorimage grestore } def
/color { setrgbcolor } def
/colorbox { color bx fill bk } def
%
%
/mazearea { aload length 2 div 1 sub cvi 3 1 roll np mv {ln} repeat cp Xrd 
sg fill bk clrm } def /mazewall { aload length 2 div 1 sub cvi 3 1 roll
np mv {ln} repeat Xro {2 lw gr} {1 lw bk} ifelse Xrp {[4 2] 0 sd} if
stroke clrm } def /mazeroom { dup /XXrp Xrp def /XXro Xro def /XXrd Xrd def 
mazearea /Xrp XXrp def /Xro XXro def /Xrd XXrd def mazewall } def
/dotmark { np 0 360 arc fill } def
%
% Graph paper
%
/MM_PortGrid { gsave 0 0 1 setrgbcolor [3 2] 4 setdash newpath
30 30 moveto 30 700 lineto 580 700 lineto 580 30 lineto closepath stroke
grestore gsave 35 5 575 { dup 30 mod 0 eq { .6 setgray .6 setlinewidth
} { .8 setgray .25 setlinewidth } ifelse newpath dup 30 moveto 700 lineto
stroke } for 35 5 695 { dup 30 mod 0 eq { .6 setgray .6 setlinewidth } {
.8 setgray .25 setlinewidth } ifelse newpath dup 30 exch moveto 580 exch lineto
stroke } for grestore gsave .8 0 0 setrgbcolor /Helvetica findfont 10 
scalefont setfont 30 30 560 { dup dup 702 moveto 4 string cvs show
dup 30 moveto 4 string cvs show } for 0 .8 0 setrgbcolor 30 30 710 {
dup dup 30 exch moveto 4 string cvs show dup 570 exch moveto 4 string cvs show
} for grestore bk } def
/MM_LandGrid { gsave gsave 0 0 1 setrgbcolor [3 2] 4 setdash newpath
30 30 moveto 30 580 lineto 700 580 lineto 700 30 lineto closepath
stroke grestore gsave 35 5 695 { dup 30 mod 0 eq { .6 setgray
.6 setlinewidth } { .8 setgray .25 setlinewidth } ifelse newpath
dup 30 moveto 580 lineto stroke } for 35 5 575 { dup 30 mod 0 eq {
.6 setgray .6 setlinewidth } { .8 setgray .25 setlinewidth } ifelse
newpath dup 30 exch moveto 700 exch lineto stroke } for grestore
gsave .8 0 0 setrgbcolor /Helvetica findfont 10 scalefont setfont
30 30 680 { dup dup 32 moveto 4 string cvs show dup 570 moveto
4 string cvs show } for 0 .8 0 setrgbcolor 30 30 580 { dup dup 5 exch moveto
4 string cvs show dup 690 exch moveto 4 string cvs show } for bk grestore
grestore } def
%
% End preamble.
%
% Ragnarok Magic Map Title Blocks
/NewPage {
    ()               15  1  30 760 380 20 ZZbox
	(PRINTED)        10 .9 410 760 110 20 ZZbox
	(REALM CREATOR)  10 .9  30 740 490 20 ZZbox
    (PAGE)           30  1 520 760  60 40 ZZrbox
	(REALM)          10  1  30 720 550 20 ZZbox

	bk txtf
	LSMODE { a -90 rotate -720 0 translate } if 
} def
/LSMODE false def
/LandscapeMap { /LSMODE true def } def
/EndPage { LSMODE { z /LSMODE false def } if showpage } def

%
% A B sz color x y w h stbox - B A 
%
/ZZstbox {
        /ZZboxHeight exch def
        /ZZboxWidth  exch def
        /ZZboxY      exch def
        /ZZboxX      exch def

        setgray
        .5 setlinewidth
        newpath
                ZZboxX ZZboxY moveto
                0 ZZboxHeight neg rlineto
                ZZboxWidth 0 rlineto
                0 ZZboxHeight rlineto
        closepath fill
        0 setgray
        newpath
                ZZboxX ZZboxY moveto  
                0 ZZboxHeight neg rlineto
                ZZboxWidth 0 rlineto  
                0 ZZboxHeight rlineto 
        closepath stroke
		/Helvetica findfont exch scalefont setfont
        exch
} def

%
% text title color x y w h box -
% 
/ZZbox {
        ZZstbox
        ZZboxX 10 add ZZboxY ZZboxHeight sub 3 add moveto
        show
        ZZboxX 2 add ZZboxY 1 6 add sub moveto
        /Helvetica findfont 6 scalefont setfont show
} def
%
% text title color x y w h rbox -                     for right-justified text
%
/ZZrbox {
        ZZstbox
        dup stringwidth pop ZZboxWidth ZZboxX add exch sub 3 sub ZZboxY ZZboxHeight sub
                5 add moveto
        show
        ZZboxX 2 add ZZboxY 1 6 add sub moveto
        /Helvetica findfont 6 scalefont setfont show
} def
%%EndProlog
%
% V5-V6 Compatibility macros
% Fizban, 06-Sep-2018
%
% /name string sdef -           (use regular def for real PostScript)
% /name number ndef -           (use regular def for real PostScript)
% 
/sdef {def} def
/ndef {def} def
/passagelength {passageLength} def
/scurveto {pop} def
%
% x y w h imageID graphic -     (make placeholder box for now)
%
/graphic {
    /MmGfxI exch def
    /MmGfxH exch def
    /MmGfxW exch def
    /MmGfxY exch def
    /MmGfxX exch def

    gsave
        bk [3 2] 4 sd 2 lw
        np MmGfxX MmGfxY moveto
        0 MmGfxH rlineto
        MmGfxW 0 rlineto
        0 MmGfxH neg rlineto
        cp stroke
        np MmGfxX MmGfxY moveto MmGfxW MmGfxH rlineto stroke
        np MmGfxX MmGfxY MmGfxH add moveto MmGfxW MmGfxH neg rlineto stroke
    grestore
    MmGfxI (IMAGE ID) 8 1 MmGfxX MmGfxY MmGfxH 2 div add 10 add MmGfxW 20 ZZbox
} def
%
% End Compatibility Code
%
''')

        def _ps(str):
            return str.replace('\\', '\\\\').replace('(','\\(').replace(')','\\)')

        now_str = time.ctime()
        for seq, page_no in enumerate(sorted(magic_map.pages)):
            page = magic_map.pages[page_no]

            dest_file.write("%%Page: {0} {1}\n".format(page_no, seq))
            dest_file.write("%---------------------[ Page {0} ]---------------------\n".format(page_no))
            if page.orient == LANDSCAPE:
                dest_file.write("LandscapeMap\n")
            dest_file.write("({0})({1})({2})({3})({4})NewPage\n".format(
                _ps(page.realm or 'Ragnarok (the world at large)'),
                page_no,
                _ps(', '.join(page.creators) if page.creators else 'The gods and wizards of Ragnarok'),
                _ps(now_str),
                _ps('Magic Map of Ragnarok')
            ))
            dest_file.write('\n'.join(page.bg))

            for room in page.rooms.values():
                dest_file.write('%---[ {0} ]---\n{1}\n'.format(room.id, '\n'.join(room.map) if isinstance(room.map, list) else (room.map or '')))
            dest_file.write('EndPage\n')
#    
#    for page in magic_map.pages.values():
#        with open(os.path.join(dest_tree, 'page', str(page.page)), 'w') as p:
#            p.write(translator.dump_page(page, gentime=compile_dtm) + '\n')
#        # XXX suppress if didn't change since last run XXX
#        
#        for room in page.rooms.values():
#            public_room_id = gen_public_room_id(room.id)
#            if not public_room_id:
#                raise ValueError('public room ID generated from %s was empty!' % room.id)
#            target_dir = os.path.join(dest_tree, 'room', public_room_id[:1], public_room_id[:2])
#            if not os.path.exists(target_dir):
#                os.makedirs(target_dir)
#
#            target_name = os.path.join(target_dir, public_room_id)
#            if os.path.exists(target_name) and room.source_modified_date:
#                # don't overwrite if we have nothing new to do
#                if datetime.datetime.utcfromtimestamp(os.stat(target_name).st_mtime) >= room.source_modified_date:
#                    continue
#
#            with open(target_name, 'w') as rm:
#                print "** writing", target_name,"**"
#                rm.write(translator.dump_room(room, public_id_filter=gen_public_room_id, gentime=compile_dtm) + '\n')
#            if room.source_modified_date:
#                #match the source's timestamp
#                print "** setting time stamp **"
#                os.utime(target_name, 
#                        (time.time(), time.mktime(room.source_modified_date.utctimetuple())))
