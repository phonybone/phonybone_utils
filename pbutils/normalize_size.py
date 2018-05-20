import os
from collections import OrderedDict
from future.utils import iteritems

def get_size(path, units='auto'):
    divisors = OrderedDict()
    divisors['bytes']=1
    divisors['kb']=1<<10
    divisors['mb']=1<<20
    divisors['gb']=1<<30
    divisors['pb']=1<<40

    units = units.lower()
    raw_size = os.stat(path).st_size
    try:
        divisor = divisors[units]
        size = raw_size/divisor
    except KeyError:
        for units, divisor in iteritems(divisors):
            size = raw_size/divisor
            if len(str(size)) <= 4:
                break
            
    return '{}{}'.format(size, units.capitalize())

if __name__=='__main__':
    # path = '/usr/local/everest/data/var/UserData/Victor/Reads/LB5025/LB5025germline_PG0-718_LB4852V_rename.fastq'
    path = '/usr/share/dict/words'
    for units in 'auto bytes kb mb gb pb'.split(' '):
        print('answer: {}\n'.format(get_size(path, units)))
