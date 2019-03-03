#! /usr/bin/python3
#
# smadata2.db.base - Abstract database interface
# Copyright (C) 2014 David Gibson <david@gibson.dropbear.id.au>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import abc

# Ad hoc samples, externally controlled
SAMPLE_ADHOC = 0
# Inverter recorded high(ish) frequency samples
SAMPLE_INV_FAST = 1
# Inverted recorded daily samples
SAMPLE_INV_DAILY = 2

SAMPLETYPES = [SAMPLE_ADHOC, SAMPLE_INV_FAST, SAMPLE_INV_DAILY]

all = ['Error', 'WrongSchema', 'StaleResults',
       'STALE_SECONDS',
       'SAMPLE_ADHOC', 'SAMPLE_INV_FAST', 'SAMPLE_INV_DAILY',
       'SAMPLETYPES']


class Error(Exception):
    pass


class WrongSchema(Error):
    pass


# For yieldat, complain if we can't find results less than a day old
STALE_SECONDS = 24*60*60

class StaleResults(Error):
    pass


class BaseDatabase(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_sample(self, serial, timestamp, sample_type, total_yield):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_one_sample(self, serial, timestamp):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_last_sample(self, serial, sample_type=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_aggregate_one_sample(self, ts, ids):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_aggregate_samples(self, from_ts, to_ts, ids):
        raise NotImplementedError()
