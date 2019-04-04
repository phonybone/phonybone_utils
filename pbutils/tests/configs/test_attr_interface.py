from pbutils.configs import get_config_from_data


def test_attr_interface():
    conf_data = '''
[default]
this = that
these = those

[orwell]
war = peace
ignorance = strength
freedom = slavery
'''
    # conf = get_config('tests/configs/config.ini')
    conf = get_config_from_data(conf_data)

    assert hasattr(conf, 'default')
    assert hasattr(conf, 'orwell')
    assert not hasattr(conf, 'fart')

    assert conf.default.this == 'that'
    assert conf.default.these == 'those'
    assert conf.this == 'that'
    assert conf.these == 'those'

    assert conf.orwell.war == 'peace'
    assert conf.orwell.ignorance == 'strength'
    assert conf.orwell.freedom == 'slavery'

    assert not hasattr(conf.orwell, 'fart')
