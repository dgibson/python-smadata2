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

from __future__ import print_function

import sys
import os.path
import time
import sqlite3
import datetime
import calendar


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

    @classmethod
    def create(cls, filename):
        # This is a convenience / sanity check
        # It's racy, so it's not secure or foolproof
        if os.path.exists(filename):
            raise ValueError("Database file %s already exists" % filename)

        conn = sqlite3.connect(filename)
        conn.execute("""
CREATE TABLE generation (inverter_serial INTEGER,
                         timestamp INTEGER,
                         total_yield INTEGER,
                         PRIMARY KEY (inverter_serial, timestamp))""")
        conn.execute("CREATE TABLE schema (magic INTEGER, version INTEGER)")
        conn.execute("""CREATE TABLE pvoutput (sid STRING,
                                               last_datetime_uploaded INTEGER)""")
        conn.execute("INSERT INTO schema (magic, version) VALUES (?, ?)",
                     (cls.DB_MAGIC, cls.DB_VERSION))
        conn.commit()
        del conn
        return cls(filename)

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

    # return midnights for each day in the database
    # @param serial the inverter seial number to retrieve midnights for
    # @return all midnights in database as datetime objects
    def midnights(self, inverters):
        c = self.conn.cursor()
        serials = ','.join(x.serial for x in inverters)
        c.execute("SELECT distinct(timestamp) "
                  "FROM generation "
                  "WHERE inverter_serial  in ( ? ) "
                  "AND timestamp % 86400 = 0 "
                  "ORDER BY timestamp ASC", (serials,))
        r = c.fetchall()
        r = map(lambda x: datetime.datetime.utcfromtimestamp(x[0]), r)
        return r

    # retrieve all entries for a day from the database
    # @note this seems to get timezone stuff right :-) "a day" is a "local" day
    # @param date a datetime object for midnight of the day you want
    # fixed
    def get_entries_for_day(self, inverters, start_datetime):
        c = self.conn.cursor()
        before_datetime = start_datetime + datetime.timedelta(days=1)
        start_unixtime = time.mktime(start_datetime.timetuple())
        before_unixtime = time.mktime(before_datetime.timetuple())
        serials = ','.join(x.serial for x in inverters)
        c.execute("SELECT timestamp,total_yield,inverter_serial "
                  "FROM generation "
                  "WHERE inverter_serial in  ( ? ) "
                  "AND timestamp >= ? and timestamp < ?"
                  "ORDER BY timestamp ASC", (serials, start_unixtime,
                                             before_unixtime))
        r = c.fetchall()
        return r

    def get_datapoint_totals_for_day(self, inverters, start_datetime):
        c = self.conn.cursor()
        before_datetime = start_datetime + datetime.timedelta(days=1)
        start_unixtime = time.mktime(start_datetime.timetuple())
        before_unixtime = time.mktime(before_datetime.timetuple())
        serials = ','.join(x.serial for x in inverters)
        c.execute("SELECT timestamp,sum(total_yield),count(inverter_serial) "
                  "FROM generation "
                  "WHERE inverter_serial in  ( ? ) "
                  "AND timestamp >= ? and timestamp < ? "
                  "group by timestamp "
                  "ORDER BY timestamp ASC", (serials, start_unixtime,
                                             before_unixtime))
        r = c.fetchall()
        return r

    # return last data for a particular day
    def get_last_entry_for_day(self, serial, date):
        c = self.conn.cursor()
        entries = self.get_entries_for_day(serial, date)
        if len(entries) == 0:
            return None
        return entries[len(entries)-1]

    # fixed
    def get_entries(self, inverters, timestamp):
        c = self.conn.cursor()
        serials = ','.join(x.serial for x in inverters)
        c.execute("SELECT timestamp,total_yield,inverter_serial "
                  "FROM generation "
                  "WHERE inverter_serial in ( ? ) "
                  "AND timestamp = ? "
                  "ORDER BY timestamp DESC LIMIT ?", (serials, timestamp, 1))
        r = c.fetchall()
        if len(r) == 0:
            return None
        return r

    # def get_entries_younger_than(self, serial, entry):
    #     timestamp = entry[0]
    #     c = self.conn.cursor()
    #     c.execute("SELECT timestamp,total_yield "
    #               "FROM generation "
    #               "WHERE inverter_serial = ? AND "
    #               " timestamp > ? "
    #               "ORDER BY timestamp ASC", (serial, str(timestamp)))
    #     r = c.fetchall()
    #     return r

    def get_productions_younger_than(self, inverters, timestamp):
        serials = ','.join(x.serial for x in inverters)
        c = self.conn.cursor()
        c.execute("SELECT timestamp,total_yield,count(inverter_serial) "
                  "FROM generation "
                  "WHERE inverter_serial in ( ? ) AND "
                  " timestamp > ? "
                  "group by timestamp "
                  "ORDER BY timestamp ASC", (serials, str(timestamp)))
        r = c.fetchall()
        return r

    def get_last_historic(self, serial):
        c = self.conn.cursor()
        c.execute("SELECT max(timestamp) FROM generation"
                  " WHERE inverter_serial = ?", (serial,))
        r = c.fetchone()
        return r[0]

    def pvoutput_get_last_datetime_uploaded(self, sid):
        c = self.conn.cursor()
        c.execute("SELECT last_datetime_uploaded "
                  "FROM pvoutput "
                  "WHERE sid = ?", (sid,))
        r = c.fetchone()
        if r is None:
            return None
        return r[0]

    def pvoutput_maybe_init_system(self, sid):
        print(sid)
        c = self.conn.cursor()
        c.execute("SELECT * FROM pvoutput"
                  " WHERE sid = ?",
                  (sid,))
        r = c.fetchone()
        if r is None:
            c = self.conn.cursor()
            c.execute("INSERT INTO pvoutput(sid) VALUES ( ? )",
                      (sid,))
            self.commit()

    def pvoutput_set_last_datetime_uploaded(self, sid, value):
        c = self.conn.cursor()
        self.pvoutput_maybe_init_system(sid)
        c.execute("update pvoutput "
                  "SET last_datetime_uploaded = ?"
                  "WHERE sid = ?", (value, sid))
        self.commit()

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
