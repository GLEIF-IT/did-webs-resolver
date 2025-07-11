# -*- encoding: utf-8 -*-
"""
dkr.app.cli.commands.resolver-service module

"""

import argparse
import logging

from keri.app import configing, directing, habbing, keeping, oobiing
from keri.app.cli.common import existing

from dkr import log_name, ogler
from dkr.core import resolving

parser = argparse.ArgumentParser(description='Expose did:webs resolver as an HTTP web service')
parser.set_defaults(handler=lambda args: launch(args), transferable=True)
parser.add_argument(
    '-p',
    '--http',
    action='store',
    default=7677,
    help='Port on which to listen for did:webs resolution requests.  Defaults to 7677',
)
parser.add_argument('-n', '--name', action='store', default='dkr', help='Name of controller. Default is dkr.')
parser.add_argument(
    '-b', '--base', required=False, default='', help='additional optional prefix to file location of KERI keystore'
)
# passcode => bran
parser.add_argument(
    '--passcode', dest='bran', default=None, help='22 character encryption passcode for keystore (is not saved)'
)
parser.add_argument('-c', '--config-dir', dest='configDir', default=None, help='directory override for configuration data')
parser.add_argument('--config-file', dest='configFile', action='store', default=None, help='configuration filename override')
parser.add_argument(
    '--static-files-dir',
    dest='staticFilesDir',
    action='store',
    default='static',
    help='static files directory to use for serving the did.json and keri.cesr files. Default is "static"',
)
parser.add_argument(
    '--loglevel',
    action='store',
    required=False,
    default='CRITICAL',
    help='Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL',
)

logger = ogler.getLogger(log_name)


def launch(args, expire=0.0):
    """
    Launches a Falcon webserver listening on /1.0/identifiers/{did} for did:webs resolution requests
    as a set of Doers
    """
    ogler.level = logging.getLevelName(args.loglevel.upper())
    logger.setLevel(ogler.level)
    name = args.name
    base = args.base
    bran = args.bran
    httpPort = args.http

    configFile = args.configFile
    configDir = args.configDir
    staticFilesDir = args.staticFilesDir

    ks = keeping.Keeper(name=name, base=base, temp=False, reopen=True)

    aeid = ks.gbls.get('aeid')

    cf = None
    if configFile is not None:
        cf = configing.Configer(name=configFile, base=base, headDirPath=configDir, temp=False, reopen=True, clear=False)
    if aeid is None:
        hby = habbing.Habery(name=name, base=base, bran=bran, cf=cf)
    else:
        hby = existing.setupHby(name=name, base=base, bran=bran, cf=cf)

    hbyDoer = habbing.HaberyDoer(habery=hby)  # setup doer
    obl = oobiing.Oobiery(hby=hby)

    doers = obl.doers + [hbyDoer]
    doers += resolving.setup(hby, hbyDoer, obl, httpPort=httpPort, cf=cf, staticFilesDir=staticFilesDir)

    logger.info(f'Launched did:webs resolver on {httpPort}')
    return doers
