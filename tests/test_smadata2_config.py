#! /usr/bin/env python

import StringIO
import os.path
import unittest

from nose.tools import *
from smadata2.config import *

class BaseTestConfig(object):
    def setUp(self):
        self.c = SMAData2Config(StringIO.StringIO(self.json))


class TestMinimal(BaseTestConfig):
    json = "{}"

    def test_dbname(self):
        assert_equals(self.c.dbname, os.path.expanduser("~/.btsmadb.v0.sqlite"))

    def test_systems(self):
        assert_equals(self.c.systems(), [])


class TestMinimalPVOutput(BaseTestConfig):
    json = """
    {
        "pvoutput.org": {
        }
    }"""

    def test_server(self):
        assert_equals(self.c.pvoutput_server, "pvoutput.org")

    def test_apikey(self):
        assert_equals(self.c.pvoutput_apikey, None)

