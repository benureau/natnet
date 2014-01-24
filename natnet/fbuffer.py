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
        self.framecount = 0 # frame from the start.

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
            self.frames.append((time.time(), frame))
            self.framecount += 1

            if self.framecount % 10 == 0:
                timestamp, frame = self.frames[0]
                while time.time() - timestamp > self.timespan:
                    self.frames.popleft()
                    timestamp, frame = self.frames[0]
            time.sleep(0.001)

