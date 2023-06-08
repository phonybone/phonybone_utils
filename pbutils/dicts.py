import json
from types import SimpleNamespace
from functools import partial

json2 = partial(json.dumps, indent=2)
json4 = partial(json.dumps, indent=4)


def keystr(d, connector=', '):
    ''' return a string containing all keys of dict joined by 'connector' '''
    return connector.join(d.keys())


def hashslice(d, *keys):
    ''' return a list of dict values for the given keys '''
    return [d[k] for k in keys]


def hashtuple(d, *keys):
    ''' return a tuple of dict values for the given keys '''
    return tuple(hashslice(d, *keys))


def hashsubset(d, *keys):
    ''' return a subset of a dict for the given keys '''
    return {k: d[k] for k in keys}


def to_dict(config, section):
    ''' return the section of config as a dict '''
    # why is this here?
    return config.items(section)


def json_copy(d):
    '''
    Make a copy of raw data by converting to json and back
    (faster than copy.deepcopy for simple data).
    '''
    return json.loads(json.dumps(d))


def from_attrs(obj, keys=None, include_nones=False):
    ''' return a dictionary based on an object's attributes (kinda like var() '''
    if keys is None:
        keys = obj.__dict__.keys()
    return hashsubset(obj.__dict__, *keys)


def remove_nones(d):
    ''' del d[k] from d if d[k] is None '''
    for k, v in d.items():
        if v is None:
            del d[k]
    return d


def simple_diff(d1, d2):
    '''
    Return 3-elem tuple containing lists of keys:
    [0]: keys in d1 that are not in d2
    [1]: keys in d2 that are not in d1
    [2]: keys where d1[k] != d2[k]
    '''
    missing_d2 = [k1 for k1 in d1.keys() if k1 not in d2]
    missing_d1 = [k2 for k2 in d2.keys() if k2 not in d1]
    diff_keys = [k1 for k1, v1 in d1.items() if k1 in d2 and v1 != d2[k1]]
    return missing_d2, missing_d1, diff_keys


def json_to_object(data_str: str) -> SimpleNamespace:
    '''
    Return a nested object based on a json string.

    For instance, on input
    {
        "k1": {
            "k1_1": "v1",
            "k1_2": ["k1_2.1", "k1_2.2"],
            "k1_3": 3.14159
        }
    }

    the function should rturn a SimpleNamspace object like:
    o.k1.k1_1 = "v1"
    o.k1.k1_2 = ["k1_2.1", "k1_2.2"]
    o.k1.k1_3 = 3.14159

    Can throw on bad data.  Note in particular that key names can only contain
    characters allowable for attributes.
    '''
    return json.loads(data_str, object_hook=lambda obj: SimpleNamespace(**obj))


def traverse_json(data, path=None, only_leaves=False):
    '''
    Traverse json data; yield (path, value) for all paths
    within data where path is a list of dict keys or list indexes
    that "lead" to the value.
    '''
    if path is None:
        path = []

    if is_scalar(data):
        yield path, data

    elif isinstance(data, dict):
        for key, value in data.items():
            if not is_scalar(value) and not only_leaves:
                yield path + [key], value
            yield from traverse_json(value, path + [key], only_leaves)

    elif isinstance(data, (list, tuple)):
        for idx, value in enumerate(data):
            if not is_scalar(value) and not only_leaves:
                yield path + [idx], value
            yield from traverse_json(value, path + [idx], only_leaves)

    else:
        raise TypeError(type(data))


def get_path_value(data, path):
    '''
    Get the value in data indicated by path.
    path is a list of keys/indexes.
    Raise IndexError or KeyError as necessary.
    '''
    root = data
    for elem in path:
        print(F"trying for {root}.{elem}")
        try:
            root = getattr(root, elem)
        except AttributeError:
            root = root[elem]
    return root


def set_path_value(data, path, value):
    '''
    Set the value in data indicated by path.
    path is a list of keys/indexes.
    Raise IndexError or KeyError as necessary.
    '''
    root = data
    for elem in path[:-1]:
        root = root[elem]
    root[path[-1]] = value


def create_path_value(data, path, value):
    '''
    Similar to set_path_value, but creates new dicts as needed.
    Does not work for type(int) values in path (which would normally
    be considered list indexes).
    '''
    root = data
    for elem in path[:-1]:
        root = root.setdefault(elem, {})
    root[path[-1]] = value


def is_scalar(thing):
    '''
    Return true if thing is of one-dimensional type:
    IE, None, str, bytes, int, float, or bool.
    '''
    return thing is None or isinstance(thing, (str, bytes, int, float, bool))


if __name__ == '__main__':
    import sys
    from streams import die

    def test_remove_nones():
        d = dict(this='that', these='those', n=None)
        print(json.dumps(remove_nones(d)))

    def test_json_to_object():
        data_str = '''
{
  "this": "that",
  "these": ["those", "them", "there"],
  "bike_colors": {
    "honda": "red", "ktm": "orange", "suzuki": "yellow", "kawasaki": "green"
  },
  "somelist": [
    {
      "id": 1,
      "name": "joe",
      "birthday": "Apr 1, 2001"
    },
    {
      "id": 2,
      "name": "frank",
      "birthday": "June 1, 2001"
    },
    {
      "id": 3,
      "name": "mary",
      "birthday": "May 1, 2001"
    }
  ],
  "uh-oh": "this should not explode",
  "uh.oh": "this doesn't either"
}
'''
        obj = json_to_object(data_str)
        assert obj.this == 'that'
        assert obj.bike_colors.honda == 'red'
        assert obj.somelist[2].name == 'mary'
        assert getattr(obj, "uh.oh") == "this doesn't either"
        print('yay')

    def test_create_path_value():
        data = {}
        create_path_value(data, ['this', 'these'], 'those')
        create_path_value(data, ['this', 'those'], 'blah')
        create_path_value(data, ['this', 'them', 'whatevs'], 'these')
        create_path_value(data, ['those'], 'these')
        create_path_value(data, ['list'], [None])  # this is pretty hacky, but...
        create_path_value(data, ['list', 0], 'fart')

        print(json.dumps(data, indent=4))

    ########################################################################
    cmds = [key for key, value in locals().items() if key.startswith('test_') and callable(value)]
    usage = F"usage: python dicts.py [{'|'.join(cmds)}]"
    if len(sys.argv) <= 1:
        die(usage)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    method = locals().get(cmd)
    if method is None:
        die(usage)
    method(*args)
