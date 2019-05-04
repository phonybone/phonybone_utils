'''
A mixin class that knows how to merge overlapping spans together.
'''


class SpanMixin(object):
    def __init__(self, start, stop):
        self.start = min(start, stop)
        self.stop = max(start, stop)

    def __eq__(self, other):
        return self.start == other.start and self.stop == other.stop

    def __neq__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.start < other.start or\
            self.start == other.start and self.stop < other.stop

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return self < other or self == other

    def __hash__(self):
        return id(self)

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
        # this is busted; not sure what args are really supposed to be (SpanMixins?  Regular tuples?)
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
    exps = [False, True, True, True, False, True]
    assert all([s2.overlap(s1) == exp for s2, exp in zip(s2s, exps)])

    # overlap w/reverse orders:
    s2_data = ((5,1), (10,5), (12,11), (22, 18), (38,23), (21, 9))
    s2s = [SpanMixin(*t) for t in s2_data]
    assert all([s2.overlap(s1) == exp for s2, exp in zip(s2s, exps)])

    def test_cmp_ops():
        assert SpanMixin(1, 2) < SpanMixin(2, 2)
        assert SpanMixin(1, 2) < SpanMixin(1, 3)

        assert SpanMixin(1, 2) == SpanMixin(1, 2)
        assert SpanMixin(1, 2) <= SpanMixin(1, 2)
        assert SpanMixin(1, 2) >= SpanMixin(1, 2)

        assert SpanMixin(3, 4) > SpanMixin(2, 3)
        assert SpanMixin(1, 2) < SpanMixin(2, 4)

        assert SpanMixin(1, 2) != SpanMixin(2, 2)

    def test_merge_overlapping():
        data = (
            ((1, 5), (4, 8)),
            ((23, 34), (43, 48), (48, 52), (51, 59), (62, 67)),
            ((23, 34), (25, 26)),
            ((1, 3), (3, 1)),
            ((3, 4), (1, 2)),
            ((3, 4), (1, 6)),
        )
        expected = (
            ((1, 8),),
            ((23, 34), (43, 59), (62, 67)),
            ((23, 34),),
            ((1, 3),),
            ((1, 2), (3, 4)),
            ((1, 6),),
        )

        for datum, exp_d in zip(data, expected):
            # print(F"datum: {datum}")
            spans = [SpanMixin(*d) for d in datum]
            new_l = SpanMixin.merge_overlapping(spans)
            # print(F'new_l: {new_l}')
            # print(ppjson('exp_d: {}'.format(exp_d)))
            assert len(new_l) == len(exp_d)
            for s1, s2 in zip(new_l, exp_d):
                assert s1 == SpanMixin(*s2), "{} != {}".format(new_l, exp_d)
            # print('-----')

    test_merge_overlapping()
    test_cmp_ops()
    print("yay")
