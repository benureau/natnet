import time
import numpy as np
import sys

import env
from natnet import FrameBuffer

addr = '239.255.42.99'
if len(sys.argv) > 1:
    addr = addr[:-len(sys.argv[1])] + sys.argv[1]
    print(addr)

fb = FrameBuffer(1.0, addr=addr)
fb.track_right()
start = time.time()
time.sleep(1.2)
fb.stop_tracking()

data = fb.tracking_slice(start, start+1.0)
print('mean tracker position: {}'.format(np.mean(np.array([d[1] for d in data]), axis = 0)))