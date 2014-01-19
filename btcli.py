#! /usr/bin/env python

from __future__ import print_function
from __future__ import division
import sys
import os
import signal
import readline
from btsma import *


class Quit(Exception):
    def __init__(self):
        super(Quit, self).__init__("Quit at user request")


def hexdump(data, prefix):
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
    if s[-1] == '\n':
        s = s[:-1]
    return s


def dump_outer(prefix, from_, to_, type_, payload):
    print("%s%s -> %s TYPE %02X" % (prefix, from_, to_, type_))
    prefix = prefix + "    "
    if type_ == OTYPE_HELLO:
        print("%sHELLO!" % prefix)
    elif type_ == OTYPE_ERROR:
        print("%sERROR in previous packet:" % prefix)
        print(hexdump(payload[4:], prefix + "    "))


def dump_ppp_raw(prefix, payload):
    info = ""
    if payload[0] == 0x7e:
        info += " frame begins"
    if payload[-1] == 0x7e:
        info += " frame ends"
    print("%sPartial PPP data%s" % (prefix, info))


def dump_ppp(prefix, protocol, payload):
    print("%sPPP frame; protocol 0x%04x [%d bytes]" 
          % (prefix, protocol, len(payload)))
    print(hexdump(payload, prefix + "    "))


class BTSMAConnectionCLI(BTSMAConnection):
    def __init__(self, addr):
        super(BTSMAConnectionCLI, self).__init__(addr)
        print("Connected %s -> %s"
              % (self.local_addr, self.remote_addr))
        self.rxpid = None

    def __del__(self):
        if self.rxpid:
            os.kill(self.rxpid, signal.SIGTERM)

    def start_rxthread(self):
        self.rxpid = os.fork()
        if self.rxpid == 0:
            while True:
                self.rx()

    def rx_raw(self, pkt):
        print("\n" + hexdump(pkt, "Rx< "))
        super(BTSMAConnectionCLI, self).rx_raw(pkt)

    def rx_outer(self, from_, to_, type_, payload):
        dump_outer("Rx<     ", from_, to_, type_, payload)
        super(BTSMAConnectionCLI, self).rx_outer(from_, to_,
                                                 type_, payload)

    def rx_ppp_raw(self, from_, payload):
        dump_ppp_raw("Rx<         ", payload)
        super(BTSMAConnectionCLI, self).rx_ppp_raw(from_, payload)

    def rx_ppp(self, from_, protocol, payload):
        dump_ppp("Rx<         ", protocol, payload)
        super(BTSMAConnectionCLI, self).rx_ppp(from_, protocol, payload)

    def rx_varval(self, from_, varid, varval):
        print("Rx<         VARVAL 0x%02x" % varid)
        if varid == OVAR_SIGNAL:
            print("Rx<             Signal level %0.1f%%"
                  % (varval[2] / 255 * 100))
        super(BTSMAConnectionCLI, self).rx_varval(from_, varid, varval)

    def tx_raw(self, pkt):
        super(BTSMAConnectionCLI, self).tx_raw(pkt)
        print("\n" + hexdump(pkt, "Tx> "))

    def tx_outer(self, from_, to_, type_, payload):
        super(BTSMAConnectionCLI, self).tx_outer(from_, to_,
                                                 type_, payload)
        dump_outer("Tx>     ", from_, to_, type_, payload)

    def tx_ppp_raw(self, to_, payload):
        super(BTSMAConnectionCLI, self).tx_ppp_raw(to_, payload)
        dump_ppp_raw("Tx>         ", payload)

    def tx_ppp(self, to_, protocol, payload):
        super(BTSMAConnectionCLI, self).tx_ppp(to_, protocol, payload)
        dump_ppp("Tx>         ", protocol, payload)

    def tx_getvar(self, to_, varid):
        super(BTSMAConnectionCLI, self).tx_getvar(to_, varid)
        print("Tx>         GETVAR 0x%02x" % varid)

    def cli(self):
        while True:
            sys.stdout.write("BTSMA %s >> " % self.remote_addr)
            try:
                line = raw_input().split()
            except EOFError:
                return

            if not line:
                continue

            cmd = 'cmd_' + line[0].lower()
            try:
                getattr(self, cmd)(*line[1:])
            except Quit:
                return
            except Exception as e:
                print("ERROR! %s" % e)

    def cmd_quit(self):
        raise Quit()

    def cmd_raw(self):
        pkt = bytearray([int(x,16) for x in args])
        self.tx_raw(pkt)

    def parse_addr(self, addr):
        if addr.lower() == "zero":
            return "00:00:00:00:00:00"
        elif addr.lower() == "local":
            return self.local_addr
        elif addr.lower() == "remote":
            return self.remote_addr
        elif addr.lower() == "bcast":
            return "ff:ff:ff:ff:ff:ff"
        else:
            return addr

    def cmd_send(self, from_, to_, type_, *args):
        from_ = self.parse_addr(from_)
        to_ = self.parse_addr(to_)
        type_ = int(type_, 16)
        payload = bytearray([int(x, 16) for x in args])
        self.tx_outer(from_, to_, type_, payload)

    def cmd_hello(self):
        self.tx_hello()

    def cmd_getvar(self, varid):
        if varid == 'signal':
            varid = OVAR_SIGNAL
        else:
            varid = int(varid, 16)
        self.tx_getvar(self.remote_addr, varid)

    def cmd_ppp(self, protocol, *args):
        protocol = int(protocol, 0)
        payload = bytearray([int(x, 16) for x in args])
        self.tx_ppp("ff:ff:ff:ff:ff:ff", protocol, payload)

    def cmd_cmd31(self):
        spl = bytearray('\x09\xA0\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x01\x80\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.tx_ppp("ff:ff:ff:ff:ff:ff", 0x6560, spl)

    def cmd_cmd31a(self):
        spl = bytearray('\x09\xA0\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x00\x80\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.tx_ppp("ff:ff:ff:ff:ff:ff", 0x6560, spl)


    def cmd_cmd57(self):
        spl = bytearray('\x09\xA0\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x00\x80\x00\x02\x80\x51\x00\x48\x21\x00\xFF\x48\x21\x00')
        self.tx_ppp("ff:ff:ff:ff:ff:ff", 0x6560, spl)

    def cmd_cmd60(self):
        spl = bytearray('\x09\xa1\xff\xff\xff\xff\xff\xff\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x00\x80\x00\x02\x00\x51\x00\x00\x20\x00\xff\xff\x50\x00\x0e')
        self.tx_ppp("ff:ff:ff:ff:ff:ff", 0x6560, spl)

    def cmd_cmd82(self):
        spl = bytearray('\x09\xE0\x4e\x00\xe1\x7e\xf6\x7e\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x01\x80\x00\x02\x00\x70\x00\x27\x0e\x50\x80\x5a\xc3\x52')
        self.tx_ppp("ff:ff:ff:ff:ff:ff", 0x6560, spl)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: btcli.py <BD addr>", file=sys.stderr)
        sys.exit(1)

    cli = BTSMAConnectionCLI(sys.argv[1])

    cli.start_rxthread()
    cli.cli()
