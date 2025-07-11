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
from keri.core import eventing
from keri.db import dbing
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
    type=bool,
    required=False,
    default=False,
    help='Whether to include metadata (True), or only return the DID document (False)',
)
parser.add_argument('-d', '--did', required=True, help='DID to generate (did:webs method)')
parser.add_argument(
    '-v',
    '--verbose',
    action='store',
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
        hbyDoer = habbing.HaberyDoer(habery=self.hby)  # setup doer
        obl = oobiing.Oobiery(hby=self.hby)
        self.did = did
        self.oobi = oobi
        self.da_reg = da_reg
        self.meta = meta
        self.verbose = verbose
        self.output_dir = output_dir

        self.toRemove = [hbyDoer] + obl.doers
        doers = list(self.toRemove)
        super(DIDArtifactGenerator, self).__init__(doers=doers)

    def recur(self, tock=0.0, **opts):
        """DoDoer lifecycle function that calls the underlying DID generation function. Runs once"""
        self.generate_artifacts()
        return True  # run once and then stop

    def retrieve_kel_via_oobi(self):
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

    def make_did_json_path(self, output_dir: str, aid: str):
        # Create the directory (and any intermediate directories in the given path) if it doesn't already exist
        dd_dir_path = os.path.join(output_dir, aid)
        if not os.path.exists(dd_dir_path):
            os.makedirs(dd_dir_path)
        return dd_dir_path

    def write_did_json_file(self, dd_dir_path: str, diddoc: dict):
        """save did.json to a file at output_dir/{aid}/{AID}.json"""
        dd_file_path = os.path.join(dd_dir_path, f'{ends.DID_JSON}')
        with open(dd_file_path, 'w') as ddf:
            json.dump(didding.toDidWeb(diddoc), ddf)

    def generate_did_doc(self, aid: str):
        """Generate the did:webs DID document and return it"""
        gen_doc = didding.generateDIDDoc(self.hby, did=self.did, aid=aid, oobi=None, reg_name=self.da_reg, meta=self.meta)

        if not gen_doc:
            return None

        diddoc = gen_doc
        if self.meta:
            diddoc = gen_doc['didDocument']
            logger.info('Generated metadata for DID document', gen_doc['didDocumentMetadata'])
        return diddoc

    def generate_artifacts(self):
        """Drive did:webs did.json and keri.cesr generation"""
        logger.debug(
            f'\nGenerate DID doc for: {self.did}'
            f'\nusing OOBI          : {self.oobi}'
            f'\nand metadata        : {self.meta}'
            f'\nregistry name       : {self.da_reg}'
        )
        domain, port, path, aid = didding.parseDIDWebs(self.did)

        logger.info(f'Generating CESR event stream data from local Habery keystore')
        keri_cesr = bytearray()
        # self.retrieve_kel_via_oobi() # not currently used; an alternative to relying on a local KEL keystore
        keri_cesr.extend(self.genKelCesr(aid))  # add KEL CESR stream
        keri_cesr.extend(self.gen_des_aliases_cesr(aid))  # add designated aliases TELs and ACDCs
        self.write_keri_cesr_file(self.output_dir, aid, keri_cesr)

        # generate did doc
        diddoc = self.generate_did_doc(aid)
        if diddoc is None:
            logger.error('DID document failed to generate')
            self.remove(self.toRemove)
            return None

        # Create the directory (and any intermediate directories in the given path) if it doesn't already exist
        dd_dir_path = self.make_did_json_path(self.output_dir, aid)
        self.write_did_json_file(dd_dir_path, diddoc)

        # TODO find out what the following lines are for down to the didData var
        #  Are they for getting the KEL stream after OOBI resolution? Why partially witnessed or signed events?
        kever = self.hby.kevers[aid]

        # construct the KEL
        pre = kever.prefixer.qb64
        preb = kever.prefixer.qb64b

        kel = []
        for _, fn, dig in self.hby.db.getFelItemPreIter(preb, fn=0):
            try:
                event = eventing.loadEvent(self.hby.db, preb, dig)
            except ValueError as e:
                raise e

            kel.append(event)

        key = dbing.snKey(pre=pre, sn=0)
        # load any partially witnessed events for this prefix
        for ekey, edig in self.hby.db.getPweItemIter(key=key):
            pre, sn = dbing.splitKeySN(ekey)  # get pre and sn from escrow item
            try:
                kel.append(eventing.loadEvent(self.hby.db, pre, edig))
            except ValueError as e:
                raise e

        # load any partially signed events from this prefix
        for ekey, edig in self.hby.db.getPseItemIter(key=key):
            pre, sn = dbing.splitKeySN(ekey)  # get pre and sn from escrow item
            try:
                kel.append(eventing.loadEvent(self.hby.db, pre, edig))
            except ValueError as e:
                raise e
        state = kever.state()._asdict()
        gen_doc = dict(didDocument=diddoc, pre=pre, state=state, kel=kel)
        didData = json.dumps(gen_doc, indent=2)

        if self.verbose:
            print(f'keri.cesr:\n{keri_cesr.decode()}\n')
            print(f'did.json:\n{json.dumps(diddoc, indent=2)}')
        logger.debug(didData)
        self.remove(self.toRemove)
        return True

    def genKelCesr(self, pre: str) -> bytearray:
        """Return a bytearray of the CESR stream of all KEL events for a given prefix."""
        msgs = bytearray()
        logger.info(f'Generating {pre} KEL CESR events')
        for msg in self.hby.db.clonePreIter(pre=pre):
            msgs.extend(msg)
        return msgs

    def genTelCesr(self, reger: viring.Reger, regk: str) -> bytearray:
        """Get the CESR stream of TEL events for a given registry."""
        msgs = bytearray()
        logger.info(f'Generating {regk} TEL CESR events')
        for msg in reger.clonePreIter(pre=regk):
            msgs.extend(msg)
        return msgs

    def genAcdcCesr(self, aid, creder) -> bytearray:
        """???"""
        # logger.info(f"Generating {creder.crd['d']} ACDC CESR events, issued by {creder.crd['i']}")
        return self.hby.habs[aid].endorse(creder)

    def gen_des_aliases_cesr(self, aid: str, schema: str = didding.DES_ALIASES_SCHEMA) -> bytearray:
        return self.genCredCesr(aid, schema)

    def get_self_issued_acdcs(self, aid: str, rgy: credentialing.Regery, schema: str = didding.DES_ALIASES_SCHEMA):
        """Get self issued ACDCs filtered by schema"""
        creds_issued = rgy.reger.issus.get(keys=aid)
        creds_by_schema = rgy.reger.schms.get(keys=schema.encode('utf-8'))

        # self-attested, there is no issuee, and schema is designated aliases
        return [
            cred_issued
            for cred_issued in creds_issued
            if cred_issued.qb64 in [cred_by_schm.qb64 for cred_by_schm in creds_by_schema]
        ]

    def genCredCesr(self, aid: str, schema: str):
        """
        Select a specific ACDC from the local registry (Regery), if it exists, to generate the
        CESR stream
        Args:
            aid: AID prefix to retrieve the ACDC for
            schema: the schema to use to select the target ACDC from the local registry

        Returns:
            bytearray: CESR stream of locally stored ACDC events for the specified AID and schema
        """
        # self-attested, there is no issuee, and schema is designated aliases
        local_creds = self.get_self_issued_acdcs(aid, self.rgy, schema)

        msgs = bytearray()
        for cred in local_creds:
            creder, *_ = self.rgy.reger.cloneCred(said=cred.qb64)
            if creder.regi is not None:
                msgs.extend(self.genTelCesr(self.rgy.reger, creder.regi))
                msgs.extend(self.genTelCesr(self.rgy.reger, creder.said))
            msgs.extend(self.genAcdcCesr(aid, creder))
        return msgs
