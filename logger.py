import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s%(reset)s:     %(white)s%(message)s%(reset)s',
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
    '''Logs the addition of a new client.'''
    logging.info(f"Added new client {ClientCount}")
    return

def loggingDebug(message):
    '''Logs a debug message.'''
    logger.debug(message)
    return

def loggingInfo(message):
    '''Logs an info message.'''
    logger.info(message)
    return

def loggingWarning(message):
    '''Logs a warning message.'''
    logger.warning(message)
    return

def loggingError(message):
    '''Logs an error message.'''
    logger.error(message)
    return