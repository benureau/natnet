import time
import numpy as np

import env
from natnet import FrameBuffer

fb = FrameBuffer(1.0)
fb.track_only()
start = time.time()
time.sleep(1.2)
fb.stop_tracking()

data = fb.tracking_period(start, start+1.0)
print('mean tracker position: {}'.format(np.mean(np.array([d[1] for d in data]), axis = 0)))