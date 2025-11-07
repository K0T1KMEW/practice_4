import logging
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = TimedRotatingFileHandler(
        'logs/employee_app.log',
        when='midnight',
        interval=1,
        backupCount=7
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger