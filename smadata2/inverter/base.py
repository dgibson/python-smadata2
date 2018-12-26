#! /usr/bin/python3
#
# smadata2.db.base - Abstract inverter interface
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

import abc


all = ["Error"]


class Error(Exception):
    pass


class InverterConnection(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def total_yield(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def daily_yield(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def historic(self, fromtime, totime):
        raise NotImplementedError()

    @abc.abstractmethod
    def historic_daily(self, fromtime, totime):
        raise NotImplementedError()
