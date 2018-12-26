#! /usr/bin/python3
#
# smadata2.db.base - Abstract database interface
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


all = ['Error', 'WrongSchema']


class Error(Exception):
    pass


class WrongSchema(Error):
    pass


class BaseDatabase(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_historic(self, serial, timestamp, total_yield):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_one_historic(self, serial, timestamp):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_last_historic(self, serial):
        raise NotImplementedError()
