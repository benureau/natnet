import env
import natnet
import time
import os

if __name__ == '__main__':
    nnclient = natnet.NatNetClient()
    c = 0
    while True:
        c += 1
        frame = nnclient.receive_frame()
        data = frame.unpack_data()
        if c % 10 == 0:
            os.system('clear')
            print natnet.pp(data)