import time
import os
import sys

import env
import natnet

addr = '239.255.42.99'
if len(sys.argv) > 1:
    addr = addr[:-len(sys.argv[1])] + sys.argv[1]

nnclient = natnet.NatNetClient(addr=addr)
c = 0
while True:
    c += 1
    frame = nnclient.receive_frame()
    data = frame.unpack_data()
    if c % 10 == 0:
        os.system('clear')
        print("from {}:{}\n{}".format(nnclient.addr, nnclient.port, natnet.pp(data)))