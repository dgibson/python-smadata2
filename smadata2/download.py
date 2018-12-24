#! /usr/bin/env python
#
# smadata2.download - Routines to download from an inverter to database
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
import time


def download_inverter(ic, db):
    lasttime = db.get_last_historic(ic.serial)
    if lasttime is None:
        lasttime = ic.starttime

    now = int(time.time())

    sma = ic.connect_and_logon()

    data = sma.historic(lasttime+1, now)

    for timestamp, total in data:
        db.add_historic(ic.serial, timestamp, total)

    db.commit()

    return data
