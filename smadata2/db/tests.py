#! /usr/bin/env python

from __future__ import print_function

import StringIO
import os
import os.path
import errno
import sqlite3

from nose.tools import *

import smadata2.db
import smadata2.db.mock
from smadata2 import check

def removef(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


class BaseDBChecker(object):
    def setUp(self):
        self.db = self.opendb()
        self.sample_data()

    def tearDown(self):
        pass

    def sample_data(self):
        pass


class MockDBChecker(BaseDBChecker):
    def opendb(self):
        return smadata2.db.mock.MockDatabase()


class BaseSQLite(object):
    def prepare_sqlite(self):
        self.dbname = "__testdb__smadata2_%s_.sqlite" % self.__class__.__name__
        self.bakname = self.dbname + ".bak"

        # Start with a blank slate
        removef(self.dbname)
        removef(self.bakname)

        self.prepopulate()

        if os.path.exists(self.dbname):
            self.original = open(self.dbname).read()
        else:
            self.original = None

    def prepopulate(self):
        pass


class SQLiteDBChecker(BaseSQLite, BaseDBChecker):
    def opendb(self):
        self.prepare_sqlite()
        return smadata2.db.sqlite.create_or_update(self.dbname)

    def tearDown(self):
        removef(self.dbname)
        removef(self.bakname)
        super(SQLiteDBChecker, self).tearDown()


class SimpleChecks(BaseDBChecker):
    def test_trivial(self):
        assert isinstance(self.db, smadata2.db.base.BaseDatabase)

    def test_add_get_historic(self):
        # Serial is defined as INTEGER, but we abuse the fact that
        # sqlite doesn't actually make a distinction
        serial = "__TEST__"

        self.db.add_historic(serial, 0, 0)
        self.db.add_historic(serial, 300, 10)
        self.db.add_historic(serial, 3600, 20)

        v0 = self.db.get_one_historic(serial, 0)
        assert_equals(v0, 0)

        v300 = self.db.get_one_historic(serial, 300)
        assert_equals(v300, 10)

        v3600 = self.db.get_one_historic(serial, 3600)
        assert_equals(v3600, 20)

        vmissing = self.db.get_one_historic(serial, 9999)
        assert vmissing is None

    def test_get_last_historic_missing(self):
        serial = "__TEST__"

        last = self.db.get_last_historic(serial)
        assert last is None

    def test_get_last_historic(self):
        serial = "__TEST__"

        self.db.add_historic(serial, 0, 0)
        assert_equals(self.db.get_last_historic(serial), 0)

        self.db.add_historic(serial, 300, 0)
        assert_equals(self.db.get_last_historic(serial), 300)

        self.db.add_historic(serial, 3600, 0)
        assert_equals(self.db.get_last_historic(serial), 3600)

        self.db.add_historic(serial, 2000, 0)
        assert_equals(self.db.get_last_historic(serial), 3600)


class AggregateChecks(BaseDBChecker):
    def sample_data(self):
        super(AggregateChecks, self).sample_data()

        self.serial1 = "__TEST__1"
        self.serial2 = "__TEST__2"

        self.dawn = 8*3600
        self.dusk = 20*3600

        sampledata = check.generate_linear(0, self.dawn, self.dusk, 24*3600,
                                           0, 1)

        for ts, y in sampledata:
            self.db.add_historic(self.serial1, ts, y)
            self.db.add_historic(self.serial2, ts, 2*y)

    def test_basic(self):
        for ts in range(0, self.dawn, 300):
            y1 = self.db.get_one_historic(self.serial1, ts)
            y2 = self.db.get_one_historic(self.serial2, ts)

            assert_equals(y1, 0)
            assert_equals(y2, 0)

        for i, ts in enumerate(range(self.dawn, self.dusk, 300)):
            y1 = self.db.get_one_historic(self.serial1, ts)
            y2 = self.db.get_one_historic(self.serial2, ts)

            assert_equals(y1, i)
            assert_equals(y2, 2*i)

        val = (self.dusk - self.dawn - 1) / 300
        for ts in range(self.dusk, 24*3600, 300):
            y1 = self.db.get_one_historic(self.serial1, ts)
            y2 = self.db.get_one_historic(self.serial2, ts)

            assert_equals(y1, val)
            assert_equals(y2, 2*val)

    def test_aggregate_one(self):
        val = self.db.get_aggregate_one_historic(self.dusk,
                                                 (self.serial1, self.serial2))
        assert_equals(val, 3*((self.dusk - self.dawn - 2) / 300))

    def check_aggregate_range(self, from_, to_):
        results = self.db.get_aggregate_historic(from_, to_,
                                                 (self.serial1, self.serial2))

        first = results[0][0]
        last = results[-1][0]

        assert_equals(first, from_)
        assert_equals(last, to_ - 300)

        for ts, y in results:
            if ts < self.dawn:
                assert_equals(y, 0)
            elif ts < self.dusk:
                assert_equals(y, 3*((ts - self.dawn) / 300))
            else:
                assert_equals(y, 3*((self.dusk - self.dawn - 1) / 300))

    def test_aggregate(self):
        yield self.check_aggregate_range, 0, 24*3600
        yield self.check_aggregate_range, 8*3600, 20*3600
        yield self.check_aggregate_range, 13*3600, 14*3600


#
# Construct the basic tests as a cross-product
#
for cset in (SimpleChecks, AggregateChecks):
    for db in (MockDBChecker, SQLiteDBChecker):
        name = "_".join(("Test", cset.__name__, db.__name__))
        globals()[name] = type(name, (cset, db), {})


#
# Tests for sqlite schema updating
#
class UpdateSQLiteChecker(Test_SimpleChecks_SQLiteDBChecker):
    PRESERVE_RECORD = ("PRESERVE", 0, 31415)

    def test_backup(self):
        assert os.path.exists(self.bakname)
        backup = open(self.bakname).read()
        assert_equals(self.original, backup)

    def test_preserved(self):
        serial, timestamp, tyield = self.PRESERVE_RECORD

        assert_equals(self.db.get_last_historic(serial), timestamp)
        assert_equals(self.db.get_one_historic(serial, timestamp), tyield)


class TestUpdateNoPVO(UpdateSQLiteChecker):
    def prepopulate(self):
        DB_MAGIC = 0x71534d41
        DB_VERSION = 0

        conn = sqlite3.connect(self.dbname)
        conn.executescript("""
CREATE TABLE generation (inverter_serial INTEGER,
                            timestamp INTEGER,
                            total_yield INTEGER,
                            PRIMARY KEY (inverter_serial, timestamp));
CREATE TABLE schema (magic INTEGER, version INTEGER);""")
        conn.execute("INSERT INTO schema (magic, version) VALUES (?, ?)",
                     (DB_MAGIC, DB_VERSION))
        conn.commit()


        conn.execute("""INSERT INTO generation (inverter_serial, timestamp,
                                                 total_yield)
                            VALUES (?, ?, ?)""", self.PRESERVE_RECORD)
        conn.commit()

        del conn


class TestUpdateV0(UpdateSQLiteChecker):
    def prepopulate(self):
        DB_MAGIC = 0x71534d41
        DB_VERSION = 0

        conn = sqlite3.connect(self.dbname)
        conn.executescript("""
CREATE TABLE generation (inverter_serial INTEGER,
                            timestamp INTEGER,
                            total_yield INTEGER,
                            PRIMARY KEY (inverter_serial, timestamp));
CREATE TABLE schema (magic INTEGER, version INTEGER);
CREATE TABLE pvoutput (sid STRING,
                       last_datetime_uploaded INTEGER);""")
        conn.execute("INSERT INTO schema (magic, version) VALUES (?, ?)",
                     (DB_MAGIC, DB_VERSION))
        conn.commit()


        conn.execute("""INSERT INTO generation (inverter_serial, timestamp,
                                                 total_yield)
                            VALUES (?, ?, ?)""", self.PRESERVE_RECORD)
        conn.commit()

        del conn


class BadSchemaSQLiteChecker(BaseSQLite):
    def setUp(self):
        self.prepare_sqlite()

    @raises(smadata2.db.WrongSchema)
    def test_open(self):
        self.db = smadata2.db.SQLiteDatabase(self.dbname)


class TestEmptySQLiteDB(BadSchemaSQLiteChecker):
    """Check that we correctly fail on an empty DB"""

    def test_is_empty(self):
        assert not os.path.exists(self.dbname)


class TestBadSQLite(BadSchemaSQLiteChecker):
    """Check that we correctly fail attempting to update an unknwon format"""

    def prepopulate(self):
        conn = sqlite3.connect(self.dbname)
        conn.execute("CREATE TABLE unrelated (random STRING, data INTEGER)")
        conn.commit()
        del conn

    @raises(smadata2.db.WrongSchema)
    def test_update(self):
        db = smadata2.db.sqlite.create_or_update(self.dbname)
