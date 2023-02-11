#! /usr/bin/python3
#
# smadata2.__init__ - Python code for the SMAData2 protocol
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

import logging.config
from smadata2.logging_config import SMA2_LOGGING_CONFIG #only this, in case file has other unwanted content

logging.config.dictConfig(SMA2_LOGGING_CONFIG)
#log = logging.getLogger(__name__)  # once in each module