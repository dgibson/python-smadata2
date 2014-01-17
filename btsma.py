#! /usr/bin/env python

from __future__ import print_function
from __future__ import division

import sys
import bluetooth
import readline

__all__ = ['BTSMAConnection', 'BTSMAError',
           'OTYPE_HELLO', 'OTYPE_SIGNALREQ', 'OTYPE_SIGNAL',
           'OTYPE_ERROR']

OUTER_HLEN = 17

OTYPE_PPP = 0x01
OTYPE_HELLO = 0x02
OTYPE_SIGNALREQ = 0x03
OTYPE_SIGNAL = 0x04
OTYPE_ERROR = 0x07

class BTSMAError(Exception):
    pass


def _check_header(hdr):
    if len(hdr) < OUTER_HLEN:
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


class BTSMAConnection(object):
    MAXBUFFER = 512

    def __init__(self, addr):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((addr, 1))

        self.remote_addr = addr
        self.local_addr = self.sock.getsockname()[0]

        self.rxbuf = bytearray()
        self.pppbuf = bytearray()

    #
    # RX side
    #

    def rx(self):
        space = self.MAXBUFFER - len(self.rxbuf)
        self.rxbuf += self.sock.recv(space)

        if len(self.rxbuf) < OUTER_HLEN:
            return

        pktlen = _check_header(self.rxbuf[:OUTER_HLEN])

        if len(self.rxbuf) < pktlen:
            return

        pkt = self.rxbuf[:pktlen]
        del self.rxbuf[:pktlen]

        self.rx_raw(pkt)

    def rx_raw(self, pkt):
        from_ = ba2str(pkt[4:10])
        to_ = ba2str(pkt[10:16])
        type_ = pkt[16]
        payload = pkt[OUTER_HLEN:]

        self.rx_outer(from_, to_, type_, payload)

    def rx_outer(self, from_, to_, type_, payload):
        if type_ == OTYPE_PPP:
            self.rx_ppp_raw(from_, payload[1:])

    def rx_ppp_raw(self, from_, payload):
        self.pppbuf += payload
        term = self.pppbuf.find('\x7e', 1)
        if term < 0:
            return

        raw = self.pppbuf[:term+1]
        del self.pppbuf[:term+1]
        assert raw[-1] == 0x7e
        if raw[0] != 0x7e:
            raise BTSMAError("Missing flag byte on PPP packet")

        raw = raw[1:-1]
        frame = bytearray()
        while raw:
            b = raw.pop(0)
            if b == 0x7d:
                frame.append(raw.pop(0) ^ 0x20)
            else:
                frame.append(b)

        if (frame[0] != 0xff) or (frame[1] != 0x03):
            raise BTSMAError("Bad header on PPP frame")

        pcrc = (frame[-1] << 8) + frame[-2]
        ccrc = crc16(0xffff, frame[:-2])
        if pcrc != ccrc:
            raise BTSMAError("Bad CRC on PPP frame")

        protocol = frame[2] + (frame[3] << 8)
        
        self.rx_ppp(from_, protocol, frame[4:-2])

    def rx_ppp(self, from_, protocol, payload):
        pass

    #
    # Tx side
    #
    def tx_raw(self, pkt):
        if _check_header(pkt) != len(pkt):
            raise ValueError("Bad packet")
        self.sock.send(str(pkt))

    def tx_outer(self, from_, to_, type_, payload):
        pktlen = len(payload) + OUTER_HLEN
        pkt = bytearray([0x7e, pktlen, 0x00, pktlen ^ 0x7e])
        pkt += str2ba(from_)
        pkt += str2ba(to_)
        pkt.append(type_)
        pkt += payload
        assert _check_header(pkt) == pktlen

        self.tx_raw(pkt)

    def tx_hello(self):
        payload = bytearray('\x00\x00\x04\x70\x00\x01\x00\x00\x00\x00\x01\x00\x00\x00')
        self.tx_outer("00:00:00:00:00:00", self.remote_addr,
                      OTYPE_HELLO, payload)

    def tx_signalreq(self):
        payload = bytearray('\x00\x05\x00')
        self.tx_outer("00:00:00:00:00:00", self.remote_addr,
                      OTYPE_SIGNALREQ, payload)

    def tx_ppp_raw(self, to_, payload):
        self.tx_outer(self.local_addr, to_, OTYPE_PPP,
                      bytearray('\x00') + payload)

    def tx_ppp(self, to_, protocol, payload):
        frame = bytearray('\xff\x03')
        frame.append(protocol & 0xff)
        frame.append(protocol >> 8)
        frame += payload

        crc = crc16(0xffff, frame)

        frame.append(crc & 0xff)
        frame.append(crc >> 8)

        rawpayload = bytearray()
        rawpayload.append(0x7e)
        for b in frame:
            # Escape \x7e (FLAG), 0x7d (ESCAPE), 0x11 (XON) and 0x13 (XOFF)
            if b in [0x7e, 0x7d, 0x11, 0x13]:
                rawpayload.append(0x7d)
                rawpayload.append(b ^ 0x20)
            else:
                rawpayload.append(b)
        rawpayload.append(0x7e)

        self.tx_ppp_raw(to_, rawpayload)
