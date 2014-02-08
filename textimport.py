#! /usr/bin/env python

from __future__ import print_function

import sys
import re
import btsmautil
import btsmadb

dbname, serial, datafile = sys.argv[1:]

db = btsmadb.BTSMADatabaseSQLiteV0(dbname)
serial = int(serial)
f = open(datafile)

pre = re.compile('(.*?): Total generation ([0-9]+)')

n_lines, n_added = 0, 0

for l in f.xreadlines():
    n_lines += 1
    m = pre.match(l)
    timestamp = btsmautil.parse_time(m.group(1))
    total = int(m.group(2))
    if total == 0xffffffff:
        continue
    xtotal = db.get_one_historic(serial, timestamp)
    if xtotal is not None:
        if xtotal != total:
            raise ValueError
        continue

    db.add_historic(serial, timestamp, total)
    n_added += 1

db.commit()
print("Added %d new entries from %d lines" % (n_added, n_lines))

