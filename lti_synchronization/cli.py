import typing
from pathlib import Path
import os
import sys
import argparse
from moodle import synchronize
from moodle.settings import BASE_DIR, DESCRIPTION


def path_type(json_path: typing.Union[str, Path]) -> Path:
    '''
    Calls sys.exit if path cannot not found.
    '''

    if os.path.exists(json_path):
        return Path(json_path)

    if os.path.exists(BASE_DIR / json_path):
        return BASE_DIR / json_path

    sys.exit(f'Cannot find a path: {json_path!r}')


parser = argparse.ArgumentParser(
    usage='lti_synchronization --in_path data/data.json',
    prog='LTI Synchronization',
    epilog='''

Development team:
  Maintained by Anton Bagryanov


    ''',
    description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('--path_in', type=path_type, help='''
Provide a path to the JSON where you list all courses you need to process.
''', default=BASE_DIR / 'data' / 'data.json')

parser.add_argument('--path_out', help='''
Specify a path to the JSON where you'd like to store proccesed data.
If not specified, all data will be processed in-memory.
''')

args = parser.parse_args()

if args.path_out:
    args.path_out = BASE_DIR / args.path_out

synchronize(json_in=args.path_in, json_out=args.path_out)
