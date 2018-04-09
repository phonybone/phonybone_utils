def delimited(fyle, delimiter='\n', bufsize=4096):
    ''' generator to yield records of a text file '''
    buf = ''
    while True:
        newbuf = fyle.read(bufsize)
        if not newbuf:
            yield buf
            return
        buf += newbuf
        lines = buf.split(delimiter)
        for line in lines[:-1]:
            yield line
        buf = lines[-1]

if __name__ == '__main__':
    fn = 'array.py'
    with open(fn) as f:
        for record in delimited(f, '\n\n'):
            print record
            print '-' * 72
            
# references: http://stackoverflow.com/questions/19600475/how-to-read-records-terminated-by-custom-separator-from-file-in-python
