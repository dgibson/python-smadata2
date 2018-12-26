#! /usr/bin/python3
#
# smadata2.inverter.smabluetooth - Support for Bluetooth enabled SMA inverters
# Copyright (C) 2014 David Gibson <david@gibson.dropbear.id.au>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import sys
import getopt
import time
import socket

from . import base
from .base import Error
from smadata2.datetimeutil import format_time

__all__ = ['Connection',
           'OTYPE_PPP', 'OTYPE_PPP2', 'OTYPE_HELLO', 'OTYPE_GETVAR',
           'OTYPE_VARVAL', 'OTYPE_ERROR',
           'OVAR_SIGNAL',
           'int2bytes16', 'int2bytes32', 'bytes2int']

OUTER_HLEN = 18

OTYPE_PPP = 0x01
OTYPE_HELLO = 0x02
OTYPE_GETVAR = 0x03
OTYPE_VARVAL = 0x04
OTYPE_ERROR = 0x07
OTYPE_PPP2 = 0x08

OVAR_SIGNAL = 0x05

INNER_HLEN = 36

SMA_PROTOCOL_ID = 0x6560


def waiter(fn):
    def waitfn(self, *args):
        fn(self, *args)
        if hasattr(self, '__waitcond_' + fn.__name__):
            wc = getattr(self, '__waitcond_' + fn.__name__)
            if wc is None:
                self.waitvar = args
            else:
                self.waitvar = wc(*args)
    return waitfn


def _check_header(hdr):
    if len(hdr) < OUTER_HLEN:
        raise ValueError()

    if hdr[0] != 0x7e:
        raise Error("Missing packet start marker")
    if (hdr[1] > 0x70) or (hdr[2] != 0):
        raise Error("Bad packet length")
    if hdr[3] != (hdr[0] ^ hdr[1] ^ hdr[2]):
        raise Error("Bad header check byte")
    return hdr[1]


def ba2bytes(addr):
    if len(addr) != 6:
        raise ValueError("Bad length for bluetooth address")
    assert len(addr) == 6
    return "%02X:%02X:%02X:%02X:%02X:%02X" % tuple(reversed(addr))


def bytes2ba(s):
    addr = [int(x, 16) for x in s.split(':')]
    addr.reverse()
    if len(addr) != 6:
        raise ValueError("Bad length for bluetooth address")
    return bytearray(addr)


def int2bytes16(v):
    return bytearray([v & 0xff, v >> 8])


def int2bytes32(v):
    return bytearray([v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff, v >> 24])


def bytes2int(b):
    v = 0
    while b:
        v = v << 8
        v += b.pop()
    return v


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


class Connection(base.InverterConnection):
    MAXBUFFER = 512
    BROADCAST = "ff:ff:ff:ff:ff:ff"
    BROADCAST2 = bytearray(b'\xff\xff\xff\xff\xff\xff')

    def __init__(self, addr):
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
                                  socket.BTPROTO_RFCOMM)
        self.sock.connect((addr, 1))

        self.remote_addr = addr
        self.local_addr = self.sock.getsockname()[0]

        self.local_addr2 = bytearray(b'\x78\x00\x3f\x10\xfb\x39')

        self.rxbuf = bytearray()
        self.pppbuf = dict()

        self.tagcounter = 0

    def gettag(self):
        self.tagcounter += 1
        return self.tagcounter

    #
    # RX side
    #

    def rx(self):
        space = self.MAXBUFFER - len(self.rxbuf)
        self.rxbuf += self.sock.recv(space)

        while len(self.rxbuf) >= OUTER_HLEN:
            pktlen = _check_header(self.rxbuf[:OUTER_HLEN])

            if len(self.rxbuf) < pktlen:
                return

            pkt = self.rxbuf[:pktlen]
            del self.rxbuf[:pktlen]

            self.rx_raw(pkt)

    @waiter
    def rx_raw(self, pkt):
        from_ = ba2bytes(pkt[4:10])
        to_ = ba2bytes(pkt[10:16])
        type_ = bytes2int(pkt[16:18])
        payload = pkt[OUTER_HLEN:]

        self.rx_outer(from_, to_, type_, payload)

    def rxfilter_outer(self, to_):
        return ((to_ == self.local_addr) or
                (to_ == self.BROADCAST) or
                (to_ == "00:00:00:00:00:00"))

    @waiter
    def rx_outer(self, from_, to_, type_, payload):
        if not self.rxfilter_outer(to_):
            return

        if (type_ == OTYPE_PPP) or (type_ == OTYPE_PPP2):
            self.rx_ppp_raw(from_, payload)

    def rx_ppp_raw(self, from_, payload):
        if from_ not in self.pppbuf:
            self.pppbuf[from_] = bytearray()
        pppbuf = self.pppbuf[from_]

        pppbuf.extend(payload)
        term = pppbuf.find(b'\x7e', 1)
        if term < 0:
            return

        raw = pppbuf[:term+1]
        del pppbuf[:term+1]

        assert raw[-1] == 0x7e
        if raw[0] != 0x7e:
            raise Error("Missing flag byte on PPP packet")

        raw = raw[1:-1]
        frame = bytearray()
        while raw:
            b = raw.pop(0)
            if b == 0x7d:
                frame.append(raw.pop(0) ^ 0x20)
            else:
                frame.append(b)

        if (frame[0] != 0xff) or (frame[1] != 0x03):
            raise Error("Bad header on PPP frame")

        pcrc = bytes2int(frame[-2:])
        ccrc = crc16(0xffff, frame[:-2])
        if pcrc != ccrc:
            raise Error("Bad CRC on PPP frame")

        protocol = bytes2int(frame[2:4])

        self.rx_ppp(from_, protocol, frame[4:-2])

    @waiter
    def rx_ppp(self, from_, protocol, payload):
        if protocol == SMA_PROTOCOL_ID:
            innerlen = payload[0]
            if len(payload) != (innerlen * 4):
                raise Error("Inner length field (0x%02x = %d bytes)" +
                            " does not match actual length (%d bytes)"
                            % (innerlen, innerlen * 4, len(payload)))
            a2 = payload[1]
            to2 = payload[2:8]
            b1 = payload[8]
            b2 = payload[9]
            from2 = payload[10:16]
            c1 = payload[16]
            c2 = payload[17]
            error = bytes2int(payload[18:20])
            pktcount = bytes2int(payload[20:22])
            tag = bytes2int(payload[22:24])
            first = bool(tag & 0x8000)
            tag = tag & 0x7fff
            type_ = bytes2int(payload[24:26])
            response = bool(type_ & 1)
            type_ = type_ & ~1
            subtype = bytes2int(payload[26:28])
            arg1 = bytes2int(payload[28:32])
            arg2 = bytes2int(payload[32:36])
            extra = payload[36:]
            self.rx_6560(from2, to2, a2, b1, b2, c1, c2, tag,
                         type_, subtype, arg1, arg2, extra,
                         response, error, pktcount, first)

    def rxfilter_6560(self, to2):
        return ((to2 == self.local_addr2) or
                (to2 == self.BROADCAST2))

    @waiter
    def rx_6560(self, from2, to2, a2, b1, b2, c1, c2, tag,
                type_, subtype, arg1, arg2, extra,
                response, error, pktcount, first):
        if not self.rxfilter_6560(to2):
            return

        pass

    #
    # Tx side
    #
    def tx_raw(self, pkt):
        if _check_header(pkt) != len(pkt):
            raise ValueError("Bad packet")
        self.sock.send(bytes(pkt))

    def tx_outer(self, from_, to_, type_, payload):
        pktlen = len(payload) + OUTER_HLEN
        pkt = bytearray([0x7e, pktlen, 0x00, pktlen ^ 0x7e])
        pkt += bytes2ba(from_)
        pkt += bytes2ba(to_)
        pkt += int2bytes16(type_)
        pkt += payload
        assert _check_header(pkt) == pktlen

        self.tx_raw(pkt)

    def tx_ppp(self, to_, protocol, payload):
        frame = bytearray(b'\xff\x03')
        frame += int2bytes16(protocol)
        frame += payload
        frame += int2bytes16(crc16(0xffff, frame))

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

        self.tx_outer(self.local_addr, to_, OTYPE_PPP, rawpayload)

    def tx_6560(self, from2, to2, a2, b1, b2, c1, c2, tag,
                type_, subtype, arg1, arg2, extra=bytearray(),
                response=False, error=0, pktcount=0, first=True):
        if len(extra) % 4 != 0:
            raise Error("Inner protocol payloads must" +
                        " have multiple of 4 bytes length")
        innerlen = (len(extra) + INNER_HLEN) // 4
        payload = bytearray()
        payload.append(innerlen)
        payload.append(a2)
        payload.extend(to2)
        payload.append(b1)
        payload.append(b2)
        payload.extend(from2)
        payload.append(c1)
        payload.append(c2)
        payload.extend(int2bytes16(error))
        payload.extend(int2bytes16(pktcount))
        if first:
            xtag = tag | 0x8000
        else:
            xtag = tag
        payload.extend(int2bytes16(xtag))
        if type_ & 0x1:
            raise ValueError
        if response:
            xtype = type_ | 1
        else:
            xtype = type_
        payload.extend(int2bytes16(xtype))
        payload.extend(int2bytes16(subtype))
        payload.extend(int2bytes32(arg1))
        payload.extend(int2bytes32(arg2))
        payload.extend(extra)

        self.tx_ppp("ff:ff:ff:ff:ff:ff", SMA_PROTOCOL_ID, payload)
        return tag

    def tx_logon(self, password=b'0000', timeout=900):
        if len(password) > 12:
            raise ValueError
        password += b'\x00' * (12 - len(password))
        tag = self.gettag()

        extra = bytearray(b'\xaa\xaa\xbb\xbb\x00\x00\x00\x00')
        extra += bytearray(((c + 0x88) % 0xff) for c in password)
        return self.tx_6560(self.local_addr2, self.BROADCAST2, 0xa0,
                            0x00, 0x01, 0x00, 0x01, tag,
                            0x040c, 0xfffd, 7, timeout, extra)

    def tx_gdy(self):
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x5400, 0x00262200, 0x002622ff)

    def tx_yield(self):
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x5400, 0x00260100, 0x002601ff)

    def tx_set_time(self, ts, tzoffset):
        payload = bytearray()
        payload.extend(int2bytes32(0x00236d00))
        payload.extend(int2bytes32(ts))
        payload.extend(int2bytes32(ts))
        payload.extend(int2bytes32(ts))
        payload.extend(int2bytes16(tzoffset))
        payload.extend(int2bytes16(0))
        payload.extend(int2bytes32(0x007efe30))
        payload.extend(int2bytes32(0x00000001))
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x20a, 0xf000, 0x00236d00, 0x00236d00, payload)

    def tx_historic(self, fromtime, totime):
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xe0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x7000, fromtime, totime)

    def tx_historic_daily(self, fromtime, totime):
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xe0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x7020, fromtime, totime)

    def wait(self, class_, cond=None):
        self.waitvar = None
        setattr(self, '__waitcond_rx_' + class_, cond)
        while self.waitvar is None:
            self.rx()
        delattr(self, '__waitcond_rx_' + class_)
        return self.waitvar

    def wait_outer(self, wtype, wpl=bytearray()):
        def wfn(from_, to_, type_, payload):
            if ((type_ == wtype) and payload.startswith(wpl)):
                return payload
        return self.wait('outer', wfn)

    def wait_6560(self, wtag):
        def tagfn(from2, to2, a2, b1, b2, c1, c2, tag,
                  type_, subtype, arg1, arg2, extra,
                  response, error, pktcount, first):
            if response and (tag == wtag):
                if (pktcount != 0) or not first:
                    raise Error("Unexpected multipacket reply")
                if error:
                    raise Error("SMA device returned error 0x%x\n", error)
                return (from2, type_, subtype, arg1, arg2, extra)
        return self.wait('6560', tagfn)

    def wait_6560_multi(self, wtag):
        tmplist = []

        def multiwait_6560(from2, to2, a2, b1, b2, c1, c2, tag,
                           type_, subtype, arg1, arg2, extra,
                           response, error, pktcount, first):
            if not response or (tag != wtag):
                return None

            if not tmplist:
                if not first:
                    raise Error("Didn't see first packet of reply")

                tmplist.append(pktcount + 1)  # Expected number of packets
            else:
                expected = tmplist[0]
                sofar = len(tmplist) - 1
                if pktcount != (expected - sofar - 1):
                    raise Error("Got packet index %d instead of %d"
                                % (pktcount, expected - sofar))

            tmplist.append((from2, type_, subtype, arg1, arg2, extra))
            if pktcount == 0:
                return True

        self.wait('6560', multiwait_6560)
        assert(len(tmplist) == (tmplist[0] + 1))
        return tmplist[1:]

    # Operations

    def hello(self):
        hellopkt = self.wait_outer(OTYPE_HELLO)
        if hellopkt != bytearray(b'\x00\x04\x70\x00\x01\x00\x00\x00' +
                                 b'\x00\x01\x00\x00\x00'):
            raise Error("Unexpected HELLO %r" % hellopkt)
        self.tx_outer("00:00:00:00:00:00", self.remote_addr,
                      OTYPE_HELLO, hellopkt)
        self.wait_outer(0x05)

    def getvar(self, varid):
        self.tx_outer("00:00:00:00:00:00", self.remote_addr, OTYPE_GETVAR,
                      int2bytes16(varid))
        val = self.wait_outer(OTYPE_VARVAL, int2bytes16(varid))
        return val[2:]

    def getsignal(self):
        val = self.getvar(OVAR_SIGNAL)
        return val[2] / 0xff

    def do_6560(self, a2, b1, b2, c1, c2, tag, type_, subtype, arg1, arg2,
                payload=bytearray()):
        self.tx_6560(self.local_addr2, self.BROADCAST2, a2, b1, b2, c1, c2,
                     tag, type_, subtype, arg1, arg2, payload)
        return self.wait_6560(tag)

    def logon(self, password=b'0000', timeout=900):
        tag = self.tx_logon(password, timeout)
        self.wait_6560(tag)

    def total_yield(self):
        tag = self.tx_yield()
        from2, type_, subtype, arg1, arg2, extra = self.wait_6560(tag)
        timestamp = bytes2int(extra[4:8])
        total = bytes2int(extra[8:12])
        return timestamp, total

    def daily_yield(self):
        tag = self.tx_gdy()
        from2, type_, subtype, arg1, arg2, extra = self.wait_6560(tag)
        timestamp = bytes2int(extra[4:8])
        daily = bytes2int(extra[8:12])
        return timestamp, daily

    def historic(self, fromtime, totime):
        tag = self.tx_historic(fromtime, totime)
        data = self.wait_6560_multi(tag)
        points = []
        for from2, type_, subtype, arg1, arg2, extra in data:
            while extra:
                timestamp = bytes2int(extra[0:4])
                val = bytes2int(extra[4:8])
                extra = extra[12:]
                if val != 0xffffffff:
                    points.append((timestamp, val))
        return points

    def historic_daily(self, fromtime, totime):
        tag = self.tx_historic_daily(fromtime, totime)
        data = self.wait_6560_multi(tag)
        points = []
        for from2, type_, subtype, arg1, arg2, extra in data:
            while extra:
                timestamp = bytes2int(extra[0:4])
                val = bytes2int(extra[4:8])
                extra = extra[12:]
                if val != 0xffffffff:
                    points.append((timestamp, val))
        return points

    def set_time(self, newtime, tzoffset):
        self.tx_set_time(newtime, tzoffset)


def ptime(str):
    return int(time.mktime(time.strptime(str, "%Y-%m-%d")))


def cmd_total(sma, args):
    if len(args) != 1:
        print("Command usage: total")
        sys.exit(1)

    timestamp, total = sma.total_yield()
    print("%s: Total generation to-date %d Wh"
          % (format_time(timestamp), total))


def cmd_daily(sma, args):
    if len(args) != 1:
        print("Command usage: daily")
        sys.exit(1)

    timestamp, daily = sma.daily_yield()
    print("%s: Daily generation %d Wh"
          % (format_time(timestamp), daily))


def cmd_historic(sma, args):
    fromtime = ptime("2013-01-01")
    totime = int(time.time())  # Now
    if len(args) > 1:
        fromtime = ptime(args[1])
    if len(args) > 2:
        totime = ptime(args[2])
    if len(args) > 3:
        print("Command usage: historic [start-date [end-date]]")
        sys.exit(1)

    hlist = sma.historic(fromtime, totime)
    for timestamp, val in hlist:
        print("[%d] %s: Total generation %d Wh"
              % (timestamp, format_time(timestamp), val))


def cmd_historic_daily(sma, args):
    fromtime = ptime("2013-01-01")
    totime = int(time.time())  # Now
    if len(args) > 1:
        fromtime = ptime(args[1])
    if len(args) > 2:
        totime = ptime(args[2])
    if len(args) > 3:
        print("Command usage: historic [start-date [end-date]]")
        sys.exit(1)

    hlist = sma.historic_daily(fromtime, totime)
    for timestamp, val in hlist:
        print("[%d] %s: Total generation %d Wh"
              % (timestamp, format_time(timestamp), val))


if __name__ == '__main__':
    bdaddr = None

    optlist, args = getopt.getopt(sys.argv[1:], 'b:')

    if not args:
        print("Usage: %s -b <bdaddr> command args.." % sys.argv[0])
        sys.exit(1)

    cmd = 'cmd_' + args[0]
    if cmd not in globals():
        print("Invalid command '%s'" % args[0])
        sys.exit(1)
    cmdfn = globals()[cmd]

    for opt, optarg in optlist:
        if opt == '-b':
            bdaddr = optarg

    if bdaddr is None:
        print("No bluetooth address specified")
        sys.exit(1)

    sma = Connection(bdaddr)

    sma.hello()
    sma.logon(timeout=60)
    cmdfn(sma, args)
