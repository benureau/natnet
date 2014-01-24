import env
from natnet import FrameBuffer
import time

fb = FrameBuffer(1.0)
time.sleep(2.0)

# should be close to 120 fps
print('optitrack: {:.2f} fps'.format(fb.fps))