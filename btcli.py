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
        dump_packet(pkt, sys.stdout, "RX ")


class Quit(Exception):
    def __init__(self):
        super(Quit, self).__init__("Quit at user request")


cli_cmds = {}


def cmd(f):
    cli_cmds[f.__name__] = f
    return f


def dump_and_write(conn, pkt):
    dump_packet(pkt, sys.stdout, "TX ")
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
