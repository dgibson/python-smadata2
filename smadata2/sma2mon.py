#! /usr/bin/env python
#
# smadata2.sma2mon - Top-level script
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

import sys
import argparse
import time
import os.path
import datetime
import dateutil.parser

import smadata2.config
import smadata2.db.sqlite
import smadata2.datetimeutil
import smadata2.download
import smadata2.upload


def status(config, args):
    for system in config.systems():
        print("%s:" % system.name)

        for inv in system.inverters():
            print("\t%s:" % inv.name)

            sma = inv.connect_and_logon()

            dtime, daily = sma.daily_yield()
            print("\t\tDaily generation at %s:\t%d Wh"
                  % (smadata2.datetimeutil.format_time(dtime), daily))

            ttime, total = sma.total_yield()
            print("\t\tTotal generation at %s:\t%d Wh"
                  % (smadata2.datetimeutil.format_time(ttime), total))

def record_now(config, args):
    db = config.database()
    for system in config.systems():
        for inv in system.inverters():
            sma = inv.connect_and_logon()
            ttime, total = sma.total_yield()
            timestamp = int(time.time())

            db.add_historic(inv.serial, timestamp, total)

    db.commit()

def upload_energy(config, args):
    uploader = config.energy_uploader()
    db = config.database()
    for system in config.systems():
        for inv in system.inverters():
            uploader.upload_missing(inv)

def yieldat(config, args):
    db = config.database()

    if args.datetime is None:
        print("No date specified", file=sys.stderr)
        sys.exit(1)

    dt = dateutil.parser.parse(args.datetime)

    for system in config.systems():
        print("%s:" % system.name)

        if dt.tzinfo is None:
            sdt = datetime.datetime(dt.year, dt.month, dt.day,
                                    dt.hour, dt.minute, dt.second,
                                    dt.microsecond, tzinfo=system.timezone())
        else:
            sdt = dt

        ts = smadata2.datetimeutil.totimestamp(sdt)
        ids = [inv.serial for inv in system.inverters()]

        val = db.get_aggregate_one_historic(ts, ids)
        print("\tTotal generation at %s: %d Wh" % (sdt, val))


def download(config, args):
    db = config.database()

    for system in config.systems():
        for inv in system.inverters():
            print("%s (SN: %s)" % (inv.name, inv.serial))

            ic = inv.connect_and_logon()

            data = smadata2.download.download_inverter(ic, db)
            if len(data):
                print("Downloaded %d observations from %s to %s"
                      % (len(data),
                         smadata2.datetimeutil.format_time(data[0][0]),
                         smadata2.datetimeutil.format_time(data[-1][0])))
            else:
                print("No new data")


def upload(config, args):
    db = config.database()

    if args.upload_date is None:
        print("No date specified", file=sys.stderr)
        sys.exit(1)

    d = dateutil.parser.parse(args.upload_date).date()

    print("Uploading data for %s" % d)

    for system in config.systems():
        print("%s" % system.name)
        smadata2.upload.upload_date(system, d, db)


def setupdb(config, args):
    dbname = config.dbname
    if not os.path.exists(dbname):
        print("Creating database '%s'..." % dbname)
    else:
        print("Updating database schema for '%s'..." % dbname)
    try:
        smadata2.db.sqlite.create_or_update(config.dbname)
    except smadata2.db.WrongSchema as e:
        print(e)


def argparser():
    parser = argparse.ArgumentParser(description="Work with Bluetooth enabled"
                                     + " SMA photovoltaic inverters")

    parser.add_argument("--config")

    subparsers = parser.add_subparsers()

    parse_status = subparsers.add_parser("status", help="Read inverter status")
    parse_status.set_defaults(func=status)

    parse_record_now = subparsers.add_parser("record_now", help="Read current inverter totals and "
                                             "write them to the database. (ignoring inverter time)")
    parse_record_now.set_defaults(func=record_now)

    parse_upload_energy = subparsers.add_parser("upload_energy", help="Upload entries to energy.nur-jan.de "
                                                "that have not yet been uploaded")
    parse_upload_energy.set_defaults(func=upload_energy)

    parse_yieldat = subparsers.add_parser("yieldat", help="Get production at"
                                          " a given date")
    parse_yieldat.set_defaults(func=yieldat)
    parse_yieldat.add_argument(type=str, dest="datetime")

    parse_download = subparsers.add_parser("download",
                                           help="Download power history"
                                           + " and record in database")
    parse_download.set_defaults(func=download)

    parse_setupdb = subparsers.add_parser("setupdb", help="Create database or"
                                          + " update schema")
    parse_setupdb.set_defaults(func=setupdb)

    parse_upload_date = subparsers.add_parser("upload", help="Upload"
                                              " power history to pvoutput.org")
    parse_upload_date.set_defaults(func=upload)
    parse_upload_date.add_argument("--date", type=str, dest="upload_date")

    return parser


def main(argv=sys.argv):
    parser = argparser()
    args = parser.parse_args(argv[1:])

    config = smadata2.config.SMAData2Config(args.config)

    args.func(config, args)


if __name__ == '__main__':
    main()
