#! /usr/bin/env python

from __future__ import print_function

import sys
import bluetooth

__all__ = ['BTSMAConnection', 'BTSMAError', 'parse_header']

class BTSMAError(Exception):
    pass


def _check_header(hdr):
    assert len(hdr) >= 4
    if (hdr[0] != 0x7e) or (hdr[2] != 0x00):
        raise BTSMAError("Missing packet start marker")
    if (hdr[3] != (hdr[1] ^ 0x7e)):
        raise BTSMAError("Bad length bytes in packet")
    return hdr[1]


def ba2str(addr):
    assert len(addr) == 6
    return "%02X:%02X:%02X:%02X:%02X:%02X" % tuple(reversed(addr))


def dump_hex(data):
    s = ''
    for i, b in enumerate(data):
        if (i % 16) == 0:
            s += '\t'
        s += '%02X' % b
        if (i % 16) == 15:
            s += '\n'
        elif (i % 16) == 7:
            s += '-'
        else:
            s += ' '
    return s

TYPEMAP = {
    0x02: "HELLO",
}

class BTSMAPacket(object):
    HDRLEN = 17

    def __init__(self, raw):
        self.raw = raw
        self.pktlen = _check_header(raw)
        self.fromaddr = ba2str(raw[4:10])
        self.toaddr = ba2str(raw[10:16])
        self.type = raw[16]

    def __len__(self):
        return self.pktlen

    def payload(self):
        return self.raw[self.HDRLEN:]

    def __str__(self):
        s = "[%d] %s -> %s : TYPE %02X" % (self.pktlen, self.fromaddr,
                                           self.toaddr, self.type)
        if self.type in TYPEMAP:
            s += " (%s)" % TYPEMAP[self.type]
        return  s + "\n" + dump_hex(self.payload())

class BTSMAConnection(object):
    MAXBUFFER = 512

    def __init__(self, addr):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((addr, 1))

        self.remote_addr = addr
        self.local_addr = self.sock.getsockname()[0]

        self.rxbuf = bytearray()

    def raw_peek_packet(self):
        if len(self.rxbuf) < 4:
            return None

        pktlen = _check_header(self.rxbuf[:4])

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
        return BTSMAPacket(self.raw_read_packet())


if __name__ == '__main__':
    conn = BTSMAConnection(sys.argv[1])
    print("Connected %s -> %s" % (conn.local_addr, conn.remote_addr))
    while True:
        pkt = conn.read_packet()
        print("IN ", pkt)

