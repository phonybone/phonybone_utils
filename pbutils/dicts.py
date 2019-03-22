import json


def keystr(d, connector=', '):
    return connector.join(d.keys())


def hashslice(d, *keys):
    return [d[k] for k in keys]


def hashtuple(d, *keys):
    return tuple(hashslice(d, *keys))


def to_dict(config, section):
    ''' return the section of config as a dict '''
    return config.items(section)


def hashsubset(d, *keys):
    return {k: d[k] for k in keys}


def json_copy(d):
    ''' make a copy of raw data by converting to json and back (faster than copy.deepcopy for simple data) '''
    return json.loads(json.dumps(d))


def from_attrs(obj, keys=None, include_nones=False):
    ''' return a dictionary based on an object's attributes '''
    if keys is None:
        keys = obj.__dict__.keys()
    return hashsubset(obj.__dict__, *keys)


def remove_nones(d):
    keys0 = [k for k in d.keys() if d[k] is None]
    for k in keys0:
        del d[k]
    return d


if __name__ == '__main__':
    d = dict(this='that', these='those', n=None)
    print(json.dumps(remove_nones(d)))
