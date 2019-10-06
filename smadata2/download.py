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
    """Gets a data set from the inverter, fast or daily samples, using the provided data_fn, 
    
    Checks the database for last sample time, and then passes to the data_fn
    the data_fn does all the work to query the inverter and parse the packets
    data_fn is from smabluetooth, is one of (sma.historic, sma.historic_daily..)
    Timestamps are int like 1548523800 (17/02/2019)
    
    :param ic: inverter 
    :param db: sqlite database object
    :param sample_type:  fast or daily samples, SAMPLE_INV_FAST, SAMPLE_INV_DAILY defined in db class 
    :param data_fn: calling function, like data_fn = <bound method Connection.historic of <smadata2.inverter.smabluetooth.Connection 
    :return: data: a list of (timestamp, reading) pairs; can be 100s of samples
    """
    lasttime = db.get_last_sample(ic.serial, sample_type)
    #when database is initial (empty) there is no last sample, so get from the c0nfig file
    if lasttime is None:
        # this starttime is not defined in the json example
        lasttime = ic.starttime

    now = int(time.time())

    data = data_fn(lasttime + 1, now)   #get data for the specified interval, using specified function

    for timestamp, total in data:
        db.add_sample(ic.serial, timestamp, sample_type, total)

    return data


def download_inverter(ic, db):
    sma = ic.connect_and_logon()        #instance of the smabluetooth Connection class

    data = download_type(ic, db, SAMPLE_INV_FAST, sma.historic)
    data_daily = download_type(ic, db, SAMPLE_INV_DAILY, sma.historic_daily)

    db.commit()

    return (data, data_daily)
