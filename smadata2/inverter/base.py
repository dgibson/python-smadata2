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

# see https://pymotw.com/3/abc/
# How ABCs Work
# abc works by marking methods of the base class as abstract, and then registering concrete classes as implementations of the abstract base.
# If an application or library requires a particular API, issubclass() or isinstance() can be used to check an object against the abstract class.
# To start, define an abstract base class to represent the API of a set of plug-ins for saving and loading data.
# Set the metaclass for the new base class to ABCMeta, and use decorators to establish the public API for the class.
# The following examples use abc_base.py.
#
# Helper Base Class
# Forgetting to set the metaclass properly means the concrete implementations do not have their APIs enforced.
# To make it easier to set up the abstract class properly, a base class is provided that sets the metaclass automatically.

import abc      # abstract base classes (ABCs) in Python, as outlined in PEP 3119;


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
