#! /usr/bin/python3
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

import time

from .db import SAMPLE_INV_FAST, SAMPLE_INV_DAILY


def download_type(ic, db, sample_type, data_fn):
    lasttime = db.get_last_sample(ic.serial, sample_type)
    if lasttime is None:
        lasttime = ic.starttime

    now = int(time.time())

    data = data_fn(lasttime + 1, now)

    for timestamp, total in data:
        db.add_sample(ic.serial, timestamp, sample_type, total)

    return data


def download_inverter(ic, db):
    sma = ic.connect_and_logon()

    data = download_type(ic, db, SAMPLE_INV_FAST, sma.historic)
    data_daily = download_type(ic, db, SAMPLE_INV_DAILY, sma.historic_daily)

    db.commit()

    return (data, data_daily)
