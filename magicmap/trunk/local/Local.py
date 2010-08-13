# vi:set ai sm nu ts=4 sw=4 expandtab:
#
###################################################################
# THIS MODULE IS FOR LOCAL MUD SITES TO MAKE CUSTOMIZED SETTINGS. #
#                                                                 #
# SEE INSTRUCTIONS BELOW.                                         #
###################################################################
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Local Settings
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
# Local room id obscuring filter
#
# You don't want players to be able to determine your room
# file names by guessing (or they'd download areas they have
# not yet visited).  Define this function to take a room ID
# string as defined in your MUDlib and return some kind of
# opaque public ID which will consistently and uniquely be
# generated from this room ID but can't easily be reversed.
#
# RESTRICTIONS:
#
# The resulting public ID MUST not include directory 
# separator characters (usually \ or /).
#
# It also MUST not contain colon (:) characters.
#
# The public ID SHOULD be at least 3 characters long.
# 

from hashlib import md5
from base64  import b64encode
from string  import translate, maketrans

def gen_public_room_id(private_id):
    "Turn private room ID to an obscured but consistent public one."

    return translate(b64encode(md5('5#m,qu3v%'+private_id+'53kreT./.').digest()),
        maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',
                  '0123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZ-abcdefghijklmnopqrstuvwxyz'),
        '=')
