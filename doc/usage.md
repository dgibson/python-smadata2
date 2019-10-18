# Python SMAData2 Usage

This shows examples of the available commands and typical output

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

<!-- What things you need to install the software and how to install them.-->

OS: Some type of Linux with Bluetooth support.  Works with a Raspberry Pi Zero W running Jessie/Debian.  The Python will run under Windows, but Bluetooth support needs some investigation.

```plantuml
A -> B
```


### sma2mon commands

A step by step series of examples that tell you how to get a development env running
Command-line arguments are handled by argparse https://docs.python.org/3/library/argparse.html.

#### --help

```sh
pi@raspberrypi:~ $ python-smadata2/sma2mon --help
usage: sma2mon [-h] [--config CONFIG]
               {status,yieldat,download,setupdb,settime,upload,historic_daily,spotacvoltage}
               ...

Work with Bluetooth enabled SMA photovoltaic inverters

positional arguments:
  {status,yieldat,download,setupdb,settime,upload,historic_daily,spotacvoltage}
    status              Read inverter status
    yieldat             Get production at a given date
    download            Download power history and record in database
    setupdb             Create database or update schema
    settime             Update inverters' clocks
    upload              Upload power history to pvoutput.org
    historic_daily      Get historic production for a date range
    spotacvoltage       Get spot AC voltage now.

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG
```
#### status
Establish a connection and Read inverter status
```sh
pi@raspberrypi:~ $ python3 python-smadata2/sma2mon status

System 20 Medway:
        20 Medway 1:
                Daily generation at Mon, 07 Oct 2019 18:15:35 ACDT:     17276 Wh
                Total generation at Mon, 07 Oct 2019 18:15:39 ACDT:     40111820 Wh
```
#### yieldat
Get production at a given date
```sh
pi@raspberrypi:~ $ python-smadata2/sma2mon yieldat "2019-02-14"
System 20 Medway:
        Total generation at 2019-02-14 00:00:00+10:30: 73189184 Wh
pi@raspberrypi:~ $ python-smadata2/sma2mon yieldat "2019-03-14"
System 20 Medway:
        Total generation at 2019-03-14 00:00:00+10:30: 37315778 Wh

```
#### download
Download power history and record in database
```sh
pi@raspberrypi:~ $ python-smadata2/sma2mon download
20 Medway 1 (SN: 2130212892)
starttime: 1546263000
1546263000
1546263000
Downloaded 268 observations from Sun, 06 Oct 2019 20:20:00 ACDT to Mon, 07 Oct 2019 18:35:00 ACDT
Downloaded 1 daily observations from Mon, 07 Oct 2019 00:00:00 ACDT to Mon, 07 Oct 2019 00:00:00 ACDT
```

#### settime
Update inverters' clocks
ToDo - does this actually work?  Example below not updating?

```sh
pi@raspberrypi:~ $ python3 python-smadata2/sma2mon settime
/home/pi/.smadata2.json
20 Medway 1 (SN: 2130212892)
                Previous time: Mon, 07 Oct 2019 19:29:05 ACDT
                New time: Mon, 07 Oct 2019 19:36:57 ACDT (TZ 34201)
                Updated time: Mon, 07 Oct 2019 19:29:05 ACDT
```

#### upload
Download power history and record in database
```sh
pi@raspberrypi:~ $ python-smadata2/sma2mon download
```

#### historic_daily [date_from] [date_to]
Get historic production for a date range
```sh
pi@raspberrypi:~ $ python-smadata2/sma2mon download
```

#### spotacvoltage
Get spot AC grid voltage now.
```sh
pi@raspberrypi:~ $ python-smadata2/sma2mon download
```
