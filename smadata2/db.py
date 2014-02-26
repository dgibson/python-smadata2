#! /usr/bin/env python
#
# smadata2.db - Database for logging data from SMA inverters
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

protocol - Python code to communicate with SMA inverters
from __future__ import print_function

import sys
import time
import sqlite3

class Error(Exception):
    pass


class SMADatabase(object):
    def __init__(self, *args):
        self.conn = self.connect(*args)

        magic, version = self.get_magic()
        if (magic != self.DB_MAGIC) or (version != self.DB_VERSION):
            raise Error("Incorrect database version (0x%x, %d)"
                        % (magic, version))

    def connect(self):
        raise NotImplementedError

    def get_magic(self):
        raise NotImplementedError


class SMADatabaseSQLiteV0(SMADatabase):
    DB_MAGIC = 0x71534d41
    DB_VERSION = 0

    def connect(self, filename):
        return sqlite3.connect(filename)

    def get_magic(self):
        c = self.conn.cursor()
        c.execute("SELECT magic, version FROM schema;")
        r = c.fetchone()
        magic, version = r[0], r[1]
        if c.fetchone() is not None:
            if c.fetchone() is not None:
                raise Error("Bad version table")
        return magic, version

    def get_last_historic(self, serial):
        c = self.conn.cursor()
        c.execute("SELECT max(timestamp) FROM generation"
                  " WHERE inverter_serial = ?", (serial,))
        r = c.fetchone()
        return r[0]

    def get_one_historic(self, serial, timestamp):
        c = self.conn.cursor()
        c.execute("SELECT total_yield FROM generation"
                  " WHERE inverter_serial = ?"
                  " AND timestamp = ?", (serial, timestamp))
        r = c.fetchone()
        if r is not None:
            return r[0]

    def add_historic(self, serial, timestamp, total_yield):
        c = self.conn.cursor()
        c.execute("INSERT INTO generation"
                  + " (inverter_serial, timestamp, total_yield)"
                  + " VALUES (?, ?, ?);",
                  (serial, timestamp, total_yield))

    def commit(self):
        self.conn.commit()
        

if __name__ == '__main__':
    db = SMADatabaseSQLiteV0(sys.argv[1])
