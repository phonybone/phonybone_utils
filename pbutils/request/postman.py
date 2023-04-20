import json
try:
    import demjson
    HAS_DEMJSON = True
except ImportError:
    HAS_DEMJSON = False


def is_postman(profiles):
    ''' are requests in postman format?  return True or False '''
    return isinstance(profiles, list) and \
        len(profiles) == 1 and \
        isinstance(profiles[0], dict) and \
        isinstance(profiles[0].get('info'), dict) and \
        '_postman_id' in profiles[0]['info']


def postman2areq(profiles, postman_env_fn):
    profiles = convert2areq(profiles)
    if postman_env_fn:
        with open(postman_env_fn) as fyle:
            if HAS_DEMJSON:
                pm_env = demjson.decode(fyle.read())
            else:
                pm_env = json.load(fyle)
            add_postman_env(profiles, pm_env)
    return profiles


def convert2areq(profiles):
    ''' Convert postman json into arequest profiles '''
    new_profiles = []
    for pm_req in profiles[0]['item']:
        req = pm_req['request']

        # extract basics:
        prof = {
            'name': pm_req['name'],
            'method': req['method'],
            'header': req['header'],
            'url': req['url']['raw'],
        }

        # querystring params:
        params = req.get('params')
        if isinstance(params, dict):
            prof['params'] = params

        # body:
        body = _extract_body(req)
        if body is not None:
            # assert isinstance(body, dict), F"type(body)={type(body)}"
            prof['body'] = body

        # change all '{{' and '}}' to '{' and '}':
        _fix_brackets(prof)
        new_profiles.append(prof)
    return new_profiles


def _extract_body(req):
    ''' extract and transform the body of the request '''
    try:
        mode = req['body']['mode']
        body = req['body'][mode]
    except KeyError as e:
        return None

    if mode == 'raw':
        # body = body.replace('\n', '')  # remove literal r'\n's
        # body = body.replace("'", '"')
        # regex = re.compile(r'([\w_]+):')  # ' -> " in keys
        # body = regex.subn(r'"\1":', body)[0]
        # body = eval(body)
        pass

    elif mode == 'formdata':
        if isinstance(body, list):
            if len(body) != 1:
                raise ValueError(F"formdata list has {len(body)} elements")
            body = {thing['key']:thing['value'] for thing in body}
        bodytext = json.dumps(body).replace('{{', '{').replace('}}', '}')
        body = json.loads(bodytext)
        
    elif mode == 'python':
        assert isinstance(body, dict)

    return body


def _fix_brackets(prof):
    for key in prof.keys():
        value = prof[key]
        if isinstance(value, str):
            value = value.replace('{{', '{').replace('}}', '}')
            prof[key] = value


def add_postman_env(profiles, pm_env):
    env = {value['key']:value['value'] for value in pm_env['values']}
    for profile in profiles:
        varrs = profile.setdefault('vars', {})
        varrs.update(env)
