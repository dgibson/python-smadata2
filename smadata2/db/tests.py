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

def removef(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


class CommonChecks(object):
    def setUp(self):
        pass

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


class TestDBMock(CommonChecks):
    def setUp(self):
        super(TestDBMock, self).setUp()
        self.db = smadata2.db.mock.MockDatabase()


class BaseSQLite(object):
    def setUp(self):
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

    def tearDown(self):
        removef(self.dbname)
        removef(self.bakname)

    def prepopulate(self):
        pass


class TestEmptySQLiteDB(BaseSQLite):
    """Check that we correctly fail on an empty DB"""

    def test_is_empty(self):
        assert not os.path.exists(self.dbname)

    @raises(smadata2.db.WrongSchema)
    def test_open(self):
        self.db = smadata2.db.SQLiteDatabase(self.dbname)


class TestCreateSQLite(BaseSQLite, CommonChecks):
    def setUp(self):
        super(TestCreateSQLite, self).setUp()
        self.db = smadata2.db.sqlite.create_or_update(self.dbname)


class BaseUpdateSQLite(TestCreateSQLite):
    def test_backup(self):
        assert os.path.exists(self.bakname)
        backup = open(self.bakname).read()
        assert_equals(self.original, backup)
