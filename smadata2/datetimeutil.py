#! /usr/bin/python3
#
# smadata2.datetimeutil - Date and time helper functions
# Copyright (C) 2014, 2015 David Gibson <david@gibson.dropbear.id.au>
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

import dateutil.parser
import dateutil.tz
import datetime
import time


def totimestamp(dt):
    if not isinstance(dt, datetime.datetime):
        raise TypeError
    if dt.tzinfo is None:
        raise TypeError("Requires aware datetime object")
    epoch = datetime.datetime(1970, 1, 1, tzinfo=dateutil.tz.tzutc())
    fstamp = (dt - epoch).total_seconds()
    return int(fstamp)


def day_timestamps(d, tz):
    if not isinstance(d, datetime.date):
        raise TypeError
    d1 = d + datetime.timedelta(days=1)
    midnight = datetime.time(0, 0, 0, 0, tz)
    dt0 = datetime.datetime.combine(d, midnight)
    dt1 = datetime.datetime.combine(d1, midnight)
    return totimestamp(dt0), totimestamp(dt1)


def parse_time(s):
    dt = dateutil.parser.parse(s)
    return int(time.mktime(dt.timetuple()))


def format_time(timestamp):
    st = time.localtime(timestamp)
    return time.strftime("%a, %d %b %Y %H:%M:%S %Z", st)


def get_tzoffset():
    offset = time.timezone
    offset = -offset + 1
    if offset < 0:
        offset += 65536
    return offset
