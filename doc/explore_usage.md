# How to use sma2-explore

The `sma2-explore` tool allows the SMA protocol to be explored interactively & tested with a command-line interface that sends commands and displays the output.  
The output packet is formatted to separate the outer bluetooth protocol from the inner PPP protocol.

This shows examples of the available commands and typical output.

## Getting Started

Ensure the application is running on your local machine.  The sma2explore command does not use the json config file. See the Deployment section in readme.md for notes on how to deploy the project on a live system.

*Note that sma2-explore does not run under Windows as it uses the unsupported ``os.fork`` in ``SMAData2CLI`` to start a second thread that listens for incoming packets.* An alternative approach is needed.

-------------------------

### sma2-explore commands

Command-line arguments are handled by class `SMAData2CLI`.
This CLI class overrides the Connection class defined in `smabluetooth`.
Implements most of the same functions, but calls a dump_ function first.  The dump function prints a formatted packet format to the stdout.
 
```sh
pi@raspberrypi:~ $ python3 python-smadata2/sma2-explore "00:80:25:2C:11:B2"
```
This will connect to the supplied Bluetooth address and starts a terminal session with the SMA inverter.

Upon initial connection, the SMA device issues a "hello" packet once per second,
until the host replies with an identical (?) hello packet.

The terminal window shows Rx (received) and Tx (transmitted) lines.  The first two lines are the raw bytes from the packet, and the following lines are interpreted by the relevant function in sma2-explore. 

```sh

pi@raspberrypi:~ $ python3 python-smadata2/sma2-explore "00:80:25:2C:11:B2"
Connected B8:27:EB:F4:80:EB -> 00:80:25:2C:11:B2
SMA2 00:80:25:2C:11:B2 >>
Rx< 0000: 7E 1F 00 61 B2 11 2C 25-80 00 00 00 00 00 00 00
Rx< 0010: 02 00 00 04 70 00 04 00-00 00 00 01 00 00 00
Rx<     00:80:25:2C:11:B2 -> 00:00:00:00:00:00 TYPE 02
Rx<         HELLO!

... repeats every second

Rx< 0000: 7E 1F 00 61 B2 11 2C 25-80 00 00 00 00 00 00 00
Rx< 0010: 02 00 00 04 70 00 04 00-00 00 00 01 00 00 00
Rx<     00:80:25:2C:11:B2 -> 00:00:00:00:00:00 TYPE 02
Rx<         HELLO!

```
Commands can be sent to the inverter by simply typing and entering in the window.  Although the "hello" messages continue to scroll up, your keystrokes are displayed and interpreted. 

The commands are coded in class SMAData2CLI and these are supported

| Command| Function | Description |
| ------ | ------ | --------- |
| `hello`| `cmd_hello(self)` | Level 1 hello command responds to the SMA with the same data packet sent. |
| `logon`| `cmd_logon(self, password=b'0000', timeout=900)` | logon to the inverter with the default password.  |
| `quit`| `cmd_quit(self)` | close the SMA connection, return to shell.  |
| `getvar`| `cmd_getvar(self, varid)` | Level 1 getvar requests the value or a variable from the SMA inverter  |
| `ppp`| `cmd_ppp(self, protocol, *args)` | Sends a SMA Level 2 packet from payload, calls tx_outer to wrap in Level 1 packet  |
| `send2`| `cmd_send2(self, *args)` | Sends a SMA Level 2 request (builds a PPP frame for Transmission and calls tx_ppp to wrap for transmission). |
| `gdy`| `cmd_gdy(self)` | Sends a SMA Level 2 request to get Daily data.|
| `yield`| `cmd_yield(self)` | Sends a SMA Level 2 request to get Yield.|
| `historic`| `cmd_historic(self, fromtime=None, totime=None)` | Sends a SMA Level 2 request to get historic data between dates specified.|


#### Packet type 0x02: "Hello"

Level 1 hello command responds to the SMA with the same data packet received in the above broadcast.

The inverter responds with three packets, and stops transmitting the hello, so the screen stops scrolling.
```
TYPE 0A
TYPE 0C
TYPE 05
```

```sh

hello

Tx> 0000: 7E 1F 00 61 00 00 00 00-00 00 B2 11 2C 25 80 00
Tx> 0010: 02 00 00 04 70 00 04 00-00 00 00 01 00 00 00
Tx>     00:00:00:00:00:00 -> 00:80:25:2C:11:B2 TYPE 02
Tx>         HELLO!
SMA2 00:80:25:2C:11:B2 >>
Rx< 0000: 7E 1F 00 61 B2 11 2C 25-80 00 00 00 00 00 00 00
Rx< 0010: 0A 00 B2 11 2C 25 80 00-01 EB 80 F4 EB 27 B8
Rx<     00:80:25:2C:11:B2 -> 00:00:00:00:00:00 TYPE 0A

Rx< 0000: 7E 14 00 6A B2 11 2C 25-80 00 00 00 00 00 00 00
Rx< 0010: 0C 00 02 00
Rx<     00:80:25:2C:11:B2 -> 00:00:00:00:00:00 TYPE 0C

Rx< 0000: 7E 22 00 5C B2 11 2C 25-80 00 00 00 00 00 00 00
Rx< 0010: 05 00 B2 11 2C 25 80 00-01 01 EB 80 F4 EB 27 B8
Rx< 0020: 02 01
Rx<     00:80:25:2C:11:B2 -> 00:00:00:00:00:00 TYPE 05


```
#### logon
Establish an authorised connection enabling further requests.  

The password is hard-coded as '0000'.  *Note: it does not use the config file entry.*

Inverter responds with a type 01 packet, containing PPP frame.

tag 0001 (first, last)      response 0x040c subtype 0xfffd
```sh
logon

Tx> 0000: 7E 52 00 2C EB 80 F4 EB-27 B8 FF FF FF FF FF FF
Tx> 0010: 01 00 7E FF 03 60 65 0E-A0 FF FF FF FF FF FF 00
Tx> 0020: 01 78 00 3F 10 FB 39 00-01 00 00 00 00 01 80 0C
Tx> 0030: 04 FD FF 07 00 00 00 84-03 00 00 AA AA BB BB 00
Tx> 0040: 00 00 00 B8 B8 B8 B8 88-88 88 88 88 88 88 88 45
Tx> 0050: 54 7E
Tx>     B8:27:EB:F4:80:EB -> ff:ff:ff:ff:ff:ff TYPE 01
Tx>         PPP frame; protocol 0x6560 [56 bytes]
Tx>             0000: 0E A0 FF FF FF FF FF FF-00 01 78 00 3F 10 FB 39
Tx>             0010: 00 01 00 00 00 00 01 80-0C 04 FD FF 07 00 00 00
Tx>             0020: 84 03 00 00 AA AA BB BB-00 00 00 00 B8 B8 B8 B8
Tx>             0030: 88 88 88 88 88 88 88 88-
Tx>             SMA INNER PROTOCOL PACKET
Tx>                 78.00.3F.10.FB.39 => FF.FF.FF.FF.FF.FF
Tx>                 control A0 00 01 00 01
Tx>                 tag 0001 (first, last)
Tx>                 command 0x040c subtype 0xfffd
Tx>                 0000: AA AA BB BB 00 00 00 00-B8 B8 B8 B8 88 88 88 88
Tx>                 0010: 88 88 88 88
SMA2 00:80:25:2C:11:B2 >>
Rx< 0000: 7E 53 00 2D B2 11 2C 25-80 00 EB 80 F4 EB 27 B8
Rx< 0010: 01 00 7E FF 03 60 65 0E-D0 78 00 3F 10 FB 39 00
Rx< 0020: 01 8A 00 1C 78 F8 7D 5E-00 01 00 00 00 00 01 80
Rx< 0030: 0D 04 FD FF 07 00 00 00-84 03 00 00 AA AA BB BB
Rx< 0040: 00 00 00 00 B8 B8 B8 B8-88 88 88 88 88 88 88 88
Rx< 0050: C5 E3 7E
Rx<     00:80:25:2C:11:B2 -> B8:27:EB:F4:80:EB TYPE 01
Rx<         Partial PPP data frame begins frame ends
Rx<         PPP frame; protocol 0x6560 [56 bytes]
Rx<             0000: 0E D0 78 00 3F 10 FB 39-00 01 8A 00 1C 78 F8 7E
Rx<             0010: 00 01 00 00 00 00 01 80-0D 04 FD FF 07 00 00 00
Rx<             0020: 84 03 00 00 AA AA BB BB-00 00 00 00 B8 B8 B8 B8
Rx<             0030: 88 88 88 88 88 88 88 88-
Rx<             SMA INNER PROTOCOL PACKET
Rx<                 8A.00.1C.78.F8.7E => 78.00.3F.10.FB.39
Rx<                 control D0 00 01 00 01
Rx<                 tag 0001 (first, last)
Rx<                 response 0x040c subtype 0xfffd
Rx<                 0000: AA AA BB BB 00 00 00 00-B8 B8 B8 B8 88 88 88 88
Rx<                 0010: 88 88 88 88
```

#### gdy  (get daily)
Sends a SMA Level 2 request to get Daily data.

Inverter responds with a type 01 packet, containing PPP frame.

tag 0005 (first, last)      0x0200 subtype 0x5400
```sh
gdy

Tx> 0000: 7E 3E 00 40 EB 80 F4 EB-27 B8 FF FF FF FF FF FF
Tx> 0010: 01 00 7E FF 03 60 65 09-A0 FF FF FF FF FF FF 00
Tx> 0020: 00 78 00 3F 10 FB 39 00-00 00 00 00 00 05 80 00
Tx> 0030: 02 00 54 00 22 26 00 FF-22 26 00 BB D6 7E
Tx>     B8:27:EB:F4:80:EB -> ff:ff:ff:ff:ff:ff TYPE 01
Tx>         PPP frame; protocol 0x6560 [36 bytes]
Tx>             0000: 09 A0 FF FF FF FF FF FF-00 00 78 00 3F 10 FB 39
Tx>             0010: 00 00 00 00 00 00 05 80-00 02 00 54 00 22 26 00
Tx>             0020: FF 22 26 00
Tx>             SMA INNER PROTOCOL PACKET
Tx>                 78.00.3F.10.FB.39 => FF.FF.FF.FF.FF.FF
Tx>                 control A0 00 00 00 00
Tx>                 tag 0005 (first, last)
Tx>                 command 0x0200 subtype 0x5400

SMA2 00:80:25:2C:11:B2 >>
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


#### yield
Sends a SMA Level 2 request to get Yield.

Inverter responds with a type 01 packet, containing PPP frame.

tag 0006 (first, last)      0x0200 subtype 0x5400

```sh
yield

Tx> 0000: 7E 3E 00 40 EB 80 F4 EB-27 B8 FF FF FF FF FF FF
Tx> 0010: 01 00 7E FF 03 60 65 09-A0 FF FF FF FF FF FF 00
Tx> 0020: 00 78 00 3F 10 FB 39 00-00 00 00 00 00 06 80 00
Tx> 0030: 02 00 54 00 01 26 00 FF-01 26 00 37 72 7E
Tx>     B8:27:EB:F4:80:EB -> ff:ff:ff:ff:ff:ff TYPE 01
Tx>         PPP frame; protocol 0x6560 [36 bytes]
Tx>             0000: 09 A0 FF FF FF FF FF FF-00 00 78 00 3F 10 FB 39
Tx>             0010: 00 00 00 00 00 00 06 80-00 02 00 54 00 01 26 00
Tx>             0020: FF 01 26 00
Tx>             SMA INNER PROTOCOL PACKET
Tx>                 78.00.3F.10.FB.39 => FF.FF.FF.FF.FF.FF
Tx>                 control A0 00 00 00 00
Tx>                 tag 0006 (first, last)
Tx>                 command 0x0200 subtype 0x5400

SMA2 00:80:25:2C:11:B2 >>
Rx< 0000: 7E 4F 00 31 B2 11 2C 25-80 00 EB 80 F4 EB 27 B8
Rx< 0010: 01 00 7E FF 03 60 65 0D-90 78 00 3F 10 FB 39 00
Rx< 0020: A0 8A 00 1C 78 F8 7D 5E-00 00 00 00 00 00 06 80
Rx< 0030: 01 02 00 54 00 00 00 00-00 00 00 00 01 01 26 00
Rx< 0040: F3 50 9C 5D 20 6D 64 02-00 00 00 00 D3 57 7E
Rx<     00:80:25:2C:11:B2 -> B8:27:EB:F4:80:EB TYPE 01
Rx<         Partial PPP data frame begins frame ends
Rx<         PPP frame; protocol 0x6560 [52 bytes]
Rx<             0000: 0D 90 78 00 3F 10 FB 39-00 A0 8A 00 1C 78 F8 7E
Rx<             0010: 00 00 00 00 00 00 06 80-01 02 00 54 00 00 00 00
Rx<             0020: 00 00 00 00 01 01 26 00-F3 50 9C 5D 20 6D 64 02
Rx<             0030: 00 00 00 00
Rx<             SMA INNER PROTOCOL PACKET
Rx<                 8A.00.1C.78.F8.7E => 78.00.3F.10.FB.39
Rx<                 control 90 00 A0 00 00
Rx<                 tag 0006 (first, last)
Rx<                 response 0x0200 subtype 0x5400
Rx<                 0000: 01 01 26 00 F3 50 9C 5D-20 6D 64 02 00 00 00 00
```
#### getvar [var]
Sends a SMA Level 1 request to get variable value, as 2 digit hex number.

Variables 01, 02, 03, 04, 05, 06: valid
Inverter responds with a type 04 packet giving a variable value.

e.g. 05 is Signal 0x00C4 is 196/255 = 76.9%

e.g. 09 is a version string: "CG2000 V1.212 Jul  2 2010 14:52:52"

Variables 0x00, 0x0B, 0x10, 0x11: Invalid
		 Causes a type 07 error packet to be issued
```sh
getvar 5

Tx> 0000: 7E 14 00 6A 00 00 00 00-00 00 B2 11 2C 25 80 00
Tx> 0010: 03 00 05 00
Tx>     00:00:00:00:00:00 -> 00:80:25:2C:11:B2 TYPE 03
Tx>         GETVAR 0x05
SMA2 00:80:25:2C:11:B2 >>
Rx< 0000: 7E 18 00 66 B2 11 2C 25-80 00 00 00 00 00 00 00
Rx< 0010: 04 00 05 00 00 00 C4 00-
Rx<     00:80:25:2C:11:B2 -> 00:00:00:00:00:00 TYPE 04
Rx<         VARVAL 0x05
Rx<             Signal level 76.9%

getvar 9

Tx> 0000: 7E 14 00 6A 00 00 00 00-00 00 B2 11 2C 25 80 00
Tx> 0010: 03 00 09 00
Tx>     00:00:00:00:00:00 -> 00:80:25:2C:11:B2 TYPE 03
Tx>         GETVAR 0x09
SMA2 00:80:25:2C:11:B2 >>
Rx< 0000: 7E 38 00 46 B2 11 2C 25-80 00 00 00 00 00 00 00
Rx< 0010: 04 00 09 00 00 00 43 47-32 30 30 30 20 56 31 2E
Rx< 0020: 32 31 32 20 4A 75 6C 20-20 32 20 32 30 31 30 20
Rx< 0030: 31 34 3A 35 32 3A 35 32-
Rx<     00:80:25:2C:11:B2 -> 00:00:00:00:00:00 TYPE 04
Rx<         VARVAL 0x09

```
#### spotacvoltage
Sends a SMA Level 1 request to get spotacvoltage.

More complex example as the response is spread across 3 frames, with 204 bytes of PPP data.  This includes voltages for 3 phase power.
```sh
spotacvoltage

Tx> 0000: 7E 3E 00 40 EB 80 F4 EB-27 B8 FF FF FF FF FF FF
Tx> 0010: 01 00 7E FF 03 60 65 09-A0 FF FF FF FF FF FF 00
Tx> 0020: 00 78 00 3F 10 FB 39 00-00 00 00 00 00 02 80 00
Tx> 0030: 02 00 51 00 48 46 00 FF-55 46 00 CF 77 7E
Tx>     B8:27:EB:F4:80:EB -> ff:ff:ff:ff:ff:ff TYPE 01
Tx>         PPP frame; protocol 0x6560 [36 bytes]
Tx>             0000: 09 A0 FF FF FF FF FF FF-00 00 78 00 3F 10 FB 39
Tx>             0010: 00 00 00 00 00 00 02 80-00 02 00 51 00 48 46 00
Tx>             0020: FF 55 46 00
Tx>             SMA INNER PROTOCOL PACKET
Tx>                 78.00.3F.10.FB.39 => FF.FF.FF.FF.FF.FF
Tx>                 control A0 00 00 00 00
Tx>                 tag 0002 (first, last)
Tx>                 command 0x0200 subtype 0x5100

SMA2 00:80:25:2C:11:B2 >>
Rx< 0000: 7E 6D 00 13 B2 11 2C 25-80 00 EB 80 F4 EB 27 B8
Rx< 0010: 08 00 7E FF 03 60 65 33-90 78 00 3F 10 FB 39 00
Rx< 0020: A0 8A 00 1C 78 F8 7D 5E-00 00 00 00 00 00 02 80
Rx< 0030: 01 02 00 51 0A 00 00 00-0F 00 00 00 01 48 46 00
Rx< 0040: DB 9C 9D 5D 9B 5E 00 00-9B 5E 00 00 9B 5E 00 00
Rx< 0050: 9B 5E 00 00 01 00 00 00-01 49 46 00 DB 9C 9D 5D
Rx< 0060: FF FF FF FF FF FF FF FF-FF FF FF FF FF
Rx<     00:80:25:2C:11:B2 -> B8:27:EB:F4:80:EB TYPE 08
Rx<         Partial PPP data frame begins

Rx< 0000: 7E 6D 00 13 B2 11 2C 25-80 00 EB 80 F4 EB 27 B8
Rx< 0010: 08 00 FF FF FF 01 00 00-00 01 4A 46 00 DB 9C 9D
Rx< 0020: 5D FF FF FF FF FF FF FF-FF FF FF FF FF FF FF FF
Rx< 0030: FF 01 00 00 00 01 50 46-00 DB 9C 9D 5D BC 00 00
Rx< 0040: 00 BC 00 00 00 BC 00 00-00 BC 00 00 00 01 00 00
Rx< 0050: 00 01 51 46 00 DB 9C 9D-5D FF FF FF FF FF FF FF
Rx< 0060: FF FF FF FF FF FF FF FF-FF 01 00 00 00
Rx<     00:80:25:2C:11:B2 -> B8:27:EB:F4:80:EB TYPE 08
Rx<         Partial PPP data

Rx< 0000: 7E 31 00 4F B2 11 2C 25-80 00 EB 80 F4 EB 27 B8
Rx< 0010: 01 00 01 52 46 00 DB 9C-9D 5D FF FF FF FF FF FF
Rx< 0020: FF FF FF FF FF FF FF FF-FF FF 01 00 00 00 95 2B
Rx< 0030: 7E
Rx<     00:80:25:2C:11:B2 -> B8:27:EB:F4:80:EB TYPE 01
Rx<         Partial PPP data frame ends
Rx<         PPP frame; protocol 0x6560 [204 bytes]
Rx<             0000: 33 90 78 00 3F 10 FB 39-00 A0 8A 00 1C 78 F8 7E
Rx<             0010: 00 00 00 00 00 00 02 80-01 02 00 51 0A 00 00 00
Rx<             0020: 0F 00 00 00 01 48 46 00-DB 9C 9D 5D 9B 5E 00 00
Rx<             0030: 9B 5E 00 00 9B 5E 00 00-9B 5E 00 00 01 00 00 00
Rx<             0040: 01 49 46 00 DB 9C 9D 5D-FF FF FF FF FF FF FF FF
Rx<             0050: FF FF FF FF FF FF FF FF-01 00 00 00 01 4A 46 00
Rx<             0060: DB 9C 9D 5D FF FF FF FF-FF FF FF FF FF FF FF FF
Rx<             0070: FF FF FF FF 01 00 00 00-01 50 46 00 DB 9C 9D 5D
Rx<             0080: BC 00 00 00 BC 00 00 00-BC 00 00 00 BC 00 00 00
Rx<             0090: 01 00 00 00 01 51 46 00-DB 9C 9D 5D FF FF FF FF
Rx<             00a0: FF FF FF FF FF FF FF FF-FF FF FF FF 01 00 00 00
Rx<             00b0: 01 52 46 00 DB 9C 9D 5D-FF FF FF FF FF FF FF FF
Rx<             00c0: FF FF FF FF FF FF FF FF-01 00 00 00
Rx<             SMA INNER PROTOCOL PACKET
Rx<                 8A.00.1C.78.F8.7E => 78.00.3F.10.FB.39
Rx<                 control 90 00 A0 00 00
Rx<                 tag 0002 (first, last)
Rx<                 response 0x0200 subtype 0x5100
Rx<                 0000: 01 48 46 00 DB 9C 9D 5D-9B 5E 00 00 9B 5E 00 00
Rx<                 0010: 9B 5E 00 00 9B 5E 00 00-01 00 00 00 01 49 46 00
Rx<                 0020: DB 9C 9D 5D FF FF FF FF-FF FF FF FF FF FF FF FF
Rx<                 0030: FF FF FF FF 01 00 00 00-01 4A 46 00 DB 9C 9D 5D
Rx<                 0040: FF FF FF FF FF FF FF FF-FF FF FF FF FF FF FF FF
Rx<                 0050: 01 00 00 00 01 50 46 00-DB 9C 9D 5D BC 00 00 00
Rx<                 0060: BC 00 00 00 BC 00 00 00-BC 00 00 00 01 00 00 00
Rx<                 0070: 01 51 46 00 DB 9C 9D 5D-FF FF FF FF FF FF FF FF
Rx<                 0080: FF FF FF FF FF FF FF FF-01 00 00 00 01 52 46 00
Rx<                 0090: DB 9C 9D 5D FF FF FF FF-FF FF FF FF FF FF FF FF
Rx<                 00a0: FF FF FF FF 01 00 00 00-
```