from pbutils.configs import load_attributes_from_config, get_config_from_data


def test_load_attributes_from_config_booleans():
    conf_data = '''
[default]
t = true
f = false
'''
    # conf = get_config('tests/configs/config.ini')
    conf = get_config_from_data(conf_data)
    class Obj:
        pass
    obj = Obj()
    load_attributes_from_config(obj, conf, 'default', prepend_section=False, overwrite=False)

    assert hasattr(obj, 't')
    assert obj.t
    assert hasattr(obj, 'f')
    assert not obj.f
