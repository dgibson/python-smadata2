#! /usr/bin/env python

import StringIO
import os.path
import unittest
import time
import datetime

from nose.tools import *

import smadata2.db


class BaseDB(object):
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


class TestDBMock(BaseDB):
    def setUp(self):
        super(TestDBMock, self).setUp()
        self.db = smadata2.db.MockDatabase()


class TestDBSQLite(BaseDB):
    def setUp(self):
        super(TestDBSQLite, self).setUp()
        self.dbname = "__testdb__smadata2_%s_.sqlite" % self.__class__.__name__
        self.db = smadata2.db.SQLiteDatabase.create(self.dbname)

    def tearDown(self):
        os.remove(self.dbname)

    def test_magic(self):
        magic, version = self.db.get_magic()
        assert_equals(magic, smadata2.db.SQLiteDatabase.DB_MAGIC)
        assert_equals(version, smadata2.db.SQLiteDatabase.DB_VERSION)


class TestEmptyDB(object):
    def setUp(self):
        self.dbname = "__testdb__smadata2_%s_.sqlite" % self.__class__.__name__

    def tearDown(self):
        os.remove(self.dbname)

    @raises(smadata2.db.Error)
    def test_empty(self):
        self.db = smadata2.db.SQLiteDatabase(self.dbname)
