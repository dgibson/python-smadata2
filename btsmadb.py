#! /usr/bin/env python

from __future__ import print_function

import sys
import time
import sqlite3

class BTSMADatabaseError(Exception):
    pass


class BTSMADatabase(object):
    def __init__(self, *args):
        self.conn = self.connect(*args)

        magic, version = self.get_magic()
        if (magic != self.DB_MAGIC) or (version != self.DB_VERSION):
            raise BTSMADatabaseError("Incorrect database version (0x%x, %d)"
                                     % (magic, version))

    def connect(self):
        raise NotImplementedError

    def get_magic(self):
        raise NotImplementedError


class BTSMADatabaseSQLiteV0(BTSMADatabase):
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
                raise BTSMADatabaseError("Bad version table")
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
    db = BTSMADatabaseSQLiteV0(sys.argv[1])
