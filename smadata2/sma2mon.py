#! /usr/bin/python3
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

import sys
import argparse
import os.path
import datetime
import dateutil.parser
import time

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

            try:
                sma = inv.connect_and_logon()

                dtime, daily = sma.daily_yield()
                print("\t\tDaily generation at %s:\t%d Wh"
                      % (smadata2.datetimeutil.format_time(dtime), daily))

                ttime, total = sma.total_yield()
                print("\t\tTotal generation at %s:\t%d Wh"
                      % (smadata2.datetimeutil.format_time(ttime), total))
            except Exception as e:
                print("ERROR contacting inverter: %s" % e, file=sys.stderr)


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

        val = db.get_yield_at(ts, ids)
        print("\tTotal generation at %s: %d Wh" % (sdt, val))


def download(config, args):
    db = config.database()

    for system in config.systems():
        for inv in system.inverters():
            print("%s (SN: %s)" % (inv.name, inv.serial))

            try:
                data, daily = smadata2.download.download_inverter(inv, db)
                if len(data):
                    print("Downloaded %d observations from %s to %s"
                          % (len(data),
                             smadata2.datetimeutil.format_time(data[0][0]),
                             smadata2.datetimeutil.format_time(data[-1][0])))
                else:
                    print("No new fast sampled data")
                if len(daily):
                    print("Downloaded %d daily observations from %s to %s"
                          % (len(daily),
                             smadata2.datetimeutil.format_time(daily[0][0]),
                             smadata2.datetimeutil.format_time(daily[-1][0])))
                else:
                    print("No new daily data")
            except Exception as e:
                print("ERROR downloading inverter: %s" % e, file=sys.stderr)


def settime(config, args):
    for system in config.systems():
        for inv in system.inverters():
            print("%s (SN: %s)" % (inv.name, inv.serial))
            try:
                sma = inv.connect_and_logon()

                oldtime, tmp = sma.total_yield()
                print("\t\tPrevious time: %s"
                      % (smadata2.datetimeutil.format_time(oldtime)))

                newts = int(time.time())
                newtz = smadata2.datetimeutil.get_tzoffset()
                print("\t\tNew time: %s (TZ %d)"
                      % (smadata2.datetimeutil.format_time(newts), newtz))

                sma.set_time(newts, newtz)

                newtime, tmp = sma.total_yield()
                print("\t\tUpdated time: %s"
                      % (smadata2.datetimeutil.format_time(newtime)))
            except Exception as e:
                print("ERROR contacting inverter: %s" % e, file=sys.stderr)


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
    parser = argparse.ArgumentParser(description="Work with Bluetooth"
                                     " enabled SMA photovoltaic inverters")

    parser.add_argument("--config")

    subparsers = parser.add_subparsers()

    parse_status = subparsers.add_parser("status", help="Read inverter status")
    parse_status.set_defaults(func=status)

    help = "Get production at a given date"
    parse_yieldat = subparsers.add_parser("yieldat", help=help)
    parse_yieldat.set_defaults(func=yieldat)
    parse_yieldat.add_argument(type=str, dest="datetime")

    help = "Download power history and record in database"
    parse_download = subparsers.add_parser("download", help=help)
    parse_download.set_defaults(func=download)

    help = "Create database or update schema"
    parse_setupdb = subparsers.add_parser("setupdb", help=help)
    parse_setupdb.set_defaults(func=setupdb)

    help = "Update inverters' clocks"
    parse_settime = subparsers.add_parser("settime", help=help)
    parse_settime.set_defaults(func=settime)

    help = "Upload power history to pvoutput.org"
    parse_upload_date = subparsers.add_parser("upload", help=help)
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
