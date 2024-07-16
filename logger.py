'''
This script is used as a dependancy for the URLServer.py file, if you are running this program as a client only, then it's safe to delete it
'''
import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(purple)s%(asctime)s%(reset)s - %(log_color)s%(levelname)s%(reset)s - %(white)s%(message)s%(reset)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
        'purple':   'purple',  # Time color
        'white':    'white',   # Message color
    }
))


# Configure logging
logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def loggingNewClient(ClientCount):
    logging.info(f"Added new client {ClientCount}")
    return

def loggingDebug(message):
    logger.debug(message)
    return

def loggingInfo(message):
    logger.info(message)
    return

def loggingWarning(message):
    logger.warning(message)
    return

def loggingError(message):
    logger.error(message)
    return