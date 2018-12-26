#! /usr/bin/python3

import os
import datetime
import time
import dateutil

from nose.tools import assert_equals
from nose.plugins.attrib import attr

import smadata2.config
import smadata2.pvoutputorg
import smadata2.datetimeutil
import smadata2.check
import smadata2.upload


def test_parse_date():
    assert_equals(smadata2.pvoutputorg.parse_date("20130813"),
                  datetime.date(2013, 8, 13))


def test_parse_time():
    assert_equals(smadata2.pvoutputorg.parse_time("14:37"),
                  datetime.time(14, 37, 0))


def test_parse_datetime():
    assert_equals(smadata2.pvoutputorg.parse_datetime("20130813", "14:37"),
                  datetime.datetime(2013, 8, 13, 14, 37, 0))


def test_format_date():
    d = datetime.date(2013, 8, 13)
    assert_equals(smadata2.pvoutputorg.format_date(d), "20130813")


def test_format_time():
    t = datetime.time(14, 37)
    assert_equals(smadata2.pvoutputorg.format_time(t), "14:37")


def test_format_datetime():
    dt = datetime.datetime(2013, 8, 13, 14, 37, 0)
    assert_equals(smadata2.pvoutputorg.format_datetime(dt),
                  ("20130813", "14:37"))


def requestkey(script, args):
    return (script, frozenset(list(args.items())))


class MockAPI(smadata2.pvoutputorg.API):
    responsetable = {
        requestkey("/service/r2/getsystem.jsp", {"donations": 1}):
            "Mock System,1234,0000,39,250,Mock Panel Model,2,5000,\
Mock Inverter Model,NE,1.0,No,,0.000000,0.000000,5;;1"
    }

    def __init__(self):
        super(MockAPI, self).__init__("http://pvoutput.example.com",
                                      "MOCKAPIKEY", "MOCKSID")

    def _request(self, script, args):
        return self.responsetable[requestkey(script, args)]


class TestMockAPI(object):
    def __init__(self):
        self.api = MockAPI()

    def test_getsystem(self):
        assert_equals(self.api.name, "Mock System")
        assert_equals(self.api.system_size, 1234)
        assert_equals(self.api.donation_mode, True)


@attr("pvoutput.org")
class RealAPIChecker(object):
    CONFIGFILE = "smadata2-test-pvoutput.json"

    def __init__(self):
        if not os.path.exists(self.CONFIGFILE):
            raise AssertionError("This test needs a special configuration")

        self.config = \
            smadata2.config.SMAData2Config("smadata2-test-pvoutput.json")
        self.system = self.config.systems()[0]
        assert_equals(self.system.name, "test")

        self.date = datetime.date.today() - datetime.timedelta(days=1)

    def delay(self):
        time.sleep(10)

    def setUp(self):
        self.api = self.config.pvoutput_connect(self.system)

        # Make sure we have a blank slate
        self.api.deletestatus(self.date)
        self.delay()

    def tearDown(self):
        self.api.deletestatus(self.date)
        self.delay()


@attr("pvoutput.org")
class TestRealAPI(RealAPIChecker):
    def test_trivial(self):
        assert isinstance(self.api, smadata2.pvoutputorg.API)

    def test_blank(self):
        results = self.api.getstatus(self.date)
        assert results is None

    # The single addstatus interface doesn't seem to work as I expect
    def test_addsingle(self):
        dt0 = datetime.datetime.combine(self.date, datetime.time(12, 0, 0))
        dt1 = datetime.datetime.combine(self.date, datetime.time(12, 5, 0))

        self.api.addstatus(dt0, 1000)
        self.delay()
        self.api.addstatus(dt1, 1007)
        self.delay()

        results = self.api.getstatus(self.date)
        assert_equals(results, [(dt0, 0), (dt1, 7)])

    def test_addbatch(self):
        dt0 = datetime.datetime.combine(self.date, datetime.time(10, 0, 0))
        batch = []
        for i in range(25):
            dt = dt0 + datetime.timedelta(minutes=5*i)
            batch.append((dt, 1000 + i))

        self.api.addbatchstatus(batch)
        self.delay()

        results = self.api.getstatus(self.date)
        assert len(results) == 25
        for i in range(25):
            assert_equals(results[i][0], batch[i][0])
            assert_equals(results[i][1], i)

    def test_addbulk(self):
        tz = dateutil.tz.tzutc()

        startyield = 1000
        ts_start, ts_end = smadata2.datetimeutil.day_timestamps(self.date, tz)
        ts_dawn = ts_start + 8*3600
        ts_dusk = ts_start + 20*3600

        data = smadata2.check.generate_linear(ts_start, ts_dawn,
                                              ts_dusk, ts_end, startyield, 1)
        output = smadata2.upload.prepare_data_for_date(self.date, data, tz)

        self.api.addstatus_bulk(output)
        self.delay()

        results = self.api.getstatus(self.date)

        assert_equals(len(results), len(output))
        for i, (dt, y) in enumerate(results):
            xdt, xy = output[i]
            assert_equals(y, xy - startyield)
            xdt = xdt.replace(tzinfo=None)
            assert_equals(dt, xdt)

    def test_getstatus_date_latest(self):
        assert(self.api.getstatus_date_latest(self.date) is None)

        dt0 = datetime.datetime.combine(self.date, datetime.time(10, 35))

        self.api.addstatus(dt0, 1000)
        self.delay()

        res = self.api.getstatus_date_latest(self.date)
        assert_equals(res[0], dt0)

        batch = []
        for m in range(0, 46, 5):
            t = datetime.time(14, m)
            dt = datetime.datetime.combine(self.date, t)
            batch.append((dt, 1000))

        assert_equals(dt.minute, 45)

        self.api.addstatus_bulk(batch)
        self.delay()

        res = self.api.getstatus_date_latest(self.date)
        assert_equals(res[0], dt)
