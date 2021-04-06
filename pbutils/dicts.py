import json
from types import SimpleNamespace


def keystr(d, connector=', '):
    return connector.join(d.keys())


def hashslice(d, *keys):
    return [d[k] for k in keys]


def hashtuple(d, *keys):
    return tuple(hashslice(d, *keys))


def hashsubset(d, *keys):
    return {k: d[k] for k in keys}


def to_dict(config, section):
    ''' return the section of config as a dict '''
    # why is this here?
    return config.items(section)


def json_copy(d):
    ''' make a copy of raw data by converting to json and back (faster than copy.deepcopy for simple data) '''
    return json.loads(json.dumps(d))


def from_attrs(obj, keys=None, include_nones=False):
    ''' return a dictionary based on an object's attributes '''
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
    ''' return a nested object based on a json string; can throw on bad data. '''
    return json.loads(data_str, object_hook=lambda obj: SimpleNamespace(**obj))


if __name__ == '__main__':
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
  ]
}
'''
        obj = json_to_object(data_str)
        assert obj.this == 'that'
        assert obj.bike_colors.honda == 'red'
        assert obj.somelist[2].name == 'mary'
        print('yay')

    test_json_to_object()
