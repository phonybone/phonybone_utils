'''
'''

class BoundingBox:
    def __init__(self, top, left, bottom, right):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def __str__(self):
        t = float(self.top)
        l = float(self.left)
        b = float(self.bottom)
        r = float(self.right)
        return F"({t:.2f}, {l:.2f}), ({b:.2f},{r:.2f})"

    @classmethod
    def from_list(cls, pts: list):
        '''
        pts: list of tuples (x,y)
        '''
        max_top = pts[0][1]
        min_left = pts[0][0]
        min_bottom = pts[0][1]
        max_right = pts[0][0]

        for pt in pts:
            max_top = max(max_top, pt[0])
            min_left = min(min_left, pt[0])
            min_bottom = min(min_bottom, pt[0])
            max_right = max(max_right, pt[0])
        return cls(max_top, min_left, min_bottom, max_right)

    @property
    def area(self):
        return abs((self.right - self.left) * (self.top - self.bottom))

    def intersection(self, other):
        min_top = min(self.top, other.top)
        max_left = max(self.left, other.left)
        max_bottom = max(self.bottom, other.bottom)
        min_right = min(self.right, other.right)
        if min_top < max_bottom or max_left > min_right:
            return None         # no intersection
        return BoundingBox(min_top, max_left, max_bottom, min_right)

    def union(self, other):
        max_top = max(self.top, other.top)
        min_left = min(self.left, other.left)
        min_bottom = min(self.bottom, other.bottom)
        max_right = max(self.right, other.right)
        return BoundingBox(max_top, min_left, min_bottom, max_right)
    
if __name__ == '__main__':
    bb1 = BoundingBox(10, 0, 0, 10)
    bb2 = BoundingBox(5, -5, -5, 5)
    print(F"bb1: {bb1}; area={bb1.area}")
    print(F"bb2: {bb2}; area={bb2.area}")
    print(F"bb1 union bb2: {bb1.union(bb2)}")
    print(F"bb1 intersection bb2: {bb1.intersection(bb2)}")

