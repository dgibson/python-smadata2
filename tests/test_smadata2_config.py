#! /usr/bin/env python

import StringIO
import os.path
import unittest

from nose.tools import *
from smadata2.config import *

class TestMinimal(object):
    def setUp(self):
        self.c = SMAData2Config(StringIO.StringIO("{}"))

    def test_dbname(self):
        assert_equals(self.c.dbname, os.path.expanduser("~/.btsmadb.v0.sqlite"))

    def test_systems(self):
        assert_equals(self.c.systems(), [])
