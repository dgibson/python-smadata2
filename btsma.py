#! /usr/bin/env python

from __future__ import print_function

import sys
import bluetooth

__all__ = ['BTSMAConnection', 'BTSMAError', 'BTSMAPacket']

HDRLEN = 17

class BTSMAError(Exception):
    pass


def _check_header(hdr):
    if len(hdr) < HDRLEN:
        raise BTSMAError("Packet too short for header")
    if (hdr[0] != 0x7e) or (hdr[2] != 0x00):
        raise BTSMAError("Missing packet start marker")
    if (hdr[3] != (hdr[1] ^ 0x7e)):
        raise BTSMAError("Bad length bytes in packet")
    return hdr[1]


def ba2str(addr):
    if len(addr) != 6:
        raise ValueError("Bad length for bluetooth address");
    assert len(addr) == 6
    return "%02X:%02X:%02X:%02X:%02X:%02X" % tuple(reversed(addr))


def str2ba(s):
    addr = [int(x, 16) for x in s.split(':')]
    addr.reverse()
    if len(addr) != 6:
        raise ValueError("Bad length for bluetooth address");
    return bytearray(addr)
    

def dump_hex(data):
    s = ''
    for i, b in enumerate(data):
        if (i % 16) == 0:
            s += '    %04x: ' % i
        s += '%02X' % b
        if (i % 16) == 15:
            s += '\n'
        elif (i % 16) == 7:
            s += '-'
        else:
            s += ' '
    if s[-1] != '\n':
        s += '\n'
    return s

def parse_hello(pkt):
    return "HELLO"

pkttype_map = {}


def pkttype_name(t):
    if t in pkttype_map:
        return "%s (%02X)" % (pkttype_map[t], t)
    else:
        return "TYPE %02X" % t


def def_pkttype(name, val):
    globals()[name] = val
    pkttype_map[val] = name


def_pkttype("HELLO", 0x02)


class BTSMAPacket(object):
    def __init__(self, fromaddr=None, toaddr=None, payload=None, raw=None):
        if raw is not None:
            if ((payload is not None)
                or (fromaddr is not None)
                or (toaddr is not None)):
                raise TypeError("Must supply either raw or payload arguments, not both")
            self.raw = raw
            self.pktlen = _check_header(raw)
            self.fromaddr = ba2str(raw[4:10])
            self.toaddr = ba2str(raw[10:16])
            self.type = raw[16]
        else:
            if ((payload is None)
                or (fromaddr is None)
                or (toaddr is None)):
                raise TypeError("Must supply either raw or payload arguments")
            self.pktlen = len(payload) + HDRLEN - 1
            self.fromaddr = fromaddr
            self.toaddr = toaddr
            self.type = payload[0]
            self.raw = bytearray([0x7e, self.pktlen, 0x00, self.pktlen ^ 0x7e])
            self.raw += str2ba(fromaddr)
            self.raw += str2ba(toaddr)
            self.raw += payload
            assert _check_header(self.raw) == self.pktlen

    def __len__(self):
        return self.pktlen

    def __str__(self):
        return "[%d bytes] %s -> %s : %s" % (self.pktlen, self.fromaddr,
                                             self.toaddr,
                                             pkttype_name(self.type))

    def dump(self, f, prefix):
        f.write(prefix + str(self) + '\n')
        f.write(dump_hex(self.raw))

class BTSMAConnection(object):
    MAXBUFFER = 512

    def __init__(self, addr):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((addr, 1))

        self.remote_addr = addr
        self.local_addr = self.sock.getsockname()[0]

        self.rxbuf = bytearray()

    def raw_peek_packet(self):
        if len(self.rxbuf) < HDRLEN:
            return None

        pktlen = _check_header(self.rxbuf[:HDRLEN])

        if len(self.rxbuf) < pktlen:
            return None

        pkt = self.rxbuf[:pktlen]
        del self.rxbuf[:pktlen]
        return pkt

    def __rxmore(self):
        space = self.MAXBUFFER - len(self.rxbuf)
        self.rxbuf += self.sock.recv(space)

    def raw_read_packet(self):
        pkt = self.raw_peek_packet()
        while pkt is None:
            self.__rxmore()
            pkt = self.raw_peek_packet()
        return pkt

    def read_packet(self):
        return BTSMAPacket(raw=self.raw_read_packet())

    def raw_write_packet(self, raw):
        pktlen = _check_header(raw)
        if pktlen != len(raw):
            raise BTSMAError("Refusing to send badly formatted packet")
        self.sock.send(str(raw))

    def write_packet(self, pkt):
        if not isinstance(pkt, BTSMAPacket):
            raise TypeError()
        self.raw_write_packet(pkt.raw)


if __name__ == '__main__':
    conn = BTSMAConnection(sys.argv[1])
    print("Connected %s -> %s" % (conn.local_addr, conn.remote_addr))
    while True:
        pkt = conn.read_packet()
        print("IN ", pkt)

