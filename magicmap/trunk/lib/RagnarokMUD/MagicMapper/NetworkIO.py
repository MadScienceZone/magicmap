# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Network I/O Handler
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

#from RagnarokMUD.MagicMapper.MapSource      import MapSource, MapFileFormatError
#from RagnarokMUD.MagicMapper.MapPage        import MapPage
#from RagnarokMUD.MagicMapper.MapRoom        import MapRoom
#from RagnarokMUD.MagicMapper.MapDataHandler import MapDataHandler
#from RagnarokMUD.MagicMapper.Local          import gen_public_room_id
#import os, os.path, datetime
from RagnarokMUD.MagicMapper.MapCacheManager import MapCacheManager
import urllib2
import time

class ServerNotAvailable (Exception):
    "Unable to contact the magic map web service"

class DataNotFound (Exception):
    "The server denies any knowledge of the alleged document."

class NetworkIO (object):
    def __init__(self, base_url, cache_dir=None, cache_age=86400, diag_callback=None):
        '''Create Network interface object.
        ------------------------------------------------------------------------------
        base_url:  base url to get map pages and rooms.  We'll append "/room/<id>" 
                   or "/page/<id>" to this string to get the full URL.
        cache_dir: directory to cache files received from server (optional).
        cache_age: minimum age (in seconds) before we check the server for newer
                   content instead of only taking our cached version.
        diag_callback: callable object to receive diagnostic feedback (optional).
                       This will be invoked with four paramters:
                         diag_callback(level, prog, total, msg)
                          level: The class(es) of message being sent:
                            1  informational and progress update
                            2  warning messages
                            4  error messages
                            8  debugging messages
                          prog: Progress on task so far or None if N/A
                          total: How for "prog" will go or None if N/A
                          msg: Message to show to user
        '''
        # XXX idea: use page timestamp on server to signal that no room
        # XXX on that page is newer, so we never check rooms on a page
        # XXX until that page file got updated.
        self.diag_callback = diag_callback
        self.base_url = base_url
        self.log('Using '+self.base_url+' as Magic Map data source.', 8)

        if cache_dir:
            self.cache = MapCacheManager(cache_dir)
            self.cache_age = cache_age
            self.log('Cache storage is %s (max age %d)' % (cache_dir, cache_age), 8)
        else:
            self.cache = None
            self.cache_age = None
            self.log('NOT using cache!', 8)


    def log(self, msg, level=1, prog=None, total=None):
        if self.diag_callback is not None:
            self.diag_callback(level, prog, total, msg)

    def _get_data(self, url, key):
        if self.cache:
            self.log('Checking cache ID '+key, 8)
            cache_entry = self.cache.retrieve(key)
            if cache_entry is not None:
                if cache_entry[1] < self.cache_age:
                    self.log('Cache hit, age %d seconds, less than max %d, using that.' % (cache_entry[1], self.cache_age), 8)
                    return cache_entry[0].read()
                else:
                    self.log('Cache hit, age %d seconds, exceeds max %d, checking server instead.' % (cache_entry[1], self.cache_age), 8)
            else:
                self.log('Nothing cached.', 8)

        #
        # From here down, if we have valid(!) cache data it will
        # be in the string buffer cached_data.  Otherwise, we better
        # be able to get something from the server.
        #
        # cache_entry may have been closed and removed.
        #
        cached_data = None
        if self.cache and cache_entry is not None:
            #
            # we have old cache data; see if the server has anything newer
            # before downloading any content
            #
            cached_data = cache_entry[0].read()
            cache_entry[0].close()
            cache_entry = None
            #
            # Get actual data timestamp
            #
            # All we need to know about the file format here is
            # that the LAST line has the format:
            #   %<checksum> <data-timestamp> <source-timestamp>
            #
            # We want the 2nd field (<data-timestamp>) and will check
            # to see if the server has anything newer than that.
            #
            cache_data_checksum, cache_data_time = filter(None, cached_data.split('\n'))[-1].split()[:2]
            if not cache_data_checksum.startswith('%'):
                self.log('Cache entry "%s" invalid (footer format error), may be corrupt.' % key, 2)
                self.cache.remove(key)
                cached_data = None
            else:
                try:
                    data_http_time = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.strptime(cache_data_time, "%Y-%m-%dT%H:%M:%S.%f"))
                except:
                    self.log('Cache timestamp not understood, trying a more conservative pattern.', 8)
                    try:
                        data_http_time = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.strptime(cache_data_time, "%Y-%m-%dT%H:%M:%S"))
                    except:
                        self.log("That didn't work, either.  What's '%s' supposed to mean?" % cache_data_time, 8)
                        self.log("Cache entry '%s' invalid (can't parse date '%s')." % (key, cache_data_time), 2)
                        self.cache.remove(key)
                        cached_data = None
                #
                # Given the date of our cached value, see if the server has something
                # new for us.
                #
                try:
                    self.log('Checking server attributes to see if newer data are available', 8)
                    hose = urllib2.urlopen(urllib2.Request(self.base_url + url, headers={
                        'If-Modified-Since': data_http_time,
                    }, unverifiable=True))
                    self.log('Server copy is newer; using that', 8)
                except urllib2.HTTPError as problem:
                    if problem.code == 304:
                        self.log('Server does not have newer copy; using cache', 8)
                        self.cache.touch(key)
                        return cached_data
                    elif problem.code == 404:
                        self.log('Map data not found on server, using old cached data anyway.', 2)
                        self.cache.touch(key)
                        return cached_data
                    else:
                        self.log('HTTP error %d trying to get new copy of %s from server; using cached copy for now.' % (
                            problem.code, key))
                        return cached_data
                except urllib2.URLError as problem:
                    self.log('Unable to contact map server (%s); using (stale) cached data anyway.' % problem.reason, 2)
                    return cached_data
        else:
            #
            # No cache, just get from server unconditionally
            #
            try:
                self.log('Opening data connection to '+self.base_url+url, 8)
                hose = urllib2.urlopen(urllib2.Request(self.base_url + url, unverifiable=True))

            except urllib2.HTTPError as problem:
                if cached_data is not None:
                    self.log('Map data not found on server, using old cached data anyway.', 2)
                    return cached_data

                self.log('Requested map data "%s" not found on server (HTTP error %d).' % (url, problem.code), 4)
                raise DataNotFound('Map data for "%s" not found on server (HTTP error %d)' % (url, problem.code))

            except urllib2.URLError as problem:
                if cached_data is not None:
                    self.log('Unable to contact map server (%s); using (stale) cached data anyway.' % problem.reason, 2)
                    return cached_data

                self.log('Unable to contact map server %s: %s ' % (self.base_url, problem.reason), 4)
                raise ServerNotAvailable("Unable to contact magic map service at %s: %s" % (self.base_url, problem.reason))
        #
        # At this point we have <hose> (a data pipe to the server),
        # either based on taking new content over cached, or by 
        # opening a new connection with no cache available.
        # If we decided to use the cache, we're already gone.
        #
        self.log('Reading data from server', 8)
        data = hose.read()
        hose.close()
        self.log('Read %d bytes' % len(data), 8)
        
        if self.cache:
            self.log('Saving data to cache node '+key, 8)
            self.cache.store_str(key, data)
        return data

    def get_page(self, page_no):
        '''int page_no -> text of page description
        This will fetch the page from local cache if it's within the allowed
        timeframe, or if the server's copy is not available.  Otherwise, it
        will contact the remote service, cache the result, and return it.'''
        self.log("Retrieving page %d from server" % page_no)
        return self._get_data('/page/%d' % page_no, '#%d' % page_no)

    def get_room(self, room_id):
        '''room_id -> text of room description
        This will fetch the room from local cache if it's within the allowed
        timeframe, or if the server's copy is not available.  Otherwise, it
        will contact the remote service, cache the result, and return it.'''
        self.log("Retrieving room data from server")
        return self._get_data('/room/'+room_id[:1] + '/' + room_id[:2] + '/' + room_id, room_id)
