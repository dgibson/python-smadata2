#! /usr/bin/env python

import os

from nose.tools import *
from smadata2.db import *

class TestDB(object):
    def setUp(self):
        self.dbname = "__testdb__smadata2_%s_.sqlite" % self.__class__.__name__
        self.db = SMADatabaseSQLiteV0.create(self.dbname)

    def tearDown(self):
        os.remove(self.dbname)

    def test_trivial(self):
        assert isinstance(self.db, SMADatabaseSQLiteV0)
