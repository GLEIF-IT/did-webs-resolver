# -*- encoding: utf-8 -*-
"""
dkr.app.cli.commands module

"""

import argparse
import logging

import falcon
import hio
import hio.core.tcp
import viking
from hio.core import http
from keri.app import configing, habbing, oobiing
from keri.app.cli.common import existing

from dkr import log_name, ogler
from dkr.core import webbing

parser = argparse.ArgumentParser(description='Launch web server capable of serving KERI AIDs as did:webs and did:web DIDs')
parser.set_defaults(handler=lambda args: launch(args), transferable=True)
parser.add_argument('-p', '--http', action='store', default=7676, help='Port on which to listen for did:webs requests')
parser.add_argument('-n', '--name', action='store', default='dkr', help='Name of controller. Default is dkr.')
parser.add_argument('-a', '--alias', action='store', default='dkr', help='Alias of controller. Default is dkr.')
parser.add_argument(
    '--base', '-b', help='additional optional prefix to file location of KERI keystore', required=False, default=''
)
parser.add_argument(
    '--passcode', help='22 character encryption passcode for keystore (is not saved)', dest='bran', default=None
)  # passcode => bran
parser.add_argument('--config-dir', '-c', dest='config_dir', help='directory override for configuration data', default=None)
parser.add_argument('--config-file', dest='config_file', action='store', default='dkr', help='configuration filename override')
parser.add_argument('--keypath', action='store', required=False, default=None)
parser.add_argument('--certpath', action='store', required=False, default=None)
parser.add_argument('--cafilepath', action='store', required=False, default=None)
parser.add_argument(
    '--loglevel',
    action='store',
    required=False,
    default='CRITICAL',
    help='Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL',
)

logger = ogler.getLogger(log_name)


def launch(args):
    ogler.level = logging.getLevelName(args.loglevel.upper())
    logger.setLevel(ogler.level)
    name = args.name
    alias = args.alias
    base = args.base
    bran = args.bran
    http_port = args.http
    keypath = args.keypath
    certpath = args.certpath
    cafilepath = args.cafilepath

    try:
        http_port = int(http_port)
    except ValueError:
        logger.error(f'Invalid port number: {http_port}. Must be an integer.')
        return []

    config_file = args.config_file
    config_dir = args.config_dir

    cf = configing.Configer(name=config_file, base=base, headDirPath=config_dir, temp=False, reopen=True, clear=False)
    hby = existing.setupHby(name=name, base=base, bran=bran, cf=cf)
    hby_doer = habbing.HaberyDoer(habery=hby)  # setup doer
    oobiery = oobiing.Oobiery(hby=hby)

    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*', allow_credentials='*', expose_headers=['cesr-attachment', 'cesr-date', 'content-type']
        )
    )
    webbing.setup(app, hby=hby)
    voodoers = viking.setup(hby=hby, alias=alias)

    if keypath is not None:
        servant = hio.core.tcp.ServerTls(
            certify=False, keypath=keypath, certpath=certpath, cafilepath=cafilepath, port=http_port
        )
    else:
        servant = None

    server = http.Server(port=http_port, app=app, servant=servant)
    http_server_doer = http.ServerDoer(server=server)

    doers = oobiery.doers + [hby_doer, http_server_doer]
    doers.extend(voodoers)

    logger.info(f'Launched did:webs artifact webserver: {http_port}')
    return doers
