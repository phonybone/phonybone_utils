def keystr(d, connector=', '):
    return connector.join(d.keys())

def hashslice(d, *keys):
    return [d[k] for k in keys]

def hashtuple(d, *keys):
    return tuple(hashslice(*keys))

def to_dict(config, section):
    ''' return the section of config as a dict '''
    return {k:v for k,v in config.items(section)}

def hashsubset(d, *keys):
    return {k:d[k] for k in keys}
