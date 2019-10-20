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
from smadata2.inverter.sma_devices import *
# AF for Windows
from bluetooth import *

# development tools only, debugging, timing
import web_pdb  # debugger  use: web_pdb.set_trace()    #set a breakpoint
from functools import wraps

from . import base
from .base import Error
from smadata2.datetimeutil import format_time
from smadata2.datetimeutil import format_time2

__all__ = ['Connection',
           'OTYPE_PPP', 'OTYPE_PPP2', 'OTYPE_HELLO', 'OTYPE_GETVAR',
           'OTYPE_VARVAL', 'OTYPE_ERROR',
           'OVAR_SIGNAL',
           'int2bytes16', 'int2bytes32', 'bytes2int']

OUTER_HLEN = 18

# commands in SMA Level 1 packet format - see document
OTYPE_PPP = 0x01
OTYPE_HELLO = 0x02
OTYPE_GETVAR = 0x03
OTYPE_VARVAL = 0x04
OTYPE_ERROR = 0x07
OTYPE_PPP2 = 0x08

OVAR_SIGNAL = 0x05

INNER_HLEN = 36

SMA_PROTOCOL_ID = 0x6560


def timing(f):
    """Decorator function to write duration of f to the console

    :param f: function to be timed
    :return: duration in s
    """

    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print('func:{!r} args:[{!r}, {!r}] took: {:2.4f} sec'.format(f.__name__, args, kw, te - ts))
        return result

    return wrap


def waiter(fn):
    """ Decorator function on the Rx functions, checks wait conditions on self, used with connection.wait() to wait for packets
    
    The trick is that the Rx functions have been decorated with @waiter, which augments the bare Rx function 
    with code to check if the special wait variables are set, and if so check the results of the Rx to 
    see if it's something we're currently waiting for, and if so put it somewhere that wait will be able to find it.
    If the wait condition matches then save the args on the waitvar attribute.
    attributes are created in the connection.wait() function below """

    def waitfn(self, *args):
        fn(self, *args)  # call the provided function, with any arguments from the decorated function
        if hasattr(self, '__waitcond_' + fn.__name__):
            wc = getattr(self, '__waitcond_' + fn.__name__)
            if wc is None:
                self.waitvar = args
            else:
                self.waitvar = wc(*args)

    return waitfn  # return the return value of the decorated function, like rx_raw, tx_raw


def _check_header(hdr):
    """ Checks for known errors in the Level 1 Outer packet header (18 bytes), raises errors.
    
    Packet length between 18 and 91 bytes     
    :param hdr:  bytearray  part of the pkt
    :return: byte: packet length
    """

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
    """Transform a bluetooth address in bytearray of length 6 to a string representation, like '00:80:25:2C:11:B2'
    
    This revereses the order of the bytes and formats as a string with the : delimiter
    
    :param addr: part of the pkt bytearray 
    :return: string like like '00:80:25:2C:11:B2'
    """

    if len(addr) != 6:
        raise ValueError("Bad length for bluetooth address")
    assert len(addr) == 6
    return "%02X:%02X:%02X:%02X:%02X:%02X" % tuple(reversed(addr))


def bytes2ba(s):
    """Transform a Bluetooth address in string representation to a bytearray of length 6

        This reverses the order of the string and convert to bytearray

        :param s string like like '00:80:25:2C:11:B2'  
        :return: bytearray length 6, addr
        """
    addr = [int(x, 16) for x in s.split(':')]
    addr.reverse()
    if len(addr) != 6:
        raise ValueError("Bad length for bluetooth address")
    return bytearray(addr)


def int2bytes16(v):
    return bytearray([v & 0xff, v >> 8])


def int2bytes32(v):
    return bytearray([v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff, v >> 24])


def bytes2int(b) -> int:
    """Convert arbitrary length bytes or bytearray in little-endian to integer

    :param b: bytes, memoryview, or bytearray; converted to bytearray which is mutable
    :return: integer
    """
    v = 0
    ba = bytearray(b)
    while ba:
        v = v << 8
        v += ba.pop()
    return v


# todo can be memoryview()? not list
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
assert (len(crc16_table) == 256)


def crc16(iv, data):
    crc = iv
    for b in data:
        crc = (crc >> 8) ^ crc16_table[(crc ^ b) & 0xff]
    return crc ^ 0xffff


class Connection(base.InverterConnection):
    """Connection via IP socket connection to inverter, with all functions needed to receive data

    Args:
        addr (str): Bluetooth address in hex, like '00:80:25:2C:11:B2'
        
    Attributes:
    """
    MAXBUFFER = 512
    BROADCAST = "ff:ff:ff:ff:ff:ff"
    BROADCAST2 = bytearray(b'\xff\xff\xff\xff\xff\xff')

    def __init__(self, addr):
        """ initialise the python IP socket as a Bluetooth socket"""
        # Original Linux connection
        # self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
        #                           socket.BTPROTO_RFCOMM)
        # self.sock.connect((addr, 1))

        # Windows connection
        self.sock = BluetoothSocket(RFCOMM)
        self.sock.connect((addr, 1))

        self.remote_addr = addr
        self.local_addr = self.sock.getsockname()[0]  # from pi, 'B8:27:EB:F4:80:EB'

        # todo what is this hardcoded for?  not from the local BT or MAC address
        self.local_addr2 = bytearray(b'\x78\x00\x3f\x10\xfb\x39')

        self.rxbuf = bytearray()
        self.pppbuf = dict()

        self.tagcounter = 0

    def gettag(self):
        """Generates an incrementing tag used in PPP packets to keep them unique for this session"""
        self.tagcounter += 1
        return self.tagcounter

    #
    # RX side
    # Function call order
    # wait()  > rx()  > rx-raw()  > rx_outer()  > rx_ppp_raw()  > rx_ppp()  >rx_6560  > rxfilter_6560
    #

    def rx(self):
        """Receive raw data from socket, pass up the chain to rx_raw, etc
        
        Called by the wait() function
        Receive raw data from socket, to the limit of available space in rxbuf
        :return: 
        """
        space = self.MAXBUFFER - len(self.rxbuf)
        self.rxbuf += self.sock.recv(space)

        while len(self.rxbuf) >= OUTER_HLEN:
            # get the pktlen, while checking this is the expected packet
            pktlen = _check_header(self.rxbuf[:OUTER_HLEN])

            # the receive buffer should be at least as long as packet
            if len(self.rxbuf) < pktlen:
                return

            # get the packet, and clear the buffer, pkt is bytearray, e.g. 31 bytes for hello
            pkt = self.rxbuf[:pktlen]
            del self.rxbuf[:pktlen]

            self.rx_raw(pkt)

    @waiter
    def rx_raw(self, pkt):
        # SMA Level 1 Packet header 0 to 18 bytes
        from_ = ba2bytes(pkt[4:10])  # Level 1 "From" bluetooth address
        to_ = ba2bytes(pkt[10:16])  # Level 1 "To" bluetooth address
        type_ = bytes2int(pkt[16:18])
        payload = pkt[OUTER_HLEN:]

        self.rx_outer(from_, to_, type_, payload)

    def rxfilter_outer(self, to_):
        """Validate that we are intended recipient of packet (return True) based on Level 1 To address

        :param to_: bytearray of To BT address
        :return: True
        """
        return ((to_ == self.local_addr) or
                (to_ == self.BROADCAST) or
                (to_ == "00:00:00:00:00:00"))

    @waiter
    def rx_outer(self, from_, to_, type_, payload):
        if not self.rxfilter_outer(to_):
            return  # discard packet

        if (type_ == OTYPE_PPP) or (type_ == OTYPE_PPP2):
            self.rx_ppp_raw(from_, payload)

    def rx_ppp_raw(self, from_, payload):
        """Validate the PPP or PPP2 packet, raise errors, strip protocol from header

        :param from_: Level 1 "From" bluetooth address
        :param payload: raw PPP or PPP2 packet
        :return: payload as frame[4:-2]
        """
        if from_ not in self.pppbuf:
            self.pppbuf[from_] = bytearray()
        pppbuf = self.pppbuf[from_]

        pppbuf.extend(payload)
        term = pppbuf.find(b'\x7e', 1)
        if term < 0:
            return

        raw = pppbuf[:term + 1]
        del pppbuf[:term + 1]

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
        """Using SMA Level 2 packet, slice into meaningful SMA data elements
        todo make this memoroyview now
        :param from_: Level 1 "From" bluetooth address (not used beyond here)
        :param protocol: expects 0x6560
        :param payload: validated PPP packet in SMA protocol
        """
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
        """Validate that we are intended recipient of packet (return True) based on Level 2 To address
        """
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
    # functions call in this order: tx_historic > tx_6560 > tx_ppp > tx_outer > tx_raw
    #
    def tx_raw(self, pkt):
        """Transmits a raw packet via Bluetooth socket interface
        
        :param pkt: bytearray PPP packet
        :return: 
        """
        if _check_header(pkt) != len(pkt):
            raise ValueError("Bad packet")
        self.sock.send(bytes(pkt))

    def tx_outer(self, from_, to_, type_, payload):
        """Builds a SMA Level 1 packet from supplied Level 2, calls tx_raw to transmit
        
        :param from_: str source Bluetooth address in string representation 
        :param to_: str destination Bluetooth address in string representation 
        :param type_: int the command to send, e.g. OTYPE_PPP = 0x01 L2 Packet start
        :param payload: bytearray Data or payload in Level 1 packet
        :return: 
        """
        pktlen = len(payload) + OUTER_HLEN  # SMA Level 2 + SMA Level 1
        pkt = bytearray([0x7e, pktlen, 0x00, pktlen ^ 0x7e])  # start, length, 0x00, check byte
        pkt += bytes2ba(from_)
        pkt += bytes2ba(to_)
        pkt += int2bytes16(type_)
        pkt += payload
        assert _check_header(pkt) == pktlen

        self.tx_raw(pkt)

    # PPP frame is built
    # (Point-to-point protocol in data link layer 2)
    # called from tx_6560 and builds the fr
    def tx_ppp(self, to_, protocol, payload):
        """Builds a SMA Level 2 packet from payload, calls tx_outer to wrap in Level 1 packet
        
        Builds a SMA Level 2 packet from payload
        Adds CRC check 2 bytes
        Adds header and footer
        Escapes any reserved characters that may be in the payload
        Calls tx_outer to wrap in Level 1 packet
        
        :param to_: str Bluetooth address in string representation 
        :param protocol: SMA_PROTOCOL_ID = 0x6560
        :param payload: 
        :return: 
        """
        # Build the Level 2 frame: Header 4 bytes; payload;
        frame = bytearray(b'\xff\x03')
        frame += int2bytes16(protocol)
        frame += payload
        frame += int2bytes16(crc16(0xffff, frame))

        rawpayload = bytearray()
        rawpayload.append(0x7e)  # Head byte
        for b in frame:
            # Escape \x7e (FLAG), 0x7d (ESCAPE), 0x11 (XON) and 0x13 (XOFF)
            if b in [0x7e, 0x7d, 0x11, 0x13]:
                rawpayload.append(0x7d)
                rawpayload.append(b ^ 0x20)
            else:
                rawpayload.append(b)
        rawpayload.append(0x7e)  # Foot byte

        self.tx_outer(self.local_addr, to_, OTYPE_PPP, rawpayload)

    def tx_6560(self, from2, to2, a2, b1, b2, c1, c2, tag,
                type_, subtype, arg1, arg2, extra=bytearray(),
                response=False, error=0, pktcount=0, first=True):
        """Builds a PPP frame for Transmission and calls tx_ppp to wrap for transmission
        
        All PPP frames observed are PPP protocol number 0x6560, which appears to
        be an SMA allocated ID for their control protocol.
        
        Parameters - too many to list
        :param from2: 
        :param to2: 
        :param a2: 
        :param b1: 
        :param b2: 
        :param c1: 
        :param c2: 
        :param tag: 
        :param type_:   byte: Command group 3; always 0x02
        :param subtype: 2 byte:  Commmand  0x0070 Request 5 min data.
        :param arg1: int fromtime
        :param arg2: int totime
        :param extra: 
        :param response: 
        :param error: 
        :param pktcount: 
        :param first: 
        :return: 
 
        :return: tag: integer unique to each PPP packet.
        """

        # Build the Level 2 frame:
        # From byte 6 Packet length, to
        # to byte
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
        # first packet 0x80, subsequent are 0x00
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

    # AF 0000 is hardcoded default user password for SMA inverter, as bytes
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
        """ EnergyProduction:
        like SBFSpot arg2 same, arg 1 different?
#         // SPOT_ETODAY, SPOT_ETOTAL
        :return: 
        """
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x5400, 0x00262200, 0x002622ff)

    def tx_yield(self):
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x5400, 0x00260100, 0x002601ff)

    # data_type = sma_data_unit.get(uom, ['Unknown', '?', '?', 1])[0]

    def tx_level2_request(self, type, subtype, arg1, arg2, extra):
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            type, subtype, arg1, arg2)

    def tx_spotacvoltage(self):
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x5100, 0x00464800,
                            0x004655FF)  # SpotACVoltage SPOT_UAC1, SPOT_UAC2, SPOT_UAC3, SPOT_IAC1, SPOT_IAC2, SPOT_IAC3
        # 0x200, 0x5100, 0x00464800, 0x004657FF)     #SpotACVoltage above and SpotGridFrequency SPOT_FREQ, can link closely related ones

    #                            0x200, 0x5100, 0x00464700, 0x004657FF)     #SpotACVoltage above and SpotGridFrequency SPOT_FREQ, can link closely related ones
    #                            0x200, 0x5380, 0x00251E00, 0x00251EFF)      #SpotDCPower SPOT_PDC1, SPOT_PDC2 2x28 bytes
    #                            0x200, 0x5380, 0x00451F00, 0x004521FF)      #SpotDCVoltage SPOT_UDC1, SPOT_UDC2, SPOT_IDC1, SPOT_IDC2 4x28 bytes

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
        """Builds a SMA request command 0x7000 for 5 min data and calls tx_6560 to wrap for transmission
        
        called by historic function to get historic fast sample data
        Uses
            Command Group 3 0x02 Request
            Commmand        0x7000 Request 5 min data.
        
        :param fromtime: 
        :param totime: 
        :return: tag: int unique packet sequence id
        """
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xe0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x7000, fromtime, totime)

    def tx_historic_daily(self, fromtime, totime):
        """Builds a SMA request command 0x7000 for daily data and calls tx_6560 to wrap for transmission
        
        called by historic function to get historic daily data
        Uses
            Command Group 3 0x02 Request
            Commmand        0x7020 Request Daily data.
        :param fromtime: 
        :param totime: 
        :return: 
        """
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xe0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            0x200, 0x7020, fromtime, totime)

    # The tx_*() function sends some request to the inverter, then we wait for a response.
    # The wait_*() functions are wrappers around wait(), which is the magic bit. wait() takes parameters saying what
    #  type of packet we're looking for at what protocol layer. It pokes those into some special variables
    #  then just calls rx() until another special variable is set.

    #@timing
    def wait(self, class_, cond=None):
        """ wait() calls rx() repeatedly looking for a packet that matches the waitcond
        Sets attribute on smadata2.inverter.smabluetooth.Connection like __waitcond_rx_outer
        and then deletes the attribute once something is received.
        
        :param class_: 
        :param cond: 
        :return: 
        """
        self.waitvar = None
        setattr(self, '__waitcond_rx_' + class_, cond)
        while self.waitvar is None:
            self.rx()
        delattr(self, '__waitcond_rx_' + class_)
        return self.waitvar

    def wait_outer(self, wtype, wpl=bytearray()):
        """Calls the above wait, with class="outer", cond = the wfn function Connection.wait_outer.<locals>.wfn
        
        :param wtype: Outer message types, defined above, like OTYPE_HELLO
        :param wpl: 
        :return: the wait function defined above, 
        """

        def wfn(from_, to_, type_, payload):
            if ((type_ == wtype) and payload.startswith(wpl)):
                return payload  # payload  a PPP packet

        return self.wait('outer', wfn)

    def wait_6560(self, wtag):
        """Called from all Level 2 requests to get SMA protocol data

AF: changed to memoryview(extra)) from extra. Appears to reduce time from  0.1010 sec to 0.0740s
        :param wtag: tag function
        :return: list of bytearray types (from2, type_, subtype, arg1, arg2, extra)
        """

        def tagfn(from2, to2, a2, b1, b2, c1, c2, tag,
                  type_, subtype, arg1, arg2, extra,
                  response, error, pktcount, first):
            if response and (tag == wtag):
                if (pktcount != 0) or not first:
                    raise Error("Unexpected multipacket reply")
                if error:
                    raise Error("SMA device returned error 0x%x\n", error)
                return (from2, type_, subtype, arg1, arg2, memoryview(extra))

        return self.wait('6560', tagfn)

    #@timing
    def wait_6560_multi(self, wtag):
        """Calls the above wait, with class="6560", cond = the multiwait_6560 function
        
        Assembles multiple packets into
        Called from sma_request to get any data element
        from sma.historic to get multiple 5 min samples
        :param wtag: 
        :return: list of bytearray types (from2, type_, subtype, arg1, arg2, extra)
        """
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
        assert (len(tmplist) == (tmplist[0] + 1))
        return tmplist[1:]

    # Operations

    # AF this hello packet is not same for my router.
    def hello(self):
        hellopkt = self.wait_outer(OTYPE_HELLO)
        # if hellopkt != bytearray(b'\x00\x04\x70\x00\x01\x00\x00\x00' +
        #                         b'\x00\x01\x00\x00\x00'):
        netID = hellopkt[4]     #depends on inverter

        if hellopkt[0:4] != bytearray(b'\x00\x04\x70\x00'):
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

    def tx_level2_request(self, type, subtype, arg1, arg2, extra):
        """Request data set from inverter

        Sends a data request in the form of a type, subtype and from & to ranges
        Seems to represent a range of registers in the SMA device memory.

        :param type:  SMA request type mostly 0x0200
        :param subtype:SMA request subtype  often 0x5100
        :param arg1: pointer to range: from
        :param arg2: pointer to range: to
        :param extra: normally 0
        :return:
        """
        return self.tx_6560(self.local_addr2, self.BROADCAST2,
                            0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
                            type, subtype, arg1, arg2)

    #@timing
    def sma_request(self, request_name):
        """Generic request from device and format response in 28-byte units
        todo split this function into parts for getting the data, and formatting repsonse/writing to db
        todo identify null values and exclude them
        todo 3-phase or 1-phase in settings, then query/report accordingly.
        :param request_name: string from  sma_request_type in sma_devices.py")
        :return: list of points
        """
        # web_pdb.set_trace()    #set a breakpoint

        # tag = self.tx_level2_request(0x200, 0x5100, 0x00464800, 0x004655FF, 0)
        # print(request_name)
        sma_rq = sma_request_type.get(request_name)  # test for not found
        if not sma_rq:
            raise Error("Connection.sma_request: Requested SMA data not recognised: ", request_name, " Check sma_request_type in sma_devices.py")
        response_data_type = sma_rq[5]
        tag = self.tx_level2_request(sma_rq[0], sma_rq[1], sma_rq[2], sma_rq[3], sma_rq[4])
        # like sma_rq = (512, 21504, 2490624, 2499327, 0)

        data = self.wait_6560_multi(tag)
        print("response_data_type is: ", response_data_type)
        # web_pdb.set_trace()    #set a breakpoint
        return self.process_sma_record(data, response_data_type)
        # process = 'process_' + response_data_type.lower()
        # print("process is: ", process)
        # #temp try:
        # function = getattr(self, process)
        # return function(data)
        # except Quit:
        #     return
        # except Exception as e:
        #     print("Connection.sma_request: ERROR! %s" % e, process)

    def process_sma_record(self, data, record_length):
        points = []
        for from2, type_, subtype, arg1, arg2, extra in data:
            print("%sPPP frame; protocol 0x%04x [%d bytes]"
                  % (1, 0x6560, len(extra)))
            print(self.hexdump(extra, 'RX<', record_length/2))
            # todo decode these number groups.
            # todo interpret the status codes
            # todo deal with default nightime values, when inverter is inactive.

            while extra:
                index = bytes2int(extra[0:1])  # index of the item (phase, object, string) part of data type
                element = bytes2int(extra[1:3])  # 2 byte units of measure, data type 0x821E, same as the FROM arg1
                record_type = bytes2int(extra[3:4])  # 1 byte SMA data type, same as element_type from the dict lookup
                #uom seems to increase 1E 82, 1F 82, 20 82, etc  40by cycle
                element_name, element_type, element_desc = sma_data_element.get(element)

                timestamp = bytes2int(extra[4:8])
                unknown = bytes2int(extra[24:28])  # padding, unused
                # element_type 0x10 =text, 0x08 = status, 0x00, 0x40 = Dword 64 bit data
                if ((element_type == 0x00) or (element_type == 0x40)):
                    # TypeError: 'NoneType' object is not iterable, here due to missing element 8520
                    data_type, units, _, divisor = sma_data_unit.get(element)
                    val1 = bytes2int(extra[8:12])
                    print('{} {:25} {} {:x} {:x} {}'.format(element, element_name, format_time2(timestamp), val1, unknown, element_desc))
                    print("{0}: {1:.3f} {2}".format(format_time2(timestamp), val1 / divisor, units))
                elif element_type == 0x08:              # status
                    val1 = bytes2int(extra[8:12])
                    print('{:25} {} {:x} {:x} {}'.format(element_name, format_time2(timestamp), val1, unknown, element_desc))
                elif element_type == 0x10:               # string
                    val1 = extra[8:22].decode(encoding="utf-8", errors="ignore")
                    print('{:25} {} {} {:x} {}'.format(element_name, format_time2(timestamp), val1, unknown, element_desc))
                else:
                    val1 = 0        # error to raise - element not found

                # note val = 0x028F5C28, 4294967295 after hours, 11pm means NULL or?
                extra = extra[record_length:]
                #to do - 2 bytes, not 4? check for element not found?
                if element != 0xffffffff:
                    #points.append((index, units, timestamp, val1, val2, val3, val4, unknown, data_type, divisor))
                    #todo, apply divisor, send units?
                    #print({element_name},  {format_time(timestamp)}, {val1:x}, {unknown:x})
                    points.append((element_name,  timestamp, val1, unknown))
        return points

    def hexdump(self, data, prefix, width):
        '''Formatted hex display of the payload

        Format such that one record displays across 2 rows
        Width was 16, change to data type width, e.g. 20, 28
        :param data: bytearray to be displayed
        :param prefix:
        :param width: record length, determines layout
        :return: formatted string, to be printed
        '''
        try:
            s = ''
            for i, b in enumerate(data):
                if (i % width) == 0:
                    s += '%s%04x: ' % (prefix, i)
                s += '%02X' % b
                if (i % width) == (width-1):
                    s += '\n'
                elif (i % width) == (width/2 -1):
                    s += '-'
                else:
                    s += ' '
            if s and (s[-1] == '\n'):
                s = s[:-1]
            return s
        except Exception as e:
            print("Connection.hexdump: ERROR! %s" % e,)
            raise e


    def spotacvoltage(self):
        # web_pdb.set_trace()    #set a breakpoint

        # tag = self.tx_level2_request(0x200, 0x5100, 0x00464800, 0x004655FF, 0)
        # sma_rq = sma_request_type.get('SpotACTotalPower')  # test for not found
        sma_rq = sma_request_type.get('SpotACVoltage')  # test for not found
        tag = self.tx_level2_request(sma_rq[0], sma_rq[1], sma_rq[2], sma_rq[3], sma_rq[4])
        # like sma_rq = (512, 21504, 2490624, 2499327, 0)

        points = []
        # for sma_rq in sma_request_type:
        # print(sma_rq[0], sma_rq[1], sma_rq[2], sma_rq[3])
        # print(bytearray(sma_rq[0]), bytearray(sma_rq[1]), bytearray(sma_rq[2]), bytearray(sma_rq[3]))
        # print(bytearray.fromhex(sma_rq[0]), bytearray.fromhex(sma_rq[2]), bytearray.fromhex(sma_rq[2]), bytearray.fromhex(sma_rq[3]) )
        # print(bytearray.fromhex(sma_rq[0]), bytearray.fromhex(sma_rq[2]), bytearray.fromhex[2], bytearray.fromhex[3] )
        # tag = self.tx_6560(self.local_addr2, self.BROADCAST2,
        # 0xa0, 0x00, 0x00, 0x00, 0x00, self.gettag(),
        # sma_rq[0], sma_rq[1], sma_rq[2], sma_rq[3])
        data = self.wait_6560_multi(tag)

        # data = [(bytearray(b'\x8a\x00\x1cx\xf8~'), 512, 20736, 10, 15, bytearray(
        #     b'\x01HF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01IF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01JF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01PF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01QF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01RF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00'))]
        # points = []
        # self = < smadata2.inverter.smabluetooth.Connection
        # object
        # at
        # 0xb61f6c50 >
        # sma_rq = (512, 21504, 2490624, 2499327, 0)
        # tag = 2

        # web_pdb.set_trace()    #set a breakpoint
        for from2, type_, subtype, arg1, arg2, extra in data:
            while extra:
                # can use 0:4, but 4th byte sometimes set to 0 or 4, but same units. maybe DC/AC?
                index = bytes2int(extra[0:1])  # index of the item (phase, object, string) part of data type
                uom = bytes2int(extra[1:3])  # 2 byte units of measure, data type
                # print("units of measure, data type: {0:x}".format(uom))
                data_type, units, _, divisor  = sma_data_unit.get(uom)
                timestamp = bytes2int(extra[4:8])
                # note val = 0x028F5C28, 4294967295 after hours, 11pm means NULL or?
                val1 = bytes2int(extra[8:12])
                val2 = bytes2int(extra[12:16])
                val3 = bytes2int(extra[16:20])
                val4 = bytes2int(extra[20:24])
                unknown = bytes2int(extra[24:28])  # padding, unused
                extra = extra[28:]
                if uom != 0xffffffff:
                    points.append((index, units, timestamp, val1, val2, val3, val4, unknown, data_type, divisor))
                # points = [(1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot line voltage phase 1', 100)]
                # points = [(1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot line voltage phase 1', 100), (1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot line voltage phase 2', 100)]
                # extra = bytearray(b'\x01PF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01QF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01RF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00')
                # extra = bytearray(b'\x01QF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x01RF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00')
                # points = [(1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1,
                #            'AC spot line voltage phase 1', 100), (
                #           1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1,
                #           'AC spot line voltage phase 2', 100), (
                #           1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1,
                #           'AC spot line voltage phase 3', 100), (
                #           1, 'mA', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1,
                #           'AC spot current phase 1', 1)]
                # extra = bytearray(b'\x01RF\x00\xbc\xa2\x9d]\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00')
                # points = [(1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot line voltage phase 1', 100), (1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot line voltage phase 2', 100), (1, 'V', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot line voltage phase 3', 100), (1, 'mA', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot current phase 1', 1), (1, 'mA', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot current phase 2', 1), (1, 'mA', 1570611900, 4294967295, 4294967295, 4294967295, 4294967295, 1, 'AC spot current phase 3', 1)]
                #
        return points

    def historic(self, fromtime, totime):
        """ Obtain Historic data (5 minute intervals), called from download_inverter which specifies "historic" as the data_fn
        
        Typical values after a couple of iterations through "data"
        extra = bytearray(b'D\x9aL\\\x81w&\x02\x00\x00\x00\x00p\x9bL\\\x81w&\x02\x00\x00\x00\x00\x9c\x9cL\\\x81w&\x02\x00\x00\x00\x00\xc8\x9dL\\\x81w&\x02\x00\x00\x00\x00\xf4\x9eL\\\x81w&\x02\x00\x00\x00\x00 \xa0L\\\x81w&\x02\x00\x00\x00\x00L\xa1L\\\x81w&\x02\x00\x00\x00\x00x\xa2L\\\x81w&\x02\x00\x00\x00\x00\xa4\xa3L\\\x81w&\x02\x00\x00\x00\x00\xd0\xa4L\\\x81w&\x02\x00\x00\x00\x00\xfc\xa5L\\\x81w&\x02\x00\x00\x00\x00(\xa7L\\\x81w&\x02\x00\x00\x00\x00T\xa8L\\\x81w&\x02\x00\x00\x00\x00\x80\xa9L\\\x81w&\x02\x00\x00\x00\x00\xac\xaaL\\\x81w&\x02\x00\x00\x00\x00\xd8\xabL\\\x81w&\x02\x00\x00\x00\x00\x04\xadL\\\x81w&\x02\x00\x00\x00\x000\xaeL\\\x81w&\x02\x00\x00\x00\x00\\\xafL\\\x81w&\x02\x00\x00\x00\x00\x88\xb0L\\\x81w&\x02\x00\x00\x00\x00\xb4\xb1L\\\x81w&\x02\x00\x00\x00\x00\xe0\xb2L\\\x81w&\x02\x00\x00\x00\x00\x0c\xb4L\\\x81w&\x02\x00\x00\x00\x008\xb5L\\\x81w&\x02\x00\x00\x00\x00d\xb6L\\\x81w&\x02\x00\x00\x00\x00\x90\xb7L\\\x81w&\x02\x00\x00\x00\x00\xbc\xb8L\\\x81w&\x02\x00\x00\x00\x00\xe8\xb9L\\\x81w&\x02\x00\x00\x00\x00\x14\xbbL\\\x81w&\x02\x00\x00\x00\x00@\xbcL\\\x81w&\x02\x00\x00\x00\x00l\xbdL\\\x81w&\x02\x00\x00\x00\x00\x98\xbeL\\\x84w&\x02\x00\x00\x00\x00\xc4\xbfL\\\x89w&\x02\x00\x00\x00\x00\xf0\xc0L\\\x91w&\x02\x00\x00\x00\x00\x1c\xc2L\\\x9cw&\x02\x00\x00\x00\x00H\xc3L\\\xa8w&\x02\x00\x00\x00\x00t\xc4L\\\xb4w&\x02\x00\x00\x00\x00\xa0\xc5L\\\xc6w&\x02\x00\x00\x00\x00')
        from2 = bytearray(b'\x8a\x00\x1cx\xf8~')
        fromtime = 1
        points = [(1548523800, 36075393), (1548524100, 36075393)]
        self = <smadata2.inverter.smabluetooth.Connection object at 0xb611c9b0>
        subtype = 28672
        tag = 2
        timestamp = 1548523800
        totime = 1550372370
        type_ = 512
        val = 36075393
        
        :param fromtime: 
        :param totime: 
        :return: 
        """
        #todo - does this need memoryview for data?
        tag = self.tx_historic(fromtime, totime)  # defines the PPP frame
        data = self.wait_6560_multi(tag)
        points = []
        # extra in 12-byte cycle (4-byte timestamp, 4-byte value in Wh, 4-byte padding)
        for from2, type_, subtype, arg1, arg2, extra in data:
            while extra:
                timestamp = bytes2int(extra[0:4])
                val = bytes2int(extra[4:8])
                extra = extra[12:]
                if val != 0xffffffff:
                    points.append((timestamp, val))
        return points

    #
    def historic_daily(self, fromtime, totime):
        """Get Historic data (daily intervals)

        Called from download_inverter in download.py (on schedule), or sma2mon command line.

        :param fromtime:
        :param totime:
        :return: point list of (timestamp, value) pairs
        """
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
    # end of the Connection class


def ptime(str):
    """Convert a string date, like "2013-01-01" into a timestamp 
    
    :param str: date like "2013-01-01" 
    :return: int: timestamp
    """

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
    """ # Command: Historic data (5 minute intervals)
    
    called from download_inverter which specifies "historic" as the data_fn

    
    :param sma: Connection class
    :param args: command line args, including [start-date [end-date]] fromtime, totime
    :return: 
    """
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


# appears unused.  where is this called from?
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


def get_devices():
    nearby_devices = bluetooth.discover_devices(
        duration=8, lookup_names=True, flush_cache=True, lookup_class=False)

    print("found %d devices" % len(nearby_devices))

    for addr, name in nearby_devices:
        try:
            print("  %s - %s" % (addr, name))
        except UnicodeEncodeError:
            print("  %s - %s" % (addr, name.encode('utf-8', 'replace')))


# code to allow running this file from command line?
if __name__ == '__main__':
    bdaddr = None

    optlist, args = getopt.getopt(sys.argv[1:], 'b:')

    if not args:
        get_devices()
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
