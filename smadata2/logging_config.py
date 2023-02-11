#! /usr/bin/python3
#
# smadata2.logging_config - source for application logging dictconfig()
# Copyright (C) 2019 Andy Frigaard
#

SMA2_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'simple': {
            'format': '%(message)s'
        },
    },
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
    'loggers': {
        '': {  # root logger
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'inverter': {
            'handlers': ['default', 'file'],
            'level': 'WARNING',
            'propagate': False
        },
        'smadata2.sma2mon': {  # monitoring
            'handlers': ['default', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}