#! /usr/bin/env python
#
# smadata2.db - Database for logging data from SMA inverters
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

from base import *

class SQLDatabase(BaseDatabase):
    def ph(self, query):
        return query % { "ph": self.placeholder }

    def commit(self):
        self.conn.commit()

    def add_historic(self, serial, timestamp, total_yield):
        c = self.conn.cursor()
        c.execute("INSERT INTO generation"
                  + " (inverter_serial, timestamp, total_yield)"
                  + self.ph(" VALUES (%(ph)s, %(ph)s, %(ph)s);"),
                  (serial, timestamp, total_yield))

    def get_one_historic(self, serial, timestamp):
        c = self.conn.cursor()
        c.execute(self.ph("SELECT total_yield FROM generation"
                          " WHERE inverter_serial = %(ph)s"
                          " AND timestamp = %(ph)s"), (serial, timestamp))
        r = c.fetchone()
        if r is not None:
            return r[0]

    def get_last_historic(self, serial):
        c = self.conn.cursor()
        c.execute(self.ph("SELECT max(timestamp) FROM generation"
                          " WHERE inverter_serial = %(ph)s"), (serial,))
        r = c.fetchone()
        return r[0]

    def get_aggregate_one_historic(self, ts, ids):
        c = self.conn.cursor()
        c.execute(self.ph("SELECT sum(total_yield) FROM generation"
                          " WHERE inverter_serial IN(" + ",".join(["%(ph)s"] * len(ids)) + ")"
                          " AND timestamp = %(ph)s"
                          " GROUP BY timestamp"), tuple(ids) + (ts,))
        r = c.fetchall()
        if not r:
            return None
        assert(len(r) == 1)
        return r[0][0]

    def get_aggregate_historic(self, from_ts, to_ts, ids):
        c = self.conn.cursor()
        c.execute(self.ph("SELECT timestamp, sum(total_yield) FROM generation"
                          " WHERE inverter_serial IN (" + ",".join(["%(ph)s"] * len(ids)) + ")"
                          + " AND timestamp >= %(ph)s AND timestamp < %(ph)s"
                          + " GROUP BY timestamp ORDER BY timestamp ASC"),
                  tuple(ids) + (from_ts, to_ts))
        return c.fetchall()

    # return midnights for each day in the database
    # @param serial the inverter seial number to retrieve midnights for
    # @return all midnights in database as datetime objects
    def midnights(self, inverters):
        c = self.conn.cursor()
        serials = ','.join(x.serial for x in inverters)
        c.execute(self.ph("SELECT distinct(timestamp) "
                          "FROM generation "
                          "WHERE inverter_serial  in (" + ",".join(["%(ph)s"] * len(serials)) + ") "
                          "AND timestamp % 86400 = 0 "
                          "ORDER BY timestamp ASC"), tuple(serials))
        r = c.fetchall()
        r = map(lambda x: datetime.datetime.utcfromtimestamp(x[0]), r)
        return r

    def get_datapoint_totals_for_day(self, inverters, start_datetime):
        c = self.conn.cursor()
        before_datetime = start_datetime + datetime.timedelta(days=1)
        start_unixtime = time.mktime(start_datetime.timetuple())
        before_unixtime = time.mktime(before_datetime.timetuple())
        serials = ','.join(x.serial for x in inverters)
        c.execute(self.ph("SELECT timestamp,sum(total_yield),count(inverter_serial) "
                          "FROM generation "
                          "WHERE inverter_serial in  (" + ",".join(["%(ph)s"] * len(serials)) + ") "
                          "AND timestamp >= %(ph)s and timestamp < %(ph)s "
                          "group by timestamp "
                          "ORDER BY timestamp ASC"), tuple(serials) + (start_unixtime, before_unixtime))
        r = c.fetchall()
        return r

    # fixed
    def get_entries(self, inverters, timestamp):
        c = self.conn.cursor()
        serials = ','.join(x.serial for x in inverters)
        c.execute(self.ph("SELECT timestamp,total_yield,inverter_serial "
                          "FROM generation "
                          "WHERE inverter_serial in (" + ",".join(["%(ph)s"] * len(serials)) + ") "
                          "AND timestamp = %(ph)s "
                          "ORDER BY timestamp DESC LIMIT %(ph)s"), tuple(serials) + (timestamp, 1))
        r = c.fetchall()
        if len(r) == 0:
            return None
        return r

    def get_productions_younger_than(self, inverters, timestamp):
        serials = map(lambda x: x.serial, inverters)
        c = self.conn.cursor()
        c.execute(self.ph("SELECT timestamp,total_yield,count(inverter_serial) "
                          "FROM generation "
                          "WHERE inverter_serial in (" + ",".join(["%(ph)s"] * len(serials)) + ") AND "
                          " timestamp > %(ph)s "
                          "group by timestamp "
                          "ORDER BY timestamp ASC"), tuple(serials) + (str(timestamp),))
        r = c.fetchall()
        return r

    def pvoutput_get_last_datetime_uploaded(self, sid):
        c = self.conn.cursor()
        c.execute(self.ph("SELECT last_datetime_uploaded "
                          "FROM pvoutput "
                          "WHERE sid = %(ph)s"), (sid,))
        r = c.fetchone()
        if r is None:
            return None
        return r[0]

    def energy_get_last_datetime_uploaded(self, sid):
        c = self.conn.cursor()
        c.execute(self.ph("SELECT last_datetime_uploaded "
                          "FROM energyupload "
                          "WHERE sid = %(ph)s"), (sid,))
        r = c.fetchone()
        if r is None:
            return 0
        return r[0]

    def pvoutput_maybe_init_system(self, sid):
        print(sid)
        c = self.conn.cursor()
        c.execute(self.ph("SELECT * FROM pvoutput WHERE sid = %(ph)s"),
                  (sid,))
        r = c.fetchone()
        if r is None:
            c = self.conn.cursor()
            c.execute("INSERT INTO pvoutput(sid) VALUES ( ? )",
                      (sid,))
            self.commit()

    def pvoutput_set_last_datetime_uploaded(self, sid, value):
        c = self.conn.cursor()
        self.pvoutput_maybe_init_system(sid)
        c.execute(self.ph("update pvoutput "
                          "SET last_datetime_uploaded = %(ph)s"
                          "WHERE sid = %(ph)s"), (value, sid))
        self.commit()

    def energy_set_last_datetime_uploaded(self, sid, value):
        c = self.conn.cursor()
        c.execute(self.ph("REPLACE INTO energyupload(sid, last_datetime_uploaded) "
                          "VALUES(%(ph)s, %(ph)s)"), (sid, value))
        self.commit()
