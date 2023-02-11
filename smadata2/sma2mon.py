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
import argparse     #see https://docs.python.org/3/howto/argparse.html
import os.path
import datetime
import dateutil.parser
import time

import logging.config
log = logging.getLogger(__name__)  # once in each module
import csv

import smadata2.config
import smadata2.db.sqlite
import smadata2.datetimeutil
import smadata2.download
import smadata2.upload
from smadata2.datetimeutil import format_time

import web_pdb

def status(config, args):
    for system in config.systems():
        config.log.info("%s:" % system.name)

        for inv in system.inverters():
            config.log.info("\t%s:" % inv.name)
            #web_pdb.set_trace()

            try:
                sma = inv.connect_and_logon()
                dtime, daily = sma.daily_yield()
                config.log.info("\tDaily generation at %s:\t%d Wh"
                      % (smadata2.datetimeutil.format_time(dtime), daily))

                ttime, total = sma.total_yield()
                config.log.info("\tTotal generation at %s:\t%d Wh"
                       % (smadata2.datetimeutil.format_time(ttime), total))
            except Exception as e:
                config.log.error("sma2mon ERROR contacting inverter: %s" % e, file=sys.stderr)


def yieldat(config, args):
    """Get production at a given date
    
    :param config: Config from json file
    :param args: command line arguments, including datetime
    :return: prints val, the aggregate for the provided date
    """
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

        details = db.get_yield_at_details(ts, ids)

        for inv in system.inverters():
            iyield, its = details[inv.serial]
            print("\t\t{}: {} Wh @ {}".format(inv.name,
                                               iyield,
                                               smadata2.datetimeutil.format_time(its)))

        sys.stdout.flush()
        val = db.get_yield_at(ts, ids)

        print("\tTotal generation at %s: %d Wh" % (sdt, val))

def historic_daily(config, args):
    db = config.database()

    if args.fromdate is None:
        print("No date specified", file=sys.stderr)
        sys.exit(1)

    fromdate = dateutil.parser.parse(args.fromdate)
    todate = dateutil.parser.parse(args.todate)
    fromtime = int(fromdate.timestamp())
    totime = int(todate.timestamp())

    for system in config.systems():
        print("%s:" % system.name)

        for inv in system.inverters():
            print("\t%s:" % inv.name)
            # web_pdb.set_trace()

            try:
                sma = inv.connect_and_logon()

                # dtime, daily = sma.historic_daily()
                # print("\t\tDaily generation at %s:\t%d Wh"
                # % (smadata2.datetimeutil.format_time(dtime), daily))
                hlist = sma.historic_daily(fromtime, totime)
                for timestamp, val in hlist:
                    print("[%d] %s: Total generation %d Wh"
                          % (timestamp, format_time(timestamp), val))
                # ttime, total = sma.total_yield()
                # print("\t\tTotal generation at %s:\t%d Wh"
                # % (smadata2.datetimeutil.format_time(ttime), total))
            except Exception as e:
                print("ERROR contacting inverter: %s" % e, file=sys.stderr)

def sma_request(config, args):
    """Get spot data from the inverters

    :param config: configuration file
    :param args:  command line args, identify the type of data requested, like 'SpotACVoltage'
    """
    db = config.database()

    for system in config.systems():
        print("%s:" % system.name)

        for inv in system.inverters():
            print("\t%s:" % inv.name)
            # web_pdb.set_trace()

            # try:
            sma = inv.connect_and_logon()
            hlist = sma.sma_request(args.request_name)
            for index, uom, timestamp, val1, val2, val3, val4, unknown, data_type, divisor in hlist:
                # print("%s: %f %f %f %s %s" % (format_time(timestamp), val1 / 100, val2 / 100, val3 / 100, unknown, data_type))
                print("{0} {1}: {2:10.3f} {3:10.3f} {4:10.3f} {6}".format(data_type, index, val1 / divisor, val2 / divisor, val3 / divisor, unknown, uom))
            # except Exception as e:
            #     print("ERROR contacting inverter: %s" % e, file=sys.stderr)

def sma_info_request(config, args):
    """Get other information from the inverters, like model, type, dates, status

    todo - does this write to a database, so structure into key-value pairs or similar
    :param config: configuration file
    :param args:  command line args, identify the type of data requested, like 'model'
    """
    db = config.database()

    for system in config.systems():
        print("%s:" % system.name)

        for inv in system.inverters():
            print("\t%s:" % inv.name)
            # web_pdb.set_trace()

            # try:
            sma = inv.connect_and_logon()
            hlist = sma.sma_request(args.request_name)
            print(hlist)
            #for index, uom, timestamp, val1, val2, val3, val4, unknown, data_type, divisor in hlist:
                # print("%s: %f %f %f %s %s" % (format_time(timestamp), val1 / 100, val2 / 100, val3 / 100, unknown, data_type))
            #    print("{0} {1}: {2:10.3f} {3:10.3f} {4:10.3f} {6}".format(data_type, index, val1 / divisor, val2 / divisor, val3 / divisor, unknown, uom))
                # print("{0}: {1:.3f} {2:.3f} {3:.3f} {4:.3f} {5}".format(format_time(timestamp), val1 / 100, val2 / 100, val3 / 100, unknown, uom))
            # except Exception as e:
            #     print("ERROR contacting inverter: %s" % e, file=sys.stderr)


def spotacvoltage(config, args):
    db = config.database()

    for system in config.systems():
        print("%s:" % system.name)

        for inv in system.inverters():
            print("\t%s:" % inv.name)
            # web_pdb.set_trace()

            try:
                sma = inv.connect_and_logon()

                # dtime, daily = sma.historic_daily()
                # print("\t\tDaily generation at %s:\t%d Wh"
                # % (smadata2.datetimeutil.format_time(dtime), daily))
                hlist = sma.spotacvoltage()
                # for val in hlist:
                # print("[%d] : Raw value %d" % (val))
                for index, uom, timestamp, val1, val2, val3, val4, unknown, data_type, divisor in hlist:
                    # print("%s: %f %f %f %s %s" % (format_time(timestamp), val1 / 100, val2 / 100, val3 / 100, unknown, data_type))
                    print("{0} {1}: {2:10.3f} {3:10.3f} {4:10.3f} {6}".format(data_type, index, val1 / divisor, val2 / divisor, val3 / divisor, unknown, uom))
                    # print("{0}: {1:.3f} {2:.3f} {3:.3f} {4:.3f} {5}".format(format_time(timestamp), val1 / 100, val2 / 100, val3 / 100, unknown, uom))
                # for timestamp, val in hlist:
                    # print("[%d] %s: Spot AC voltage %d Wh" % (timestamp, format_time(timestamp), val))
                # ttime, total = sma.total_yield()
                # print("\t\tTotal generation at %s:\t%d Wh"
                # % (smadata2.datetimeutil.format_time(ttime), total))
            except Exception as e:
                print("ERROR contacting inverter: %s" % e, file=sys.stderr)

def download(config, args):
    """Download power history and record in database
    
    :param config: Config from json file
    :param args: command line arguments, not used
    :return: prints observations qty, from, to or error
    """
    db = config.database()

    for system in config.systems():
        for inv in system.inverters():
            print("%s (SN: %s)" % (inv.name, inv.serial))
            print("starttime: %s" % (inv.starttime))

            #try:
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
            #except Exception as e:
             #   print("ERROR downloading inverter: %s" % e, file=sys.stderr)

# AF updated by DGibson Sept 2019
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


def yieldlog(config, args):
    db = config.database()

    if args.start is None:
        print("No start date specified", file=sys.stderr)
        sys.exit(1)

    if args.end is None:
        print("No end date specified", file=sys.stderr)
        sys.exit(1)

    start = dateutil.parser.parse(args.start)
    end = dateutil.parser.parse(args.end)

    l = [s for s in config.systems() if s.name.find(args.system) >= 0]
    if len(l) != 1:
        print("Must specify exactly one system", file=sys.stderr)
        sys.exit(1)

    system = l[0]

    if start.tzinfo is None:
        start = datetime.datetime(start.year, start.month, start.day,
                                  start.hour, start.minute, start.second,
                                  start.microsecond, tzinfo=system.timezone())
    start_ts = smadata2.datetimeutil.totimestamp(start)

    if end.tzinfo is None:
        end = datetime.datetime(end.year, end.month, end.day,
                                end.hour, end.minute, end.second,
                                end.microsecond, tzinfo=system.timezone())
    end_ts = smadata2.datetimeutil.totimestamp(end)

    if args.csv:
        csvf = csv.writer(sys.stdout)
    else:
        print("{}: {} ({}) .. {} ({})".format(system.name,
                                              start, start_ts,
                                              end, end_ts))

    ids = [inv.serial for inv in system.inverters()]
    data = db.get_daily_yields(start_ts, end_ts, ids)
    if args.csv:
        csvf.writerow(["Date"] + [inv.name for inv in system.inverters()])
    else:
        print("Date\t\t\t" + "\t".join(inv.name for inv in system.inverters()))
    for row in data:
        if args.csv:
            ds = time.strftime(time.strftime("%Y-%m-%d", time.localtime(row[0])))
            csvf.writerow((ds,) + row[1:])
        else:
            print(smadata2.datetimeutil.format_date(row[0]) + "\t"
                  + "\t".join(str(y) for y in row[1:]))

#return smabluetooth.Connection(self.bdaddr)

def scan(config, args):
    try:
        smadata2.inverter.smabluetooth.get_devices()
    except:
        print("Scan failed")


def argparser():
    """Creates argparse object for the application, imported lib

    - ArgumentParser -- The main entry point for command-line parsing. As the
        example above shows, the add_argument() method is used to populate
        the parser with actions for optional and positional arguments. Then
        the parse_args() method is invoked to convert the args at the
        command-line into an object with attributes.

    Extend this for new arguments with an entry below, a corresponding display/database function above,
    and a corresponding function in smabluetooth that gets data from the inverter

    :return: parser: ArgumentParser object, used by main
    """
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

    help = "Get historic production for a date range"
    parse_historic_daily = subparsers.add_parser("historic_daily", help=help)
    parse_historic_daily.set_defaults(func=historic_daily)
    parse_historic_daily.add_argument(type=str, dest="fromdate")
    parse_historic_daily.add_argument(type=str, dest="todate")

    help = "Get spot AC voltage now."
    parse_spotac = subparsers.add_parser("spotacvoltage", help=help)
    parse_spotac.set_defaults(func=spotacvoltage)

    help = "Get spot reading by name (SpotACVoltage, ..) from sma_request_type ."
    parse_sma_request = subparsers.add_parser("spot", help=help)
    parse_sma_request.set_defaults(func=sma_request)
    parse_sma_request.add_argument(type=str, dest="request_name")

    help = "Get device Info by name (TypeLabel, ..) from sma_request_type ."
    parse_sma_info_request = subparsers.add_parser("info", help=help)
    parse_sma_info_request.set_defaults(func=sma_info_request)
    parse_sma_info_request.add_argument(type=str, dest="request_name")

    help = "Scan for bluetooth devices."
    parse_scan = subparsers.add_parser("scan", help=help)
    parse_scan.set_defaults(func=scan)

    help = "Get daily production totals"
    parse_yieldlog = subparsers.add_parser("yieldlog", help=help)
    parse_yieldlog.set_defaults(func=yieldlog)
    parse_yieldlog.add_argument(type=str, dest="start")
    parse_yieldlog.add_argument(type=str, dest="end")
    parse_yieldlog.add_argument("--system", type=str, dest="system", default="")
    parse_yieldlog.add_argument("--csv", action='store_true', dest="csv")

    return parser

def ptime(str):
    return int(time.mktime(time.strptime(str, "%Y-%m-%d")))

def main(argv=sys.argv):

    parser = argparser()
    args = parser.parse_args(argv[1:])      #args is a Namespace for command line args
    #log.debug("Startup with args: ", args)

    # creates config object, using an optional file supplied on the command line
    config = smadata2.config.SMAData2Config(args.config)
    # calls
    args.func(config, args)


if __name__ == '__main__':
    #log = logging.getLogger(__name__)  # once in each module
    main()
