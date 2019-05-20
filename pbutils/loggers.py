import logging
import logging.handlers
import os
import sys

from pbutils.times import ep2asc


def create_module_logger(mod_name,
                         filename=None,
                         mode='w',
                         level=logging.DEBUG,
                         format_str='[%(module)s:%(filename)s:%(lineno)d] %(message)s'):
    """
    Create a logger dedicated to a particular module.
    @param mod_name: name of the module (and sub-modules) to capture logging for
    @param filename: name of file to store logs; defaults to mod_name
    @mode: write-mode of file (use 'a' for append)
    @level, @format_str: passed to logging config (level can be string or logging.INFO, etc)
    """
    if not filename:
        # create a log file in the same directory as the module:
        module = sys.modules[mod_name]
        mod_dir = os.path.dirname(module.__file__)
        filename = os.path.abspath(os.path.join(mod_dir, '{}.log'.format(module.__name__)))

    if '%' in filename:
        filename = ep2asc(fmt=filename)

    logger = logging.getLogger(mod_name)
    logger.propegate = False

    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logger.setLevel(level)

    handler = logging.FileHandler(filename, mode=mode, encoding='utf-8')
    logger.addHandler(handler)

    formatter = logging.Formatter(format_str)
    handler.setFormatter(formatter)
    return logger

if __name__ == '__main__':
    log = create_module_logger(__name__, mode='a')
    log.debug('Hi from {}'.format(__name__))
