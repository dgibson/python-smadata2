#! /usr/bin/python3
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

import datetime
from . import datetimeutil


def prepare_data_for_date(date, data, tz):
    """Translate a day's data from the database format to be ready for upload
    to pvoutput.org"""

    # First trim the non-generating periods from the beginning and end
    while len(data) > 1:
        if data[0][1] == data[1][1]:
            # the next data point is the same as the first datapoint:
            data.pop(0)
        else:
            break

    while len(data) > 1:
        if data[-1][1] == data[-2][1]:
            # last datapoint == second last datapoint
            data.pop()
        else:
            break

    # Now convert the timestamps to datetime objects
    output = [(datetime.datetime.fromtimestamp(ts, tz), y) for ts, y in data]

    # Sanity check
    assert all(dt.date() == date for dt, y in output)

    return output


def load_data_for_date(db, sc, date):
    ts_start, ts_end = datetimeutil.day_timestamps(date, sc.timezone())

    ids = [i.serial for i in sc.inverters()]

    results = db.get_aggregate_samples(ts_start, ts_end, ids)
    return prepare_data_for_date(date, results, sc.timezone())


def upload_date(db, sc, date):
    data = load_data_for_date(db, sc, date)

    for ts, y in data:
        print("%s: %d Wh" % (datetimeutil.format_time(ts), y))
