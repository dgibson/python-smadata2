#! /usr/bin/env python

from __future__ import print_function
from __future__ import division

import sys
import bluetooth
import readline

__all__ = ['BTSMAConnection', 'BTSMAError', 'dump_packet',
           'make_crc_packet', 
           'make_packet', 'make_hello_packet', 'make_signalreq_packet']

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
    

def dump_hex(data, prefix):
    s = ''
    for i, b in enumerate(data):
        if (i % 16) == 0:
            s += '%s%04x: ' % (prefix, i)
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
        name = pkttype_map[t][0]
        return "%s (%02X)" % (name, t)
    else:
        return "TYPE %02X" % t


def pkttype_dump(f, type_, pkt, prefix):
    if type_ in pkttype_map:
        dump = pkttype_map[type_][1]
        if dump is not None:
            dump(f, pkt, prefix)


def def_pkttype(name, val, dump=None):
    globals()[name] = val
    pkttype_map[val] = (name, dump)


crc16_table = [0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
               0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
               0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
               0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
               0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
               0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
               0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
               0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
               0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
               0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
               0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
               0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
               0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
               0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
               0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
               0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
               0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
               0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
               0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
               0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
               0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
               0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
               0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
               0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
               0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
               0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
               0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
               0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
               0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
               0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
               0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
               0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78]
assert(len(crc16_table) == 256)


def crc16(iv, data):
    crc = iv
    for b in data:
        crc = (crc >> 8) ^ crc16_table[(crc ^ b) & 0xff]
    return crc ^ 0xffff


def unescape(data):
    out = bytearray()
    while data:
        b = data.pop(0)
        if b == 0x7d:
            out.append(data.pop(0) ^ 0x20)
        else:
            out.append(b)
    return out


def dump_pkt_crc(f, pkt, prefix):
    if ((pkt[17] != 0x00)
        or (pkt[18] != 0x7e)
        or (pkt[-1] != 0x7e)):
        f.write("%sCRC unexpected framing\n" % prefix)
    spl = unescape(pkt[19:-3])
    pcrc = (pkt[-2] << 8) + pkt[-3]
    ccrc = crc16(0xffff, spl)
    if ccrc == pcrc:
        f.write("%sValid CRC 0x%04x\n" % (prefix, ccrc))
    else:
        f.write("%sBad CRC 0x%04x (expected 0x%04x)\n" % (prefix, pcrc, ccrc))
    f.write(dump_hex(spl, prefix + "    "))


def dump_pkt_peers(f, pkt, prefix):
    payload = pkt[HDRLEN:]

    if (len(payload) % 7) != 0:
        f.write("%s!!! Unexpected PEERS format" % prefix)
    else:
        for i in range(0, len(payload), 7):
            n = payload[i]
            addr = ba2str(payload[i+1:i+7])
            f.write("%sPEER %02X: %s\n" % (prefix, n, addr))

def dump_pkt_signal(f, pkt, prefix):
    payload = pkt[HDRLEN:]
    signal = (payload[5] / 0xff) * 100
    f.write("%sSIGNAL %.1f%%\n" % (prefix, signal))


def dump_pkt_error(f, pkt, prefix):
    f.write("%sERROR in packet:\n" % prefix)
    dump_packet(pkt[21:], f, prefix + "    ")

def_pkttype("CRC", 0x01, dump_pkt_crc)
def_pkttype("HELLO", 0x02)
def_pkttype("PEERS?", 0x0a, dump_pkt_peers)
def_pkttype("SIGNALREQ?", 0x03)
def_pkttype("SIGNAL?", 0x04, dump_pkt_signal)
def_pkttype("ERROR", 0x07, dump_pkt_error)

def dump_packet(pkt, f, prefix):
    pktlen = _check_header(pkt)
    fromaddr = ba2str(pkt[4:10])
    toaddr = ba2str(pkt[10:16])
    type_ = pkt[16]

    f.write("%s[%d bytes] %s -> %s : %s\n" % (prefix, pktlen, fromaddr,
                                              toaddr, pkttype_name(type_)))
    prefix = " " * len(prefix)
    f.write(dump_hex(pkt, prefix))
    pkttype_dump(f, type_, pkt, prefix + "    ")
    

def make_packet(fromaddr, toaddr, payload):
    pktlen = len(payload) + HDRLEN - 1
    pkt = bytearray([0x7e, pktlen, 0x00, pktlen ^ 0x7e])
    pkt += str2ba(fromaddr)
    pkt += str2ba(toaddr)
    pkt += payload
    assert _check_header(pkt) == pktlen
    return pkt


def make_crc_packet(conn, subpayload):
    crc = crc16(0xffff, subpayload)
    payload = bytearray('\x01\x00\x7e')
    payload += subpayload
    payload.append(crc & 0xff)
    payload.append(crc >> 8)
    payload.append(0x7e)
    return make_packet(conn.local_addr, "ff:ff:ff:ff:ff:ff", payload)

    
def make_hello_packet(conn):
    hello = bytearray('\x02\x00\x00\x04\x70\x00\x01\x00\x00\x00\x00\x01\x00\x00\x00')
    return make_packet("00:00:00:00:00:00", conn.remote_addr, hello)


def make_signalreq_packet(conn):
    signalreq = bytearray('\x03\x00\x05\x00')
    return make_packet("00:00:00:00:00:00", conn.remote_addr, signalreq)


class BTSMAConnection(object):
    MAXBUFFER = 512

    def __init__(self, addr):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((addr, 1))

        self.remote_addr = addr
        self.local_addr = self.sock.getsockname()[0]

        self.rxbuf = bytearray()
        self.pppbuf = bytearray()

    def peek_packet(self):
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
        pkt = self.peek_packet()
        while pkt is None:
            self.__rxmore()
            pkt = self.peek_packet()
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

