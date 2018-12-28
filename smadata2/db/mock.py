#! /usr/bin/python3
#
# smadata2.db - Database for logging data from SMA inverters
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

from .base import BaseDatabase


class MockDatabase(BaseDatabase):
    def __init__(self):
        super(MockDatabase, self).__init__()
        self.samples = set()

    def add_sample(self, serial, timestamp, sample_type, total_yield):
        self.samples.add((serial, timestamp, total_yield))

    def get_one_sample(self, serial, timestamp):
        for s, t, y in self.samples:
            if (s == serial) and (t == timestamp):
                return y
        return None

    def get_last_sample(self, serial, sample_type=None):
        stamps = set(t for s, t, y in self.samples)
        if stamps:
            return max(stamps)
        else:
            return None

    def get_aggregate_one_sample(self, ts, ids):
        vals = set(y for s, t, y in self.samples
                   if (t == ts) and (s in ids))
        return sum(vals)

    def get_aggregate_samples(self, from_ts, to_ts, ids):
        rd = {}
        for s, t, y in self.samples:
            if (s in ids) and (t >= from_ts) and (t < to_ts):
                if t not in rd:
                    rd[t] = y
                else:
                    rd[t] += y
        rl = []
        for t in sorted(rd.keys()):
            rl.append((t, rd[t]))
        return rl
