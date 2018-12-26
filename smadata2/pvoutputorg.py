#! /usr/bin/python3
#
# pvoutput.py - Poke pvoutput.org with data
# Copyright (C) 2014 Peter Barker <pbarker@barker.dropbear.id.au>
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
import urllib.request
import urllib.parse
import urllib.error
import time
import datetime


class Error(Exception):
    pass


def parse_date(pvodate):
    """ parse a date supplied by pvoutput.org
    @param pvoutput_date a date in pvoutput API form
    @return a date object
    """
    dt = datetime.datetime.strptime(pvodate, "%Y%m%d")
    return dt.date()


def parse_time(pvodate):
    """ parse a date supplied by pvoutput.org
    @param pvoutput_date a date in pvoutput API form
    @return a date object
    """
    dt = datetime.datetime.strptime(pvodate, "%H:%M")
    return dt.time()


# parse a date and time supplied by pvoutput.org
# @param pvoutput_date a date in pvoutput API form
# @param pvoutput_time a time in pvoutput API form
# @return a datetime object
def parse_datetime(pvodate, pvotime):
    return datetime.datetime.combine(parse_date(pvodate), parse_time(pvotime))


def format_date(d):
    """ format a date object into a format suitable for the pvoutput API
    @param d a date object
    @return a formatted date
    """
    return d.strftime("%Y%m%d")


def format_time(t):
    return t.strftime("%H:%M")


# format a datetime object into date and time suitable for pvoutput API
# @param dt a datetime object
# @return a formatted tuple of strings, (date,time)
def format_datetime(dt):
    d, t = dt.date(), dt.time()
    return format_date(d), format_time(t)


class API(object):
    """Represents the pvoutput.org web API, for a particular system

    API documentation can be found at http://pvoutput.org/help.html#api-spec"""

    def __init__(self, baseurl, apikey, sid):
        if not baseurl:
            raise ValueError("Bad or missing base URL")

        if not apikey:
            raise ValueError("Bad or missing apikey")

        if not sid:
            raise ValueError("Bad or missing sid")

        self.baseurl = baseurl
        self.apikey = apikey
        self.sid = sid

        self.__getsystem()

    def _request(self, script, args):
        """Invoke a specific API script

        Args:
           script (str): The path to the script to invoke
           args (dict): Arguments to the script
        Returns:
           str.  The data returned by the server
        Raises:
           pvoutputorg.Error
        """
        url = self.baseurl + script

        req = urllib.request.Request(url=url,
                                     data=urllib.parse.urlencode(args))
        req.add_header("X-Pvoutput-Apikey", self.apikey)
        req.add_header("X-Pvoutput-SystemId", self.sid)
        f = urllib.request.urlopen(req)
        code = f.getcode()
        if code != 200:
            raise Error("Bad HTTP response code (%d) on %s" % (code, url))
        return f.read()

    def __getsystem(self):
        """Update self with information from the getsystem API call"""

        data = self._request("/service/r2/getsystem.jsp", {"donations": 1})
        sysinfo, tarriffs, donation = data.split(";")

        sysinfo = sysinfo.split(",")

        self.name = sysinfo[0]
        self.system_size = int(sysinfo[1])
        self.donation_mode = int(donation) > 0

    def __str__(self):
        return ("SID %s: \"%s\" (%d W) [donation mode: %s]"
                % (self.sid, self.name, self.system_size, self.donation_mode))

    #
    # Methods dealing with live status information
    #
    def status_batchsize(self):
        """ number of statuses allowed in a batch
        @return the number of statuses allowed in a batch
        """
        if self.donation_mode:
            return 100
        return 30

    def addstatus(self, dt, total_production):
        """add a single data point to the server
        @param dt datetime object to add data for (naive, or correct timezone)
        @param total_production total system production at date and time dt
        @return None
        @fixme check API response"""
        fdate, ftime = format_datetime(dt)
        self._request("/service/r2/addstatus.jsp", {
            "d": fdate,
            "t": ftime,
            "c1": 1,
            "v1": total_production,
            "v2": -1,
        })

    def addbatchstatus(self, batch):
        """upload a whole bunch of statuses at the same time
        @param batch a list of lists to upload [[ datetime,totalprod ], ...]
        @return None
        @fixme should check server response rather than just printing..."""
        data = [format_datetime(dt) + (str(y), "-1")
                for dt, y in batch]
        data = ";".join(",".join(x) for x in data)

        results = self._request("/service/r2/addbatchstatus.jsp", {
            "data": data,
            "c1": 1
        })
        results = results.split(";")
        if len(results) != len(batch):
            raise Error("Unexpected number of results from addbatchstatus")

        for r in results:
            d, t, status = r.split(",")
            if status != "1":
                raise Error("Failed to upload status for %s %s" % (d, t))

    def addstatus_bulk(self, data):
        """Upload a whole bunch of statuses, splitting into multiple
        requests as necessary"""

        batchsize = self.status_batchsize()

        done = 0
        while done < len(data):
            batch = data[done:done+batchsize]
            self.addbatchstatus(batch)
            time.sleep(60)
            done += len(batch)

    def deletestatus(self, dt):
        """Delete status information
        @param dt a date or datetime object
        @return None"""
        if isinstance(dt, datetime.datetime):
            fdate, ftime = format_datetime(dt)
            opts = {
                "d": fdate,
                "t": ftime,
            }
        elif isinstance(dt, datetime.date):
            opts = {
                "d": format_date(dt),
            }
        else:
            raise TypeError

        self._request("/service/r2/deletestatus.jsp", opts)

    def getstatus(self, date, from_=None, to=None):
        opts = {
            "d": format_date(date),
            "h": 1,
            "limit": 288,
            "asc": 1,
        }
        if from_ is not None:
            opts["from"] = format_time(from_)

        if to is not None:
            opts["to"] = format_time(to)

        try:
            data = self._request('/service/r2/getstatus.jsp', opts)
        except urllib.error.HTTPError as e:
            # API gives an error if no data is present
            if e.code == 400:
                message = e.read()
                if message == "Bad request 400: No status found":
                    return None
            # Anything else, propagate the error
            raise

        data = data.split(';')

        ret = []
        for output in data:
            vals = output.split(',')
            # this throws away most of the data returned:
            dt = parse_datetime(vals[0], vals[1])
            ret.append((dt, int(vals[2])))

        return ret

    def getstatus_date_latest(self, date):
        opts = {
            "d": format_date(date),
            "h": 1,
            "limit": 1,
            "asc": 0,
        }

        try:
            data = self._request('/service/r2/getstatus.jsp', opts)
        except urllib.error.HTTPError as e:
            # API gives an error if no data is present
            if e.code == 400:
                message = e.read()
                if message == "Bad request 400: No status found":
                    return None
            # Anything else, propagate the error
            raise

        data = data.split(';')
        if len(data) != 1:
            raise Error("getstatus with limit 1 returned multiple records")

        vals = data[0].split(',')
        # this throws away most of the data returned:
        dt = parse_datetime(vals[0], vals[1])
        y = int(vals[2])

        return dt, y

    # Here be dragons...
    def addoutput(self, somedate, somedelta):
        """ add a daily output to pvoutput
        @param date to add output for
        @param delta production for this day
        @return None
        @fixme check API response
        """

        content = self._request("/service/r2/addoutput.jsp", {
            "d": format_date(somedate),
            "g": somedelta,
        })
        print("Server said: " + content)

    def getmissing(self, datefrom, dateto):
        """ Get Missing service retrieves a list of output dates missing
        @param datefrom first date to check
        @param dateto last date to check
        @return a list of date objects
        """
        if datefrom is None:
            raise Error("datefrom is None")
        if dateto is None:
            raise Error("dateto is null")

        formatted_datefrom = format_date(datefrom)
        formatted_dateto = format_date(dateto)

        data = self._request('/service/r2/getmissing.jsp', {
            'df': formatted_datefrom,
            'dt': formatted_dateto,
        })
        missings = data.split(',')

        print("missings: " + str(missings))

        dateobjects = [parse_date(missingdate)
                       for missingdate in missings]

        return dateobjects

    # returns the number of days ago you can set values using the batchstatus
    # script
    # @fixme rename me
    # @return number of days ago the batchstatus script will take in API
    def days_ago_accepted_by_api(self):
        if self.donation_mode:
            return 90
        return 14


def main():
    if len(sys.argv) == 3:
        baseurl = "http://pvoutput.org"
        apikey = sys.argv[1]
        sid = sys.argv[2]
    elif len(sys.argv) == 4:
        baseurl = sys.argv[1]
        apikey = sys.argv[2]
        sid = sys.argv[3]
    else:
        raise ValueError

    api = API(baseurl, apikey, sid)
    print(api)


if __name__ == "__main__":
    main()
