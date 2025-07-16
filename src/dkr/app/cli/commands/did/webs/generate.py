# -*- encoding: utf-8 -*-
"""
dkr.app.cli.commands module

"""

import argparse
import json
import logging
import os

from hio.base import doing
from keri.app import habbing, oobiing
from keri.app.cli.common import existing
from keri.core import serdering
from keri.db import basing
from keri.vdr import credentialing, viring

from dkr import log_name, ogler
from dkr.core import didding, ends

parser = argparse.ArgumentParser(description='Generate a did:webs DID document and KEL, TEL, and ACDC CESR stream file')
parser.set_defaults(handler=lambda args: handler(args), transferable=True)
parser.add_argument('-n', '--name', action='store', default='dkr', help='Name of controller. Default is dkr.')
parser.add_argument(
    '-b', '--base', required=False, default='', help='additional optional prefix to file location of KERI keystore'
)
parser.add_argument(
    '-p', '--passcode', dest='bran', default=None, help='22 character encryption passcode for keystore (is not saved)'
)  # passcode => bran
parser.add_argument(
    '--output-dir',
    required=False,
    default='.',
    help='Directory to output the generated files. Default is current directory.',
)
parser.add_argument(
    '-o',
    '--oobi',
    required=False,
    default=None,
    help='OOBI to use for resolving the AID',
)
parser.add_argument(
    '-da',
    '--da_reg',
    required=False,
    default=None,
    help='Name of Regery to find designated aliases attestation. Default is None.',
)
parser.add_argument(
    '-m',
    '--meta',
    action='store_true',
    required=False,
    default=False,
    help='Whether to include metadata (True), or only return the DID document (False)',
)
parser.add_argument('-d', '--did', required=True, help='DID to generate (did:webs method)')
parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    required=False,
    default=False,
    help='Show the verbose output of DID generation artifacts.',
)
parser.add_argument(
    '--loglevel',
    action='store',
    required=False,
    default='CRITICAL',
    help='Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL',
)

logger = ogler.getLogger(log_name)


def handler(args: argparse.Namespace) -> list[doing.Doer]:
    """
    Perform did:webs artifact generation for the DID document and keri.cesr CESR stream and then shut down.
    """
    ogler.level = logging.getLevelName(args.loglevel.upper())
    logger.setLevel(ogler.level)
    gen = DIDArtifactGenerator(
        name=args.name,
        base=args.base,
        bran=args.bran,
        did=args.did,
        oobi=args.oobi,
        da_reg=args.da_reg,
        meta=args.meta,
        verbose=args.verbose,
        output_dir=args.output_dir,
    )
    return [gen]


class DIDArtifactGenerator(doing.DoDoer):
    """
    Generates a did:webs DID document and the associated CESR stream for the {AID}.json and keri.cesr files.
    - {AID}.json contains the DID document
    - keri.cesr contains the CESR event stream for the KELs, TELs, and ACDCs associated with the DID.
    """

    def __init__(self, name, base, bran, did, oobi, da_reg, meta=False, verbose=False, output_dir='.'):
        """
        Initializes the did:webs DID file generator.

        Parameters:
            name (str): Name of the controller keystore (Habery) to use for generating the DID document.
            base (str): Base path (namespace for local file tree) for the KERI keystore (Habery) to use for generating the DID document.
            bran (str): Passcode for the controller of the local KERI keystore.
            did (str): The did:webs DID showing the domain and AID to generate the DID document and CESR stream for.
            oobi (str): OOBI to use for resolving the AID (not currently used).
            da_reg (str): Name of the local registry (Regery) to use find designated aliases self-attestation (issued locally).
            meta (bool): Whether to include metadata in the DID document generation. Defaults to False.
            verbose (bool): Whether to print the generated DID artifacts at the command line. Defaults to False
            output_dir (str): Directory to output the generated files. Default is current directory.
        """
        self.name = name
        self.base = base
        self.bran = bran
        self.hby = existing.setupHby(name=name, base=base, bran=bran)
        self.rgy = credentialing.Regery(hby=self.hby, name=self.hby.name, base=self.hby.base)
        self.bran = bran
        hby_doer = habbing.HaberyDoer(habery=self.hby)  # setup doer
        oobiery = oobiing.Oobiery(hby=self.hby)
        self.did = did
        self.oobi = oobi
        self.da_reg = da_reg
        self.meta = meta
        self.verbose = verbose
        self.output_dir = output_dir

        self.toRemove = [hby_doer] + oobiery.doers
        doers = list(self.toRemove)
        super(DIDArtifactGenerator, self).__init__(doers=doers)

    def recur(self, tock=0.0, **opts):
        """DoDoer lifecycle function that calls the underlying DID generation function. Runs once"""
        self.generate_artifacts()
        return True  # run once and then stop

    def retrieve_kel_via_oobi(self):
        """
        Possibly retrieve the KEL via OOBI resolution.
        TODO finish implementing this
        """
        # if self.oobi is not None or self.oobi == "":
        #     logger.info(f"Using oobi {self.oobi} to get CESR event stream")
        #     obr = basing.OobiRecord(date=helping.nowIso8601())
        #     obr.cid = aid
        #     self.hby.db.oobis.pin(keys=(self.oobi,), val=obr)

        #     logger.info(f"Resolving OOBI {self.oobi}")
        #     roobi = self.hby.db.roobi.get(keys=(self.oobi,))
        #     while roobi is None or roobi.state != oobiing.Result.resolved:
        #         roobi = self.hby.db.roobi.get(keys=(self.oobi,))
        #         _ = yield tock
        #     logger.info(f"OOBI {self.oobi} resolved {roobi}")

        #     oobiHab = self.hby.habs[aid]
        #     logger.info(f"Loading hab for OOBI {self.oobi}:\n {oobiHab}")
        #     msgs = oobiHab.replyToOobi(aid=aid, role="controller", eids=None)
        #     logger.info(f"OOBI {self.oobi} CESR event stream {msgs.decode('utf-8')}")
        pass

    @staticmethod
    def make_keri_cesr_path(output_dir: str, aid: str):
        """Create keri.cesr enclosing dir, and any intermediate dirs, if not existing"""
        kc_dir_path = os.path.join(output_dir, aid)
        if not os.path.exists(kc_dir_path):
            logger.debug(f'Creating directory for KERI CESR events: {kc_dir_path}')
            os.makedirs(kc_dir_path)
        return os.path.join(kc_dir_path, f'{ends.KERI_CESR}')

    def write_keri_cesr_file(self, output_dir: str, aid: str, keri_cesr: bytearray):
        """Write the keri.cesr file to output path, making any enclosing directories"""
        kc_file_path = self.make_keri_cesr_path(output_dir, aid)
        with open(kc_file_path, 'w') as kcf:
            tmsg = keri_cesr.decode('utf-8')
            logger.debug(f'Writing CESR events to {kc_file_path}: \n{tmsg}')
            kcf.write(tmsg)

    @staticmethod
    def make_did_json_path(output_dir: str, aid: str):
        """Create the directory (and any intermediate directories in the given path) if it doesn't already exist"""
        dd_dir_path = os.path.join(output_dir, aid)
        if not os.path.exists(dd_dir_path):
            os.makedirs(dd_dir_path)
        return dd_dir_path

    @staticmethod
    def write_did_json_file(dd_dir_path: str, diddoc: dict, meta: bool = False):
        """save did.json to a file at output_dir/{aid}/{AID}.json"""
        dd_file_path = os.path.join(dd_dir_path, f'{ends.DID_JSON}')
        with open(dd_file_path, 'w') as ddf:
            json.dump(didding.to_did_web(diddoc, meta), ddf)

    def generate_artifacts(self):
        """Drive did:webs did.json and keri.cesr generation"""
        logger.debug(
            f'\nGenerate DID doc for: {self.did}'
            f'\nusing OOBI          : {self.oobi}'
            f'\nand metadata        : {self.meta}'
            f'\nregistry name       : {self.da_reg}'
        )
        domain, port, path, aid = didding.parse_did_webs(self.did)

        logger.info(f'Generating CESR event stream data from local Habery keystore')
        hab = self.hby.habs[aid]
        reger = self.rgy.reger
        keri_cesr = bytearray()
        # self.retrieve_kel_via_oobi() # not currently used; an alternative to relying on a local KEL keystore
        keri_cesr.extend(self.gen_kel_cesr(self.hby.db, aid))  # add KEL CESR stream
        keri_cesr.extend(self.gen_des_aliases_cesr(hab, reger, aid))  # add designated aliases TELs and ACDCs
        self.write_keri_cesr_file(self.output_dir, aid, keri_cesr)

        # generate did doc
        diddoc = didding.generate_did_doc(self.hby, did=self.did, aid=aid, oobi=None, reg_name=self.da_reg, meta=self.meta)
        if diddoc is None:
            logger.error('DID document failed to generate')
            self.remove(self.toRemove)
            return None

        # Create the directory (and any intermediate directories in the given path) if it doesn't already exist
        dd_dir_path = self.make_did_json_path(self.output_dir, aid)
        self.write_did_json_file(dd_dir_path, diddoc, self.meta)

        if self.verbose:
            print(f'keri.cesr:\n{keri_cesr.decode()}\n')
            print(f'did.json:\n{json.dumps(diddoc, indent=2)}')
        self.remove(self.toRemove)
        return True

    @staticmethod
    def gen_kel_cesr(db: basing.Baser, pre: str) -> bytearray:
        """Return a bytearray of the CESR stream of all KEL events for a given prefix."""
        msgs = bytearray()
        logger.info(f'Generating {pre} KEL CESR events')
        for msg in db.clonePreIter(pre=pre):
            msgs.extend(msg)
        return msgs

    @staticmethod
    def gen_tel_cesr(reger: viring.Reger, regk: str) -> bytearray:
        """Get the CESR stream of TEL events for a given registry."""
        msgs = bytearray()
        logger.info(f'Generating {regk} TEL CESR events')
        for msg in reger.clonePreIter(pre=regk):
            msgs.extend(msg)
        return msgs

    @staticmethod
    def gen_acdc_cesr(hab: habbing.Hab, creder: serdering.SerderACDC) -> bytearray:
        """Add the CESR stream of the self attestation ACDCs for the given AID including signatures."""
        logger.info(f'Generating {creder.sad["d"]} ACDC CESR events, issued by {creder.sad["i"]}')
        return hab.endorse(creder)

    def gen_des_aliases_cesr(
        self, hab: habbing.Hab, reger: credentialing.Reger, aid: str, schema: str = didding.DES_ALIASES_SCHEMA
    ) -> bytearray:
        """
        Select a specific ACDC from the local registry (Regery), if it exists, to generate the
        CESR stream
        Args:
            hab: The local Hab to use for generating the CESR stream
            aid: AID prefix to retrieve the ACDC for
            reger: The Regery to use for retrieving the ACDC
            schema: the schema to use to select the target ACDC from the local registry

        Returns:
            bytearray: CESR stream of locally stored ACDC events for the specified AID and schema
        """
        # self-attested, there is no issuee, and schema is designated aliases
        local_creds = self.get_self_issued_acdcs(aid, reger, schema)

        msgs = bytearray()
        for cred in local_creds:
            creder, *_ = reger.cloneCred(said=cred.qb64)
            if creder.regi is not None:
                # TODO check if this works if we only get the regi CESR stream once
                msgs.extend(self.gen_tel_cesr(reger, creder.regi))
                msgs.extend(self.gen_tel_cesr(reger, creder.said))
            msgs.extend(self.gen_acdc_cesr(hab, creder))
        return msgs

    @staticmethod
    def get_self_issued_acdcs(aid: str, reger: credentialing.Reger, schema: str = didding.DES_ALIASES_SCHEMA):
        """Get self issued ACDCs filtered by schema"""
        creds_issued = reger.issus.get(keys=aid)
        creds_by_schema = reger.schms.get(keys=schema.encode('utf-8'))

        # self-attested, there is no issuee, and schema is designated aliases
        return [
            cred_issued
            for cred_issued in creds_issued
            if cred_issued.qb64 in [cred_by_schm.qb64 for cred_by_schm in creds_by_schema]
        ]
