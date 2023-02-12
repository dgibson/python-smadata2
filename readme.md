# Python SMAData 2

Python code for communicating with SMA photovoltaic inverters within built in Bluetooth.

The code originates from dgibson (written for his own use only) and I came across his project while looking for a fully Python-based SMA inverter tool, that would be easier to maintain & enhance than the various C-language projects, like SBFSpot.  
I liked the code and spent some time to understand how it works and to set it up.  It has some nice features for discovering the SMA protocol at the command line.

The purpose of this fork initially is to make this code-base accessible to a wider audience with some good documentation.  Then, depending on time, to extend with some other features.

- Support for a wider range of inverter data, including real-time "spot" values.
- Sending inverter data via MQTT, for use in home automation, or remote monitoring.
- Provide a ready to use Docker image (for x86 and ARM)
- Make it possible to run the application on a ESP32 or ESP8266 
- Consolidate information on the protocol and commands for SMA Inverters - see ``/doc/protocol.md``


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

<!-- What things you need to install the software and how to install them.-->

OS: Should run on Linux with Bluetooth support.  Tested with a Raspberry Pi Zero W running Jessie/Debian.  The application will also run under Windows, but requires PyBluez for Bluetooth support.

Software: This requires Python 3.x, and was earlier converted from 2.7 by dgibson, the original author.  I am running on 3.6, and am not aware of any version dependencies.

Packages: 
- It uses the "dateutil" external package for date/time formatting.  
- PyBluez is used to provide Bluetooth functions on both Linux and Windows.
- readline was used for command line support, but is not required (legacy from 2.7?). 

Debugging: For remote debugging code on the Pi Zero I found web_pdb to be useful. [https://pypi.org/project/web-pdb/]()
This displays a remote debug session over http on port 5555, e.g. [http://192.168.1.25:5555/]()

Testing:

Hardware: This runs on a Linux PC with Bluetooth (e.g. Raspberry Pi Zero W).
Inverter: Any type of SunnyBoy SMA inverter that supports their Bluetooth interface. This seems to be most models from the last 10 years.  However this has not been tested widely, only on a SMA5000TL


### Installing

<!-- A step by step series of examples that tell you how to get a development env running-->

Install or clone the project to an appropriate location, for example.

```sh
Linux:
/home/pi/python-smadata2
Windows:
C:\workspace\python-smadata2
```
Install and activate a virtual environment, as needed.
Install any required packages

Windows: To install Pybluez under Windows, pip may not work. It is more reliable to download the whl file from here
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pybluez
Examples tutorial:
https://people.csail.mit.edu/albert/bluez-intro/x232.html

```shell script
pip install -r requirements.txt
```
Next install a configuration file and database.   Copy the example file from the doc folder to your preferred location and edit for your local settings.

```shell script
Example file:
/python-smadata2/doc/example.smadata2.json
Copy to:
~/.smadata2.json
```
These lines in the json file determine the location of the database:
```json
    "database": {
        "filename": "~/.smadata2.sqlite"
```

The json file with configuration details (for development environment) should be stored separately, in a file stored in home, say: ```/home/pi/smadata2.json```.
This file should not be in Git, as it will contain the users confidential data.
There is an example provided in the source ```/doc/example.samdata2.json``` file and below.
The source file config.py references that file, so ensure that is  correct for your environment:
```pythonstub
# for Linux
# DEFAULT_CONFIG_FILE = os.path.expanduser("~/.smadata2.json")
# DEFAULT_CONFIG_FILE = os.environ.get('USERPROFILE') + "\.smadata2.json"
# Windows
DEFAULT_CONFIG_FILE = "C:\workspace\.smadata2.json"
```  
Then run this command to create the database:
```shell script
pi@raspberrypi:~/python-smadata2 $ python3 sma2mon setupdb
Creating database '/home/pi/.smadata2.sqlite'...
```

TODO - where a new user can discover these values.

## Settings file
The json file with configuration details (for development environment) should be stored separately, in the user's home, say: ```/home/pi/smadata2.json```.

This file should not be in Git, as it will contain the users confidential data.

There is an example provided in the source ```/doc/example.samdata2.json``` file and below.

The source file ``config.py`` references that file, so ensure the path is correct for your environment:

```json
{
    "database": {
        "filename": "~/.smadata2.sqlite"
    },
    "pvoutput.org": {
        "apikey": "2a0ahhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh"
    },
    "systems": [{
        "name": "My Photovoltaic System",
        "pvoutput-sid": NNNNN,
        "inverters": [{
            "name": "Inverter 1",
            "bluetooth": "00:80:25:xx:yy:zz",
            "serial": "2130012345",
            "start-time": "2019-10-17",
            "password": "1234"            
        }, {
            "name": "Inverter 2",
            "bluetooth": "00:80:25:pp:qq:rr",
            "serial": "2130012346"
	}]
    }]
}

```
These are optional parameters:

Todo - full explanation
```json
            "start-time": "2019-10-17",
            "password": "0000"
```

If all is setup correctly, then run an example command likst ``sma2mon status`` which will login to the SMA device and report on the 
daily generation:

```sh
pi@raspberrypi:~/python-smadata2 $ python3 sma2mon status
System 2My Photovoltaic System:
        Inverter 1:
                Daily generation at Sun, 20 Oct 2019 21:27:40 ACDT:     30495 Wh
                Total generation at Sun, 20 Oct 2019 19:43:37 ACDT:     40451519 Wh
pi@raspberrypi:~/python-smadata2 $

```
For further commands see the other documents in the ``/doc`` folder

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

See also the ``/doc/usage.md`` file for explanation and examples of the command line options.

### on Raspberry Pi
I have been running this on a dedicated Raspberry Pi Zero W (built-in Wifi and Bluetooth).  This is convenient as it can be located close to the inverter (Bluetooth range ~5m) and within Wifi range of the home router.  It runs headless (no display) and any changes are made via SSH, VNC.

The package is copied to an appropriate location, say:  ```/home/pi/python-smadata2``` and another directory for the database, say: ```/home/pi/python-smadata2```.  
The json file with configuration details (local configuration for that environment) should be stored separately, in a file stored in the user's home, say: ```/home/pi/smadata2.json```

This file is referenced in the config object loaded from ``smadata2/config.py`` on startup
```pythonstub
# Linux 
DEFAULT_CONFIG_FILE = os.path.expanduser("~/.smadata2.json")
```
### on Windows
This does run on Windows device with built-in Bluetooth.  

The json file with configuration details (local configuration for that environment) should be stored separately, in a file stored in the user's profile, say: ```C:\Users\<user>\smadata2.json```

This file is referenced in the config object loaded from ``smadata2/config.py`` on startup
```pythonstub
# Windows
DEFAULT_CONFIG_FILE = "C:\Users\<user>\.smadata2.json"
```

## Built With


## Contributing

Feedback is very welcome, and suggestions for other features.  Do log an issue.

Testing with other SMA devices is also needed.  The protocol should be similar for all devices.
<!-- Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.-->

<!-- 
## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors


See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.
-->
## License

This project is licensed under the GNU General Public License - see [https://www.gnu.org/licenses/]() .

## Acknowledgments

* dgibson [https://github.com/dgibson/python-smadata2]()
* SBFspot [https://github.com/SBFspot/SBFspot]()
* Stuart Pittaway [https://github.com/stuartpittaway/nanodesmapvmonitor]()
