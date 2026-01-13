# -*- encoding: utf-8 -*-
"""
dws.app.cli.commands module

"""

import multicommand
from keri.app import directing

from dws.app.cli import commands


def main():
    """Run the dws CLI app."""
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()

    if not hasattr(args, 'handler'):
        parser.print_help()
        return 0

    try:
        doers = args.handler(args)
        directing.runController(doers=doers, expire=0.0)
        return 0
    except Exception as ex:
        import os

        if os.getenv('DEBUG_DWS'):
            import traceback

            traceback.print_exc()
        else:
            print(f'ERR: {ex}')
        return -1


if __name__ == '__main__':
    main()
