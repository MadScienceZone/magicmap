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
# RAGNAROK MAGIC MAPPER SOURCE CODE: Network I/O Handler
#

#from RagnarokMUD.MagicMapper.MapSource      import MapSource, MapFileFormatError
#from RagnarokMUD.MagicMapper.MapPage        import MapPage
#from RagnarokMUD.MagicMapper.MapRoom        import MapRoom
#from RagnarokMUD.MagicMapper.MapDataHandler import MapDataHandler
#from RagnarokMUD.MagicMapper.Local          import gen_public_room_id
#import os, os.path, datetime


#
# For proxied connections
# ProxyService(remote_hostname='rag.com', report_port=2222, local_hostname='localhost', local_port=2222, target_viewer=None)
#   the target_viewer targets the AnsiParser to send events
#   to as they're parsed. Calls
#       .tracking_start(player_name)
#       .tracking_stop()
#       .tracking_position(id)
#       .tracking_sync(i, total, modtime, checksum, id)
#
# .set_socks_proxy(version, server, port, username=None, password=None)
# ._negotiate_with_socks_proxy()
#      ->._grab_bytes(size) 
# .close_local_port()
# .open_local_port()
# .poll()       call as idle task to process more I/O
#       incoming connection to local port
#           telnetlib.Telnet()
#               sets .handle_telnet_option() to take telnet options
#           ->._negotiatite_with_socks_proxy() if one is set
#       data from mud client
#           grab up to 1k of data
#           look for FFxxyy bytes; filter them out of the stream
#           write to server
#       socket error
#           disconnect
#       try reading from server -> data=ansi_parser.filter(data)
#           will wait for complete ANSI sequence to be received
#           if any (non-ANSI) data left, send to client
#
# .hangup()  (tells client that server hungup)
# .handle_telnet_option(socket, command, option)
#       if server says WILL ECHO
#           set .echo false
#           send IAC WILL ECHO to client
#       if server says WONT ECHO
#           set .echo true
#           send IAC WONT ECHO to client
#       if server says DO echo
#           set .echo true
#           send IAC DO ECHO to client
#       if server says DONT echo
#           set .echo false
#           send IAC DONT ECHO to client
#       so the .echo attribute tells us if we should be echoing the user's
#       input.
#
# NEW:
#   no need for poll() function anymore
#
#   .run()
#       start threaded handling of communication.
#   .stop()
#       shut down communications and stop the running threads.
#       blocks until threads are finished working.


from RagnarokMUD.MagicMapper.MapCacheManager import MapCacheManager
from RagnarokMUD.MagicMapper.AnsiParser      import AnsiParser
import urllib.request, urllib.error, urllib.parse
import time
import select
import socket
import telnetlib
import queue
import threading

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
            cache_data_checksum, cache_data_time = [_f for _f in cached_data.split('\n') if _f][-1].split()[:2]
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
                    req = urllib.request.Request(self.base_url + url, headers={
                        'If-Modified-Since': data_http_time,
                    }, unverifiable=True)
                    #if self.config.has_option('proxy', 'map_proxy_url'):
                        #req.set_proxy(self.config.get('proxy', 'map_proxy_url'))
                    #req.set_proxy()
                    hose = urllib.request.urlopen(req)
                    self.log('Server copy is newer; using that', 8)
                except urllib.error.HTTPError as problem:
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
                except urllib.error.URLError as problem:
                    self.log('Unable to contact map server (%s); using (stale) cached data anyway.' % problem.reason, 2)
                    return cached_data
        else:
            #
            # No cache, just get from server unconditionally
            #
            try:
                self.log('Opening data connection to '+self.base_url+url, 8)
                hose = urllib.request.urlopen(urllib.request.Request(self.base_url + url, unverifiable=True))

            except urllib.error.HTTPError as problem:
                if cached_data is not None:
                    self.log('Map data not found on server, using old cached data anyway.', 2)
                    return cached_data

                self.log('Requested map data "%s" not found on server (HTTP error %d).' % (url, problem.code), 4)
                raise DataNotFound('Map data for "%s" not found on server (HTTP error %d)' % (url, problem.code))

            except urllib.error.URLError as problem:
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
    def __init__(self, remote_hostname='rag.com', remote_port=2222, local_hostname='localhost', local_port=2222, event_queue=None, client_queue=None):
        self.local_hostname  = local_hostname
        self.local_port      = local_port
        self.remote_hostname = remote_hostname
        self.remote_port     = remote_port
        self.local_socket    = None
        self.mud_client      = None
        self.mud_server      = None
        self.echo            = True
        self._client_hold_data = ''
        self._server_hold_data = ''
        self.socks_server    = None
        self.socks_port      = None
        self.socks_version   = None
        self.socks_username  = None
        self.socks_password  = None
        self.event_queue = event_queue
        self.client_queue = client_queue

        self.manager_thread = None
        self.local_read_thread = None
        self.local_write_thread = None
        self.remote_read_thread = None
        self.remote_write_thread = None

        self.local_sender = None
        self.remote_sender = None

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

                print("XXX Requesting proxy via SOCKS4: {}".format(tiny_hexdump(send)))
            else:
                send = ('\4\1'
                        + chr((self.remote_port >> 8) & 0xff)
                        + chr((self.remote_port     ) & 0xff)
                        + '\0\0\0\1'
                        + (self.socks_username or '') + '\0'
                        + self.remote_hostname + '\0')
                print("XXX Requesting proxy via SOCKS4a: {}".format(tiny_hexdump(send)))

            self.mud_server.write(send)
            self._grab_bytes(2)
            while self._socks_recv[0] != '\0':
                if 0x5a <= ord(self._socks_recv[0]) <= 0x5d:
                    print("XXX It appears the SOCKS4 proxy dropped the NULL byte; adjusting...")
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
            print("XXX SOCKS4 proxy connection established ({})".format(tiny_hexdump(self._socks_recv)))
            if len(self._socks_recv) > 8:
                print("XXX Over-read by {}; passing '{}' on to MUD session...".format(len(self._socks_recv)-8, tiny_hexdump(self._socks_recv[8:])))
                self._server_hold_data += self._socks_recv[8:]
            self._socks_recv = ''

        #--- SOCKS5 ---#
        elif self.socks_version == '5':
            send = '\5\2\0\2'
            print("XXX Requesting proxy via SOCKS5: {}".format(tiny_hexdump(send)))
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
                print("XXX Server requests username/password auth, sending: {}".format(tiny_hexdump(send)))
                self._grab_bytes(2)
                if self._socks_recv[0] != '\1':
                    self.hangup()
                    raise SocksError("Protocol error in auth subnegotiation response from SOCKS5 server: '{}'".format(tiny_hexdump(self._socks_recv)))
                reply = ord(self._socks_recv[1])
                if reply != 0:
                    self.hangup()
                    raise SocksError("Login to SOCKS5 proxy failed (code {})".format(reply))

                print("XXX Login to SOCKS5 server successful.")

            elif auth_method == 0:
                # method 0: nothing at all, move along...
                print("XXX SOCKS5 server does not require logins.")

            else:
                self.hangup()
                raise SocksError("SOCKS5 proxy requires an authentication method we don't support.")

            self._socks_recv = ''
            if len(self.remote_hostname) > 255:
                self.hangup()
                raise SocksError("Remote host name too long")

            send='\5\1\0\3' + chr(len(self.remote_hostname)) + self.remote_hostname \
                    + chr((self.remote_port >> 8) & 0xff) + chr(self.remote_port & 0xff)
            print("XXX Requesting proxied connection to MUD server: {}".format(tiny_hexdump(send)))
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
                
            print("XXX SOCKS5 connection established to", host)
            if len(self._socks_recv) > extra:
                print("XXX Over-read by {}; passing '{}' on to MUD session...".format(len(self._socks_recv)-extra, 
                        tiny_hexdump(self._socks_recv[extra:])))
                self._server_hold_data += self._socks_recv[extra:]
            self._socks_recv = ''


    def _grab_bytes(self, size):
        while len(self._socks_recv) < size:
            print("XXX Waiting for {} more byte{} from SOCKS server... got '{}' so far".format(size-len(self._socks_recv), (
                '' if size-len(self._socks_recv)==1 else 's'), tiny_hexdump(self._socks_recv)))
            #self._socks_recv += self.mud_server.read_some()
            self._socks_recv += self.mud_server.rawq_getchar()
        print("XXX Read {} from source: {}".format(len(self._socks_recv), tiny_hexdump(self._socks_recv)))

    def run(self):
        "Start communications with the world. Launches threads to handle I/O."
        #
        # This opens our local proxy and (when a client connects to it) an outbound connection to
        # the MUD server. We launch threads:
        #   * accept incoming connections from local side
        #       when connected, connect to remote and launch other threads:
        #          * read data from local side
        #          * read data from remote side
        #          * write data to local side
        #          * write data to remote side
        #       wait for connection to drop; join threads and wait for another connection
        #
        if self.manager_thread:
            print("Asked to run() proxy service while already running! Stopping the old one first...")
            self.stop()

        self.local_sender = queue.Queue()
        self.remote_sender = queue.Queue()

        self.manager_thread = threading.Thread(target=self._manage_threads)
        self.manager_thread.start()

    def _manage_threads(self):
        "(run in a separate thread) waits for incoming connection, then spawns worker threads to talk to it."
        self._open_local_port()
        while True:
            print("Ready for local connection")
            self.mud_client, self.mud_client_address = self.local_socket.accept()
            print(f"Connection from {self.mud_client_address} to magicmap... proxying to {self.remote_hostname}, {self.remote_port}")
            try:
                if self.socks_version is not None:
                    self.mud_server = socket.create_connection((self.socks_server, self.socks_port))
                    self.mud_server.setblocking(True)
                    self._negotiate_with_socks_proxy()
                else:
                    self.mud_server = socket.create_connection((self.remote_hostname, self.remote_port))
                    self.mud_server.setblocking(True)
            except Exception as err:
                print(f'Connection to MUD {self.remote_hostname}, port {self.remote_port} error: {err}')
                self.mud_client.sendall(f'Connection to MUD {self.remote_hostname}, port {self.remote_port} error: {err}')
                self.mud_client.close()
                self.mud_client = None
                self.mud_server = None
                continue

            print(f'Connected to remote server.')
            self.local_read_thread = threading.Thread(target=self._input_pipe, args=(self.mud_client, self.remote_sender))
            self.remote_write_thread = threading.Thread(target=self._output_pipe, args=(self.mud_server, self.remote_sender))

            self.local_write_thread = threading.Thread(target=self._output_pipe, args=(self.mud_client, self.local_sender))
            self.remote_read_thread = threading.Thread(target=self._input_parser, args=(self.mud_server, self.local_sender))
        
            self.local_read_thread.start()
            self.local_write_thread.start()
            self.remote_read_thread.start()
            self.remote_write_thread.start()
            print('Set up I/O threads.')

            #
            # wait for the threads to stop, which they'll do
            # when they can't talk anymore on their sockets
            #
            self.remote_read_thread.join()
            self.remote_read_thread = None
            print('Stopped remote receiver.')
            self._stop_io_threads()
            self.remote_write_thread.join()
            self.remote_write_thread = None
            print('Stopped remote sender.')
            self.local_read_thread.join()
            self.local_read_thread = None
            print('Stopped local receiver.')
            self.local_write_thread.join()
            self.local_write_thread = None
            print('Stopped local sender.')

        self._close_local_port()

    def _stop_io_threads(self):
        #
        # violate the conditions upon which the I/O threads
        # need to keep running. This should make them give up
        # and stop.
        #
        if self.mud_client:
            self.mud_client.shutdown(socket.SHUT_RDWR)
            self.mud_client.close()
            self.mud_client = None
        if self.mud_server:
            self.mud_server.shutdown(socket.SHUT_RDWR)
            self.mud_server.close()
            self.mud_server = None
        if self.local_sender:
            self.local_sender.put(b'')
        if self.remote_sender:
            self.remote_sender.put(b'')

    def stop(self):
        "Stop communications with the world. Stops I/O threads (blocks until they finish)."
        #
        # Tell our manager thread to stop accepting any more incoming connections.
        # Close sockets, wait for threads to terminate
        #
        if self.manager_thread:
            if self.mud_client:
                self.mud_client.close()
            if self.mud_server:
                self.mud_server.close()
            self.manager_thread.join()

        self.mud_client = None
        self.mud_server = None
        self.manager_thread = None
        self.local_sender = None
        self.remote_sender = None


    def _close_local_port(self):
        "Close the incoming local proxy port"

        if self.local_socket:
            self.local_socket.close()
            self.local_socket = None

    def _open_local_port(self):
        "Open the incoming local proxy port"

        self._close_local_port()

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
        print("Opened local proxy {} on {}:{} ({})".format(self.local_socket, self.local_hostname, self.local_port, sa))
        

    def _input_pipe(self, sock, q):
        print("input pipe started")
        try:
            while True:
                print("input pipe trying to read")
                data = sock.recv(4096)
                print(f"input pipe read {len(data)}")
                if not data:
                    print('EOF on input pipe')
                    break
                q.put(data)
        except Exception as err:
            print(f"Terminating _output_pipe on errror {err}")
            return

    def _output_pipe(self, sock, q):
        try:
            while True:
                sock.sendall(q.get())
        except Exception as err:
            print(f"Terminating _output_pipe on errror {err}")
            return


    def _input_parser(self, sock, q):
        WILL = 0xfb
        WONT = 0xfc
        DO = 0xfd
        DONT = 0xfe
        IAC = 0xff
        ECHO = 0x01
        WILL_ECHO = bytes((WILL, ECHO))
        WONT_ECHO = bytes((WONT, ECHO))
        DO_ECHO = bytes((DO, ECHO))
        DONT_ECHO = bytes((DONT, ECHO))
        ansi_parser = AnsiParser(event_queue = self.event_queue, client_queue = q)

        data = b''
        try:
            while True:
                new_data = sock.recv(4096)
                if not new_data:
                    print('EOF reading input')
                    break
                data += new_data
                # look for control sequence in data stream
                telnet_cmd = data.find(IAC)
                while telnet_cmd >= 0:
                    ansi_parser.parse(data[:telnet_cmd])
                    data = data[telnet_cmd:]
                    if len(data) < 3:
                        break
                    if data[1:3] == WILL_ECHO or data[1:3] == DONT_ECHO:
                        print("*** TURN OFF ECHO ***")
                    elif data[1:3] == WONT_ECHO or data[1:3] == DO_ECHO:
                        print("*** TURN ON ECHO ***")
                    q.put(data[0:3])
                    data = data[3:]
                    telnet_cmd = data.find(IAC)
                if len(data) > 0:
                    ansi_parser.parse(data)
                    data = b''
        except Exception as err:
            print(f"Terminating _output_pipe on errror {err}")
            return

#    def poll(self):
#        "See if there's work to do, and carry it out.  This should be called as an idle task."
#
#        # We don't really care about blocking on writes (at this point),
#        # but we need a way to quickly check to see if we have incoming
#        # data to move on to its destination.
#
#        f_list = [_f for _f in [self.local_socket, self.mud_client] if _f]
#        if f_list:
#            reads, writes, errors = select.select(f_list, [], [], 0)
#
#            if self.local_socket in reads:
#                # Someone's knocking on my door... better let them in
#                # XXX log connection from client
#                if self.mud_client:
#                    # One's company, two's a crowd.  We don't want to be mapping for
#                    # more than one player at a time.
#                    connection, address = self.local_socket.accept()
#                    connection.send("Sorry, there is already a client connected to the Magic Mapper.\r\n")
#                    connection.close()
#                    print("XXX Connection refused to {} (too many clients)".format(address))
#                else:
#                    self.mud_client, self.mud_client_address = self.local_socket.accept()
#                    # XXX log connection
#                    print("XXX Connection from {} to magicmap... proxying to {}:{}".format(
#                            self.mud_client_address, self.remote_hostname, self.remote_port))
#                    try:
#                        if self.socks_version is not None:
#                            self.mud_server = telnetlib.Telnet(self.socks_server, self.socks_port, 30)
#                            #self.mud_server.set_debuglevel(10)
#                            self.mud_server.set_option_negotiation_callback(self.handle_telnet_option)
#                            self._negotiate_with_socks_proxy()
#                        else:
#                            self.mud_server = telnetlib.Telnet(self.remote_hostname, self.remote_port, 30)
#                            self.mud_server.set_option_negotiation_callback(self.handle_telnet_option)
#                        print("XXX Connected to MUD {}, port {}".format(self.remote_hostname, self.remote_port))
#                    except Exception as err:
#                        print('Connection to MUD {}, port {} error: {}\r\n'.format(
#                                self.remote_hostname, self.remote_port, err))
#                        self.mud_client.send(
#                                'Connection to MUD {}, port {} error: {}\r\n'.format(
#                                self.remote_hostname, self.remote_port, err))
#                        self.mud_client.close()
#                        self.mud_client = None
#                        self.mud_server = None
#
#            if self.mud_client in reads:
#                # Hark! The user has typed a command!
#                try:
#                    data = self._client_hold_data + self.mud_client.recv(1024)
#                    self._client_hold_data = ''
#                    pos = data.find('\xff')
#                    while pos >= 0:
#                        if len(data) < pos+3:
#                            print("XXX Telnet protocol bytes incomplete; wating for more from client...")
#                            self._client_hold_data = data
#                            data = None
#                            return
#
#                        print("XXX Ignoring Telnet protocol bytes {:02x}{:02x}{:02x}".format(
#                                ord(data[pos]), ord(data[pos+1]), ord(data[pos+2])))
#                        data = data[:pos] + data[pos+3:]
#                        pos = data.find('\xff')
#
#                    if self.echo:
#                        print("XXX received", len(data), "from client:", tiny_hexdump(data))
#                    else:
#                        print("XXX received", len(data), "from client: [not shown]")
#                    self.mud_server.write(data)
#
#                except socket.error:
#                    # On second thought, they rang just to say they hung up on us.
#                    # That's not very nice
#                    # XXX log disconnect
#                    print("XXX client disconnected from proxy.")
#                    if self.mud_client:
#                        self.mud_client.close()
#                        self.mud_client = None
#                    if self.mud_server:
#                        self.mud_server.close()
#                        self.mud_server = None
#
#        
#        # non-blocking attempt to read from the MUD game
#        if self.mud_server:
#            try:
#                data = self._server_hold_data + self.mud_server.read_very_eager()
#                self._server_hold_data = ''
#                data = self.ansi_parser.filter(data)
#            except EOFError:
#                print("XXX MUD disconnected.")
#                self.hangup()
#                data = None
#            except IncompleteSequence:
#                print("XXX Incomplete ANSI sequence received.  Saving {} for later.".format(data))
#                self._server_hold_data = data
#                data = None
#
#            if data:
#                self.mud_client.sendall(data)
#
#    def hangup(self):
#        print("XXX severing connection to MUD.")
#        self.mud_server = None
#        if self.mud_client:
#            self.mud_client.sendall("MUD Server closed the connection.\r\n")
#            self.mud_client.close()
#            self.mud_client = None
#

#    def handle_telnet_option(self, socket, command, option):
#        # command: telnetlib.WILL|WONT
#        # option: telnetlib.ECHO
#        if option == telnetlib.ECHO:
#            if command == telnetlib.WILL:
#                # server is (lying about) saying it will echo stuff
#                self.echo = False
#                if self.mud_client:
#                    self.mud_client.sendall(telnetlib.IAC+telnetlib.WILL+telnetlib.ECHO)
#                print("XXX turning echo off")
#
#            elif command == telnetlib.WONT:
#                # server is saying it won't echo, so we have to
#                self.echo = True
#                if self.mud_client:
#                    self.mud_client.sendall(telnetlib.IAC+telnetlib.WONT+telnetlib.ECHO)
#                print("XXX turning echo on")
#            elif command == telnetlib.DO:
#                # server is asking US to echo now?  okay...
#                self.echo = True
#                if self.mud_client:
#                    self.mud_client.sendall(telnetlib.IAC+telnetlib.DO+telnetlib.ECHO)
#                print("XXX turning echo on")
#            elif command == telnetlib.DONT:
#                # server is asking US to NOT echo.
#                self.echo = False
#                if self.mud_client:
#                    self.mud_client.sendall(telnetlib.IAC+telnetlib.DONT+telnetlib.ECHO)
#                print("XXX turning echo off")
#            else:
#                print("XXX unknown echo command {}".format(command))
#        else:
#            print("XXX unknown telnet protocol option setting {}.{}".format(command, option))


# Copyright (c) 2010, 2015, 2021 by Steven L. Willoughby, Aloha, Oregon, USA.
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
