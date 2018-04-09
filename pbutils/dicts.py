import json

def keystr(d, connector=', '):
    return connector.join(d.keys())

def hashslice(d, *keys):
    return [d[k] for k in keys]

def hashtuple(d, *keys):
    return tuple(hashslice(d, *keys))

def to_dict(config, section):
    ''' return the section of config as a dict '''
    return {k:v for k,v in config.items(section)}

def hashsubset(d, *keys):
    return {k:d[k] for k in keys}

def json_copy(d):
    ''' make a copy of raw data by converting to json and back (faster than copy.deepcopy for simple data) '''
    return json.loads(json.dumps(d))
