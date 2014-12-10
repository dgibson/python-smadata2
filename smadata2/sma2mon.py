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

import smadata2.config
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


def argparser():
    parser = argparse.ArgumentParser(description="Work with Bluetooth enabled"
                                     + " SMA photovoltaic inverters")

    parser.add_argument("--config")

    subparsers = parser.add_subparsers()

    parse_status = subparsers.add_parser("status", help="Read inverter status")
    parse_status.set_defaults(func=status)

    return parser


def main(argv=sys.argv):
    parser = argparser()
    args = parser.parse_args(argv[1:])

    config = smadata2.config.SMAData2Config(args.config)

    args.func(config, args)


if __name__ == '__main__':
    main()
