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
from keri.db import basing
from keri.help import helping

from dkr import log_name, ogler
from dkr.core import didding

parser = argparse.ArgumentParser(description='Resolve a did:keri DID')
parser.set_defaults(handler=lambda args: handler(args), transferable=True)
parser.add_argument('-n', '--name', action='store', default='dkr', help='Name of controller. Default is dkr.')
parser.add_argument(
    '--base', '-b', help='additional optional prefix to file location of KERI keystore', required=False, default=''
)
parser.add_argument(
    '--passcode', help='22 character encryption passcode for keystore (is not saved)', dest='bran', default=None
)  # passcode => bran
parser.add_argument('--did', '-d', help='DID to resolve (did:keri method)', required=True)
parser.add_argument('--oobi', '-o', help='OOBI to use for resolving the DID', required=False)
parser.add_argument(
    '--meta',
    '-m',
    help='Whether to include metadata (True), or only return the DID document (False)',
    type=bool,
    required=False,
    default=None,
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
    hbyDoer = habbing.HaberyDoer(habery=hby)  # setup doer
    obl = oobiing.Oobiery(hby=hby)
    res = KeriResolver(hby=hby, hbyDoer=hbyDoer, obl=obl, did=args.did, oobi=args.oobi, meta=args.meta)
    return [res]


class KeriResolver(doing.DoDoer):
    """Resolve did:keri DID document from the KEL retrieved during OOBI resolution of the provided OOBI."""

    def __init__(self, hby, hbyDoer, obl, did, oobi, meta):
        self.hby: habbing.Habery = hby
        self.did: str = did
        self.oobi: str = oobi
        self.meta: bool = meta

        self.result: dict = {}
        self.toRemove = [hbyDoer] + obl.doers
        doers = list(self.toRemove)
        super(KeriResolver, self).__init__(doers=doers)

    def recur(self, tock=0.0, **opts):
        self.resolve(hby=self.hby, did=self.did, oobi=self.oobi, meta=self.meta, tock=tock)
        return True

    def resolve_oobi(self, hby: habbing.Habery, aid: str, oobi: str, tock=0.0):
        """Resolve the OOBI to retrieve the KEL."""
        obr = basing.OobiRecord(date=helping.nowIso8601())
        obr.cid = aid
        hby.db.oobis.pin(keys=(oobi,), val=obr)

        while hby.db.roobi.get(keys=(oobi,)) is None:
            _ = yield tock

    def resolve(self, hby: habbing.Habery, did: str, oobi: str, meta: bool, tock=0.0):
        aid = didding.parseDIDKeri(did)
        self.resolve_oobi(hby=hby, aid=aid, oobi=oobi, tock=tock)

        didresult = didding.generateDIDDoc(hby, did=did, aid=aid, oobi=oobi, meta=meta)
        dd = didresult[didding.DD_FIELD]
        result = didresult if meta else dd
        self.result = result
        logger.info(f'did:keri Resolution result: {result}')
        self.remove(self.toRemove)
