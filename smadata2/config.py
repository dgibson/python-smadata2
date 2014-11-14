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

import sys
import os
import time
import calendar
import dateutil.parser
import json

import protocol
import pvoutputorg
import util
import db

DEFAULT_CONFIG_FILE = os.path.expanduser("~/.smadata2.json")


class SMAData2InverterConfig(object):
    def __init__(self, name, bdaddr, serial, starttime, pvoutput_sid):
        self.name = name
        self.bdaddr = bdaddr
        self.serial = serial
        self.starttime = starttime
        self.pvoutput_sid = pvoutput_sid

    def connect(self):
        return protocol.SMAData2BluetoothConnection(self.bdaddr)

    def connect_and_logon(self):
        conn = self.connect()
        conn.hello()
        conn.logon()
        return conn

    def __str__(self):
        return ("%s:\n" % self.name
                + "\tSerial number: '%s'\n" % self.serial
                + "\tBluetooth address: %s\n" % self.bdaddr)

DEFAULT_START_TIME = "2010-01-01"


class SMAData2Config(object):
    def __init__(self, configfile=DEFAULT_CONFIG_FILE):
        f = open(configfile, "r")

        alljson = json.load(f)

        dbname = os.path.expanduser("~/.btsmadb.v0.sqlite")
        if "database" in alljson:
            dbjson = alljson["database"]
            if "filename" in dbjson:
                dbname = dbjson["filename"]
        self.dbname = os.path.expanduser(dbname)

        if "pvoutput.org" in alljson:
            pvojson = alljson["pvoutput.org"]
            self.pvoutput_server = pvojson.get("server", None)
            self.pvoutput_apikey = pvokson.get("apikey", None)

        self.invs = []
        if "inverters" in alljson:
            for i, invjson in enumerate(alljson["inverters"]):
                name = invjson.get("name", "inverter-%04d" % i)
                addr = invjson["bluetooth"]
                serial = invjson["serial"]
                pvoutput_sid = invjson.get("pvoutput-sid", None)
                starttime = invjson.get("start-time", None)
                if starttime is not None:
                    starttime = util.parse_time(starttime)
                inv = SMAData2InverterConfig(name, addr, serial,
                                             starttime, pvoutput_sid)
                self.invs.append(inv)

    def inverters(self):
        return self.invs

    def pvoutput_connect(self):
        return pvoutputorg.PVOutputOrgConnection(self.pvoutput_server,
                                                 self.pvoutput_apikey)

    def database(self):
        return db.SMADatabaseSQLiteV0(self.dbname)


if __name__ == '__main__':
    if sys.argv[1:]:
        config = SMAData2Config(sys.argv[1])
    else:
        config = SMAData2Config()
    for inv in config.inverters():
        print(inv)
