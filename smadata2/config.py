#! /usr/bin/env python
#
# smadata2.config - Configuration file handling for SMAData2 code
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
    def __init__(self, name, bdaddr, serial, starttime, pvoutput_sid):
        self.name = name
        self.bdaddr = bdaddr
        self.serial = serial
        self.starttime = starttime
        self.pvoutput_sid = pvoutput_sid

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
            self.dbname = os.path.expanduser(config.get('DATABASE',
                                                        'filename'))
        else:
            self.dbname = os.path.expanduser("~/.btsmadb.v0.sqlite")

        if config.has_option('pvoutput.org', 'config'):
            self.pvoutput_config_filepath = \
                os.path.expanduser(config.get('pvoutput.org', 'config'))
        else:
            self.pvoutput_config_filepath = \
                os.path.expanduser("~/.pvoutput.org.rc")

        for s in config.sections():
            if s == 'DATABASE':
                continue
            if s == 'pvoutput.org':
                continue

            addr = config.get(s, 'bluetooth')
            serial = config.getint(s, 'serial')
            pvoutput_sid = config.get(s, 'pvoutput-sid')
            starttime = smadata2.util.parse_time(config.get(s, 'start_time'))
            inv = SMAData2InverterConfig(s, addr, serial,
                                         starttime, pvoutput_sid)
            self.invs.append(inv)

    def inverters(self):
        return self.invs


if __name__ == '__main__':
    config = SMAData2Config()
    for inv in config.inverters():
        print("%s:" % inv.name)
        print("\tBluetooth address: %s" % inv.bdaddr)
