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

import os
import shutil
import re
import sqlite3

from base import *


all = ['SQLiteDatabase']

_whitespace = re.compile('\s+')

def squash_schema(sqls):
    l = []
    for sql in sqls:
        l.append(_whitespace.sub(' ', sql.strip()))
    return frozenset(l)


def sqlite_schema(conn):
    c = conn.cursor()
    c.execute("SELECT sql FROM sqlite_master WHERE type = 'table'")
    sqls = [x[0] for x in c.fetchall()]
    return squash_schema(sqls)


class SQLiteDatabase(BaseDatabase):
    DDL = [
"""CREATE TABLE generation (inverter_serial INTEGER,
                            timestamp INTEGER,
                            total_yield INTEGER,
                            PRIMARY KEY (inverter_serial, timestamp))""",
"""CREATE TABLE pvoutput (sid STRING,
                          last_datetime_uploaded INTEGER)""",
    ]

    def __init__(self, filename):
        super(SQLiteDatabase, self).__init__()

        self.conn = sqlite3.connect(filename)

        schema = sqlite_schema(self.conn)
        if schema != squash_schema(self.DDL):
            raise WrongSchema("Incorrect database schema")

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


SCHEMA_CURRENT = squash_schema(SQLiteDatabase.DDL)


SCHEMA_EMPTY = frozenset()


def create_from_empty(conn):
    for sql in SQLiteDatabase.DDL:
        conn.execute(sql)
    conn.commit()


SCHEMA_V0 = squash_schema((
"""CREATE TABLE generation (inverter_serial INTEGER,
                            timestamp INTEGER,
                            total_yield INTEGER,
                            PRIMARY KEY (inverter_serial, timestamp))""",
"""CREATE TABLE schema (magic INTEGER, version INTEGER)""",
"""CREATE TABLE pvoutput (sid STRING,
                          last_datetime_uploaded INTEGER)"""))


def update_v0(conn):
    conn.execute("DROP TABLE schema")
    conn.execute("VACUUM")
    conn.commit()


_schema_table = {
    SCHEMA_CURRENT: None,
    SCHEMA_EMPTY: create_from_empty,
    SCHEMA_V0: update_v0,
}

def try_open(filename):
    try:
        db = SQLiteDatabase(filename)
        return db
    except WrongSchema:
        return None


def create_or_update(filename):
    db = try_open(filename)

    if db is None:
        bkname = filename + ".bak"
        shutil.copyfile(filename, bkname)

    while db is None:
        conn = sqlite3.connect(filename)

        old_schema = sqlite_schema(conn)

        if old_schema not in _schema_table:
            raise WrongSchema("Unrecognized database schema")

        conv = _schema_table[old_schema]
        assert conv is not None

        conv(conn)

        new_schema = sqlite_schema(conn)

        assert old_schema != new_schema
        assert new_schema in _schema_table

        del conn

        # Try again
        db = try_open(filename)

    return db
