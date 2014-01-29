import socket
import struct
import time

from toolbox import gfx

_sizeref = {
    'h': 2,
    'i': 4,
    'I': 4,
    'f': 4,
    's': 1,
}


class NatNetClient(object):

    def __init__(self, addr= '239.255.42.99', port = 1511, buff_size = 100000, byteorder = '@'):
        self.addr = addr
        self.port = port
        self.buff_size = buff_size
        self.byteorder = byteorder

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((addr, port))
        mreq = struct.pack("4sl", socket.inet_aton(addr), socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def receive_frame(self):
        data = self._sock.recv(self.buff_size)
        frame = NatNetFrame(data = data, byteorder = self.byteorder)

        return frame

class NatNetFrame(object):

    def __init__(self, data = '', byteorder = '@'):
        self.byteorder = byteorder

        self._data     = data
        self._offset   = 0


    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._offset = 0
        self._data   = value

    def _read(self, fmt, size = None, update_offset = True):
        """ Read a portion of the message, and unpack it.
            The unpacked data will be returned as a tuple, except there is only one elements;
            the element will then be returned directly

            :param fmt:            the format to unpack to. See struct module for more details.
            :param size:           the length to read. if None, it is calculated from the format.
                                   currently, the automatic size calculation does not support numerals.
            :param update_offset:
        """
        if size is None:
            size = sum(_sizeref[e] for e in fmt)
        assert self._offset + size <= len(self._data)
        u_data = struct.unpack(self.byteorder+fmt, self._data[self._offset:self._offset+size])
        if update_offset:
            self._offset += size
        if len(u_data) == 1:
            return u_data[0]
        return u_data

    def unpack_data(self):
        self._offset = 0

        dd = {} # data dict

        dd['message_id'], byte_length = self._read('hh')
        assert byte_length + 4 == len(self._data), "message's length ({}) is not the same as the embedded value ({})".format(len(self._data), byte_length + 4)

        if dd['message_id'] != 7:
            print("non-supported message id : {}".format(dd['message_id']))
            return dd

        dd['frame_number'] = self._read('i')

        dd['markersets'] = {} # identified markers sets
        dd['u_markers']  = [] # unidentified markers
        dd['rbs']        = [] # rigid bodies
        dd['skeletons']  = [] # ibit
        dd['lb_markers'] = [] # ibit

        ## markers ##
        n_imarkersets = self._read('i')
        for _ in range(n_imarkersets):
            setname, positions = self._unpack_imarkerset()
            dd['markersets'][setname] = positions

        n_umarkers = self._read('i') # number of unidentified markers
        for _ in range(n_umarkers):
            dd['u_markers'].append(self._read('fff'))

        ## rigid bodies ##
        n_rb = self._read('i')
        dd['rb'] = tuple(self._unpack_rb() for _ in range(n_rb))

        ## skeletons ##
        n_skeletons = self._read('i')
        dd['skeletons'] = tuple(self._unpack_skeleton() for _ in range(n_skeletons))

        ## labeled markers ##
        n_labeledmarkers = self._read('i')
        dd['lb_markers'] = tuple(self._unpack_lb_marker() for _ in range(n_labeledmarkers))

        ## time ##
        dd['latency']           = self._read('f')
        dd['timecode']          = self._read('i')
        dd['timecode_subframe'] = self._read('i')

        eod = self._read('i')

        if self._offset != len(self._data) or eod != 0:
            print('warning: unread data, {} bytes.'.format(len(self._data) - self._offset))
        elif eod != 0:
            print('warning: weird final 4 bytes of data (expected 0, got {})'.format(eod))

        return dd

    def _unpack_name(self):
        """ Unpack a name terminated by C zero character (\0) """
        chunk = self._data[self._offset:self._offset+256]
        name_len = chunk.find('\0')
        name = self._read(str(name_len)+'s', size = name_len) # maker set name
        self._offset += 1 # C zero char

        return name


    def _unpack_imarkerset(self):
        """ Unpack a marker set"""
        setname = self._unpack_name()

        n_markers = self._read('i') # number of marker in the set
        positions = tuple(self._read('fff') for _ in range(n_markers))

        return setname, positions


    def _unpack_rb(self):
        """ Unpack a rigid body.

            We assume that the offset is positionned at the beginning of the rigid body data
        """
        rbd = {}
        rbd['id']          = self._read('i')
        rbd['position']    = self._read('fff')
        rbd['orientation'] = self._read('ffff')
        nMarkers           = self._read('i')

        rbMarkers = [{} for _ in range(nMarkers)]
        for md in rbMarkers:
            md['position'] = self._read('fff')
        for md in rbMarkers:
            md['id'] = self._read('I')
        for md in rbMarkers:
            md['size'] = self._read('f')

        rbd['markers'] = rbMarkers
        rbd['mean_error'] = self._read('f')

        return rbd


    def _unpack_lb_marker(self):
        """ Unpack a labeled marker.

            We assume that the offset is positionned at the beginning of the labeled marker data
        """
        lbd = {}
        lbd['id']       = self._read('i')
        lbd['position'] = self._read('fff')
        lbd['size']     = self._read('f')

        return lbd


    def _unpack_skeleton(self):
        skd = {}
        skd['id']  = self._read('i')
        n_skrb     = self._read('i') # number of rigid bodies in the skeleton
        skd['rbs'] = tuple(self._unpack_rb() for _ in range(n_skrb))
        return skd


    def _unpack_rbdesc(self):
        """ Unpack a rigid body description

            We assume that the offset is positionned at the beginning of the rigid body description
        """
        rbd = {}
        rbd['name']      = self._unpack_name()
        rbd['id']        = self._read('i')
        rbd['parent_id'] = self._read('i')
        rbd['offsets']   = self._read('fff')

        return rbd

expandable_type = set((tuple, dict, list, str))

def pp(d):
    order = None
    if 'frame_number' in d:
        order = ['frame_number',
                 'markersets',
                 'u_markers',
                 'rb',
                 'skeletons',
                 'lb_markers',
                 'latency',
                 'timecode',
                 'timecode_subframe']
    return _pp(d, keys = order)

def _pp(d, ident = 0, keys = None):
    """Pretty printing of dictionary"""
#    s = '{' + '{}'.format('\n'.join('{}: {}'.format(key, value) for key, value in d.items())) + '}'
    if type(d) == dict:
        s = ''
        len_maxkey = max(len(key) for key in d.keys())
        if keys is None:
            keys = d.keys()
        n = len(keys)
        for i, key in enumerate(keys):
            pp_value = _pp(d[key], ident = ident + len(key) + 3)
            if i == 0:
                s += '{{{}{}{}: {}'.format(gfx.green, key, gfx.end, pp_value)
            else:
                s += '{}{}{}{}: {}'.format(' '*(ident+1), gfx.green, key, gfx.end, pp_value)
            if i == n-1:
                s += '}'
            else:
                s += ',\n'
        return s
    elif type(d) == list:
        n = len(d)
        if n == 0 or not type(d[0]) in expandable_type:
            return str(d)
        else:
            s = ''
            for i, value in enumerate(d):
                pp_value = _pp(value, ident = ident + 1)
                if i == 0:
                    s += '[{}'.format(pp_value)
                else:
                    s += '{}{}'.format(' '*(ident+1), pp_value)
                if i == n-1:
                    s += ']'
                else:
                    s += ',\n'
            return s
    elif type(d) == tuple:
        n = len(d)
        if n == 0:
            return str(d)
        elif not type(d[0]) in expandable_type:
            return '({})'.format(','.join(_pp(e) for e in d))
        else:
            s = ''
            for i, value in enumerate(d):
                pp_value = _pp(value, ident = ident + 1)
                if i == 0:
                    s += '({}'.format(pp_value)
                else:
                    s += '{}{}'.format(' '*(ident+1), pp_value)
                if i == n-1:
                    s += ')'
                else:
                    s += ',\n'
            return s
    elif type(d) == str:
        return "{}'{}'{}".format(gfx.cyan, d, gfx.end)
    elif type(d) == float:
        return '{}{: 5.4f}{}'.format(gfx.purple, d, gfx.end)
    elif type(d) == int:
        return '{}{}{}'.format(gfx.red, d, gfx.end)
    return str(d)


