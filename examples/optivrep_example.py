#!/usr/bin/env python
# encoding: utf-8
"""
optivrep_example.py

Created by Paul Fudal on 2014-01-27.
Copyright (c) 2014 __MyCompanyName__. All rights reserved.
"""

import time
import numpy as np
from surrogates.vrepsim import vrepcom
from surrogates.stemsim import optivrepar
import env
from natnet import FrameBuffer
import treedict

def main(move_time=10.0):
    
    fb = FrameBuffer(move_time)
    fb.track_only()
    start = time.time()
    time.sleep(move_time)
    fb.stop_tracking()
    end = time.time()
    trajectory = fb.tracking_period(start, end)
    
    ovar = optivrepar.OptiVrepAR()
    ovar.execute(trajectory)

if __name__ == '__main__':
    main()

