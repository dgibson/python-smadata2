#! /usr/bin/env python

import StringIO
import os.path
import unittest
import time
import datetime

from nose.tools import *

import smadata2.config
import smadata2.db


class BaseTestConfig(object):
    def setUp(self):
        self.c = smadata2.config.SMAData2Config(StringIO.StringIO(self.json))


class TestMinimalConfig(BaseTestConfig):
    json = "{}"

    def test_dbname(self):
        assert_equals(self.c.dbname,
                      os.path.expanduser("~/.btsmadb.v0.sqlite"))

    def test_systems(self):
        assert_equals(self.c.systems(), [])


class TestConfigWithPVOutput(BaseTestConfig):
    json = """
    {
        "pvoutput.org": {
        }
    }"""

    def test_server(self):
        assert_equals(self.c.pvoutput_server, "pvoutput.org")

    def test_apikey(self):
        assert_equals(self.c.pvoutput_apikey, None)


class TestConfigEmptySystem(BaseTestConfig):
    json = """
    {
        "pvoutput.org": {
            "server": "pvoutput.example.com",
            "apikey": "TESTTESTTESTTEST"
        },
        "systems": [
            {
                "name": "Test System",
                "pvoutput-sid": "12345",
                "inverters": []
            }
        ]
    }"""

    def test_systems(self):
        syslist = self.c.systems()
        assert_equals(len(syslist), 1)

    def test_inverters(self):
        system = self.c.systems()[0]
        assert not system.inverters()

    def test_pvosystem(self):
        system = self.c.systems()[0]
        assert_equals(system.pvoutput_sid, "12345")


class TestConfigSimpleSystem(TestConfigEmptySystem):
    json = """
    {
        "pvoutput.org": {
            "server": "pvoutput.example.com",
            "apikey": "TESTTESTTESTTEST"
        },
        "systems": [
            {
                "name": "Test System",
                "pvoutput-sid": "12345",
                "inverters": [
                    {
                        "name": "Test Inverter",
                        "bluetooth": "aa:bb:cc:dd:ee:ff",
                        "serial": "TESTSERIAL",
                        "start-time": "2000-01-01"
                    }
                ]
            }
         ]
    }"""

    def test_systems(self):
        syslist = self.c.systems()
        assert_equals(len(syslist), 1)

    def test_inverters(self):
        system = self.c.systems()[0]
        invlist = system.inverters()
        assert_equals(len(invlist), 1)

    def test_inv(self):
        system = self.c.systems()[0]
        inv = system.inverters()[0]
        assert_equals(inv.name, "Test Inverter")
        assert_equals(inv.bdaddr, "aa:bb:cc:dd:ee:ff")
        assert_equals(inv.serial, "TESTSERIAL")
        xtime = time.mktime(datetime.datetime(2000, 1, 1).timetuple())
        assert_equals(inv.starttime, xtime)
        assert isinstance(str(inv), str)


class TestConfigBareInverter(BaseTestConfig):
    json = """
    {
        "pvoutput.org": {
            "server": "pvoutput.example.com",
            "apikey": "TESTTESTTESTTEST"
        },
        "inverters": [
            {
                "name": "Test Inverter",
                "bluetooth": "aa:bb:cc:dd:ee:ff",
                "serial": "TESTSERIAL",
                "start-time": "2000-01-01"
            }
        ]
    }"""

    def test_inverters(self):
        system = self.c.systems()[0]
        invlist = system.inverters()
        assert_equals(len(invlist), 1)

    def test_inv(self):
        system = self.c.systems()[0]
        inv = system.inverters()[0]
        assert_equals(inv.name, "Test Inverter")
        assert_equals(inv.bdaddr, "aa:bb:cc:dd:ee:ff")
        assert_equals(inv.serial, "TESTSERIAL")
        xtime = time.mktime(datetime.datetime(2000, 1, 1).timetuple())
        assert_equals(inv.starttime, xtime)
        assert isinstance(str(inv), str)


class TestDB(object):
    def setUp(self):
        self.dbname = "__testdb__smadata2_%s_.sqlite" % self.__class__.__name__
        self.db = smadata2.db.SMADatabaseSQLiteV0.create(self.dbname)

    def tearDown(self):
        os.remove(self.dbname)

    def test_trivial(self):
        assert isinstance(self.db, smadata2.db.SMADatabaseSQLiteV0)

    def test_magic(self):
        magic, version = self.db.get_magic()
        assert_equals(magic, smadata2.db.SMADatabaseSQLiteV0.DB_MAGIC)
        assert_equals(version, smadata2.db.SMADatabaseSQLiteV0.DB_VERSION)

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
