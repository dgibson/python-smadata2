#! /usr/bin/env python

from __future__ import print_function

import sys
import bluetooth

__all__ = ['BTSMAConnection', 'BTSMAError', 'dump_packet', 'make_packet']

HDRLEN = 17

class BTSMAError(Exception):
    pass


def _check_header(hdr):
    if len(hdr) < HDRLEN:
        raise ValueError()

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


def dump_packet(pkt, f, prefix):
    pktlen = _check_header(pkt)
    fromaddr = ba2str(pkt[4:10])
    toaddr = ba2str(pkt[10:16])
    type_ = pkt[16]

    f.write("%s[%d bytes] %s -> %s : %s\n" % (prefix, pktlen, fromaddr,
                                              toaddr, pkttype_name(type_)))

    f.write(dump_hex(pkt))

def make_packet(fromaddr, toaddr, payload):
    pktlen = len(payload) + HDRLEN - 1
    pkt = bytearray([0x7e, pktlen, 0x00, pktlen ^ 0x7e])
    pkt += str2ba(fromaddr)
    pkt += str2ba(toaddr)
    pkt += payload
    assert _check_header(pkt) == pktlen
    return pkt


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

    def read_packet(self):
        pkt = self.raw_peek_packet()
        while pkt is None:
            self.__rxmore()
            pkt = self.raw_peek_packet()
        return pkt

    def write_packet(self, pkt):
        if _check_header(pkt) != len(pkt):
            raise ValueError("Bad packet")
        self.sock.send(str(pkt))


if __name__ == '__main__':
    conn = BTSMAConnection(sys.argv[1])
    print("Connected %s -> %s" % (conn.local_addr, conn.remote_addr))
    while True:
        pkt = conn.read_packet()
        print("IN ", pkt)

