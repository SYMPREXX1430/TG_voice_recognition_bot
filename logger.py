import sys
import logging
import logging.handlers


def get_logger(name: str, filename: str = f'{sys.argv[0]}.log'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s [%(name)-6s] [%(levelname)-5.5s]  %(message)s')

    file_handler = logging.handlers.RotatingFileHandler(
        filename=filename,
        maxBytes=8 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger