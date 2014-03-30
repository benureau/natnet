import threading
from collections import deque
import time
import atexit

from . import natnet

kLeft        =  1
kAny         =  0
kRight       = -1
kUpperLeft   = 10
kUpperRight  = 11
kBottomLeft  = 12
kBottomRight = 13


class MarkerError(Exception):
    pass

class FrameBuffer(threading.Thread):

    def __init__(self, timespan, nnclient = None, addr= '239.255.42.99', port = 1511, raise_to_exc_info=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self._stop = threading.Event()

        self.nnclient = nnclient
        if self.nnclient is None:
            self.nnclient = natnet.NatNetClient(addr=addr, port=port)
        self.timespan = timespan

        self.frames = deque()
        self.trackdata = deque()
        self.framecount = 0 # frame from the start.

        self._tracking   = False
        self._track_side = kLeft
        self._dual_track = False

        def cleanup():
            self.stop()
            self.join(0.2)
        atexit.register(cleanup)

        self.exc_info = False
        self.start()

    def stop(self):
        """Stop the thread after the end of the current loop"""
        self._stop.set()

    @property
    def fps(self):
        n = len(self.frames)
        if n == 0:
            return 0.0
        return n/(self.frames[-1][0]-self.frames[0][0])

    def stopped(self):
        return self._stop.isSet()


    def run(self):
        try:
            while not self.stopped():
                frame = self.nnclient.receive_frame()
                timestamp = time.time()
                self.frames.append((timestamp, frame.unpack_data()))
                self.framecount += 1

                if self._tracking:
                    self.trackdata.append((timestamp, self._tracker_pos()))

                if self.framecount % 10 == 0:
                    timestamp, frame = self.frames[0]
                    while time.time() - timestamp > self.timespan:
                        self.frames.popleft()
                        timestamp, frame = self.frames[0]
                time.sleep(0.001)
        except Exception as e:
            import sys
            self.exc_info = sys.exc_info()

    def _tracker_pos(self):
        if len(self.frames) == 0:
            raise IOError("no frames in buffer")

        u_ms = self.frames[-1][1]['u_markers']

        if self._track_side == kLeft:
            u_ms_side = [u for u in u_ms if u[0] >= 0]
        elif self._track_side == kRight:
            u_ms_side = [u for u in u_ms if u[0] < 0]
        #CRAP CODE
        elif self._track_side == kUpperLeft:
            u_ms_side = [u for u in u_ms if u[0] >= 0 and u[1] >= 0]
        elif self._track_side == kUpperRight:
            u_ms_side = [u for u in u_ms if u[0]  < 0 and u[1] >= 0]
        elif self._track_side == kBottomLeft:
            u_ms_side = [u for u in u_ms if u[0] >= 0 and u[1]  < 0]
        elif self._track_side == kBottomRight:
            u_ms_side = [u for u in u_ms if u[0]  < 0 and u[1]  < 0]
        else:
            u_ms_side = u_ms

        if len(u_ms_side) > 1:
            raise MarkerError("expected at maximum one marker, got more ({}: {})".format(len(u_ms_side), u_ms_side))
        if len(u_ms_side) == 1:
            return u_ms_side[0]
        if len(u_ms_side) == 0:
            return None


    def _track(self):
        if len(self.frames) == 0:
            time.sleep(0.01)
        if self._tracker_pos() is None:
            raise MarkerError('no marker detected')

        self._tracking = True

    def track(self, side='any'):
        self._track_side = {'any': kAny, 'left':kLeft, 'right':kRight,
                            'upper.left':kUpperLeft, 'upper.right':kUpperRight,
                            'bottom.left':kBottomLeft, 'bottom.right':kBottomRight}[side]
        self._track()

    def track_left(self):
        """ If only one marker is present, track it.
            Else, raise ValueError.
        """
        self._track_side = kLeft
        self._track()

    def track_right(self):
        """ If only one marker is present, track it.
            Else, raise ValueError.
        """
        self._track_side = kRight
        self._track()

    def stop_tracking(self):
        self._tracking = False

    def purge_tracking(self):
        self.track_data = deque()

    def tracking_slice(self, start, end):
        if self.exc_info:
            raise self.exc_info[1], None, self.exc_info[2]

        tdata = []
        for ts, p in self.trackdata:
            if start < ts < end:
                tdata.append((ts, p))
            #if start > ts:
            #    break
        return tdata

    def track_nearest(self, p, exclusion=2.0):
        """ Track the nearest marker of p across frames

            :param exclusion: how much times farther other markers must be
                              from p than the closest one
        """
        raise NotImplementedError
