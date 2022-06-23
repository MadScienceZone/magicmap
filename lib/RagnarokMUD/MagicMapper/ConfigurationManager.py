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
# RAGNAROK MAGIC MAPPER SOURCE CODE: Configuration Manager
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
#@[00]@| Ragnarok MagicMapper 6.1.0-alpha.0
#@[01]@|
#@[10]@| Copyright © 2010, 2018, 2020, 2021, 2022 by Steven L. Willoughby, Aloha, Oregon, USA.
#@[11]@| All Rights Reserved. Licensed under the terms and conditions of the BSD-3-Clause
#@[12]@| License as described in the accompanying LICENSE file distributed with MagicMapper.
#@[13]@|
#@[20]@| Based on earlier code from the Ragnarok MudShell (MSH) client,
#@[21]@| Copyright © 1993, 2000-2003 by Steven L. Willoughby, Aloha, Oregon, USA.
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
#@[44]@| CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES,
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
