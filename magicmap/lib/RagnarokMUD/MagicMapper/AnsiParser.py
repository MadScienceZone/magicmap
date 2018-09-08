#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
# RAGNAROK MAGIC MAPPER SOURCE CODE: ANSI Sequence Parser
# $Header$
#
# Copyright (c) 2012 by Steven L. Willoughby, Aloha, Oregon, USA.
# All Rights Reserved.  Licensed under the Open Software License
# version 3.0.  See http://www.opensource.org/licenses/osl-3.0.php
# for details.
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

class IncompleteSequence (Exception): pass

class AnsiParser (object):
    def __init__(self, target_viewer=None):
        self.inline_images_enabled = True
        self.target_viewer = target_viewer

    def filter(self, s):
        '''filter out our ANSI sequences from s and act on them.
        returns s without those sequences.  The result may include
        other ANSI sequences we weren't looking for.'''

        filtered_text = []
        suppressing = False
        stringvalue = None

        # multiline: wrap in split/join on newlines
        # We only care about $[> sequences
        remainder = 0
        i = s.find('\33[>')

        while i >=0 :
            if not suppressing:
                filtered_text.append(s[remainder:i])
            else:
                newline = s.find('\n', remainder, i)
                if newline >= 0:
                    filtered_text.append(s[newline+1:i])

            parameters = []
            accumulator = None
            #
            # Scan sequence up to unquoted non-numeric character
            # which terminates the sequence.  Ours are in the private
            # range p..~  (we implement p,s,t,u,v,w,x,~ so far)
            #
            # parameters are separated by ';' and must be either numeric
            # or double-quoted strings.  They may be completely empty.
            # 
            # we aren't required to, but we'll be forgiving enough to
            # allow adjacent strings and strings adjacent to integers
            # without the separator, hence '12"foo"34"bar""baz"' would
            # be the same as '12;"foo";34;"bar";"baz"', although the
            # latter is preferred.
            #
            # id;"name";"fmt" w     create gauge
            # id;v;max u            update gauge value
            # id x                  delete gauge
            # 1;"name" p            start tracking map for <name>
            # 0p                    stop tracking map
            # "id" ~                player location update
            # i;n;[m];[s];id s      force (re)load of map room from server
            # 1t                    suppress output to \n
            # 2t                    ditto but only if we're displaying in-line images
            # 0t                    stop suppression
            # "id" v                display inline image
            #
            for i, ch in enumerate(s[i+3:], start=i+3):
                if ch == '"':
                    # quoted string parameter value
                    if stringvalue is None:
                        if accumulator is not None:
                            parameters.append(accumulator)
                            accumulator = None
                        stringvalue = []
                    else:
                        accumulator = ''.join(stringvalue)
                        stringvalue = None

                elif stringvalue is not None:
                    stringvalue.append(ch)

                elif ch.isdigit():
                    if isinstance(accumulator, str):
                        parameters.append(accumulator)
                        accumulator=None
                    accumulator = (0 if accumulator is None else accumulator) * 10 + int(ch)

                elif ch == ';':
                    # parameter separator, push and reset
                    parameters.append(accumulator)
                    accumulator = None

                elif ch == 'p':
                    # map tracking control
                    self._param_range(parameters, accumulator, 2)

                    if not parameters[0]:
                        self.handle_tracking_stop()
                    else:
                        self.handle_tracking_start(parameters[1])
                    break

                elif ch == 'q':
                    # debugging support
                    self._param_range(parameters, accumulator)
                    self.handle_debug(parameters)
                    break

                elif ch == 's':
                    # i;n;[m];[s];id s      force (re)load of map room from server
                    self._param_range(parameters, accumulator, 5, 5)
                    self.handle_location_sync(*parameters)
                    break

                elif ch == 't':
                    self._param_range(parameters, accumulator, 1, 1)
                    if parameters[0] == 2:
                        suppressing = self.inline_images_enabled
                    else:
                        suppressing = bool(parameters[0])
                    break

                elif ch == 'u':
                    # update gauge
                    self._param_range(parameters, accumulator, 3, 3)
                    self.handle_gauge_update(*parameters)
                    break

                elif ch == 'v':
                    # display in-line image
                    self._param_range(parameters, accumulator, 1, 1)
                    if parameters[0] and self.inline_images_enabled:
                        self.handle_image(parameters[0])
                    break

                elif ch == 'w':
                    # create gauge
                    self._param_range(parameters, accumulator, 2, 3)
                    self.handle_gauge_create(*parameters)
                    break

                elif ch == 'x':
                    # delete gauge
                    self._param_range(parameters, accumulator, 1, 1)
                    self.handle_gauge_destroy(parameters[0])
                    break

                elif ch == '~':
                    # update position on map
                    self._param_range(parameters, accumulator, 1, 1)
                    if parameters[0]:
                        self.handle_tracking_position(parameters[0])
                    else:
                        self.handle_tracking_position(None) # We don't know where we are
                    break

                else:
                    # invalid private sequence detected if we reach here.
                    # We'll just ignore the sequence and go on.
                    # XXX log it!
                    self._param_range(parameters, accumulator, 0)
                    filtered_text.append('\33[>' + ';'.join([
                        '"' + x + '"' if isinstance(x, str) else str(x)
                        for x in parameters
                    ]) + ch)
                    break
            else:
                # we reached the end of the string w/o terminating the sequence!
                raise IncompleteSequence('End of input received before sequence was complete')

            remainder = i+1
            i = s.find('\33[>', remainder)

        result = ''.join(filtered_text)
        if not suppressing:
            return result + s[remainder:]
        else:
            newline = s.find('\n', remainder)
            if newline >= 0:
                return result + s[newline+1:]
            else:
                return result

    def _param_range(self, parameters, accumulator=None, min=1, max=None):
        if accumulator is not None:
            parameters.append(accumulator)
            accumulator = None

        while len(parameters) < min:
            parameters.append(None)

        if max is not None and len(parameters) > max:
            # XXX log error!
            del parameters[max:]

    # external interfaces.  We want to trap exceptions here
    # and report them out, so they don't stop everything else
    # going on.  None of these should be fatal.

    def trapErrors(f):
        def wrapper(self, *args, **kw):
            try:
                f(self, *args, **kw)
            except Exception as err:
                print("XXX Error in {} call: {}".format(
                        f.__name__, err))
        return wrapper

    @trapErrors
    def handle_tracking_start(self, player_name):
        if self.target_viewer:
            self.target_viewer.tracking_start(player_name)

    @trapErrors
    def handle_tracking_stop(self):
        if self.target_viewer:
            self.target_viewer.tracking_stop()

    @trapErrors
    def handle_tracking_position(self, id=None):
        print("XXX handle_tracking_position(id={})".format(id))
        if self.target_viewer:
            self.target_viewer.tracking_position(id)

    @trapErrors
    def handle_location_sync(self, i, total, modtime, checksum, id):
        if self.target_viewer:
            self.target_viewer.tracking_sync(i, total, modtime, checksum, id)

    def handle_gauge_create(self, id, name, fmt): pass
    def handle_gauge_update(self): pass
    def handle_gauge_destroy(self): pass
    def handle_image(self, id):
        print("XXX display inline image {}".format(id))

    def handle_debug(self):
        # in the production code, we don't.
        pass
