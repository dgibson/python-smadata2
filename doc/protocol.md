# Notes on the protocol for Bluetooth enabled SMA inverters

There seem to be two "interesting" protocol layers in the SMA
bluetooth protocol.  The "outer" protocol is a packet protocol over
Bluetooth RFCOMM.  It seems mainly to deal with Bluetooth specific
things - signal levels etc.

Speculation:
 - Used for communication between the bluetooth adapters, rather than
   the equipment itself?
 - e.g. SMA bluetooth repeaters would talk this protocol, then forward
   the inner frames on to the actual equipment?

Some of the outer protocol frame types encapsulate PPP frames.  All
PPP frames observed are PPP protocol number 0x6560, which appears to
be an SMA allocated ID for their control protocol.

Speculation:
 - Is PPP and the inner protocol used directly over serial when using
   RS485 instead of Bluetooth connections?
    - Allows for shared use of RS485 lines, maybe?

## Outer protocol

Packet based protocol over RFCOMM channel 1 over Bluetooth.  The same
packet format appears to be used in both directions.


### Packet header
```text
Offset		Value
---------------------
0		0x7e
1		length of packet (including header), max 0x70
2		0x00
3		check byte, XOR of bytes 0..2 inclusive
4..9		"From" bluetooth address
10..15		"To" bluetooth address
16..17		Packet type (LE16)

18..		Payload (format depends on packet type)
```

The bluetooth addresses are encoded in the reverse order to how they're usually written.  So `00:80:25:2C:11:B2` would be sent in the
packet header as: `B2 11 2C 25 80 00` and that can be seen in the example below.

For packets which don't relate to the inner protocol, 00:00:00:00:00:00 seems to be used instead of the initiating host's
MAC address.

In this example packet `50` is the length, ln, `2E` the checksum, etc.  The payload starts with the `0D 90` in the second row.  The packet is 5 rows on 16 bytes, i.e. length 0x50.

The payload is 52 or 0x34 bytes,  printed again for clarity below, and broken down into the known elements.
```sh
             ln    chk <--   from   --> <--    to     -->
Rx< 0000: 7E 50 00 2E B2 11 2C 25-80 00 EB 80 F4 EB 27 B8
Rx< 0010: 01 00 7E FF 03 60 65 0D-90 78 00 3F 10 FB 39 00
Rx< 0020: A0 8A 00 1C 78 F8 7D 5E-00 00 00 00 00 00 05 80
Rx< 0030: 01 02 00 54 01 00 00 00-01 00 00 00 01 22 26 00
Rx< 0040: 81 7D 5D 9C 5D 31 5D 00-00 00 00 00 00 3C 94 7E
Rx<     00:80:25:2C:11:B2 -> B8:27:EB:F4:80:EB TYPE 01

Rx<         Partial PPP data frame begins frame ends
Rx<         PPP frame; protocol 0x6560 [52 bytes]
Rx<             0000: 0D 90 78 00 3F 10 FB 39-00 A0 8A 00 1C 78 F8 7E
Rx<             0010: 00 00 00 00 00 00 05 80-01 02 00 54 01 00 00 00
Rx<             0020: 01 00 00 00 01 22 26 00-81 7D 9C 5D 31 5D 00 00
Rx<             0030: 00 00 00 00

Rx<             SMA INNER PROTOCOL PACKET
Rx<                 8A.00.1C.78.F8.7E => 78.00.3F.10.FB.39
Rx<                 control 90 00 A0 00 00
Rx<                 tag 0005 (first, last)
Rx<                 response 0x0200 subtype 0x5400
Rx<                 0000: 01 22 26 00 81 7D 9C 5D-31 5D 00 00 00 00 00 00
```

### Packet type 0x01: PPP frame (last piece)

```text
Offset		Value
16		0x01
17		0x00
18..		PPP data
```
The PPP data is raw as it would be transmitted over serial. i.e. it
includes flag bytes (0x7e at start and end of each PPP packet), PPP
escaping, and the PPP CRC16 checksum at end of each frame.

### Packet type 0x02: "Hello"

Upon connection, SMA device issues one of these ~once per second,
until host replies with an identical (?) hello packet.
```text
Offset		Value
---------------------
16		0x02
17		0x00
18		0x00
19		0x04
20		0x70
21		0x00
22		0x01    or 0x04
23		0x00
24		0x00
25		0x00
26		0x00
27		0x01		NetID???
28		0x00
29		0x00
30		0x00 
```
### Packet type 0x03: GETVAR

Causes device to issue a type 04 packet giving a variable value (?)
```text

Offset		Value
---------------------
16		0x03
17		0x00
18..19		variable ID (LE16)
```

### Packet type 0x04: VARIABLE

```
Offset		Value
---------------------
16		0x04
17		0x00
18..19		variable ID (LE16)
20..		variable contents
```

Variables:
	Variable 0x00, 0x10, 0x11: Invalid
		 Causes a type 07 error packet to be issued

	Variable 0x05: Signal Level
```
Offset		 Value
----------------------
`18		0x05
19		0x00
20		0x00
21		0x00
22		signal level, out of 255
23		0x00`

ID		Meaning		Length
--------------------------------------
0x05		signal level	4 bytes
```

### Packet type 0x05: Unknown

### Packet type 0x07: Error

### Packet type 0x08: PPP frame (not last piece)
As type 0x01

### Packet type 0x0a: Unknown

### Packet type 0x0c: Unknown


## Inner protocol (PPP protocol 0x6560)

```
Offset		Value
----------------------
0		Length of packet, in 32-bit words, including (inner) header, but not ppp header??
1		? A2
2..7		to address
8		? B1
9		? B2
10..15		from address
16..17		??? C1,C2
18..19		error code?
20..21		packet count for multi packet response
22..23		LE16, low 15 bits are tag value
		MSB is "first packet" flag for multi packet response??
24..25		Packet type
		LSB is command/response flag
26..27		Packet subtype
28..31		Arg 1 (LE)
32..35		Arg 2 (LE)
```


### Command: Total Yield

```
COMMAND:
	A2:		A0
	B1,B2:		00 00
	C1,C2:		00 00
	Type:		0200
	Subtype:	5400
	Arg1:		0x00260100
	Arg2:		0x002601ff

RESPONSE:
	PAYLOAD:
		0..3	timestamp (LE)
		4..7	total yield in Wh (LE)
```

### Command: Daily  Yield

```
COMMAND:
	A2:		A0
	B1,B2:		00 00
	C1,C2:		00 00
	Type:		0200
	Subtype:	5400
	Arg1:		0x00262200
	Arg2:		0x002622ff

RESPONSE:
	PAYLOAD:
		0..3	timestamp (LE)
		4..7	day's yield in Wh (LE)
```

### Command: Historic data (5 minute intervals)

```
COMMAND:
	A2:		E0
	B1,B2:		00 00
	C1,C2:		00 00
	Type:		0200
	Subtype:	7000
	Arg1:		start time
	Arg2:		end time

RESPONSE:
	PAYLOAD:
		0..3	timestamp (LE)
		4..7	yield in Wh (LE)
		8..11	unknown
		PATTERN REPEATS
```

### Command: Historic data (daily intervals)
```
COMMAND:
	A2:		E0
	B1,B2:		00 00
	C1,C2:		00 00
	Type:		0200
	Subtype:	7020
	Arg1:		start time (unix date, LE)
	Arg2:		end time (unix date, LE)

RESPONSE:
	PAYLOAD:
		0..3	timestamp (unix date, LE)
		4..7	total yield at that time in Wh (LE)
		8..11	???
		...	Pattern repeated
```

### Command: Set time
```
COMMAND:
	A2:		A0
	B1,B2:		00 00
	C1,C2:		00 00
	Type:		020A
	Subtype:	F000
	Arg1:		0x00236d00
	Arg2:		0x00236d00
	PAYLOAD:
		0..3	00 6D 23 00
		4..7	timestamp
		8..11	timestamp (again)
		12..15	timestamp (again)
		16..17	localtime offset from UTC in seconds
		18..19	00 00
		20..23	30 FE 7E 00
		24..27	01 00 00 00

RESPONSE:
	PAYLOAD:
```
```
(smadata_venv) C:\workspace\python-smadata2>python sma2mon info TypeLabel
C:\workspace\.smadata2.json
System 20 Medway:
        20 Medway 1:
TypeLabel
func:'wait_6560_multi' args:[(<smadata2.inverter.smabluetooth.Connection
2250 sec
response_data_type is:  smaStr1
process is:  process_smastr1
Start smaStr1:
b'prefix'PPP frame; protocol 0x0000 [1 bytes]
1PPP frame; protocol 0x0000 [160 bytes]
259520000: 01 1E 82 10 E2 83 A3 5D 53 4E-3A 20 32 31 33 30 32 31 32 38
259520014: 39 32 00 00 10 00-00 00 10 00 00 00 00 00 00 00 00 00 00 00
259520028: 01 1F-82 08 E2 83 A3 5D 41 1F 00 01 42 1F 00 00 FE FF-FF 00
25952003c: 00 00 00 00 00 00 00 00 00 00 00 00 00 00-00 00 00 00 00 00
259520050: 01 20 82 08 E2 83 A3 5D 72 23-00 00 73 23 00 00 74 23 00 01
259520064: CD 23 00 00 D3 23-00 00 D4 23 00 00 D5 23 00 00 D6 23 00 00
259520078: 01 20-82 08 E2 83 A3 5D FE FF FF 00 00 00 00 00 00 00-00 00
25952008c: 00 00 00 00 00 00 00 00 00 00 00 00 00 00-00 00 00 00 00 00

                            uint32_t code = ((uint32_t)get_long(pcktBuf + ii));
                            LriDef lri = (LriDef)(code & 0x00FFFF00);
                            uint32_t cls = code & 0xFF;
                            unsigned char dataType = code >> 24;
                            time_t datetime = (time_t)get_long(pcktBuf + ii + 4);

RESPONSE:
	PAYLOAD:
		0   	index? 01
		1..2	data type, 0x821E, corresponds to middle 2 bytes of arg1 LriDef in SMASpot
		3	    datatype  0x10 =text, 0x08 = status, 0x00, 0x40 = Dword 64 bit data
		4..7	timestamp (unix date, LE)
		4..7	total yield at that time in Wh (LE)
		8..22	text string, terminated in 00 00 10
		23.31   padding 00
		...	Pattern repeated on 40 byte cycle, 4 times
```
```