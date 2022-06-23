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
# RAGNAROK MAGIC MAPPER SOURCE CODE: ANSI Sequence Parser
#
# We emit the following events to the specified queue
# as the ANSI codes come in to us:
#0+ $[c1;c2;...;cn;m            AnsiColor           c: color codes
#2  $[[r];[c]H                  AnsiCursor          row, col default to 1 (top left)
#1  $[nJ                        AnsiClear
#1  $[nK                        AnsiClearEOL
#
#1  $[>"id"v                    AnsiImage           display image with given id
#2  $[>s[;"name"]p              AnsiTrack           s: 0=stop, 1=start tracking map for player name
#5  $[>i;n;[m];[s];"id"s        AnsiUpdateLocation  i: n: m: s: id:
#1  $[>"id"~                    AnsiCurrentLocation id:
#3  $[>g;[name[;fmt]]w          AnsiCreateGauge     g: name: fmt:
#3  $[>g;v;[max]u               AnsiUpdateGauge     g: v: max:
#1  $[>gx                       AnsiDeleteGauge     g:
#1  $[>"challenge"}             AnsiAuthChallenge
#1  $[>[n]q                     AnsiCacheControl    n:
class AnsiEvent:
    def __init__(self, raw_bytes):
        self.raw_bytes = raw_bytes

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<<AnsiEvent>>"

class AnsiColor (AnsiEvent):
    def __init__(self, raw_bytes, *colors):
        AnsiEvent.__init__(self, raw_bytes)
        self.foreground = None
        self.background = None
        self.bold = None
        self.underlined = None
        self.reverse = None

        for color_code in colors:
            if   color_code == 0: self.reset()
            elif color_code == 1: self.bold = True
            elif color_code == 4: self.underlined = True
            elif color_code == 7: self.reverse = True
            elif 30 <= color_code <= 37: self.foreground = color_code - 30
            elif 40 <= color_code <= 47: self.foreground = color_code - 40
                
    def reset(self):
        self.foreground = -1
        self.background = -1
        self.bold = False
        self.underlined = False
        self.reverse = False

    def apply(self, updates):
        "Apply the colors in the AnsiColor object <updates> to our current set."
        #
        # if their attribute is None, they don't modify our state in that way at
        # all. If they have an explicit value, they do.
        # Note that fg/bg color of -1 means to use the terminal's default color.
        #
        if updates.foreground is not None: self.foreground = updates.foreground
        if updates.background is not None: self.background = updates.background
        if updates.bold is not None: self.bold = updates.bold
        if updates.underlined is not None: self.underlined = updates.underlined
        if updates.reverse is not None: self.reverse = updates.reverse

    def __str__(self):
        return f"<<AnsiColor fg={self.foreground} bg={self.background} bf={self.bold} ul={self.underlined} rv={self.reverse}>>"

class AnsiCursor (AnsiEvent):
    def __init__(self, raw_bytes, row=1, col=1):
        AnsiEvent.__init__(self, raw_bytes)
        self.row = 1 if row is None or row < 1 else row
        self.col = 1 if col is None or col < 1 else col

    def __str__(self):
        return f"<<AnsiCursor row={self.row} col={self.col}>>"

class AnsiClear (AnsiEvent):
    def __init__(self, raw_bytes, mode=0):
        AnsiEvent.__init__(self, raw_bytes)
        self.mode = mode or 0
        # mode is 0=clear from cursor to end of screen
        #         1=clear from cursor to beginning of screen
        #         2=clear entire screen
        #         3=clear entire screen and delete scrollback buffer contents

    def __str__(self):
        return f"<<AnsiClear mode={self.mode}>>"

class AnsiClearEOL (AnsiEvent):
    def __init__(self, raw_bytes, mode=0):
        AnsiEvent.__init__(self, raw_bytes)
        self.mode = mode or 0
        # mode is 0=clear from cursor to end of line
        #         1=clear from cursor to beginning of line
        #         2=clear entire line

    def __str__(self):
        return f"<<AnsiClearEOF mode={self.mode}>>"

class AnsiImage (AnsiEvent):
    def __init__(self, raw_bytes, image_id):
        AnsiEvent.__init__(self, raw_bytes)
        self.image_id = image_id

    def __str__(self):
        return f"<<AnsiImage id={self.image_id}>>"

class AnsiTrack (AnsiEvent):
    def __init__(self, raw_bytes, state, name=None):
        AnsiEvent.__init__(self, raw_bytes)
        self.state = state
        self.name = name
        # state 0=stop tracking location
        #       1=start tracking for player <name>

    def __str__(self):
        return f"<<AnsiTrack state={self.state} name={self.name}>>"
        
class AnsiUpdateLocation (AnsiEvent):
    def __init__(self, raw_bytes, i, n, modtime, checksum, location_id):
        AnsiEvent.__init__(self, raw_bytes)
        self.i = i
        self.n = n
        self.modtime = modtime
        self.checksum = checksum
        self.location_id = location_id

    def __str__(self):
        return f"<<AnsiUpdateLocation #{self.i} of {self.n} mod={self.modtime} sha={self.checksum}, id={self.location_id}>>"

class AnsiCurrentLocation (AnsiEvent):
    def __init__(self, raw_bytes, location_id=None):
        AnsiEvent.__init__(self, raw_bytes)
        self.location_id = location_id

    def __str__(self):
        return f"<<AnsiCurrentLocation id={self.location_id}>>"

class AnsiCreateGauge (AnsiEvent):
    def __init__(self, raw_bytes, gauge_id, name=None, fmt=None):
        AnsiEvent.__init__(self, raw_bytes)
        self.gauge_id = gauge_id
        self.name = name
        self.fmt = fmt

    def __str__(self):
        return f"<<AnsiCreateGauge id={self.gauge_id} name={self.name} fmt={self.fmt}>>"
    
class AnsiUpdateGauge (AnsiEvent):
    def __init__(self, raw_bytes, gauge_id, value, maxvalue=None):
        AnsiEvent.__init__(self, raw_bytes)
        self.gauge_id = gauge_id
        self.value = value
        self.maxvalue = maxvalue

    def __str__(self):
        return f"<<AnsiUpdateGauge id={self.gauge_id} value={self.value} max={self.maxvalue}>>"

class AnsiDeleteGauge (AnsiEvent):
    def __init__(self, raw_bytes, gauge_id):
        AnsiEvent.__init__(self, raw_bytes)
        self.gauge_id = gauge_id

    def __str__(self):
        return f"<<AnsiDeleteGauge id={self.gauge_id}>>"

class AnsiAuthChallenge (AnsiEvent):
    def __init__(self, raw_bytes, challenge):
        AnsiEvent.__init__(self, raw_bytes)
        self.challenge = challenge

    def __str__(self):
        return f"<<AnsiAuthChallenge {self.challenge}>>"

class AnsiCacheControl (AnsiEvent):
    def __init__(self, raw_bytes, op):
        AnsiEvent.__init__(self, raw_bytes)
        self.op = op or 0
        # operation op: 0=expire cache
        #               1=delete cache

    def __str__(self):
        return f"<<AnsiCacheControl op={self.op}>>"

class AnsiParser:
    def __init__(self, event_queue=None, client_queue=None, inline_images=True):
        self.inline_images_enabled = inline_images
        self.event_queue = event_queue
        self.client_queue = client_queue
        self.buffer = b''
        self.suppressing = False

    def parse(self, s):
        '''read bytes from s as input, dispatching the text and/or events to the
        queues set up when the AnsiParser was created. If we're partially through
        an ANSI sequence that we care about, we'll hold on to it until the next
        call completes that sequence. Note that the output may include raw ANSI
        sequences (not necessarily complete) if they aren't ones we're watching for.'''

        if not isinstance(s, bytes):
            s = bytes(s)

        if self.buffer:
            s = self.buffer + s
            self.buffer = b''

        seq_start = s.find(b'\33[')

        while seq_start >=0 :
            #
            # First, send all the text up to the start of the
            # escape sequence, skipping to newline if we've been
            # asked to suppress the rest of the line.
            #
            if not self.suppressing:
                self.emit_text(s[:seq_start])
            else:
                newline = s.find(b'\n', 0, seq_start)
                if newline >= 0:
                    self.emit_text(s[newline+1:seq_start])
                    self.suppressing = False
            #
            # Interpret the escape code.
            # If $[>... then it's probably one of our private ones; let's handle it here
            # 
            if len(s) <= seq_start+2:
                # we already know we don't have enough yet; wait for more
                self.buffer = s[seq_start:]
                return

            if chr(s[seq_start+2]) == '>':
                # special private range $[>...
                private = True
                offset = 3
            else:
                # common range $[...
                private = False
                offset = 2

            parameters = []
            accumulator = None
            stringvalue = None

            # 
            # we aren't required to, but we'll be forgiving enough to
            # allow adjacent strings and strings adjacent to integers
            # without the separator, hence '12"foo"34"bar""baz"' would
            # be the same as '12;"foo";34;"bar";"baz"', although the
            # latter is preferred.
            #
            for i, ch_byte in enumerate(s[seq_start+offset:], start=seq_start+offset):
                ch = chr(ch_byte)
                if ch == '"':
                    # quoted string parameter value
                    if stringvalue is None:
                        if accumulator is not None:
                            parameters.append(accumulator)
                            accumulator = None
                        stringvalue = b''
                    else:
                        accumulator = stringvalue
                        stringvalue = None

                elif stringvalue is not None:
                    stringvalue += bytes((ch_byte,))

                elif ch.isdigit():
                    if isinstance(accumulator, (bytes, str)):
                        parameters.append(accumulator)
                        accumulator=None
                    accumulator = (0 if accumulator is None else accumulator) * 10 + int(ch)

                elif ch == ';':
                    # parameter separator, push and reset
                    # this allows ;; to specify a nil parameter in the list
                    parameters.append(accumulator)
                    accumulator = None

                else:
                    # this terminates the sequence
                    raw_seq = s[seq_start:i+1]
                    s = s[i+1:]

                    if private:
                        if ch == 'p':
                            self._param_range(parameters, accumulator, 2, 2)
                            self.emit_event(AnsiTrack(raw_seq, *parameters))

                        elif ch == 'q':
                            self._param_range(parameters, accumulator, 1, 1)
                            self.emit_event(AnsiCacheControl(raw_seq, *parameters))

                        elif ch == 's':
                            self._param_range(parameters, accumulator, 5, 5)
                            self.emit_event(AnsiUpdateLocation(raw_seq, *parameters))

                        elif ch == 't':
                            self._param_range(parameters, accumulator, 1, 1)
                            if parameters[0] == 2:
                                self.suppressing = self.inline_images_enabled
                            else:
                                self.suppressing = bool(parameters[0])

                        elif ch == 'u':
                            self._param_range(parameters, accumulator, 3, 3)
                            self.emit_event(AnsiUpdateGauge(raw_seq, *parameters))

                        elif ch == 'v':
                            self._param_range(parameters, accumulator, 1, 1)
                            if self.inline_images_enabled:
                                self.emit_text(AnsiImage(raw_seq, *parameters))
                            else:
                                self.emit_event(AnsiImage(raw_seq, *parameters))

                        elif ch == 'w':
                            self._param_range(parameters, accumulator, 3, 3)
                            self.emit_event(AnsiCreateGauge(raw_seq, *parameters))

                        elif ch == 'x':
                            self._param_range(parameters, accumulator, 1, 1)
                            self.emit_event(AnsiDeleteGauge(raw_seq, *parameters))

                        elif ch == '~':
                            self._param_range(parameters, accumulator, 1, 1)
                            self.emit_event(AnsiCurrentLocation(raw_seq, *parameters))

                        elif ch == '}':
                            self._param_range(parameters, accumulator, 1, 1)
                            self.emit_event(AnsiAuthChallenge(raw_seq, *parameters))

                        else:
                            #
                            # Oh... this isn't one of our escape codes after all.
                            # in that case, pass it on through.
                            #
                            self.emit_text(raw_seq)
                    else:
                        if ch == 'm':
                            self._param_range(parameters, accumulator, 0)
                            self.emit_text(AnsiColor(raw_seq, *parameters))
                        elif ch == 'H':
                            self._param_range(parameters, accumulator, 2, 2)
                            self.emit_text(AnsiCursor(raw_seq, *parameters))
                        elif ch == 'J':
                            self._param_range(parameters, accumulator, 1, 1)
                            self.emit_text(AnsiClear(raw_seq, *parameters))
                        elif ch == 'K':
                            self._param_range(parameters, accumulator, 1, 1)
                            self.emit_text(AnsiClearEOL(raw_seq, *parameters))
                        else:
                            self.emit_text(raw_seq)
                    break
            else:
                # We ran out of string before the sequence was finished!
                self.buffer = s[seq_start:]
                return

            # look for another sequence after this
            seq_start = s.find(b'\33[')
        #
        # we've handled everything up to and including the last
        # complete escape sequence now; ship out any remaining text.
        #
        if s:
            self.emit_text(s)

    def emit_text(self, thing):
        print(f'text: {thing}')
        if self.client_queue:
            if isinstance(thing, str):
                self.client_queue.put(bytes(thing))
            elif isinstance(thing, bytes):
                self.client_queue.put(thing)
            elif isinstance(thing, AnsiEvent):
                self.client_queue.put(thing.raw_bytes)
        elif self.event_queue:
            self.event_queue.put(thing)

    def emit_event(self, thing):
        print(f'event: {thing}')
        if self.event_queue:
            self.event_queue.put(thing)

    def _param_range(self, parameters, accumulator=None, min=1, max=None):
        "Commit accumulator and ensure parameters within required bounds"
        if accumulator is not None:
            parameters.append(accumulator)
            accumulator = None

        while len(parameters) < min:
            parameters.append(None)

        if max is not None and len(parameters) > max:
            del parameters[max:]

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
