#! /usr/bin/env python

import StringIO
import os.path
import unittest
import time
import datetime
import dateutil.tz

from nose.tools import *

import smadata2.upload
import smadata2.check


def test_prepare1():
    dawn = 8*3600
    dusk = 20*3600
    dayend = 24*3600

    data = smadata2.check.generate_linear(0, dawn, dusk, dayend, 0, 1)

    output = smadata2.upload.prepare_data_for_date(datetime.date(1970, 1, 1),
                                                   data, dateutil.tz.tzutc())

    dtdawn = datetime.datetime(1970, 1, 1, 8, tzinfo=dateutil.tz.tzutc())
    dtdusk = datetime.datetime(1970, 1, 1, 20, tzinfo=dateutil.tz.tzutc())

    assert_equals(len(output), ((dusk - dawn) / 300) + 1)
    for i, (dt, y) in enumerate(output):
        assert_equals(dt, dtdawn + datetime.timedelta(minutes=5*i))
        assert_equals(y, 300*i)

