import env
from natnet import FrameBuffer
import time
import sys

addr = '239.255.42.99'
if len(sys.argv) > 1:
    addr = addr[:-len(sys.argv[1])] + sys.argv[1]

fb = FrameBuffer(1.0, addr=addr)
time.sleep(2.0)

# should be close to 120 fps
print('optitrack: {:.2f} fps'.format(fb.fps))