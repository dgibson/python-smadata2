#! /usr/bin/env python

import datetime

from nose.tools import *

import smadata2.pvoutputorg


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
    return (script, frozenset(args.items()))


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
