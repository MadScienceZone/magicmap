# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Unit Test: Network Communications
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
import datetime
import threading
import SimpleHTTPServer, BaseHTTPServer
import urllib
import posixpath
import os, os.path
import urllib2
import time
import shutil
import email.utils

if __name__ == '__main__':
    import sys
    sys.path.append('../lib')

import unittest
from RagnarokMUD.MagicMapper.NetworkIO import NetworkIO, ServerNotAvailable, DataNotFound
from RagnarokMUD.MagicMapper.MapCacheManager import MapCacheManager

WEB_DOCROOT_LIST=['data','compiled_good']
CACHE_TEST_DIR=os.path.join('data','net_io_test_cache')
CACHE_TEST_SRC=os.path.join('data','net_io_test_cache_src')

TEST_ROOM_17261_ID='706c61796572732f66697a62616e2f696e6469612f6d617261'
TEST_ROOM_17261_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617261 21 / @ 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%aKUz1WtTsPzpSqMcxgbnoqC6TwE= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'
TEST_ROOM_17261_CACHED_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617261 21 / @CACHE 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%KJQ/lf17ITYGyehoSbtC4VfsvQI= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'
TEST_ROOM_17261_SERVER_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617261 21 / @SERVER 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%Wo8kesFY3qzG6Wo7ovTWmQ5POuQ= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'

TEST_ROOM_17262_ID='706c61796572732f66697a62616e2f696e6469612f6d617262'
TEST_ROOM_17262_CACHED_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617262 21 / @CACHE 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%jqqjwtYTeMCglESbLr0z0C0ExkM= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'
TEST_ROOM_17262_SERVER_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617262 21 / @SERVER 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%tF8mOGR0kt6GMzZJFAMWX46NSPE= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'

TEST_ROOM_17263_ID='706c61796572732f66697a62616e2f696e6469612f6d617263'
TEST_ROOM_17263_CACHED_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617263 21 / @CACHE 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%FonTC8FyWwIoA/ZHeOGvu73xlwE= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'
TEST_ROOM_17263_SERVER_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617263 21 / @SERVER 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%FzPcpJ+xLb9HwgRLWNwBWWeNtSs= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'

TEST_ROOM_17264_ID='706c61796572732f66697a62616e2f696e6469612f6d617264'
TEST_ROOM_17264_CACHED_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617264 21 / @CACHE 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%wUOyUsxS43iXvV4mMEBM6UjTWk8= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'
TEST_ROOM_17264_SERVER_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617264 21 / @SERVER 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%D+CqYfJvslM0nEDCxtlWo0/kqhg= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'

TEST_ROOM_17265_ID='706c61796572732f66697a62616e2f696e6469612f6d617265'
TEST_ROOM_17265_CACHED_DATA='R6 /706c61796572732f66697a62616e2f696e6469612f6d617265 21 / @CACHE 315 350 2\r\n:4 :8 R 290 340 50 20 Mara%27s Statue :3 :2 e 20 :2 w 20 :2 s 20 :2 P :4 360\r\n350 420 350 :5 V 290 340 280 330 :4 S 290 330 Dn\r\n%qARbefRrlwvnj1CNHvvzBywDF6o= 2010-04-12T01:36:04.725000 2010-04-12T01:36:06.268000\r\n'

TEST_ROOM_f7436_ID='706c61796572732f6265656b65722f7436'
TEST_ROOM_f7436_SERVER_DATA='R6 /706c61796572732f6265656b65722f7436 6 / @ 315 350 1\r\n:1 :4 S 100 100 foo\r\n%l6ldDOaTL3DHAxN9uXwJoCY8vAk= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.684000\r\n'
TEST_ROOM_f7436_CACHED_DATA='R6 /706c61796572732f6265656b65722f7436 6 / @CACHE 315 350 1\r\n:1 :4 S 100 100 foo\r\n%ZIv1pOlg+Y2oTE4vG2nB5L9nNEs= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.684000\r\n'


TEST_ROOM_f7437_ID='706c61796572732f6265656b65722f7437'
TEST_ROOM_f7437_SERVER_DATA='R6 /706c61796572732f6265656b65722f7437 7 / @ 315 350 1\r\n:1 :4 S 100 100 foo\r\n%f3kKrloj2k3G3fgVx0x+F1koxGo= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.693000\r\n'
TEST_ROOM_f7437_CACHED_DATA='R6 /706c61796572732f6265656b65722f7437 7 / @CACHE 315 350 1\r\n:1 :4 S 100 100 foo\r\n%f3kKrloj2k3G3fgVx0x+F1koxGo= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.693000\r\n'

TEST_ROOM_f7438_ID='706c61796572732f6265656b65722f7438'
TEST_ROOM_f7438_SERVER_DATA='R6 /706c61796572732f6265656b65722f7438 10 / @ 0 0 1\r\n:1 :4 S 100 100 foo\r\n%f3kKrloj2k3G3fgVx0x+F1koxGo= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.693000\r\n'
TEST_ROOM_f7438_CACHED_DATA='R6 /706c61796572732f6265656b65722f7438 10 / @CACHE 315 350 1\r\n:1 :4 S 100 100 foo\r\n%f3kKrloj2k3G3fgVx0x+F1koxGo= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.693000\r\n'

TEST_PAGE_5_ID=5
TEST_PAGE_5_DATA='P6 5 P / @fizban,beeker 1\r\n:0\r\n%L7jU1PcK3zJ96T/GQp/zcWoZQkI= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'
TEST_PAGE_5_CACHED_DATA='P6 5 P / @CACHE 1\r\n:0\r\n%sVFeqSJDKJ6HSfhgtJGBMG/TYHY= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'
TEST_PAGE_5_SERVER_DATA='P6 5 P / @SERVER 1\r\n:0\r\n%e0Wa04QJuSIOqBNzx3UFG7NRtZM= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'

TEST_PAGE_6_ID=6
TEST_PAGE_6_CACHED_DATA='P6 6 P / @CACHE 1\r\n:0\r\n%GRr1ge56B8GRJtWBsWbCHh3cFyw= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'
TEST_PAGE_6_SERVER_DATA='P6 6 P / @ 1\r\n:0\r\n%ThT6Nmqi9RoIuLpJgCSc9QMfnrc= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.680000\r\n'

TEST_PAGE_7_ID=7
TEST_PAGE_7_CACHED_DATA='P6 7 P / @CACHE 1\r\n:0\r\n%NFXi1RIuN8dftZWa3/tVU4JDDik= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'
TEST_PAGE_7_SERVER_DATA='P6 7 P / @ 1\r\n:0\r\n%NnwbbNLu6jdYzgZ4wfxARUiBuh0= 2010-04-12T23:55:36.408000 2010-04-12T23:55:36.689000\r\n'

TEST_PAGE_8_ID=8
TEST_PAGE_8_CACHED_DATA='P6 8 P / @CACHE 1\r\n:0\r\n%3Iex42zJedj6i+pI8gp/3Sfu0nQ= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'
TEST_PAGE_8_SERVER_DATA='P6 8 P / @SERVER 1\r\n:0\r\n%G7GKVNvvxfiOe4tRP7R9O1/h8w8= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'

TEST_PAGE_9_ID=9
TEST_PAGE_9_CACHED_DATA='P6 9 P / @CACHE 1\r\n:0\r\n%NWGYFe/Z8cCmojQqSsAjfG+lmMo= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'
TEST_PAGE_10_ID=10
TEST_PAGE_10_CACHED_DATA='P6 10 P / @CACHE 1\r\n:0\r\n%NWGYFe/Z8cCmojQqSsAjfG+lmMo= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'
TEST_PAGE_10_SERVER_DATA='P6 10 P / @beeker 1\r\n:0\r\n%NWGYFe/Z8cCmojQqSsAjfG+lmMo= 2010-04-12T01:36:04.725000 2010-04-12T01:36:04.990000\r\n'

TEST_PAGE_404_ID=404
TEST_ROOM_404_ID='404'

class TestWebServiceRequestHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        return "text/plain"

    def translate_path(self, path):
        words = filter(None, posixpath.normpath(urllib.unquote(path)).split('/'))
        if words[0] == 'magicmap':
            new_path = os.path.join(*(WEB_DOCROOT_LIST + words[1:]))
        else:
            raise IOError('Unrecognized URL '+path)

        print "path in:", path, "out:", new_path
        return new_path

    def do_GET(self):
        if 'if-modified-since' in self.headers:
            print "***Client asks for %s only if newer than %s***" % (self.path, self.headers['if-modified-since'])
            modified_since = time.mktime(email.utils.parsedate(self.headers['if-modified-since']))
            path = self.translate_path(self.path)
            if os.path.exists(path) and os.path.getmtime(path) <= modified_since:
                print "---Reply: no, file updated %s, no data for you!" % (time.ctime(os.path.getmtime(path)))
                self.send_response(304)
                self.end_headers()
                return None
            print "---Reply: yes, new data or file not found; dropping to normal server GET handler."
        return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


class NetworkIOTest (unittest.TestCase):
    def __init__(self, *a, **k):
        unittest.TestCase.__init__(self, *a, **k)
        self.http_server = None
        self.server_thread = None

    def assertEqualsModuloCRLF(self, a, b):
        self.assertEquals(a.replace('\r\n','\n'), b.replace('\r\n', '\n'))

    def assertEqualsModuloCRLFandFooter(self, a, b):
        apct = a.find('\n%')
        bpct = b.find('\n%')
        if apct > 0: a = a[:apct+1]
        if bpct > 0: b = b[:bpct+1]

        self.assertEquals(a.replace('\r\n','\n'), b.replace('\r\n', '\n'))

    def _diag(self, level, progress, of, msg):
        print "DIAG TRACE: %s%s%s%s %s" % (
                ('D' if level & 8 else '-'),
                ('e' if level & 4 else '-'),
                ('w' if level & 2 else '-'),
                ('i' if level & 1 else '-'),
                msg
        )
        if progress is not None:
            print "DIAG PROGRESS: %3d of %3d" % (progress, of)
        self.diags.append((level, progress, of, msg))

    def setUp(self):
        # start a web server running on 127.0.0.1:8000
        if self.http_server is not None:
            print "Stopping previous server instance"
            self._stop_web_server()

        self.http_server = BaseHTTPServer.HTTPServer(('', 8000), TestWebServiceRequestHandler)
        self.server_thread = threading.Thread(target=self.http_server.serve_forever)
        self.server_thread.start()
        print "** STARTED SERVER **"
        #
        # get a client to the server
        #
        self._setup_cache_for_testing()
        self.diags = []
        self.client = NetworkIO('http://localhost:8000/magicmap', cache_dir=CACHE_TEST_DIR, diag_callback=self._diag)

    def tearDown(self):
        self._stop_web_server()

    def _stop_web_server(self):
        print "-- stopping server --"
        if self.server_thread and self.server_thread.is_alive():
            self.http_server.shutdown()

        tries = 10
        while self.server_thread and self.server_thread.is_alive():
            print "(waiting)"
            time.sleep(1)
            tries -= 1
            if tries <= 0:
                print "**FAILED TO STOP SERVER**"
                raise Exception('Failed to stop web server')

        print "** STOPPED SERVER **"
        self.server_thread = None
        self.http_server = None

    #
    # Test basic server data pull capability
    #
    def test_get_page(self):
        self.assertEqualsModuloCRLFandFooter(urllib2.urlopen('http://localhost:8000/magicmap/page/5').read(), TEST_PAGE_5_DATA)

    def test_get_room(self):
        self.assertEqualsModuloCRLFandFooter(urllib2.urlopen('http://localhost:8000/magicmap/room/7/70/706c61796572732f66697a62616e2f696e6469612f6d617261').read(), TEST_ROOM_17261_DATA)

    #
    # Network connectivity and caching tests
    #
    # We have set up the following test data in various states so we can determine
    # what's happening and what's being fetched from where.  The server copies 
    # all have @SERVER as their "also" and "creator" fields; the cached copies
    # all have @CACHE instead.  Since we only look at timestamps this discrepancy
    # won't be an issue here.  The timestamps for the files is significant and if
    # possible we will reset them in our setup code.
    # 
    #   PAGE  ROOM   CONDITION
    #     5   17261  On server, NOT in cache
    #         17262  NOT on server, IS in cache and RECENT
    #     6   f7436  On server, cache is NEWER and RECENT
    #         17263  NOT on server, IS in cache and STALE
    #     7   f7437  On server, cache is NEWER and STALE
    #     8   17264  NOT on server, IS in cache and RECENT
    #     9   17265  NOT on server, IS in cache and STALE
    #    10   f7438  On server, cache is OLDER and STALE
    #   404   404    NOT on server, NOT in cache (basically does not exist)
    def _setup_cache_for_testing(self):
        def _set_file_internal_timestamp(pathname, timestamp):
            #
            # Set time value inside file to specified time value.
            # This updates the "compiled time" value (2nd element in footer line).
            #
            with open(pathname, 'r') as mapfile:
                file_data = filter(None, mapfile.read().replace('\r\n', '\n').split('\n'))

            if file_data[-1][0] != '%':
                raise ValueError('cache file %s: invalid footer line %s' % (pathname, file_data[-1]))
            footer_data = file_data[-1].split()
            if len(footer_data) != 3:
                raise ValueError('cache file %s: invalid footer line %s' % (pathname, file_data[-1]))
            footer_data[1] = datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f')
            file_data[-1] = ' '.join(footer_data)

            with open(pathname, 'w') as mapfile:
                mapfile.write('\n'.join(file_data))
        #
        # get fresh copy of cache for testing
        #
        if os.path.exists(CACHE_TEST_DIR):
            shutil.rmtree(CACHE_TEST_DIR)
        shutil.copytree(CACHE_TEST_SRC, CACHE_TEST_DIR)
        #
        # cache files
        #
        c = MapCacheManager(CACHE_TEST_DIR)
        self.cache_node = {}
        for pageid, roomid, age in (
                (TEST_PAGE_5_ID, TEST_ROOM_17261_ID,  None),    # remove!
                (TEST_PAGE_6_ID, TEST_ROOM_17262_ID,   100),    # fresh
                (TEST_PAGE_6_ID, TEST_ROOM_f7436_ID,   100),    # fresh
                (TEST_PAGE_7_ID, TEST_ROOM_17263_ID, 90000),    # stale
                (TEST_PAGE_7_ID, TEST_ROOM_f7437_ID, 90000),    # stale
                (TEST_PAGE_8_ID, TEST_ROOM_17264_ID,   100),    # fresh
                (TEST_PAGE_9_ID, TEST_ROOM_17265_ID, 90000),    # stale
                (TEST_PAGE_10_ID, TEST_ROOM_f7438_ID, 90000),    # stale
        ):
            for target in '#%d' % pageid, roomid:
                d1, d2, leaf = c._encode_filename(target)
                filepath = os.path.join(CACHE_TEST_DIR, d1, d2, leaf)
                self.cache_node[target] = filepath
                if age is None:
                    if os.path.exists(filepath):
                        os.unlink(filepath)
                else:
                    ts = time.time() - age
                    _set_file_internal_timestamp(filepath, ts)
                    os.utime(filepath, (time.time(), ts))
        #
        # server files
        #
        for pageid, roomid, age in (
                (TEST_PAGE_6_ID, TEST_ROOM_f7436_ID, 100000),   # older than cache
                (TEST_PAGE_7_ID, TEST_ROOM_f7437_ID, 100000),   # older than cache
                (TEST_PAGE_10_ID, TEST_ROOM_f7438_ID,    60),   # newer than cache
        ):
            for filepath in (
                    os.path.join(*(WEB_DOCROOT_LIST + ['page', str(pageid)])), 
                    os.path.join(*(WEB_DOCROOT_LIST + ['room', roomid[:1], roomid[:2], roomid]))
            ):
                os.utime(filepath, (time.time(), time.time() - age))  
    #
    # Combination of conditions to test:       SERVER CACHED RESULT
    #                                          ------ ------ ----------------------------------
    #   **NOT HANDLED HERE**                   DOWN   BAD    Cache deleted; Error (server down)
    #   **NOT HANDLED HERE**                   404    BAD    Cache deleted; Error (no data)
    #                                          DOWN   NO     Error (server down)
    def test_nocache_noserver(self):
        self._stop_web_server()
        self.assertRaises(ServerNotAvailable, self.client.get_page, TEST_PAGE_5_ID)
        self.assertRaises(ServerNotAvailable, self.client.get_room, TEST_ROOM_17261_ID)
    #
    #                                          DOWN   YES    Cached copy; NO server check
    def test_cache_noserver(self):
        self._stop_web_server()
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_6_ID), TEST_PAGE_6_CACHED_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_17262_ID), TEST_ROOM_17262_CACHED_DATA)
        self.assertTrue(not any (['Opening data connection' in i[3] for i in self.diags]))
    #
    #                                          DOWN   OLD    Cached copy; warning (server down)
    def test_oldcache_noserver(self):
        self._stop_web_server()
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_7_ID), TEST_PAGE_7_CACHED_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_17263_ID), TEST_ROOM_17263_CACHED_DATA)
        self.assertTrue(any (['Unable to contact' in i[3] for i in self.diags]), 'Did not warn about server outage')
    #
    #                                          404    NO     Error (no data)
    def test_nocache_404server(self):
        self.assertRaises(DataNotFound, self.client.get_page, TEST_PAGE_404_ID)
        self.assertRaises(DataNotFound, self.client.get_room, TEST_ROOM_404_ID)
    #                                          OK     NO     Server copy; cache written
    def test_okserver_nocache(self):
        self.assertFalse(os.path.exists(self.cache_node['#5']))
        self.assertFalse(os.path.exists(self.cache_node[TEST_ROOM_17261_ID]))
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_5_ID), TEST_PAGE_5_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_17261_ID), TEST_ROOM_17261_DATA)
        self.assertTrue(os.path.exists(self.cache_node['#5']))
        self.assertTrue(os.path.exists(self.cache_node[TEST_ROOM_17261_ID]))
    #
    #                                          404    YES    Cached copy; NO server check
    def test_404server_okcache(self):
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_8_ID), TEST_PAGE_8_CACHED_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_17264_ID), TEST_ROOM_17264_CACHED_DATA)
        self.assertTrue(not any (['Opening data connection' in i[3] for i in self.diags]))
    #                                          OK     YES    Cached copy; NO server check
    def test_okserver_okcache(self):
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_6_ID), TEST_PAGE_6_CACHED_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_17262_ID), TEST_ROOM_17262_CACHED_DATA)
        self.assertTrue(not any (['Opening data connection' in i[3] for i in self.diags]))
    #                                          404    OLD    Cached copy; Warning (no data)
    def test_404server_oldcache(self):
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_9_ID), TEST_PAGE_9_CACHED_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_17265_ID), TEST_ROOM_17265_CACHED_DATA)
        self.assertTrue(any (['Map data not found on server' in i[3] for i in self.diags]))
    #                                          OK     OLD    Cached copy; cache time updated; NO data download
    def test_okserver_oldcache(self):
        self.assertTrue(os.path.getmtime(self.cache_node[TEST_ROOM_f7437_ID]) < (time.time()-3))
        self.assertTrue(os.path.getmtime(self.cache_node['#7']) < (time.time()-3))
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_7_ID), TEST_PAGE_7_CACHED_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_f7437_ID), TEST_ROOM_f7437_CACHED_DATA)
        self.assertTrue(os.path.getmtime(self.cache_node[TEST_ROOM_f7437_ID]) > (time.time()-3))
        self.assertTrue(os.path.getmtime(self.cache_node['#7']) > (time.time()-3))
        self.assertTrue(not any (['Opening data connection' in i[3] for i in self.diags]))
        self.assertTrue(any (['Checking server attributes' in i[3] for i in self.diags]))
    #
    #                                          NEWER  OLD    Server copy; cache updated
    def test_newerserver_oldcache(self):
        self.assertTrue(os.path.getmtime(self.cache_node[TEST_ROOM_f7438_ID]) < (time.time()-3))
        self.assertTrue(os.path.getmtime(self.cache_node['#10']) < (time.time()-3))
        self.assertEqualsModuloCRLFandFooter(self.client.get_page(TEST_PAGE_10_ID), TEST_PAGE_10_SERVER_DATA)
        self.assertEqualsModuloCRLFandFooter(self.client.get_room(TEST_ROOM_f7438_ID), TEST_ROOM_f7438_SERVER_DATA)
        self.assertTrue(os.path.getmtime(self.cache_node[TEST_ROOM_f7438_ID]) > (time.time()-3))
        self.assertTrue(os.path.getmtime(self.cache_node['#10']) > (time.time()-3))

if __name__ == '__main__':
    # Run test web server until stopped
    print "Starting web serer on port 8000"
    httpd = BaseHTTPServer.HTTPServer(('', 8000), TestWebServiceRequestHandler)
    httpd.serve_forever()
