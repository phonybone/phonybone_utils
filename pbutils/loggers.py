import logging
import logging.handlers
import os
import sys

def create_module_logger(mod_name,
                         filename=None,
                         mode='w',
                         level=logging.DEBUG,
                         format_str='[%(module)s:%(filename)s:%(lineno)d] %(message)s'):
    if not filename:
        # create a log file in the same directory as the module:
        module = sys.modules[mod_name]
        mod_dir = os.path.dirname(module.__file__)
        filename = os.path.abspath(os.path.join(mod_dir, '{}.log'.format(module.__name__)))
        print('filename: {}'.format(filename))

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
    #mod = sys.modules['loggers']
    print('name: {}'.format(__name__))
    #print('mod: {}'.format(mod))
    log = create_module_logger(__name__, mode='a')
    log.debug('Hi from {}'.format(__name__))
              
