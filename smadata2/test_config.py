#! /usr/bin/python3

import io
import os.path
import time
import datetime
import dateutil.tz

from nose.tools import assert_equals

import smadata2.config


class BaseTestConfig(object):
    def setUp(self):
        self.c = smadata2.config.SMAData2Config(io.StringIO(self.json))


class TestMinimalConfig(BaseTestConfig):
    json = "{}"

    def test_dbname(self):
        assert_equals(self.c.dbname,
                      os.path.expanduser("~/.smadata2.sqlite"))

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
                "pvoutput-sid": "12345"
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

    def test_timezone(self):
        system = self.c.systems()[0]
        assert isinstance(system.timezone(), dateutil.tz.tzlocal)


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
                "serial": "TESTSERIAL"
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
        assert inv.starttime is None
        assert isinstance(str(inv), str)


class TestConfigUTCSystem(TestConfigEmptySystem):
    json = """
    {
        "systems": [
            {
                "name": "Test System",
                "pvoutput-sid": "12345",
                "timezone": "UTC"
            }
         ]
    }"""

    def test_timezone(self):
        system = self.c.systems()[0]
        dt = datetime.datetime(2007, 11, 5,
                               15, 37, 56, 9999, system.timezone())
        assert_equals(dt.tzname(), "UTC")
