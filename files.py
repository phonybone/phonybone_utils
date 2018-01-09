import os
from collections import OrderedDict
import pkg_resources as pr

def get_size(path, units='auto'):
    ''' Return a user-friendly, auto-scaled string representation of the size of a file. '''
    divisors = OrderedDict()
    divisors['bytes']=1
    divisors['kb']=1<<10
    divisors['mb']=1<<20
    divisors['gb']=1<<30
    divisors['tb']=1<<40
    divisors['pb']=1<<50
    
    units = units.lower()
    raw_size = os.stat(path).st_size
    try:
        divisor = divisors[units]
        size = raw_size/divisor
    except KeyError:
        for units, divisor in divisors.iteritems():
            size = raw_size/divisor
            if len(str(size)) <= 4:
                break
            
    return '{}{}'.format(size, units.capitalize())

def get_timestamp(path):
    ''' return the file modification time '''
    ts = os.path.getmtime(path)
    return time.strftime('%Y-%m-%d %H:%M', time.gmtime(ts))

def replace_ext(path, new_ext, n_exts=1):
    ''' 
    replace the extension on a path with a new extension.  Replacement occurs
    even if there was no extension on the original path.
    '''
    head = path
    while n_exts >= 1:
        head, tail = os.path.splitext(head)
        n_exts -= 1
    return head + '.' + new_ext

def package_fileres(pack, fn):
    return pr.resource_filename(pack, fn)

if __name__=='__main__':
    path = '/usr/local/everest/data/var/UserData/Victor/Reads/LB5025/LB5025germline_PG0-718_LB4852V_rename.fastq'
    # for units in 'auto bytes kb mb gb pb'.split(' '):
    #     print 'answer: {}\n'.format(get_size(path, units))

    print replace_ext(path, 'fq')
    print replace_ext('/usr/local/bin', 'txt')
    print replace_ext('/usr/local/bin/fart.html', 'txt')
    print replace_ext('/usr/local/bin/fart.orig.html', 'txt')
    print replace_ext('/', '.bin')
