"""
This is the doctring.
"""

from pbutils.argparsers import parser_stub, wrap_main
from pbutils.strings import ppjson


def main(config):
    print('this is main')
    for section in config.sections():
        print(F"[{section}]\n{ppjson(dict(config.items(section)))}")
    return 1


def make_parser():
    parser = parser_stub(__doc__)
    parser.add_argument('required_arg')
    parser.add_argument('-i', '--input-file', help='input file', default='-')
    parser.add_argument('--section1.key2', default='fred')
    return parser


if __name__ == '__main__':
    parser = make_parser()
    wrap_main(main, parser)
