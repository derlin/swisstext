import logging
from os import makedirs
from logging.config import dictConfig

makedirs('logs', exist_ok=True)
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    }},
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'default',
            'when': 'h',
            'interval': 24,
            'backupCount': 31,
            'filename': 'logs/colistock.log'
        }},
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
})


def getLogger(name):
    return logging.getLogger(name)
