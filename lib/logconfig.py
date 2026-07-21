LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '[%(levelname)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'PIL': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'lib': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': True
        },
    },
}