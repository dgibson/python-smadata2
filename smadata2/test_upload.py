#! /usr/bin/python3

import datetime
import dateutil.tz
import json

from nose.tools import assert_equals

import smadata2.upload
import smadata2.check
import smadata2.db.sqlite
from smadata2.db.tests import SQLiteDBChecker
from smadata2.db import SAMPLE_ADHOC


def test_prepare1():
    dawn = 8*3600
    dusk = 20*3600
    dayend = 24*3600

    data = smadata2.check.generate_linear(0, dawn, dusk, dayend, 12345, 1)

    output = smadata2.upload.prepare_data_for_date(datetime.date(1970, 1, 1),
                                                   data, dateutil.tz.tzutc())

    dtdawn = datetime.datetime(1970, 1, 1, 8, tzinfo=dateutil.tz.tzutc())
    # dtdusk = datetime.datetime(1970, 1, 1, 20, tzinfo=dateutil.tz.tzutc())

    assert_equals(len(output), (dusk - dawn) / 300)
    for i, (dt, y) in enumerate(output):
        assert_equals(dt, dtdawn + datetime.timedelta(minutes=5*i))
        assert_equals(y, i + 12345)


class TestLoad(SQLiteDBChecker):
    def test_load(self):
        sysjson = json.loads("""{
            "name": "Test System",
            "timezone": "Australia/Sydney",
            "inverters": [
                {
                    "name": "Test Inverter",
                    "bluetooth": "00:00:00:00:00:00",
                    "serial": "TESTSERIAL",
                    "start-time": "2010-01-01"
                }
            ]
        }""")
        sc = smadata2.config.SMAData2SystemConfig(0, sysjson)

        date = datetime.date(2010, 2, 7)
        midnight = datetime.time(0, tzinfo=sc.timezone())
        dtstart = datetime.datetime.combine(date, midnight)

        daystart = smadata2.datetimeutil.totimestamp(dtstart)
        dawn = daystart + 8*3600
        dusk = daystart + 20*3600
        dayend = daystart + 24*3600

        data = smadata2.check.generate_linear(daystart, dawn, dusk, dayend,
                                              12345, 1)

        for ts, y in data:
            self.db.add_sample("TESTSERIAL", ts, SAMPLE_ADHOC, y)

        outdata = smadata2.upload.load_data_for_date(self.db, sc, date)

        assert_equals(len(outdata), (dusk - dawn) / 300)

        dtdawn = datetime.time(8, tzinfo=sc.timezone())
        dtdawn = datetime.datetime.combine(date, dtdawn)

        for i, (dt, y) in enumerate(outdata):
            xdt = dtdawn + datetime.timedelta(minutes=5*i)
            assert_equals(dt, xdt)
            assert_equals(y, i + 12345)
