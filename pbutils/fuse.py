class Fuse(object):
    ''' A class useful for counting down during a loop '''
    def __init__(self, fuse):
        self.fuse = fuse

    def __str__(self):
        return 'fuse: {}'.format(self.fuse)

    def boom(self):
        self.fuse -= 1
        return self.fuse == 0

if __name__ == '__main__':
    import sys
    fuse = Fuse(int(sys.argv[1]))

    while not fuse.boom():
        print 'not yet'
    print 'boom'
