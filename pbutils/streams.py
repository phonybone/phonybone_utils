import sys, os
import re
from contextlib import contextmanager
import subprocess

from pbutils.strings import qw

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

    Also see PipedCmd()
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

def gather_input(prompts):
    ''' Loop over prompts using raw_input; fill in the fields '''
    _rx = re.compile(' ')
    
    def _get_value(key, info):
        prompt = info.get('prompt', 'Enter {}'.format(key))
        while True:
            value = raw_input('{}: '.format(prompt))
            if 'validate' in info:
                validate = info['validate']
                if isinstance(validate, list):
                    if value in validate:
                        info['value'] = value
                        return

                elif type(validate) is type(_rx):
                    try:
                        mg = validate.search(value)
                        if mg:
                            info['value'] = value
                            return
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        print e
                        continue

                elif callable(validate):
                    try:
                        info['value'] = validate(value)
                        return
                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        print e
                        continue
                else:
                    raise RuntimeError("Don't know how to validate {} using {} (type={})".format(key, validate, type(validate)))
                
            else:               # no validation info given
                info['value'] = value
                return
            print('unable to validate {}; try again'.format(value))
            if 'validation_help' in info:
                print info['validation_help']
                
    for key, info in prompts.iteritems():
        if 'value' not in info:
            _get_value(key, info)

if __name__ == '__main__':
    def test_gather_input():
        from collections import OrderedDict
        prompts = OrderedDict()
        prompts['name'] = {'prompt': 'Give me a name', 'validate': str}
        prompts['age'] = {'validate': int}
        prompts['email'] = {'validate': re.compile('[\w.]+@[\w.]+\.(com|org|net|edu|co)'), 'validation_help': 'not a valid email address'}
        prompts['color'] = {'validate': qw('red blue yellow'), 'validation_help': 'Must be one of red, blue, or yellow'}
        try:
            gather_input(prompts)
            for key, info in prompts.iteritems():
                print('{}: {}'.format(key, info['value']))
        except EOFError:
            print('never mind')
