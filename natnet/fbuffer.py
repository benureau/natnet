import threading
from collections import deque
import time
import atexit

from . import natnet

class FrameBuffer(threading.Thread):

    def __init__(self, timespan, nnclient = None):
        threading.Thread.__init__(self)
        self.daemon = True
        self._stop = threading.Event()

        self.nnclient = nnclient
        if self.nnclient is None:
            self.nnclient = natnet.NatNetClient()
        self.timespan = timespan

        self.frames = deque()
        self.trackdata = deque()
        self.framecount = 0 # frame from the start.

        self._track_id = None

        def cleanup():
            self.stop()
            self.join(0.2)
        atexit.register(cleanup)

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
        while not self.stopped():

            frame = self.nnclient.receive_frame()
            timestamp = time.time()
            self.frames.append((timestamp, frame.unpack_data()))
            self.framecount += 1

            if self._track_id is not None:
                for lbm in self.frames[-1][1]['lb_markers']:
                    if lbm['id'] == self._track_id:
                        self.trackdata.append((timestamp, lbm['position']))

            if self.framecount % 10 == 0:
                timestamp, frame = self.frames[0]
                while time.time() - timestamp > self.timespan:
                    self.frames.popleft()
                    timestamp, frame = self.frames[0]
            time.sleep(0.001)

    def track_only(self):
        """ If only one marker is present, track it.
            Else, raise ValueError.
        """
        if len(self.frames) == 0:
            time.sleep(0.01)
        last_frame = self.frames[-1][1]
        if len(last_frame['u_markers']) == len(last_frame['lb_markers']) == 1:
            self._track_id = last_frame['lb_markers'][0]['id']
        else:
            self._track_id = None
            raise ValueError

    def stop_tracking(self):
        self._track_id = None

    def tracking_period(self, start, end):
        tdata = []
        for ts, p in self.trackdata:
            if ts < start:
                break
            elif ts < end:
                tdata.append((ts, p))
        return tdata

    def track_nearest(self, p, exclusion=2.0):
        """ Track the nearest marker of p across frames

            :param exclusion: how much times farther other markers must be
                              from p than the closest one
        """
        raise NotImplementedError
