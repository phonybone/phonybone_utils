'''
Utilities for dealing with pysam and samtools.
'''
import sys
import os
import re
import pysam
import Bio.SeqIO
import csv
from collections import Counter, namedtuple
import subprocess as sp
from streams import warn, get_output_stream
from strings import ppjson, qw
from span_mixin import SpanMixin
from files import ensure_folder

import logging
log = logging.getLogger(__name__)

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


class GeneSpan(SpanMixin):
    def __init__(self, chrom, gene, start, stop):
        self.chrom = chrom
        self.gene = gene
        self.start = start
        self.stop = stop

    def __str__(self):
        return '{}.{}: {}-{}'.format(self.chrom, self.gene, self.start, self.stop)

    def merge(self, other):
        if not self.chrom == other.chrom:
            raise ValueError('{} != {}'.format(self.chrom, other.chrom))
        super(GeneSpan, self).merge(other)
        self.gene = self.gene + '-' + other.gene
        return self

########################################################################

def bed2ref_fa(bed_fn, ref_fa, ref_genome_dir, get_gene_name, flank_bp=0, prepend_chr=False):
    ''' 
    Create amplicon .fasta from .bed file and a ref genome.
    
    bed_fn: 
        a .BED file (input)
    ref_fa: 
        file in which to write the genome (.fasta format) (may be '-' for stdout)
    ref_genome_dir: 
        a directory that contains .fa sequenes for each chromosome mentioned in the .BED file (in .fasta format)
    get_gene_name: 
        a callable that takes one parameter, a list obtained from each line of the .BED file; must return a gene name
    flank_bp: 
        number of flanking bases on each side of gene sequence to add to the output sequence.

    returns: None
    '''
    chroms = {}
    with open(bed_fn) as bed:
        reader = csv.reader(bed, delimiter='\t')
        header = reader.next() # burn the header
        for bline in reader:
            gene_name = get_gene_name(bline)
            if gene_name is None:
                log.debug('Cannot extract gene name from {}\nget_gene_name: {!r}'.format(bline, get_gene_name))
                continue
            gene = GeneSpan(
                chrom=bline[0],
                start=int(bline[1]) - flank_bp,
                stop=int(bline[2]) + flank_bp,
                gene=get_gene_name(bline),
            )
            chroms.setdefault(gene.chrom, []).append(gene)

    rx = re.compile(r'^chr(\d|1\d|2[012]|X|Y)$')
    fixable = re.compile(r'^\d|1\d|2[012]|X|Y$') # ugh
    
    with get_output_stream(ref_fa) as output:
        for chrom, genes in chroms.iteritems():
            genespans = SpanMixin.merge_overlapping(genes)
            for span in genespans:
                if not re.match(rx, span.chrom):
                    if re.match(fixable, span.chrom):
                        span.chrom = 'chr{}'.format(span.chrom)
                    else:
                        raise ValueError('bad chromosome name: {}'.format(span.chrom))
                chrm_fa = os.path.join(ref_genome_dir, '{}.fa'.format(span.chrom))
                seq_fa = fastasize(get_seq(chrm_fa, span.start, span.stop))
                title = '>{}_{}_{}_{}'.format(span.chrom, span.gene, span.start, span.stop)
                output.write('{}\n'.format(title))
                output.write('{}\n'.format(seq_fa.strip()))
                
########################################################################

def create_fasta_fai(ref_fa, samtools):
    try:
        cmd = [samtools, 'faidx', ref_fa]
        output = sp.check_output(cmd, stderr=sp.PIPE)
        return output
    except sp.CalledProcessError as e:
        cmd_str = ' '.join(cmd)
        setattr(e, 'cmd', cmd_str)
        raise e

def bowtie2_build(fasta_fn, bowtie_idxs, idx_name, bowtie2_build_exe):
    ''' 
    call bowtie2-build to create bowtie2 indexes from a .fasta file.
    returns the output of the bowtie2 build command.
    '''
    ensure_folder(bowtie_idxs)
    bt_build_cmd = [bowtie2_build_exe, fasta_fn, os.path.join(bowtie_idxs, idx_name)]

    try:
        output = sp.check_output(bt_build_cmd, stderr=sp.PIPE)
        return output
    except sp.CalledProcessError as e:
        cmd_str = ' '.join(bt_build_cmd)
        setattr(e, 'cmd', cmd_str)
        raise e


def grep_indels(vcf_file, filter_field=7, filter_str='INDEL'):
    ''' 
    extract variants marked as INDEL from a vcf file 
    '''
    with open(vcf_file) as f:
        reader = csv.reader(f, delimiter='\t')
        for fields in reader:
            if fields[0].startswith('##'):
                continue
            if fields[0].startswith('#'):
                field_names = fields
                field_names[0] = field_names[0].replace('#', '')
                continue
            if filter_str not in fields[filter_field]:
                continue
            yield {f:v for f,v in zip(field_names, fields)}
                
                

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
