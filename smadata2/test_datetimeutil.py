#! /usr/bin/env python

import StringIO
import os.path
import unittest
import time
import datetime
import dateutil.tz

from nose.tools import *

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
