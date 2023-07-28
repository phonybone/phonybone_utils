'''
Implement a simple (naive) LRU cache
'''

class LRUCacheNode:
    def __init__(self, key, value, nxt=None, prv=None):
        self.key = key
        self.value = value
        self.nxt = nxt
        self.prv = prv

    def __str__(self):
        nxt_key = self.nxt.key if self.nxt else '<none>'
        prv_key = self.prv.key if self.prv else '<none>'
        return F"[{self.key}]: nxt={nxt_key} prv={prv_key}"

class LRUCache:
    def __init__(self, max_size):
        self.max_size = max_size
        self.size = 0
        self.cache = {}
        self._first_key = None
        self._last_key = None
        
    def __repr__(self):
        return F"size={self.size}/{self.max_size}, first={self._first_key}, last={self._last_key}"

    def _first_node(self):
        ''' return the first '''
        if self._first_key is None:
            return None
        return self.cache[self._first_key]

    def first(self):
        ''' return the first (newest) value in cache, or None if empty '''
        node = self._first_node()
        return node.value if node is not None else None

    def _last_node(self):
        if self._last_key is None:
            return None
        return self.cache[self._last_key]

    def last(self):
        ''' return the last (oldest) value in cache, or None if empty '''
        node = self._last_node()
        return node.value if node is not None else None

    def insert(self, key, value):
        '''
        insert value at [key]; inserted value is now most recent.
        returns new node (hmmn...)
        '''
        
        # key already present?  replace:
        if key in self.cache:
            old_node = self.remove(key)

        # insert as first:
        node = LRUCacheNode(key=key, value=value, nxt=self._first_node(), prv=None)

        old_first = self._first_node()
        if old_first is not None:
            old_first.prv = node

        self.cache[key] = node
        self._first_key = key
        self.size += 1
        if self.size == 1:
            self._last_key = key


        if self.size > self.max_size:
            old_last = self.remove(self._last_key)

        return node
        
    def remove(self, key):
        ''' remove and return node, maintain chain '''
        old_node = self.cache[key]
        if old_node.nxt:
            old_node.nxt.prv = old_node.prv
            
        if old_node.prv:
            old_node.prv.nxt = old_node.nxt

        if old_node.key == self._first_key:
            self._first_key = old_node.nxt.key if old_node.nxt else None
        if old_node.key == self._last_key:
            self._last_key = old_node.prv.key if old_node.prv else None

        del self.cache[key]
        self.size -= 1
        return old_node

    def get(self, key, default=None):
        ''' fetch the value at [key], or default if key not present '''
        return getattr(self.cache.get(key, default), 'value', None)

    def _nodes(self):
        node = self._first_node()
        while True:
            if node is None:
                return
            yield node
            node = node.nxt
            # what happens if node is deleted???

    def keys(self):
        ''' iterate through keys from newest to oldest '''
        for node in self._nodes():
            yield node.key

    def values(self):
        ''' iterate through values from newest to oldest '''
        for node in self._nodes():
            yield node.value


if __name__ == '__main__':
    def dump(cache):
        print(F"{cache!r}")
        for key in cache.keys():
            value = cache.get(key)
            print(F"cache[{key}]={value}")
        print('-' * cache.size)

    cache = LRUCache(4)
    assert cache.size == 0
    assert cache._first_key is None
    assert cache._last_key is None
    
    n1 = cache.insert('one', 1)
    dump(cache)
    assert cache.size == 1
    assert cache._first_key == 'one'
    assert cache._last_key == 'one'
    assert cache.first() == 1
    assert cache.last() == 1
    assert n1.key == 'one'
    assert n1.nxt is None
    assert n1.prv is None

    n2 = cache.insert('two', 2)
    dump(cache)
    assert cache.size == 2
    assert cache._first_key == 'two'
    assert cache._last_key == 'one'
    assert cache.first() == 2
    assert cache.last() == 1
    assert n2.key == 'two'
    assert n2.nxt is n1
    assert n2.prv is None

    assert n1.prv is n2, F"n1.prv={n1.prv}"
    assert n1.nxt is None
    
    n3 = cache.insert('three', 3)
    dump(cache)

    n4 = cache.insert('four', 4)
    dump(cache)
    assert cache.size == 4
    assert cache._first_key == 'four'
    assert cache._last_key == 'one'
    assert cache.first() == 4
    assert cache.last() == 1
    assert n4.key == 'four'
    assert n4.nxt is n3
    assert n4.prv is None

    assert n1.prv is n2, F"n1.prv={n1.prv}"
    assert n1.nxt is None
            
    n5 = cache.insert('five', 5)
    dump(cache)
    assert cache.size == 4
    assert cache._first_key == 'five'
    assert cache._last_key == 'two'
    assert cache.first() == 5
    assert cache.last() == 2
    assert n5.key == 'five'
    assert n5.nxt is n4
    assert n5.prv is None

    assert n4.prv is n5
    assert n4.nxt is n3

    # remove a node
    try:
        cache.remove('one')
    except KeyError as e:
        assert str(e) == "'one'"

    print('-' * 32)
    cache.remove('two')
    dump(cache)
    assert cache._first_key == 'five'
    assert cache._last_key == 'three'
    assert cache.first() == 5
    assert cache.last() == 3

    cache.remove('four')
    dump(cache)
    assert cache._first_key == 'five'
    assert cache._last_key == 'three'
    assert cache.first() == 5
    assert cache.last() == 3

    cache.remove('three')
    dump(cache)
    assert cache._first_key == 'five'
    assert cache._last_key == 'five'
    assert cache.first() == 5
    assert cache.last() == 5

    cache.remove('five')
    dump(cache)
    assert cache.size == 0
    assert cache._first_key is None
    assert cache._last_key is None
    assert cache.first() is None
    assert cache.last() is None

    # update a node
    cache.insert('six', 6)
    dump(cache)
    assert cache.size == 1
    assert cache._first_key == 'six'
    assert cache._last_key == 'six'

    cache.insert('six', 'fart')
    dump(cache)
    assert cache.get('six') == 'fart'
    assert cache.size == 1
    assert cache._first_key == 'six'
    assert cache._last_key == 'six'
    assert cache.first() == 'fart'
    assert cache.last() == 'fart'

    print('yay')
