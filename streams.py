import sys, os
from contextlib import contextmanager

@contextmanager
def get_output_stream(filename, mode='w', verbose_stream=None):
    if filename == '-':
        stream = sys.stdout
    else:
        stream = open(filename, mode)
    yield stream
    if filename != '-':
        stream.close()
        if verbose_stream is not None:
            verbose_stream.write('{} written\n'.format(filename))

@contextmanager
def get_input_stream(filename):
    if filename is None or filename == '-':
        inp = sys.stdin
    else:
        inp = open(filename)
    yield inp
    if inp is not sys.stdin:
        inp.close()
    
            
def warn(s, force=False):
    ''' print a mesage to stderr if 'DEBUG' set in environment, or if force flag given '''
    if os.environ.get('DEBUG') or force:
        sys.stderr.write("{}\n".format(s))

def records(stream, delimiter):
    '''
    Generate all records found in the stream, using delimiter as an end-record delimitier.
    '''
    parts=[]
    for line in stream.readlines():
        parts.append(line)
        if line.startswith(delimiter):
            yield ''.join(parts)
            parts = []
    if parts:
        yield ''.join(parts)    # last one
        
def get_root(path):
    ''' return the basename of a file path, with extension stripped '''
    fn = os.path.basename(path)
    return os.path.splitext(fn)[0]
