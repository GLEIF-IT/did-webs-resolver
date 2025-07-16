# -*- encoding: utf-8 -*-
"""
dkr.app.cli.commands module

"""

import argparse
import logging

from keri.app import configing, directing, habbing, keeping, oobiing
from keri.app.cli.common import existing

from dkr import log_name, ogler
from dkr.core import resolving

parser = argparse.ArgumentParser(description='Expose did:keri resolver as an HTTP web service')
parser.set_defaults(handler=lambda args: launch(args), transferable=True)
parser.add_argument(
    '-p',
    '--http',
    action='store',
    default=7678,
    help='Port on which to listen for did:keri resolution requests.  Defaults to 7678',
)
parser.add_argument('-n', '--name', action='store', default='dkr', help='Name of controller. Default is dkr.')
parser.add_argument(
    '--base', '-b', help='additional optional prefix to file location of KERI keystore', required=False, default=''
)
parser.add_argument(
    '--passcode', help='22 character encryption passcode for keystore (is not saved)', dest='bran', default=None
)  # passcode => bran
parser.add_argument('--config-dir', '-c', dest='config_dir', help='directory override for configuration data', default=None)
parser.add_argument('--config-file', dest='config_file', action='store', default=None, help='configuration filename override')
parser.add_argument(
    '--loglevel',
    action='store',
    required=False,
    default='CRITICAL',
    help='Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL',
)

logger = ogler.getLogger(log_name)


def launch(args, expire=0.0):
    ogler.level = logging.getLevelName(args.loglevel.upper())
    logger.setLevel(ogler.level)
    name = args.name
    base = args.base
    bran = args.bran
    http_port = args.http

    config_file = args.config_file
    config_dir = args.config_dir

    ks = keeping.Keeper(name=name, base=base, temp=False, reopen=True)

    aeid = ks.gbls.get('aeid')

    cf = None
    if aeid is None:
        if config_file is not None:
            cf = configing.Configer(name=config_file, base=base, headDirPath=config_dir, temp=False, reopen=True, clear=False)

        hby = habbing.Habery(name=name, base=base, bran=bran, cf=cf)
    else:
        hby = existing.setupHby(name=name, base=base, bran=bran)

    hby_doer = habbing.HaberyDoer(habery=hby)  # setup doer
    oobiery = oobiing.Oobiery(hby=hby)

    doers = oobiery.doers + [hby_doer]
    doers += resolving.setup(hby, hby_doer, oobiery, http_port=http_port)

    logger.info(f'Launched did:keri resolver as an HTTP web service on {http_port}')
    return doers
