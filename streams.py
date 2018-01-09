import sys, os
from contextlib import contextmanager
import subprocess


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

def do_pipe(cmds):
    '''
    Run a set of piped commands.  

    cmds is a list of lists; each element is a cmd as may be fed to subprocess.Popen.

    Return the set of pipe objects created and the final output.

    Attempts to handle input redirection for the first command and
      output redirection for the last command.  Whitespace required 
      between '>' and filename, '<' and filename.

    Pretty primitive; caller beware.
    '''
    cmd0 = cmds.pop(0)
    if '<' in cmd0:
        idx = cmd0.index('<')
        src = cmd0.pop(idx+1)
        cmd0.remove('<')
        cmds.insert(0, ['cat', src])
        idx = 1
    else:
        idx = 0
    cmds.insert(idx, cmd0)

    cmdZ = cmds.pop()
    if '>' in cmdZ:
        idx = cmdZ.index('>')
        dst = cmdZ.pop(idx+1)
        cmdZ.remove('>')
    else:
        dst = None
    cmds.append(cmdZ)

    pipes=[subprocess.Popen(cmds[0], stdout=subprocess.PIPE)] # first command, no stdin=
    for i, cmd in enumerate(cmds[1:]):
        p=subprocess.Popen(cmd, stdin=pipes[i].stdout, stdout=subprocess.PIPE) # i is 0-based
        pipes.append(p)
    output=pipes[-1].communicate()[0]

    if dst is not None:
        with open(dst, 'w') as f:
            f.write(output)
            
    return pipes, output
