#! /usr/bin/env python

from __future__ import print_function

import sys
import time

from btsma import *
from btcli import *

if len(sys.argv) != 2:
    print("Usage: btcli.py <BD addr>", file=sys.stderr)
    sys.exit(1)

sma = BTSMAConnectionCLI(sys.argv[1])

print("Exchanging HELLOs")
#    17	:init $END;   //Can only be run once
#    18	R 7E 1F 00 61 $ADDR 00 00 00 00 00 00 02 00 00 04 70 00 $END;
#    19	E $INVCODE $END;
#    20	S 7E 1F 00 61 00 00 00 00 00 00 $ADDR 02 00 00 04 70 00 $INVCODE 00 00 00 00 01 00 00 00 $END;
#    21	R 7E 22 00 5C $ADDR 00 00 00 00 00 00 05 00 $ADDR $END;

sma.hello()

print("Checking signal")
#    22	E $ADD2 $END;
#    23	:setup $END;  //Can be rerun
#    24	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    25	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    26	E $SIGNAL $END;

sig = sma.getsignal()
print("Signal %.1f" % (sig * 100))

#    27	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    28	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    29	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    30	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    31	S 7E 3F 00 41 $ADD2 FF FF FF FF FF FF 01 00 7E FF 03 60 65 09 A0 FF FF FF FF FF FF 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 00 02 00 00 00 00 00 00 00 00 00 00 $CRC 7E $END;

magicaddr = [0x78, 0x00, 0x3f, 0x10, 0xfb, 0x39]
count = 1
sma.do_6560(0x09, 0xa0, 0x00, 0x00, bytearray('\x00\x00\x00\x00\x00\x00'), count,
            bytearray('\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'))

#    32	S 7E 3B 00 45 $ADD2 FF FF FF FF FF FF 01 00 7E FF 03 60 65 08 A0 FF FF FF FF FF FF 00 03 78 00 $UNKNOWN 00 03 00 00 00 00 00 80 0E 01 FD FF FF FF FF FF $CRC 7E $END;
count += 1
sma.do_6560(0x08, 0xa0, 0x00, 0x03, bytearray('\x00\x03\x00\x00\x00\x00'), count,
            bytearray('\x0e\x01\xfd\xff\xff\xff\xff\xff'))

#    33	S 7E 54 00 2A $ADD2 FF FF FF FF FF FF 01 00 7E FF 03 60 65 0E A0 FF FF FF FF FF FF 00 01 78 00 $UNKNOWN 00 01 00 00 00 00 $CNT 80 0C 04 FD FF 07 00 00 00 84 03 00 00 $TIME 00 00 00 00 $PASSWORD $CRC 7E $END;

reporttime = int(time.time())
print("reporttime = %d" % reporttime)

password = bytearray([(0x88 + ord('0')) & 0xff] * 4 + [0x88] * 8)

count += 1
sma.do_6560(0x0e, 0xa0, 0x00, 0x01, bytearray('\x00\x01\x00\x00\x00\x00'), count,
            bytearray('\x0c\x04\xfd\xff\x07\x00\x00\x00\x84\x03\x00\x00')
            + int2bytes32(reporttime) + bytearray('\x00\x00\x00\x00') + password)

#    34	#R 7E 6a 00 14 $ADDR $ADD2 $END;
#    35	R 7E 6a 00 14 $ADDR $END;
#    36	E $SER $END;
#    37	:setinverter time $END;
#    38	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    39	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    40	E $SIGNAL $END;
#    41	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    42	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    43	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    44	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    45	S 7e 5c 00 22 $ADD2 ff ff ff ff ff ff 01 00 7e ff 03 60 65 10 a0 ff ff ff ff ff ff 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 0a 02 00 f0 00 6d 23 00 00 6d 23 00 00 6d 23 00 $TIME $TIME $TIME $TIMEZONE 00 00 $TIMESET 01 00 00 00 $CRC 7e $END;

timeval = int(time.time())
utime = int2bytes32(timeval)
tz = int2bytes32(-time.timezone)

count += 1
sma.do_6560(0x10, 0xa0, 0x00, 0x00, bytearray('\x00\x00\x00\x00\x00\x00'), count,
            bytearray('\x0a\x02\x00\xf0\x00\x6d\x23\x00\x00\x6d\x23\x00\x00\x6d\x23\x00') +
            utime + utime + utime + tz + bytearray('\x00\x00') + utime + bytearray('\x01\x00\x00\x00'))

#    46	:startsetup time $END;
#    47	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    48	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    49	E $SIGNAL $END;
#    50	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    51	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    52	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    53	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    54	S 7e 5b 00 25 $ADD2 ff ff ff ff ff ff 01 00 7e ff 03 60 65 10 a0 ff ff ff ff ff ff 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 0a 02 00 f0 00 6d 23 00 00 6d 23 00 00 6d 23 00 $TMPL $TMMI $TMPL 00 00 00 00 01 00 00 00 01 00 00 00 $CRC 7e $END;

count += 1
sma.do_6560(0x10, 0xa0, 0x00, 0x00, bytearray('\x00\x00\x00\x00\x00\x00'), count,
            bytearray('\x0a\x02\x00\xf0\x00\x6d\x23\x00\x00\x6d\x23\x00\x00\x6d\x23\x00')
            + int2bytes32(timeval+1) + int2bytes32(timeval - 1) + int2bytes32(timeval + 1)
            + bytearray('\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00'))

#    55	S 7E 3F 00 41 $ADD2 FF FF FF FF FF FF 01 00 7E FF 03 60 65 09 A0 FF FF FF FF FF FF 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 00 02 00 58 00 1E 82 00 FF 21 82 00 $CRC 7E $END;

count += 1
sma.do_6560(0x09, 0xa0, 0x00, 0x00, bytearray('\x00\x00\x00\x00\x00\x00'), count,
            bytearray('\x00\x02\x00\x58\x00\x1e\x82\x00\xff\x21\x82\x00'))

#    56	S 7E 3F 00 41 $ADD2 FF FF FF FF FF FF 01 00 7E FF 03 60 65 09 A0 FF FF FF FF FF FF 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 00 02 00 58 00 1e a2 00 FF 1e a2 00 $CRC 7E $END;

count += 1
sma.do_6560(0x09, 0xa0, 0x00, 0x00, bytearray('\x00\x00\x00\x00\x00\x00'), count,
            bytearray('\x00\x02\x00\x58\x00\x1e\xa2\x00\xff\x1e\xa2\x00'))

#    57	S 7E 3F 00 41 $ADD2 FF FF FF FF FF FF 01 00 7E FF 03 60 65 09 A0 FF FF FF FF FF FF 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 00 02 80 51 00 48 21 00 FF 48 21 00 $CRC 7E $END;

count += 1
sma.do_6560(0x09, 0xa0, 0x00, 0x00, bytearray('\x00\x00\x00\x00\x00\x00'), count,
            bytearray('\x00\x02\x80\x51\x00\x48\x21\x00\xff\x48\x21\x00'))

#    58	R 7e 5a 00 24 $ADDR $ADD2 01 00 7e ff 03 60 65 $END;
#    59	E $TIMESTRING $END;
#    60	S 7E 5B 00 25 $ADD2 FF FF FF FF FF FF 01 00 7E FF 03 60 65 10 A0 FF FF FF FF FF FF 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 0A 02 00 F0 00 6D 23 00 00 6D 23 00 00 6D 23 00 $TIMESTRING $CRC 7E $END;

#count += 1
#sma.tx_ppp("ff:ff:ff:ff:ff:ff", 0x6560, bytearray(
#    [0x10, 0xa0, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
#     0x00, 0x00] + magicaddr +
#    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, count, 0x80,
#     0x0a, 0x02, 0x00, 0xf0, 0x00, 0x6d, 0x23, 0x00, 0x00, 0x6d, 0x23, 0x00, 0x00#, 0x6d, 0x23, 0x00, 

#    61	R 7E 66 00 1a $ADDR $END;
#    62	E $POW $END;
#    63	:getlivevalues $END;  //get live data
#    64	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    65	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    66	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    67	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    68	S 7E 40 00 3E $ADD2 ff ff ff ff ff ff 01 00 7E FF 03 60 65 09 a1 ff ff ff ff ff ff 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 00 02 00 51 00 00 20 00 ff ff 50 00 0e $CRC 7e $END;
#    69	R 7E 66 00 1a $ADDR $ADD2 $END;
#    70	E $POW $END;
#    71	S 7e 3f 00 41 $ADDR ff ff ff ff ff ff 01 00 7e ff 03 60 65 09 a0 ff ff ff ff ff ff 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 00 02 80 51 00 00 20 00 ff ff 50 00 $CRC 7e $END;
#    72	R 7E 66 00 1a $ADDR $ADD2 $END;
#    73	E $POW $END;
#    74	:getrangedata $END;  //get archived data for a particular date range
#    75	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    76	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    77	E $SIGNAL $END;
#    78	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    79	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    80	S 7E 14 00 6A 00 00 00 00 00 00 $ADDR 03 00 05 00 $END;
#    81	R 7E 18 00 66 $ADDR 00 00 00 00 00 00 04 00 05 00 00 00 $END;
#    82	S 7E 40 00 3E $ADD2 $ADDR 01 00 7E FF 03 60 65 09 E0 $ARCHCODE 00 $SER 00 00 78 00 $UNKNOWN 00 00 00 00 00 00 $CNT 80 00 02 00 70 $TIMEFROM1 $TIMETO1 $CRC 7e $END;
#    83	R 7E 66 00 1a $ADDR $END;
#    84	E $ARCHIVEDATA1 $END;
#    85	:unit conversions
#    86	3f 26	"Total Power"		Watts			1
#    87	1e 41	"Max Phase 1"		Watts			1	
#    88	1f 41	"Max Phase 2"		Watts			1
#    89	20 41	"Max Phase 3"		Watts			1
#    90	66 41	"Unknown"		Unknown			1
#    91	7f 41	"Unknown"		Unknown			1
#    92	40 46	"Output Phase 1"	Watts			1
#    93	41 46	"Output Phase 2"	Watts			1
#    94	42 46	"Output Phase 3"	Watts			1
#    95	48 46	"Line Voltage Phase 1"	Volts			100
#    96	49 46	"Line Voltage Phase 2"	Volts			100
#    97	4a 46	"Line Voltage Phase 3"	Volts			100
#    98	50 46	"Line Current Phase 1"	Amps			1000
#    99	51 46	"Line Current Phase 2"	Amps			1000
#   100	52 46	"Line Current Phase 3"	Amps			1000
#   101	57 46	"Grid Frequency"	Hertz			100
#   102	1e 82   "Unit Serial"		none			1
#   103	:end unit conversions

sma.rxloop()
