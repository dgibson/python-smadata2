#! /usr/bin/python3
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

import sys
import os
import dateutil.parser
import dateutil.tz
import json

from .inverter import smabluetooth
from . import pvoutputorg
from . import datetimeutil
from . import db

DEFAULT_CONFIG_FILE = os.path.expanduser("~/.smadata2.json")


class SMAData2InverterConfig(object):
    def __init__(self, invjson, defname):
        self.bdaddr = invjson["bluetooth"]
        self.serial = invjson["serial"]
        self.name = invjson.get("name", defname)
        if "start-time" in invjson:
            self.starttime = datetimeutil.parse_time(invjson["start-time"])
        else:
            self.starttime = None

    def connect(self):
        return smabluetooth.Connection(self.bdaddr)

    def connect_and_logon(self):
        conn = self.connect()
        conn.hello()
        conn.logon()
        return conn

    def __str__(self):
        return ("\t%s:\n" % self.name +
                "\t\tSerial number: '%s'\n" % self.serial +
                "\t\tBluetooth address: %s\n" % self.bdaddr)


class SMAData2SystemConfig(object):
    def __init__(self, index, sysjson=None, invjson=None):
        if sysjson:
            assert invjson is None

            self.name = sysjson.get("name", "system-%04d" % index)
            self.pvoutput_sid = sysjson.get("pvoutput-sid", None)
            self.tz = sysjson.get("timezone", None)

            self.invs = []
            if "inverters" in sysjson:
                for i, invjson in enumerate(sysjson["inverters"]):
                    defname = "%s-inverter-%04d" % (self.name, i)
                    self.invs.append(SMAData2InverterConfig(invjson, defname))
        else:
            assert invjson is not None

            inv = SMAData2InverterConfig(invjson,
                                         "standalone-inverter-%04d" % index)
            self.name = inv.name
            self.pvoutput_sid = invjson.get("pvoutput-sid", None)
            self.tz = invjson.get("timezone", None)

            self.invs = [inv]

    def inverters(self):
        return self.invs

    def timezone(self):
        if self.tz is None:
            return dateutil.tz.tzlocal()
        else:
            return dateutil.tz.gettz(self.tz)

    def __str__(self):
        return ("%s: (pvoutput.org SID '%s')\n" % (self.name,
                                                   self.pvoutput_sid) +
                "".join(str(inv) for inv in self.invs))


class SMAData2Config(object):
    def __init__(self, configfile=None):
        if configfile is None:
            configfile = DEFAULT_CONFIG_FILE

        if isinstance(configfile, str):
            f = open(configfile, "r")
        else:
            f = configfile

        alljson = json.load(f)

        dbname = os.path.expanduser("~/.smadata2.sqlite")
        if "database" in alljson:
            dbjson = alljson["database"]
            if "filename" in dbjson:
                dbname = dbjson["filename"]
        self.dbname = os.path.expanduser(dbname)

        if "pvoutput.org" in alljson:
            pvojson = alljson["pvoutput.org"]
            self.pvoutput_server = pvojson.get("server", "pvoutput.org")
            self.pvoutput_apikey = pvojson.get("apikey", None)

        self.syslist = []
        if "systems" in alljson:
            for i, sysjson in enumerate(alljson["systems"]):
                self.syslist.append(SMAData2SystemConfig(i, sysjson=sysjson))

        if "inverters" in alljson:
            for i, invjson in enumerate(alljson["inverters"]):
                self.syslist.append(SMAData2SystemConfig(i, invjson=invjson))

    def systems(self):
        return self.syslist

    def pvoutput_connect(self, system):
        return pvoutputorg.API("http://" + self.pvoutput_server,
                               self.pvoutput_apikey, system.pvoutput_sid)

    def database(self):
        return db.SQLiteDatabase(self.dbname)


if __name__ == '__main__':
    if sys.argv[1:]:
        config = SMAData2Config(sys.argv[1])
    else:
        config = SMAData2Config()
    for system in config.systems():
        print(system)
