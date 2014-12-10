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

import smadata2.config
import smadata2.db.sqlite
import smadata2.util


def status(config, args):
    for system in config.systems():
        print("%s:" % system.name)

        for inv in system.inverters():
            print("\t%s:" % inv.name)

            sma = inv.connect_and_logon()

            dtime, daily = sma.daily_yield()
            print("\t\tDaily generation at %s:\t%d Wh"
                  % (smadata2.util.format_time(dtime), daily))

            ttime, total = sma.total_yield()
            print("\t\tTotal generation at %s:\t%d Wh"
                  % (smadata2.util.format_time(ttime), total))


def download(config, args):
    db = config.database()

    for system in config.systems():
        for inv in system.inverters():
            print("%s (SN: %s)" % (inv.name, inv.serial))

            lasttime = db.get_last_historic(inv.serial)
            if lasttime is None:
                lasttime = inv.starttime

            now = int(time.time())

            print("Retrieving data from %s to %s"
                  % (smadata2.util.format_time(lasttime),
                     smadata2.util.format_time(now)))

            sma = inv.connect_and_logon()

            data = sma.historic(lasttime+1, now)
            if len(data):
                print("Downloaded %d observations from %s to %s"
                      % (len(data), smadata2.util.format_time(data[0][0]),
                         smadata2.util.format_time(data[-1][0])))
            else:
                print("No new data")

            for timestamp, total in data:
                db.add_historic(inv.serial, timestamp, total)

            db.commit()


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

    parse_download = subparsers.add_parser("download",
                                           help="Download power history"
                                           + " and record in database")
    parse_download.set_defaults(func=download)

    parse_setupdb = subparsers.add_parser("setupdb", help="Create database or"
                                          + " update schema")
    parse_setupdb.set_defaults(func=setupdb)

    return parser


def main(argv=sys.argv):
    parser = argparser()
    args = parser.parse_args(argv[1:])

    config = smadata2.config.SMAData2Config(args.config)

    args.func(config, args)


if __name__ == '__main__':
    main()
