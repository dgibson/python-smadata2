#! /usr/bin/env python

from __future__ import print_function

import sys

from btsma import *
from btcli import *

if len(sys.argv) != 2:
    print("Usage: btcli.py <BD addr>", file=sys.stderr)
    sys.exit(1)

sma = BTSMAConnectionCLI(sys.argv[1])

print("Waiting for hello")
hello = sma.wait_outer(OTYPE_HELLO)

sma.tx_hello()

sma.wait_outer(0x0a)
