#! /usr/bin/python3
#
# smadata2.inverter.mock - Mock inverter connections
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

from .base import InverterConnection


class MockInverterZero(InverterConnection):
    def __init__(self):
        super(InverterConnection, self).__init__()

    def total_yield(self):
        return 0

    def daily_yield(self):
        return 0

    def historic(self, fromtime, totime):
        tmp = []
        for timestamp in range(fromtime, totime, 5*60):
            tmp.append((timestamp, 0))
        return tmp

    def historic_daily(self, fromtime, totime):
        raise NotImplementedError
