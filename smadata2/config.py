#! /usr/bin/env python

from __future__ import print_function

import os
import time
import calendar
import dateutil.parser
import ConfigParser

import smadata2.protocol
import smadata2.util

DEFAULT_CONFIG_FILE = os.path.expanduser("~/.smadata2rc")

class SMAData2InverterConfig(object):
    def __init__(self, name, bdaddr, serial, starttime):
        self.name = name
        self.bdaddr = bdaddr
        self.serial = serial
        self.starttime = starttime

    def connect(self):
        return smadata2.protocol.SMAData2BluetoothConnection(self.bdaddr)


    def connect_and_logon(self):
        conn = self.connect()
        conn.hello()
        conn.logon()
        return conn


DEFAULT_START_TIME = "2010-01-01"

class SMAData2Config(object):
    def __init__(self, configfile=DEFAULT_CONFIG_FILE):
        config = ConfigParser.SafeConfigParser(
            {'start_time': DEFAULT_START_TIME}
        )
        config.read(configfile)

        self.invs = []

        if config.has_option('DATABASE', 'filename'):
            self.dbname = os.path.expanduser(config.get('DATABASE', 'filename'))
        else:
            self.dbname = os.path.expanduser("~/.btsmadb.v0.sqlite")

        for s in config.sections():
            if s == 'DATABASE':
                continue

            addr = config.get(s, 'bluetooth')
            serial = config.getint(s, 'serial')
            starttime = smadata2.util.parse_time(config.get(s, 'start_time'))
            inv = SMAData2InverterConfig(s, addr, serial, starttime)
            self.invs.append(inv)

    def inverters(self):
        return self.invs


if __name__ == '__main__':
    config = SMAData2Config()
    for inv in config.inverters():
        print("%s:" % inv.name)
        print("\tBluetooth address: %s" % inv.bdaddr)
