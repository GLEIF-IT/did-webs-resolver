# -*- encoding: utf-8 -*-
"""
dkr.app.cli.commands module

"""

import argparse
import json
import logging

from hio.base import doing
from keri.app import habbing, oobiing
from keri.app.cli.common import existing

from dkr import log_name, ogler
from dkr.core import resolving

parser = argparse.ArgumentParser(description='Resolve a did:webs DID')
parser.set_defaults(handler=lambda args: handler(args), transferable=True)
parser.add_argument('-n', '--name', action='store', default='dkr', help='Name of controller. Default is dkr.')
parser.add_argument(
    '-b', '--base', required=False, default='', help='additional optional prefix to file location of KERI keystore'
)
# passcode => bran
parser.add_argument(
    '--passcode', dest='bran', default=None, help='22 character encryption passcode for keystore (is not saved)'
)
parser.add_argument('-d', '--did', required=True, help='DID to resolve')
parser.add_argument(
    '-m',
    '--meta',
    action='store_true',
    required=False,
    default=False,
    help='Whether to include metadata (True), or only return the DID document (False)',
)
parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    required=False,
    default=False,
    help='Show the verbose output of DID resolution',
)
parser.add_argument(
    '--loglevel',
    action='store',
    required=False,
    default='CRITICAL',
    help='Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL',
)

logger = ogler.getLogger(log_name)


def handler(args):
    ogler.level = logging.getLevelName(args.loglevel.upper())
    logger.setLevel(ogler.level)
    hby = existing.setupHby(name=args.name, base=args.base, bran=args.bran)
    hby_doer = habbing.HaberyDoer(habery=hby)  # setup doer
    oobiery = oobiing.Oobiery(hby=hby)
    res = WebsResolver(hby=hby, hby_doer=hby_doer, oobiery=oobiery, did=args.did, meta=args.meta, verbose=args.verbose)
    return [res]


class WebsResolver(doing.DoDoer):
    """Resolve did:webs DID document from the KERI database."""

    def __init__(
        self, hby: habbing.Habery, hby_doer: habbing.HaberyDoer, oobiery: oobiing.Oobiery, did: str, meta: bool, verbose: bool
    ):
        """
        Initialize the WebsResolver.
        """
        self.hby = hby
        self.did = did
        self.meta = meta
        self.verbose = verbose

        self.toRemove = [hby_doer] + oobiery.doers
        doers = list(self.toRemove)
        super(WebsResolver, self).__init__(doers=doers)

    def recur(self, tock=0.0, **opts):
        self.resolve()
        return True

    def resolve(self):
        """Resolve the did:webs DID."""
        resolved, resolution = resolving.resolve(hby=self.hby, did=self.did, meta=self.meta)
        if resolved:
            if self.verbose:
                print(f'Resolution result for {self.did}: {json.dumps(resolution, indent=2)}')
            print(f'Verification success for {self.did}')
            self.success = True
        else:
            print(f'Verification failure for {self.did}\nResolution: {json.dumps(resolution, indent=2)}')
            self.success = False
        self.remove(self.toRemove)
        if not self.success:
            raise ValueError(f'Verification failure for {self.did}')
