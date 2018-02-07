'''
A mixin class that knows how to merge overlapping spans together.
'''
from strings import ppjson, qw

class SpanMixin(object):
    def __init__(self, start, stop):
        self.start = min(start, stop)
        self.stop = max(start, stop)

    def __eq__(self, other):
        return self.start == other.start and self.stop == other.stop
    
    def __cmp__(self, other):
        if self.start < other.start:
            return -1
        if self.start == other.start:
            return 0
        return 1

    def __repr__(self):
        return 'S({}, {})'.format(self.start, self.stop)

    def overlap(self, other):
        if (other.start <= self.start and other.stop >= self.start) or (other.start <= self.stop and other.stop >= self.stop):
            return True
        if (self.start >= other.start and self.stop <= other.stop) or (self.start <= other.start and self.stop >= other.stop):
            return True
        return False

    def merge(self, other):
        ''' merge 'other' into self '''
        self.start = min(self.start, other.start)
        self.stop = max(self.stop, other.stop)
        return self
    
    @staticmethod
    def merge_overlapping(spans):
        answer = set()
        for span in spans:
            to_rm = [blob for blob in answer if span.overlap(blob)]
            for blob in to_rm:
                span = span.merge(blob)
                answer.remove(blob)
            answer.add(span)
        answer = list(answer)
        answer.sort()
        return answer

if __name__ == '__main__':
    # verify correctness of ovlp:
    s1 = SpanMixin(10, 20)
    s2_data = ((1,5), (5,10), (11,12), (18, 22), (23,38), (9, 21))
    s2s = [SpanMixin(*t) for t in s2_data]
    exp = [False, True, True, True, False, True]
    answer = [s2.overlap(s1) == exp[i] for i, s2 in enumerate(s2s)]
    assert all(answer)

    # overlap w/reverse orders:
    s2_data = ((5,1), (10,5), (12,11), (22, 18), (38,23), (21, 9)) 
    s2s = [SpanMixin(*t) for t in s2_data]
    answer = [s2.overlap(s1) == exp[i] for i, s2 in enumerate(s2s)]
    assert all(answer)
    print 'overlap passes'

    # test merge:
    data = (
        ((1, 5), (4, 8)),
        ((23, 34), (43, 48), (48, 52), (51, 59), (62, 67)),
        ((23, 34),),
        ((1,3),(3,1)),
        ((3,4), (1,2)),
        ((3,4), (1,6)),
        )
    expected = (
        ((1, 8),),
        ((23, 34), (43, 59), (62, 67)),
        ((23, 34),),
        ((1,3),),
        ((1,2),(3,4)),
        ((1,6),),
    )

    for spans_data, exp_data in zip(data, expected):
        spans = [SpanMixin(*t) for t in spans_data]
        new_l = SpanMixin.merge_overlapping(spans)
        exp_l = [SpanMixin(*t) for t in exp_data]
        print ppjson('new_l: {}'.format(new_l))
        print ppjson('exp_l: {}'.format(exp_l))
        assert new_l == exp_l, "{} != {}".format(new_l, exp_l)
        print
    
