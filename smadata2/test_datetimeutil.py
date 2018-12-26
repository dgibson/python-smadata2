#! /usr/bin/python3

import datetime
import dateutil.tz

from nose.tools import assert_equals, raises

import smadata2.datetimeutil


def test_totimestamp():
    tz = dateutil.tz.gettz("Australia/Sydney")
    dt = datetime.datetime(2014, 12, 28, 12, 20, 8, 0, tz)
    assert_equals(smadata2.datetimeutil.totimestamp(dt), 1419729608)


# Make sure naive datetimes give an error
@raises(TypeError)
def test_naive_totimestamp():
    dt = datetime.datetime(1987, 11, 5)
    ts = smadata2.datetimeutil.totimestamp(dt)


def test_daytimestamps_utc():
    d = datetime.date(1970, 1, 1)
    tst = smadata2.datetimeutil.day_timestamps(d, dateutil.tz.tzutc())
    assert_equals(tst, (0, 86400))


def test_daytimestamps_local():
    d = datetime.date(2014, 6, 6)
    tz = dateutil.tz.gettz("Australia/Sydney")
    tst = smadata2.datetimeutil.day_timestamps(d, tz)
    assert_equals(tst, (1401976800, 1401976800 + 24*60*60))


def test_daytimestamps_dstend():
    d = datetime.date(2014, 4, 6)
    tz = dateutil.tz.gettz("Australia/Sydney")
    tst = smadata2.datetimeutil.day_timestamps(d, tz)
    assert_equals(tst, (1396702800, 1396702800 + 25*60*60))


def test_daytimestamps_dstbegin():
    d = datetime.date(2014, 10, 5)
    tz = dateutil.tz.gettz("Australia/Sydney")
    tst = smadata2.datetimeutil.day_timestamps(d, tz)
    assert_equals(tst, (1412431200, 1412431200 + 23*60*60))
