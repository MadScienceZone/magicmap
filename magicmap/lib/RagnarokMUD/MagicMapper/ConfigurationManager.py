#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Configuration Manager
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

import configparser
import os.path, sys

class InvalidHomeDirectory (Exception): pass
class ConfigurationManager (configparser.SafeConfigParser):
    def __init__(self, ini_list=None):
        configparser.SafeConfigParser.__init__(self)
        self._ini_file_path = None
        #
        # defaults
        #
        my_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GUI', 'images')
        self.image_path = my_image_path
        my_home_dir = os.path.expanduser('~')
        if my_home_dir == '~':
            raise InvalidHomeDirectory("unable to determine home directory")
        my_home_dir = os.path.join(my_home_dir, '.MagicMapper')
#                ('MagicMapper' if sys.platform.startswith('win') else '.MagicMapper'))

        for section_name, section_contents in {
                'rendering': {
                    'bezier_points':        '20',
                    'spline_points':        '20',
                    'canvas_left_margin':   '30',
                    'canvas_top_margin':    '50',
                    'font_magnification':   '0.85',
                    'logo_image':           os.path.join(my_image_path, 'logo_bg.gif'),
                    'background_tile':      os.path.join(my_image_path, 'parchment.gif'),
                    'page_number_font':     'r',
                    'page_number_size':     '32',
                    'page_number_x':        '180',
                    'page_number_y':        '730',
                    'page_title_font':      's',
                    'page_title_size':      '12',
                    'page_title_x':         '300',
                    'page_title_y':         '745',
                    'page_title2_x':        '300',
                    'page_title2_y':        '730',
                },
                'fonts': {
                    'bold_family':          'Helvetica',
                    'bold_weight':          'bold',
                    'bold_slant':           'roman',
                    'italic_family':        'Times',
                    'italic_weight':        'normal',
                    'italic_slant':         'italic',
                    'serif_family':         'Times',
                    'serif_weight':         'normal',
                    'serif_slant':          'roman',
                    'slanted_family':       'Helvetica',
                    'slanted_weight':       'normal',
                    'slanted_slant':        'italic',
                    'roman_family':         'Helvetica',
                    'roman_weight':         'normal',
                    'roman_slant':          'roman',
                    'roman_size':           '6',
                    'sans_family':          'Helvetica',
                    'sans_weight':          'normal',
                    'sans_slant':           'roman',
                    'text_family':          'Helvetica',
                    'text_weight':          'bold',
                    'text_slant':           'roman',
                    'text_size':            '8',
                    'typewriter_family':    'Courier',
                    'typewriter_weight':    'bold',
                    'typewriter_slant':     'roman',
                },
                'preview':  {
                    'location_delay':       '1.0',
                    'image_dir':            os.path.join(my_home_dir, 'mapimages'),
                },
                'connection': {
                    'local_hostname':       'localhost',
                    'local_port':           '2222',
                    'remote_hostname':      'rag.com',
                    'remote_port':          '2222',
                },
                'cache': {
                    'recheck_age':          '{0:d}'.format(60*60*24*3),  # 3 days
                    'location':             os.path.join(my_home_dir, 'cache'),
                    'db_base':              os.path.join(my_home_dir, 'maps'),
                },
                'server': {
                    'base_url':             'https://www.rag.com/magicmap',
                },
        }.items():
            self.add_section(section_name)
            for field_name, field_value in section_contents.items():
                self.set(section_name, field_name, field_value)

        self._ini_file_path = os.path.join(my_home_dir, 'MagicMapper.ini')
            
        if not os.path.exists(my_home_dir):
            os.mkdir(my_home_dir)

        self.read(self._ini_file_path)
        if ini_list is not None:
            self.read(ini_list)

    def save(self):
        if self._ini_file_path is not None:
            with open(self._ini_file_path, 'w') as f:
                self.write(f)

    def save_first(self):
        if self._ini_file_path is not None and not os.path.exists(self._ini_file_path):
            self.save()
