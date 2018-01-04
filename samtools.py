'''
Utilities for dealing with pysam and samtools.
'''
import os
import re
import Bio.SeqIO

def get_ref_ids(bamfile):
    ''' generator for sequence ids contained in the bamfile header '''
    return (h['SN'] for h in bamfile.header['SQ'])

def get_ref_ids_and_len(bamfile):
    return ((h['SN'],h['LN']) for h in bamfile.header['SQ'])


def ingest_amplicon(amplicon_fn):
    ''' 
    Return a dictionary of name -> sequence.
    '''
    # This can return the full dict because we're only returning a few hundred sequences at most.
    # But you could write this as a generator if necessary.
    return {record.id:record.seq for record in Bio.SeqIO.parse(amplicon_fn, "fasta")}

def get_amplicon_fn(opts, samfile):
    ''' 
    Attempt to extract the amplicon filename using info the samtools header.  
    Return name, or None on failure. 
    '''
    amplicon_fn = opts.amplicon_fn
    if not amplicon_fn:
        header = samfile.header
        PG = header['PG']
        record0 = PG[0]
        CL = record0['CL']
        regex = re.compile(r'-x ([^\s]+)') # extract index specifier
        mg = regex.search(CL)
        if not mg:
            raise RuntimeError("Unable to extract -x flag from '{}'".format(CL))
        bt2_idx = mg.group(1)
        amplicon_name = os.path.basename(bt2_idx)
        amplicon_fn = os.path.join(opts.sequence_dir, '{}.fasta'.format(amplicon_name))
    return amplicon_fn

    
def get_seq(fasta_fn, start, end):
    '''
    Extract a length of sequence from a .fasta file, using seek() and read() for speed.
    Assumes that there is only a single sequence in the .fasta file.
    '''
    if start > end:
        raise ValueError(start, end)
    if start < 0:
        raise ValueError(start)
    if end < 0:
        raise ValueError(end)
    try:
        fasta_stream = open(fasta_fn)
        do_not_close = False
    except TypeError:
        fasta_stream = fasta_fn
        do_not_close = True

    try:
        line0 = fasta_stream.readline()
        hlen = len(line0)
        line1 = fasta_stream.readline()
        llen = len(line1)

        n_lines = start/(llen-1)
        offset0 = hlen + start + n_lines

        n_lines = end/(llen-1)
        offset1 = hlen + end + n_lines
        seq_len = offset1 - offset0
        fasta_stream.seek(offset0)
        seq = fasta_stream.read(seq_len).replace('\n', '')
        return seq
    except Exception as e:
        raise 
    finally:
        if not do_not_close:
            fasta_stream.close()

def get_seq_slow(fasta_fn, start, end):
    '''
    A slower, simpler version of get_seq() used for testing.  Reads the entire sequence
    in to memory and then returns a string slice.
    '''
    with open(fasta_fn) as f:
        header = f.readline()
        lines = [l[:-1] for l in f.readlines()]
        seq = ''.join(lines)
        return seq[start:end]
            
def fastasize(seq, llen=50):
    ''' Insert '\n' characters into seq every llen characters; return new string '''
    i = 0
    lines = []
    while True:
        lines.append(seq[i:i+llen])
        i += llen
        if i > len(seq):
            return '\n'.join(lines)

if __name__ == '__main__':
    def test_seq():
        import random
        chrm_dir = '/usr/local/everest/data/setup/Genome/hg19'
        sample_len = 1<<15

        for i in xrange(1,23):
            path = os.path.join(chrm_dir, 'chr{}.fa'.format(i))
            raw_size = os.stat(path).st_size
            print 'path: {}\t\t{}'.format(path, raw_size)
            start = random.randint(1, raw_size-sample_len-1)
            end = start + sample_len
            print '  start: {}, end: {}'.format(start, end)
            seq1 = get_seq(path, start, end)
            seq2 = get_seq_slow(path, start, end)
            print 'seq1: {}..{}'.format(seq1[:10], seq1[-10:])
            print 'seq2: {}..{}'.format(seq2[:10], seq2[-10:])
            assert seq1 == seq2

    def test_ingest_amplicon():
        amplicon_fn = 'sequences/amplicon3_exons.fasta'
        amplicon = ingest_amplicon(amplicon_fn)
        from strings import ppjson
        print ppjson(amplicon)

    test_ingest_amplicon()
