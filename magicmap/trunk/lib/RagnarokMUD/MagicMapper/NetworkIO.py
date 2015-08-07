# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: Network I/O Handler
# $Header$
#
# Copyright (c) 2010, 2015 by Steven L. Willoughby, Aloha, Oregon, USA.
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
if __name__ == '__main__':
    import sys
    sys.path.append('../..')

from RagnarokMUD.MagicMapper.MapCacheManager import MapCacheManager
from RagnarokMUD.MagicMapper.AnsiParser      import AnsiParser, IncompleteSequence
import urllib2
import time
import select
import socket
import telnetlib

def tiny_hexdump(data):
    if data is None:
        return '|None|'

    if not data:
        return '|nil|'

    return "|" + ' '.join(['{:02X}'.format(ord(i)) for i in data]) + '|' + ''.join(
            [(ch if ' ' <= ch <= '~' else '.') for ch in data]) + '|'

class ServerNotAvailable (Exception):
    "Unable to contact the magic map web service"

class DataNotFound (Exception):
    "The server denies any knowledge of the alleged document."

class SocksError (Exception):
    "We failed to get a connection started via SOCKS proxy."

class NetworkIO (object):
    def __init__(self, base_url, cache_dir=None, cache_age=86400, diag_callback=None, config=None):
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

        self.config = config


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
                    req = urllib2.Request(self.base_url + url, headers={
                        'If-Modified-Since': data_http_time,
                    }, unverifiable=True)
                    #if self.config.has_option('proxy', 'map_proxy_url'):
                        #req.set_proxy(self.config.get('proxy', 'map_proxy_url'))
                    #req.set_proxy()
                    hose = urllib2.urlopen(req)
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

class ConnectionFailed (Exception): pass
class LocalProxyFailed (Exception): pass

class ProxyService (object):
    def __init__(self, remote_hostname='rag.com', remote_port=2222, local_hostname='localhost', local_port=2222, target_viewer=None):
        self.local_hostname  = local_hostname
        self.local_port      = local_port
        self.remote_hostname = remote_hostname
        self.remote_port     = remote_port
        self.local_socket    = None
        self.mud_client      = None
        self.mud_server      = None
        self.echo            = True
        self.open_local_port()
        self.ansi_parser     = AnsiParser(target_viewer=target_viewer)
        self._client_hold_data = ''
        self._server_hold_data = ''
        self.socks_server    = None
        self.socks_port      = None
        self.socks_version   = None
        self.socks_username  = None
        self.socks_password  = None

    #
    # My own quick and dirty code to negotiate with a SOCKS proxy
    # on the way out to connect to the MUD.
    #
    def set_socks_proxy(self, version, server, port, username=None, password=None):
        if version in ('4', 4, 'SOCKS4'):
            self.socks_version = '4'
        elif version in ('4a', 'SOCKS4a', 'SOCKS4A'):
            self.socks_version = '4a'
        elif version in ('5', 5, 'SOCKS5'):
            self.socks_version = '5'
        else:
            raise ValueError('Unsupported SOCKS protocol version {}'.format(version))

        self.socks_server = server
        self.socks_port = port
        self.socks_username = username
        self.socks_password = password

    def _negotiate_with_socks_proxy(self):
        self._socks_recv = ''

        #--- SOCKS4(a) ---#
        if self.socks_version in ('4', '4a'):
            if self.socks_version == '4':
                try:
                    octets = [int(i) for i in socket.gethostbyname(self.remote_hostname).split('.')]
                    assert len(octets) == 4
                except Exception as err:
                    raise SocksError("Unable to look up IPv4 address for {}: {}".format(self.remote_hostname, err))

                send = ('\4\1'
                        + chr((self.remote_port >> 8) & 0xff)
                        + chr((self.remote_port     ) & 0xff)
                        + chr(octets[0] & 0xff)
                        + chr(octets[1] & 0xff)
                        + chr(octets[2] & 0xff)
                        + chr(octets[3] & 0xff)
                        + (self.socks_username or '') + '\0')

                print "XXX Requesting proxy via SOCKS4: {}".format(tiny_hexdump(send))
            else:
                send = ('\4\1'
                        + chr((self.remote_port >> 8) & 0xff)
                        + chr((self.remote_port     ) & 0xff)
                        + '\0\0\0\1'
                        + (self.socks_username or '') + '\0'
                        + self.remote_hostname + '\0')
                print "XXX Requesting proxy via SOCKS4a: {}".format(tiny_hexdump(send))

            self.mud_server.write(send)
            self._grab_bytes(2)
            while self._socks_recv[0] != '\0':
                if 0x5a <= ord(self._socks_recv[0]) <= 0x5d:
                    print "XXX It appears the SOCKS4 proxy dropped the NULL byte; adjusting..."
                    self._socks_recv = '\0' + self._socks_recv
                    continue

                self.hangup()
                raise SocksError("Protocol error in response from SOCKS4 server: '{}'".format(tiny_hexdump(self._socks_recv)))

            if self._socks_recv[1] != '\x5a':
                self.hangup()
                raise SocksError("SOCKS proxy denied connection ({})".format(
                    ('Request rejected or failed' if self._socks_recv[1] == '\x5b' else
                        'Client not running identd' if self._socks_recv[1] == '\x5c' else
                        'Client identd validation failure' if self._socks_recv[1] == '\x5d' else
                        'Unknown reason code 0x{:02x}'.format(ord(self._socks_recv[1])))))
            self._grab_bytes(8)
            print "XXX SOCKS4 proxy connection established ({})".format(tiny_hexdump(self._socks_recv))
            if len(self._socks_recv) > 8:
                print "XXX Over-read by {}; passing '{}' on to MUD session...".format(len(self._socks_recv)-8, tiny_hexdump(self._socks_recv[8:]))
                self._server_hold_data += self._socks_recv[8:]
            self._socks_recv = ''

        #--- SOCKS5 ---#
        elif self.socks_version == '5':
            send = '\5\2\0\2'
            print "XXX Requesting proxy via SOCKS5: {}".format(tiny_hexdump(send))
            self.mud_server.write(send)
            self._grab_bytes(2)
            if self._socks_recv[0] != '\5':
                self.hangup()
                raise SocksError("Protocol error in response from SOCKS5 server: '{}'".format(tiny_hexdump(self._socks_recv)))
            auth_method = ord(self._socks_recv[1])
            self._socks_recv = ''

            if auth_method == 2:
                # method 2: simple username/password pair
                if self.socks_username is None: self.socks_username = ''
                if self.socks_password is None: self.socks_password = ''

                if len(self.socks_username) > 255 or len(self.socks_password) > 255:
                    self.hangup()
                    raise SocksError("SOCKS authentication password/username too long")

                send = '\1'+chr(len(self.socks_username))+self.socks_username+chr(len(self.socks_password))+self.socks_password
                print "XXX Server requests username/password auth, sending: {}".format(tiny_hexdump(send))
                self._grab_bytes(2)
                if self._socks_recv[0] != '\1':
                    self.hangup()
                    raise SocksError("Protocol error in auth subnegotiation response from SOCKS5 server: '{}'".format(tiny_hexdump(self._socks_recv)))
                reply = ord(self._socks_recv[1])
                if reply != 0:
                    self.hangup()
                    raise SocksError("Login to SOCKS5 proxy failed (code {})".format(reply))

                print "XXX Login to SOCKS5 server successful."

            elif auth_method == 0:
                # method 0: nothing at all, move along...
                print "XXX SOCKS5 server does not require logins."

            else:
                self.hangup()
                raise SocksError("SOCKS5 proxy requires an authentication method we don't support.")

            self._socks_recv = ''
            if len(self.remote_hostname) > 255:
                self.hangup()
                raise SocksError("Remote host name too long")

            send='\5\1\0\3' + chr(len(self.remote_hostname)) + self.remote_hostname \
                    + chr((self.remote_port >> 8) & 0xff) + chr(self.remote_port & 0xff)
            print "XXX Requesting proxied connection to MUD server: {}".format(tiny_hexdump(send))
            self.mud_server.write(send)
            self._grab_bytes(2)
            if self._socks_recv[0] != '\5':
                self.hangup()
                raise SocksError("SOCKS5 protocol error in final handshake step: {}".format(tiny_hexdump(self._socks_recv)))

            reply = ord(self._socks_recv[1])
            if reply != 0:
                self.hangup()
                raise SocksError("Proxied connection to MUD failed ({})".format(
                    'General failure' if reply == 1 else
                    'Denied due to ruleset' if reply == 2 else
                    'Network unreachable' if reply == 3 else
                    'Host unreachable' if reply == 4 else
                    'Connection refused by destination host' if reply == 5 else
                    'TTL expired' if reply == 6 else
                    'Command not supported or protocol error' if reply == 7 else
                    'Address type not supported' if reply == 8 else
                    'Unknown error code {}'.format(reply)))

            self._grab_bytes(4)
            if self._socks_recv[2] != '\0':
                self.hangup()
                raise SocksError("SOCKS5 protocol error in final handshake step: {}".format(tiny_hexdump(self._socks_recv)))
            
            addr_style = ord(self._socks_recv[3])
            if addr_style == 1:
                self._grab_bytes(10)
                host = 'IPv4 host {}, port {}'.format(
                    '.'.join(['{:d}'.format(ord(i)) for i in self._socks_recv[4:8]]),
                    (ord(self._socks_recv[8]) << 8) | ord(self._socks_recv[9]))
                extra = 10

            elif addr_style == 3:
                self._grab_bytes(5)
                name_len = ord(self._socks_recv[4])
                self._grab_bytes(5+name_len+2)
                host = 'named host {}, port {}'.format(
                    self._socks_recv[5:5+name_len],
                    (ord(self._socks_recv[5+name_len]) << 8) | ord(self._socks_recv[6+name_len]))
                extra = 7+name_len

            elif addr_style == 4:
                self._grab_bytes(22)
                host = 'IPv6 host {}, port {}'.format(
                        ':'.join(['{:02x}'.format(ord(i)) for i in self._socks_recv[4:20]]),
                        (ord(self._socks_recv[20]) << 8) | ord(self._socks_recv[21]))
                extra = 22

            else:
                self.hangup()
                raise SocksError("SOCKS5 gave unintelligible reply to final handshake: {}".format(tiny_hexdump(self._socks_recv)))
                
            print "XXX SOCKS5 connection established to", host
            if len(self._socks_recv) > extra:
                print "XXX Over-read by {}; passing '{}' on to MUD session...".format(len(self._socks_recv)-extra, 
                        tiny_hexdump(self._socks_recv[extra:]))
                self._server_hold_data += self._socks_recv[extra:]
            self._socks_recv = ''


    def _grab_bytes(self, size):
        while len(self._socks_recv) < size:
            print "XXX Waiting for {} more byte{} from SOCKS server... got '{}' so far".format(size-len(self._socks_recv), (
                '' if size-len(self._socks_recv)==1 else 's'), tiny_hexdump(self._socks_recv))
            #self._socks_recv += self.mud_server.read_some()
            self._socks_recv += self.mud_server.rawq_getchar()
        print "XXX Read {} from source: {}".format(len(self._socks_recv), tiny_hexdump(self._socks_recv))


    def close_local_port(self):
        "Close the incoming local proxy port"

        if self.local_socket:
            self.local_socket.close()
            self.local_socket = None

    def open_local_port(self):
        "Open the incoming local proxy port"

        self.close_local_port()

        for family, socktype, protocol, name, sa in socket.getaddrinfo(
                self.local_hostname, self.local_port, socket.AF_UNSPEC,
                socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            try:
                self.local_socket = socket.socket(family, socktype, protocol)
                self.local_socket.bind(sa)
                self.local_socket.listen(1)
            except socket.error:
                if self.local_socket:
                    self.local_socket.close()
                    self.local_socket = None
                continue
            break


        if self.local_socket is None:
            raise LocalProxyFailed('Unable to open proxy port {}:{}'.format(
                self.local_hostname, self.local_port))

        # XXX log connection
        print "Opened local proxy {} on {}:{} ({})".format(self.local_socket, self.local_hostname, self.local_port, sa)
        

    def poll(self):
        "See if there's work to do, and carry it out.  This should be called as an idle task."

        # We don't really care about blocking on writes (at this point),
        # but we need a way to quickly check to see if we have incoming
        # data to move on to its destination.

        f_list = filter(None, [self.local_socket, self.mud_client])
        if f_list:
            reads, writes, errors = select.select(f_list, [], [], 0)

            if self.local_socket in reads:
                # Someone's knocking on my door... better let them in
                # XXX log connection from client
                if self.mud_client:
                    # One's company, two's a crowd.  We don't want to be mapping for
                    # more than one player at a time.
                    connection, address = self.local_socket.accept()
                    connection.send("Sorry, there is already a client connected to the Magic Mapper.\r\n")
                    connection.close()
                    print "XXX Connection refused to {} (too many clients)".format(address)
                else:
                    self.mud_client, self.mud_client_address = self.local_socket.accept()
                    # XXX log connection
                    print "XXX Connection from {} to magicmap... proxying to {}:{}".format(
                            self.mud_client_address, self.remote_hostname, self.remote_port)
                    try:
                        if self.socks_version is not None:
                            self.mud_server = telnetlib.Telnet(self.socks_server, self.socks_port, 30)
                            #self.mud_server.set_debuglevel(10)
                            self.mud_server.set_option_negotiation_callback(self.handle_telnet_option)
                            self._negotiate_with_socks_proxy()
                        else:
                            self.mud_server = telnetlib.Telnet(self.remote_hostname, self.remote_port, 30)
                            self.mud_server.set_option_negotiation_callback(self.handle_telnet_option)
                        print "XXX Connected to MUD {}, port {}".format(self.remote_hostname, self.remote_port)
                    except Exception as err:
                        print 'Connection to MUD {}, port {} error: {}\r\n'.format(
                                self.remote_hostname, self.remote_port, err)
                        self.mud_client.send(
                                'Connection to MUD {}, port {} error: {}\r\n'.format(
                                self.remote_hostname, self.remote_port, err))
                        self.mud_client.close()
                        self.mud_client = None
                        self.mud_server = None

            if self.mud_client in reads:
                # Hark! The user has typed a command!
                try:
                    data = self._client_hold_data + self.mud_client.recv(1024)
                    self._client_hold_data = ''
                    pos = data.find('\xff')
                    while pos >= 0:
                        if len(data) < pos+3:
                            print "XXX Telnet protocol bytes incomplete; wating for more from client..."
                            self._client_hold_data = data
                            data = None
                            return

                        print "XXX Ignoring Telnet protocol bytes {:02x}{:02x}{:02x}".format(
                                ord(data[pos]), ord(data[pos+1]), ord(data[pos+2]))
                        data = data[:pos] + data[pos+3:]
                        pos = data.find('\xff')

                    if self.echo:
                        print "XXX received", len(data), "from client:", tiny_hexdump(data)
                    else:
                        print "XXX received", len(data), "from client: [not shown]"
                    self.mud_server.write(data)

                except socket.error:
                    # On second thought, they rang just to say they hung up on us.
                    # That's not very nice
                    # XXX log disconnect
                    print "XXX client disconnected from proxy."
                    if self.mud_client:
                        self.mud_client.close()
                        self.mud_client = None
                    if self.mud_server:
                        self.mud_server.close()
                        self.mud_server = None

        
        # non-blocking attempt to read from the MUD game
        if self.mud_server:
            try:
                data = self._server_hold_data + self.mud_server.read_very_eager()
                self._server_hold_data = ''
                data = self.ansi_parser.filter(data)
            except EOFError:
                print "XXX MUD disconnected."
                self.hangup()
                data = None
            except IncompleteSequence:
                print "XXX Incomplete ANSI sequence received.  Saving {} for later.".format(data)
                self._server_hold_data = data
                data = None

            if data:
                self.mud_client.sendall(data)

    def hangup(self):
        print "XXX severing connection to MUD."
        self.mud_server = None
        if self.mud_client:
            self.mud_client.sendall("MUD Server closed the connection.\r\n")
            self.mud_client.close()
            self.mud_client = None


    def handle_telnet_option(self, socket, command, option):
        # command: telnetlib.WILL|WONT
        # option: telnetlib.ECHO
        if option == telnetlib.ECHO:
            if command == telnetlib.WILL:
                # server is (lying about) saying it will echo stuff
                self.echo = False
                if self.mud_client:
                    self.mud_client.sendall(telnetlib.IAC+telnetlib.WILL+telnetlib.ECHO)
                print "XXX turning echo off"

            elif command == telnetlib.WONT:
                # server is saying it won't echo, so we have to
                self.echo = True
                if self.mud_client:
                    self.mud_client.sendall(telnetlib.IAC+telnetlib.WONT+telnetlib.ECHO)
                print "XXX turning echo on"
            elif command == telnetlib.DO:
                # server is asking US to echo now?  okay...
                self.echo = True
                if self.mud_client:
                    self.mud_client.sendall(telnetlib.IAC+telnetlib.DO+telnetlib.ECHO)
                print "XXX turning echo on"
            elif command == telnetlib.DONT:
                # server is asking US to NOT echo.
                self.echo = False
                if self.mud_client:
                    self.mud_client.sendall(telnetlib.IAC+telnetlib.DONT+telnetlib.ECHO)
                print "XXX turning echo off"
            else:
                print "XXX unknown echo command {}".format(command)
        else:
            print "XXX unknown telnet protocol option setting {}.{}".format(command, option)



if __name__ == '__main__':
    # start standalone proxy for testing
    p = ProxyService(remote_port=2222)
    while True:
        p.poll()
