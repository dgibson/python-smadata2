#! /usr/bin/env python

import dateutil.parser
import time


def parse_time(s):
    dt = dateutil.parser.parse(s)
    return int(time.mktime(dt.timetuple()))


def format_time(timestamp):
    st = time.localtime(timestamp)
    return time.strftime("%a, %d %b %Y %H:%M:%S %Z", st)
