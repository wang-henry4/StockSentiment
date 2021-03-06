import logging

def get_loggers(name, log_file):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(log_file)
    f_handler.setLevel(logging.WARNING)
    c_handler.setLevel(logging.INFO)
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger
    