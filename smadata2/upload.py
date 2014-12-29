#! /usr/bin/env python
#
# smadata2.upload - Routines to upload information to pvoutput.org
# Copyright (C) 2014 David Gibson <david@gibson.dropbear.id.au>
# Copyright (C) 2014 Peter Barker <pbarker@barker.dropbear.id.au>
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

from __future__ import print_function

import datetimeutil


def trim_date(results):
    """Remove the non-generating periods from the beginning and end of day's
    generation results"""


    while len(results) > 1:
        if results[0][1] == results[1][1]:
            # the next data point is the same as the first datapoint:
            results.pop(0)
        else:
            break

    while len(results) > 1:
        if results[-1][1] == results[-2][1]:
            # last datapoint == second last datapoint
            results.pop()
        else:
            break


def upload_date(sc, date, db):
    ts_start, ts_end = datetimeutil.day_timestamps(date, sc.timezone())

    ids = [i.serial for i in sc.inverters()]

    results = db.get_aggregate_historic(ts_start, ts_end, ids)
    trim_date(results)

    for ts, y in results:
        print("%s: %d Wh" % (datetimeutil.format_time(ts), y))
