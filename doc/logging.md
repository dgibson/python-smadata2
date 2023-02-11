# How to use logging

The application uses Python standard logging to log information and (debugging) data from the inverter sessions.

This is highly configurable through changes to the `smadata2.logging_config.py` file.  This contains a Python dictionary definition that is used to initialise the logging, based on the `dictconfig()` model.

References
[https://docs.python.org/3/howto/logging.html]()
[https://docs.python.org/3/howto/logging-cookbook.html]()
 
A common scenario is to modify the way that logs are stored or sent
[https://docs.python.org/3/howto/logging-cookbook.html#customizing-handlers-with-dictconfig]()

This shows examples of the available commands and typical output.

## How it works

Within the application, information is written to the log as in the example below.
The logging level is `info` in the example, and more detailed messages may use `debug`.

```pythonstub
log.info("\tDaily generation at %s:\t%d Wh" % (smadata2.datetimeutil.format_time(dtime), daily))
```
The logging_config file has a section `handlers`.
This shows that all the logged information is written to either the console (`default, 'stream': 'ext://sys.stdout'`) and to a file (`'filename': 'sma2.log'`).  The level for each is set in the handler.

```pythonstub
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'sma2.log',
        },
    },
```

## Reference

Logging levels are as below

|Level | When it’s used |
|------|----------------|
|DEBUG|Detailed information, typically of interest only when diagnosing problems.  Details of the messages to/from the inverter, the database are shown at this level.|
|INFO|Confirmation that things are working as expected. Results like Power, Voltage from the inverter are at this level.|
|WARNING|An indication that something unexpected happened, or indicative of some problem in the near future . The software is still working as expected.|
|ERROR|Due to a more serious problem, the software has not been able to perform some function.|
|CRITICAL|A serious error, indicating that the program itself may be unable to continue running.|

