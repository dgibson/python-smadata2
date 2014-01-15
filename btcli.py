#! /usr/bin/env python

from __future__ import print_function
import sys
import os
import signal
from btsma import *

def rx_thread(conn):
    while True:
        pkt = conn.read_packet()
        print()
        pkt.dump(sys.stdout, "RX ")


class Quit(Exception):
    def __init__(self):
        super(Quit, self).__init__("Quit at user request")


cli_cmds = {}


def cmd(f):
    cli_cmds[f.__name__] = f
    return f


@cmd
def quit(conn):
    raise Quit()


@cmd
def raw(conn, *args):
    pkt = bytearray([int(x,16) for x in args])
    conn.raw_write_packet(pkt)


@cmd
def send0(conn, *args):
    payload = bytearray([int(x, 16) for x in args])
    pkt = BTSMAPacket("00:00:00:00:00:00", conn.remote_addr, payload)
    pkt.dump(sys.stdout, "TX ")
    conn.write_packet(pkt)


def cli_thread(conn):
    while True:
        sys.stdout.write("BTSMA %s >> " % conn.remote_addr)
        line = raw_input().split()
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
