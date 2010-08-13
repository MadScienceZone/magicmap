# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Setup
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
# Setup script for installing MagicMapper on your system.
# To install, run:
#
#    setup.py install
#

from distutils.core import setup

setup(
    name = 'MagicMapper',
    version = '3.0a1',
    description = 'Ragnarok MUD Mapping Client',
    long_description = '''
        The Magic Mapper client draws a real-time map of your exploration
        of the Ragnarok MUD game.  You may use it as a full player client
        (stand-alone mode), or in conjunction with a client of your choice
        (mapping proxy mode).
    ''',
    author = 'Steve Willoughby',
    author_email = 'fizban@rag.com',
    url = 'http://www.rag.com/downloads/MagicMapper',
    packages = [
        'RagnarokMUD',
        'RagnarokMUD.MagicMapper',
    ],
    scripts = [
        'dist_bin/magicmapper',
    ],
    package_dir = {'': 'lib'},
    requires = [
    ],
    provides = ['RagnarokMUD.MagicMapper'],
)
