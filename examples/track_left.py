import time
import numpy as np

import env
from natnet import FrameBuffer

fb = FrameBuffer(1.0, addr='239.255.42.98'))
fb.track_left()
start = time.time()
time.sleep(1.2)
fb.stop_tracking()

data = fb.tracking_slice(start, start+1.0)
print('mean tracker position: {}'.format(np.mean(np.array([d[1] for d in data]), axis = 0)))