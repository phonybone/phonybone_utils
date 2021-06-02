import json
import pkg_resources as pr
from pbutils.dicts import traverse_json, is_scalar, drill_path


def test_traverse_all():
    fn = pr.resource_filename('pbutils', 'request/profiles/get.dev.41.json')
    with open(fn) as json_file:
        profiles = json.load(json_file)
    for path, value in traverse_json(profiles):
        ppath = 'profiles' + ''.join([F"[{elem}]" for elem in path])
        print(F"{ppath} = {value}")
        assert drill_path(profiles, path) == value


def test_traverse_leaves_only():
    fn = pr.resource_filename('pbutils', 'request/profiles/get.dev.41.json')
    with open(fn) as json_file:
        profiles = json.load(json_file)
    for path, value in traverse_json(profiles, only_leaves=True):
        ppath = 'profiles' + ''.join([F"[{elem}]" for elem in path])
        print(F"{ppath} = {value}")
        assert is_scalar(value)
        assert drill_path(profiles, path) == value
