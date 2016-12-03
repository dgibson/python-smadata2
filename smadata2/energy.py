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

from datetime import datetime
import httplib
import json

class Uploader(object):
    def __init__(self, database, base_uri, api_key):
        self.db = database
        self.base_uri = base_uri
        self.api_key = api_key

    def upload_missing(self, inverter):
        last_entry_time = self.db.energy_get_last_datetime_uploaded(inverter.serial)
        entries = self.db.get_productions_younger_than([inverter], last_entry_time)
        if len(entries) == 0:
            return

        path = "/api/inverters/" + inverter.serial + "/readings"
        body = json.dumps({"readings": map(lambda e: { "time": datetime.fromtimestamp(e[0]).isoformat() + "Z", "value": e[1] }, entries)})
        headers = { "Content-type": "application/json", "X-Api-Key": self.api_key }
        conn = httplib.HTTPSConnection(self.base_uri)
        conn.request("POST", path, body, headers)
        if conn.getresponse().status == 201:
            last_entry_time = entries[-1][0]
            self.db.energy_set_last_datetime_uploaded(inverter.serial, last_entry_time)
        else:
            print "Response did not indicate success."

        conn.close()
