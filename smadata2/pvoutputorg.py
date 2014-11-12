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

import urllib
import urllib2
import time
import json
import datetime


class Error(Exception):
    pass

# documentation for the API is here:
# http://pvoutput.org/help.html#api-spec


class PVOutputOrg(object):
    def __init__(self, config_filepath):
        self.config = json.load(open(config_filepath, "r"))
        self.apikey = self.config["apikey"]
        self.hostnameport = self.config["hostname"]

        if not apikey:
            raise Error("No or bad apikey in pvoutput config")

        if not hostnameport:
            raise Error("No or bad hostname in pvoutput config")

    # call a script on the server configured in the config file
    # @fixme currently server includes port number
    # @param sid pvoutput.org system id
    # @param scriptpath path to script on server
    # @param data content of request
    # @return filehandle-ish thing containing response from server
    def make_request(self, sid, scriptpath, data):
        url = "http://" + self.hostnameport + scriptpath

        req = urllib2.Request(url=url, data=data)
        req.add_header("X-Pvoutput-Apikey", self.apikey)
        req.add_header("X-Pvoutput-SystemId", sid)
        filehandle = urllib2.urlopen(req)
        responsecode = filehandle.getcode()
        if responsecode != 200:
            raise Error("Bad HTTP response code (%s) from %s"
                        % (str(responsecode), self.hostnameport))
        return filehandle

    # add a single data point to the server
    # @param sid a pvoutput system id
    # @param timestamp Unix timestamp to add the data for
    # @param total_production total system production at this timestamp
    # @return None
    # @fixme check API response
    def addstatus(self, sid, timestamp, total_production):
        print("addstatus")

        data = urllib.urlencode({
            "d": time.strftime("%Y%m%d", time.localtime(timestamp)),
            "t": time.strftime("%H:%M", time.localtime(timestamp)),
            "c1": 1,
            "v1": total_production,
        })
        self.make_request(self, sid, "/service/r2/addstatus.jsp", data)

    # upload a whole bunch of statuses at the same time
    # @param sid a a system ID
    # @param batch a list of lists to upload [[ timestamp,totalprod ], ...]
    # @return None
    # @fixme should check server response rather than just printing...
    def addbatchstatus(self, sid, batch):
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
        data = urllib.urlencode({
            "data": productiondata,
            "c1": 1
        })
        filehandle = self.make_request(sid, "/service/r2/addbatchstatus.jsp",
                                       data)
        content = filehandle.read()
        print("Content returned from server: %s" % content)

    # delete a day's status
    # @param sid a pvoutput system id
    # @param date a datetime object for the first time to return (?!)
    # @return None
    def deletestatus(self, sid, date):
        formatted_date, formatted_time = self.format_date_and_time(date)
        opts = {
            'd': formatted_date,
            # 'h': 1,
        }
        data = urllib.urlencode(opts)
        self.make_request(sid, "/service/r2/deletestatus.jsp", data)

    # retrieve data for a time period - always from midnight ATM
    # @param sid a pvoutput system id
    # @param date a datetime object for the first time to return (?!)
    # @return a list of lists
    # @fixme this is just dodgy, dodgy, dodgy
    def getstatus(self, sid, date, timefrom, timeto):
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

        request = urllib.urlencode(opts)
        filehandle = self.make_request(sid, '/service/r2/getstatus.jsp',
                                       request)
        data = filehandle.read()
        outputs = data.split(';')
        ret = []
        for output in outputs:
            outputentries = output.split(',')
            # this throws away most of the data returned:
            ret.append([outputentries[0], outputentries[1],
                        int(outputentries[2])])
        return ret

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

    # format a datetime object into date and time suitable for pvoutput API
    # @param datetime a datetime object
    # @return a formatted tuple of strings, (date,time)
    def format_date_and_time(self, datetime):
        formatted_date = time.strftime("%Y%m%d", datetime.timetuple())
        formatted_time = time.strftime("%H:%M", datetime.timetuple())
        return (formatted_date, formatted_time)

    # returns true if a donation has been made for the apikey being used
    # @fixme this should pull its return value from the config
    # @return whether the api-key can use donation-mode
    def donation_mode(self):
        return True

    # returns the number of days ago you can set values using the batchstatus
    # script
    # @fixme rename me
    # @return number of days ago the batchstatus script will take in API
    def days_ago_accepted_by_api(self):
        if self.donation_mode():
            return 90
        return 14
