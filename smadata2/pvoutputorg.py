#! /usr/bin/env python
#
# pvoutput.py - Poke pvoutput.org with data
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

import urllib
import urllib2
import time
import json

class Error(Exception):
    pass

# http://pvoutput.org/help.html#api-spec

class PVOutputOrg(object):
    def __init__(self,pvoutput_config_filepath):
        self.pvoutput_config_filepath = pvoutput_config_filepath
#        print("config=" + self.pvoutput_config_filepath);
        self.pvoutput_config = json.load(open(self.pvoutput_config_filepath,"r"))

    def addstatus(self,sid,timestamp,total_production):
        print ("addstatus")

        apikey = self.pvoutput_config["apikey"]
        hostnameport = self.pvoutput_config["hostname"]

        if (len(apikey) == 0):
            raise(Error("No or bad apikey in pvoutput config"))

        if (len(hostnameport) == 0):
            raise(Error("No or bad hostname in pvoutput config"))

        d = time.strftime("%Y%m%d",time.localtime(timestamp))
        t = time.strftime("%H:%M",time.localtime(timestamp))

        data = urllib.urlencode({
            "d": d,
            "t": t,
            "c1": 1,
            "v1": total_production,
        })
        liveoutputurl = "http://" + hostnameport + "/service/r2/addstatus.jsp"
        req = urllib2.Request(url=liveoutputurl,
                              data=data)
        req.add_header("X-Pvoutput-Apikey",apikey)
        req.add_header("X-Pvoutput-SystemId",sid)
        filehandle = urllib2.urlopen(req)
        responsecode = filehandle.getcode()
        if (responsecode != 200):
            raise Error("Bad HTTP response code (" + str(responsecode) + ") from " + hostnameport)

    def addbatchstatus(self,sid,timestamp,total_production):
        print ("addstatus")
