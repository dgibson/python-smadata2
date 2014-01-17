#! /usr/bin/env python

from __future__ import print_function
import sys
import os
import signal
import readline
from btsma import *

def rx_thread(conn):
    while True:
        pkt = conn.read_packet()
        print()
        dump_packet(pkt, sys.stdout, "RX  ")


class Quit(Exception):
    def __init__(self):
        super(Quit, self).__init__("Quit at user request")


cli_cmds = {}


def cmd(f):
    cli_cmds[f.__name__] = f
    return f


def dump_and_write(conn, pkt):
    dump_packet(pkt, sys.stdout, "TX  ")
    conn.write_packet(pkt)


@cmd
def quit(conn):
    raise Quit()


@cmd
def raw(conn, *args):
    pkt = bytearray([int(x,16) for x in args])
    conn.raw_write_packet(pkt)


def parse_addr(addr, conn):
    if addr.lower() == "zero":
        return "00:00:00:00:00:00"
    elif addr.lower() == "local":
        return conn.local_addr
    elif addr.lower() == "remote":
        return conn.remote_addr
    elif addr.lower() == "bcast":
        return "ff:ff:ff:ff:ff:ff"
    else:
        return addr

@cmd
def send(conn, from_, to, *args):
    from_ = parse_addr(from_, conn)
    to = parse_addr(to, conn)
    payload = bytearray([int(x, 16) for x in args])
    pkt = make_packet(from_, to, payload)
    dump_and_write(conn, pkt)

@cmd
def scrc(conn, *args):
    subpayload = bytearray([int(x, 16) for x in args])
    pkt = make_crc_packet(conn, subpayload)
    dump_and_write(conn, pkt)

@cmd
def cmd1(conn):
    spl = bytearray('\xFF\x03\x60\x65\x09\xA0\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x01\x80\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    pkt = make_crc_packet(conn, spl)
    dump_and_write(conn, pkt)

@cmd
def cmdpow(conn):
    spl = bytearray('\xFF\x03\x60\x65\x09\xa1\xff\xff\xff\xff\xff\xff\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x00\x80\x00\x02\x00\x51\x00\x00\x20\x00\xff\xff\x50\x00\x0e')
    pkt = make_crc_packet(conn, spl)
    dump_and_write(conn, pkt)

def scrc1(conn, n):
    ss = [bytearray('\xFF\x03\x60\x65\x09\xA0\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x78\x00\x3f\x10\xfb\x39\x00\x00\x00\x00\x00\x00\x01\x80\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
          bytearray('\xFF\x03\60\x65\x08\xA0\xFF\xFF\xFF\xFF\xFF\xFF\x00\x03\x78\x00\x3f\x10\xfb\x39\x00\x03\x00\x00\x00\x00\x00\x80\x0E\x01\xFD\xFF\xFF\xFF\xFF\xFF'),
          bytearray('\xFF\x03\x60\x65\x0E\xA0\xFF\xFF\xFF\xFF\xFF\xFF\x00\x01\x78\x00\x3f\x10\xfb\x39\x00\x01\x00\x00\x00\x00\x02\x80\x0C\x04\xFD\xFF\x07\x00\x00\x00\x84\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x88\x88\x88\x88\x88\x88\x88\x88\x88\x88\x88\x88')]
    subpayload = ss[int(n)]
    pkt = make_crc_packet(conn, subpayload)
    dump_and_write(conn, pkt)
    

@cmd
def hello(conn, *args):
    pkt = make_hello_packet(conn)
    dump_and_write(conn, pkt)


@cmd
def signalreq(conn, *args):
    pkt = make_signalreq_packet(conn)
    dump_and_write(conn, pkt)


def cli_thread(conn):
    while True:
        sys.stdout.write("BTSMA %s >> " % conn.remote_addr)
        try:
            line = raw_input().split()
        except EOFError:
            return
        if not line:
            continue

        cmd = line[0].lower()
        if cmd in cli_cmds:
            try:
                cli_cmds[cmd](conn, *line[1:])
            except Quit:
                return
            except Exception as e:
                print("ERROR! %s" % e)
        else:
            print("Bad command", file=sys.stderr)
       
        
        
def main():
    if len(sys.argv) != 2:
        print("Usage: btcli.py <BD addr>", file=sys.stderr)
        sys.exit(1)

    conn = BTSMAConnection(sys.argv[1])
    print("Connected %s -> %s" % (conn.local_addr, conn.remote_addr))

    rxpid = os.fork()
    if rxpid == 0:
        rx_thread(conn)

    try:
        cli_thread(conn)
    finally:
        os.kill(rxpid, signal.SIGTERM)

main()
