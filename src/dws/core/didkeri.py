import datetime
import json
from typing import List

from hio.base import Doer, doing
from keri import kering
from keri.app import configing, habbing, oobiing
from keri.db import basing
from keri.help import helping
from keri.vdr import credentialing

from dws import log_name, ogler
from dws.core import didding, habs

logger = ogler.getLogger(log_name)


class KeriResolver(doing.DoDoer):
    """Resolve did:keri DID document from the KEL retrieved during OOBI resolution of the provided OOBI."""

    TimeoutOOBIResolve = 5.0  # seconds to wait for OOBI resolution before timing out

    def __init__(
        self,
        did: str,
        oobi: str | None = None,
        meta: bool = False,
        verbose: bool = False,
        hby: habbing.Habery | None = None,
        rgy: credentialing.Regery | None = None,
        cf: configing.Configer | None = None,
        name: str | None = None,
        base: str | None = None,
        bran: str | None = None,
        config_file: str | None = None,
        config_dir: str | None = None,
    ):
        """
        Initializes the set of Doers needed to resolve a did:keri DID document based on the KEL of
        the embedded AID.

        Parameters:
            did: The did:keri DID to resolve.
            oobi: OOBI to use for resolving the DID (optional).
            meta: Whether to include metadata in the resolution result.
            verbose: Whether to print verbose output.
            hby: Existing Habery instance (optional).
            rgy: Existing Regery instance (optional).
            cf: Configurationer instance (optional).
            name: Name of the Habery.
            base: Base directory for the Habery.
            bran: Passcode for the Habery (optional).
            config_file: Habery configuration file name (optional).
            config_dir: Directory for Habery configuration data (optional).
        """
        cf = cf if cf else habs.get_habery_configer(name=config_file, base=base, head_dir_path=config_dir)
        if hby is None:
            hby, hby_doer = habs.get_habery_and_doer(name, base, bran, cf)
        else:
            hby_doer = habbing.HaberyDoer(habery=hby)
        self.hby: habbing.Habery = hby
        self.rgy = (
            rgy if rgy else credentialing.Regery(hby=self.hby, name=self.hby.name, base=self.hby.base, temp=self.hby.temp)
        )
        self.did: str = did
        self.oobiery = oobiing.Oobiery(hby=hby)
        self.meta: bool = meta
        self.verbose = verbose

        self.result: dict = {}
        resolve_doer = doing.doify(self.resolve, hby=hby, did=did, oobi=oobi, meta=meta)
        self.toRemove: List[Doer] = [hby_doer, resolve_doer] + self.oobiery.doers
        doers = list(self.toRemove)
        super(KeriResolver, self).__init__(doers=doers)

    def resolve_oobi(self, aid: str, oobi: str, tock=0.0):
        # Resolve provided OOBI to get the KEL of the AID passed in
        if self.hby.kevers.get(aid) is not None:
            return  # return early if AID is known
        start_time = helping.nowUTC()
        obr = basing.OobiRecord(date=helping.nowIso8601())
        obr.cid = aid
        self.hby.db.oobis.pin(keys=(oobi,), val=obr)

        while (
            self.hby.db.roobi.get(keys=(oobi,)) is None or aid not in self.hby.kevers
        ):  # wait for aid in hby.kevers waits for delegates to have their AES found
            now = helping.nowUTC()
            self.hby.kvy.processEscrows()  # for delegated AIDs so authorizing event seals (AES) from delegator ixn evts are found
            if (now - start_time) > datetime.timedelta(seconds=self.TimeoutOOBIResolve):
                raise kering.KeriError(f'OOBI resolution timed out after {self.TimeoutOOBIResolve} seconds for OOBI: {oobi}')
            _ = yield tock

    def resolve(self, hby: habbing.Habery, did: str, oobi: str, meta: bool, tock=0.0, tymth=None):
        """
        Resolve the did:keri DID document by retrieving the KEL from the OOBI resolution.
        """
        self.wind(tymth)  # prime generator
        self.tock = tock  # prime generator
        yield self.tock  # prime generator

        aid, query = didding.parse_did_keri(did)
        if query is not None and oobi is None:
            query_params = didding.parse_query_string(query)
            oobi = query_params.get('oobi', None)

        # Once the OOBI is resolved and the AID's KEL is available in the local Habery then generate the DID artifacts
        try:
            aid, query = didding.parse_did_keri(did)

            # Resolve provided OOBI to get the KEL of the AID passed in
            yield from self.resolve_oobi(aid=aid, oobi=oobi, tock=tock)

            self.result = didding.generate_did_doc(hby, rgy=self.rgy, did=did, aid=aid, meta=meta)
            logger.info(f'did:keri Resolution result: {json.dumps(self.result, indent=2)}')
            if self.verbose:
                print(self.result)
                logger.info(f'Resolution result for did:keri DID {self.did}:\n{json.dumps(self.result, indent=2)}')
            logger.info(f'Verification success for did:keri DID: {self.did}')
            print(f'did:keri verification success for {self.did}')
        except Exception as ex:
            logger.info(f'Verification failure for did:keri DID: {did}: {ex}')
            self.result = {'error': str(ex)}
            raise ex
        finally:
            self.remove(self.toRemove)
