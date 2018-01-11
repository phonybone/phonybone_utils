import subprocess

class PipedCmd(object):
    def __init__(self, cmds):
        self.cmds = cmds
        # check that each command is a list of lists

    def __str__(self):
        return ' | '.join([' '.join(cmd) for cmd in cmds])
    
    def start(self):
        # check for input redirection:
        cmd0 = self.cmds.pop(0)
        if '<' in cmd0:
            idx = cmd0.index('<')
            src = cmd0.pop(idx+1)
            cmd0.remove('<')
            self.cmds.insert(0, ['cat', src])
            idx = 1
        else:
            idx = 0
        self.cmds.insert(idx, cmd0)

        # check for output redirection:
        cmdZ = self.cmds.pop()
        if '>' in cmdZ:
            idx = cmdZ.index('>')
            self.dst = cmdZ.pop(idx+1)
            cmdZ.remove('>')
        else:
            self.dst = None
        self.cmds.append(cmdZ)

        # create Popen objects
        print 'starting to launch cmds'
        pipe=[subprocess.Popen(self.cmds[0], stdout=subprocess.PIPE)] # first command, no stdin=
        for i, cmd in enumerate(self.cmds[1:]):
            p=subprocess.Popen(cmd, stdin=pipe[i].stdout, stdout=subprocess.PIPE) # i is 0-based
            pipe.append(p)
        self.pipe = pipe


    def wait(self):
        # wait for all commands to finish
        for cmd in self.pipe:
            cmd.wait()
            # print 'process {} done: rc={}'.format(cmd.pid, cmd.poll())


    def output(self):
        # communicated with last cmd to get output
        output = self.pipe[-1].communicate()[0]

        # write output if needed:
        dst = getattr(self, 'dst', None)
        if dst is not None:
            with open(dst, 'w') as f:
                f.write(output)

        return output

    def status(self):
        ''' return return codes for all processes in pipe; if processes are not done, rc is None '''
        return all([cmd.poll() is not None for cmd in self.pipe])

if __name__=='__main__':
    def test_pipe(cmds):
        print cmds
        p = PipedCmd(cmds)
        p.start()
        p.wait()
        output = p.output()
        print 'output:\n',output
        print '-' * 72

    all_cmds = [
        ['echo this that these those'.split(' '), 'wc -l'.split(' ')],
        [['ls'], ['grep', 'pipe'], ['sort']],
        [['ls', '-l', '>', 'fred']],
        [['cut', '-c8-12', '<', 'fred']],
        [['ls', 'fart']],       # error
        [['echo', 'fart'], ['sleep', '3']],
        [['sleep', '3'], ['echo', 'fart']],
    ]
    for cmds in all_cmds:
        test_pipe(cmds)
