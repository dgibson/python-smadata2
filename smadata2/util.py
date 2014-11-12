#! /usr/bin/env python
#
# smadata2.util - Utility functions for SMAData2 code
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

from __future__ import print_function

import dateutil.parser
import time


def parse_time(s):
    dt = dateutil.parser.parse(s)
    return int(time.mktime(dt.timetuple()))


def format_time(timestamp):
    st = time.localtime(timestamp)
    return time.strftime("%a, %d %b %Y %H:%M:%S %Z", st)
