#! /usr/bin/env python

from nose.tools import *

import smadata2.pvoutputorg


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
