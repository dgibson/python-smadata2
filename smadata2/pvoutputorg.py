#! /usr/bin/env python
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

from __future__ import print_function

import sys
import urllib
import urllib2
import time
import datetime


class Error(Exception):
    pass


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

        req = urllib2.Request(url=url, data=urllib.urlencode(args))
        req.add_header("X-Pvoutput-Apikey", self.apikey)
        req.add_header("X-Pvoutput-SystemId", self.sid)
        f = urllib2.urlopen(req)
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

    def addoutput(self, somedate, somedelta):
        """ add a daily output to pvoutput
        @param date to add output for
        @param delta production for this day
        @return None
        @fixme check API response
        """

        content = self._request("/service/r2/addoutput.jsp", {
            "d": self.format_date(somedate),
            "g": somedelta,
        })
        print("Server said: " + content)

    # add a single data point to the server
    # @param timestamp Unix timestamp to add the data for
    # @param total_production total system production at this timestamp
    # @return None
    # @fixme check API response
    def addstatus(self, timestamp, total_production):
        print("addstatus")

        self._request("/service/r2/addstatus.jsp", {
            "d": time.strftime("%Y%m%d", time.localtime(timestamp)),
            "t": time.strftime("%H:%M", time.localtime(timestamp)),
            "c1": 1,
            "v1": total_production,
        })

    # upload a whole bunch of statuses at the same time
    # @param batch a list of lists to upload [[ timestamp,totalprod ], ...]
    # @return None
    # @fixme should check server response rather than just printing...
    def addbatchstatus(self, batch):
        new = []
        for prodinfo in batch:
            timestamp, production = prodinfo
            new.append([
                time.strftime("%Y%m%d", time.localtime(timestamp)),
                time.strftime("%H:%M", time.localtime(timestamp)),
                str(production),
                str(-1)
            ])

        productiondata = ';'.join(','.join(x) for x in new)

        print("productiondata=" + productiondata)
        content = self._request("/service/r2/addbatchstatus.jsp", {
            "data": productiondata,
            "c1": 1
        })
        print("Content returned from server: %s" % content)

    # delete a day's status
    # @param date a datetime object for the first time to return (?!)
    # @return None
    def deletestatus(self, date):
        formatted_date, formatted_time = self.format_date_and_time(date)
        self._request("/service/r2/deletestatus.jsp", {
            'd': formatted_date,
            # 'h': 1,
        })

    def getstatusx(self, date, timefrom, timeto):
        """ retrieve data for a time period - always from midnight ATM
        @param date a datetime object for the first time to return (?!)
        @return a list of lists
        @fixme this is just dodgy, dodgy, dodgy
        """
        formatted_date, formatted_time = self.format_date_and_time(date)
        opts = {
            'd': formatted_date,
            'h': 1,
            'limit': 288,
            'asc': 1,
        }
        if timefrom is not None:
            opts['from'] = timefrom
            if timeto is not None:
                opts['to'] = timeto

        data = self._request('/service/r2/getstatus.jsp', opts)
        outputs = data.split(';')
        ret = []
        for output in outputs:
            outputentries = output.split(',')
            # this throws away most of the data returned:
            ret.append([outputentries[0], outputentries[1],
                        int(outputentries[2])])
        return ret

    # retrieve data for a time period - always from midnight ATM
    # @param fromdatetime first datetime to return status for
    # @param number of entries to return
    # @return a list of lists
    # @fixme this is just dodgy, dodgy, dodgy
    def getstatus(self, fromdatetime, count):
        formatted_date, formatted_time = self.format_date_and_time(fromdatetime)
        opts = {
            'd': formatted_date,
            't': formatted_time,
            'h': 1,
            'limit': count,
            'asc': 1,
        }
        # if timefrom is not None:
        #     opts['from'] = timefrom
        #     if timeto is not None:
        #         opts['to'] = timeto

        data = self._request('/service/r2/getstatus.jsp', opts)
        outputs = data.split(';')
        ret = []
        for output in outputs:
            outputentries = output.split(',')
            # this throws away most of the data returned:
            ret.append([outputentries[0], outputentries[1],
                        int(outputentries[2])])
        return ret

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

        formatted_datefrom = self.format_date(datefrom)
        formatted_dateto = self.format_date(dateto)

        data = self._request('/service/r2/getmissing.jsp', {
            'df': formatted_datefrom,
            'dt': formatted_dateto,
        })
        missings = data.split(',')

        print("missings: " + str(missings))

        dateobjects = [self.parse_date(missingdate)
                       for missingdate in missings]

        return dateobjects

    # parse a date and time supplied by pvoutput.org
    # @param pvoutput_date a date in pvoutput API form
    # @param pvoutput_time a time in pvoutput API form
    # @return a datetime object
    def parse_date_and_time(self, pvoutput_date, pvoutput_time):
        return datetime.datetime(int(pvoutput_date[0:4]),
                                 int(pvoutput_date[4:6]),
                                 int(pvoutput_date[6:8]),
                                 int(pvoutput_time[0:2]),
                                 int(pvoutput_time[3:5]))

    def parse_date(self, pvoutput_date):
        """ parse a date supplied by pvoutput.org
        @param pvoutput_date a date in pvoutput API form
        @return a date object
        """
        return datetime.date(int(pvoutput_date[0:4]),
                             int(pvoutput_date[4:6]),
                             int(pvoutput_date[6:8]))

    # format a datetime object into date and time suitable for pvoutput API
    # @param datetime a datetime object
    # @return a formatted tuple of strings, (date,time)
    def format_date_and_time(self, datetime):
        formatted_date = time.strftime("%Y%m%d", datetime.timetuple())
        formatted_time = time.strftime("%H:%M", datetime.timetuple())
        return (formatted_date, formatted_time)

    def format_date(self, date):
        """ format a date object into a format suitable for the pvoutput API
        @param date a date object
        @return a formatted date
        """
        return date.strftime("%Y%m%d")

    # returns the number of days ago you can set values using the batchstatus
    # script
    # @fixme rename me
    # @return number of days ago the batchstatus script will take in API
    def days_ago_accepted_by_api(self):
        if self.donation_mode:
            return 90
        return 14

    def batchstatus_count_accepted_by_api(self):
        """ number of statuses allowed in a batch
        @return the number of statuses allowed in a batch
        """
        if self.donation_mode:
            return 100
        return 30


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
