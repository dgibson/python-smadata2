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

from sql import *


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


class SQLiteDatabase(SQLDatabase):
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
        self.placeholder = "?"

        schema = sqlite_schema(self.conn)
        if schema != squash_schema(self.DDL):
            raise WrongSchema("Incorrect database schema")

SCHEMA_CURRENT = squash_schema(SQLiteDatabase.DDL)


SCHEMA_EMPTY = frozenset()


def create_from_empty(conn):
    for sql in SQLiteDatabase.DDL:
        conn.execute(sql)
    conn.commit()


SCHEMA_NOPVO = squash_schema((
"""CREATE TABLE generation (inverter_serial INTEGER,
                            timestamp INTEGER,
                            total_yield INTEGER,
                            PRIMARY KEY (inverter_serial, timestamp))""",
"""CREATE TABLE schema (magic INTEGER, version INTEGER)"""))


def update_nopvo(conn):
    conn.execute("""CREATE TABLE pvoutput (sid STRING,
                                           last_datetime_uploaded INTEGER)""")
    conn.execute("VACUUM")
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
    SCHEMA_NOPVO: update_nopvo,
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
