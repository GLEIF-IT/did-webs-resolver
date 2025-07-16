# -*- encoding: utf-8 -*-
"""
dkr.core.webbing module

"""

import falcon
from keri import kering
from keri.app import habbing
from keri.db import basing

KERI_CESR = 'keri.cesr'
CESR_MIME = 'application/cesr'


class KeriCesrResourceEnd:
    """
    keri.cesr resource endpoint for accessing all KEL, TEL, and ACDC artifacts needed for did:webs DIDs
    """

    def __init__(self, hby):
        """
        Parameters:
            hby (Habery): Database environment for AIDs to expose

        """
        self.hby = hby
        super().__init__()

    def on_get(self, req, rep, aid):
        """GET endpoint for accessing {KERI_CESR} stream for AID

        Parameters:
            req (Request) Falcon HTTP Request object:
            rep (Response) Falcon HTTP Response object:
            aid (str): AID to access {KERI_CESR} stream for

        """
        # Read the DID from the parameter extracted from path or manually extract
        if not req.path.endswith(f'/{KERI_CESR}'):
            raise falcon.HTTPBadRequest(description=f'invalid {KERI_CESR} DID URL {req.path}')

        if aid not in self.hby.kevers:
            raise falcon.HTTPNotFound(description=f'KERI AID {aid} not found')

        baser = self.hby.db
        hab = self.hby.habs[aid]
        content = load_kel(baser, aid)
        roles_and_urls = load_end_roles_loc_schemes(baser, hab, aid)
        content.extend(roles_and_urls)
        # TODO add in ACDC and TEL artifacts for designated aliases

        rep.status = falcon.HTTP_200
        rep.content_type = CESR_MIME
        rep.data = content


def load_kel(baser: basing.Baser, aid: str) -> bytearray:
    """Load KEL messages for the given AID."""
    msgs = bytearray()
    for msg in baser.clonePreIter(pre=aid):
        msgs.extend(msg)
    return msgs


def load_end_roles_loc_schemes(baser: basing.Baser, hab: habbing.Hab, aid: str) -> bytearray:
    """Load endpoint role and location scheme messages for the given AID."""
    msgs = bytearray()
    for eid in hab.kever.wits:
        if eid == aid:
            pass
        else:
            msgs.extend(hab.loadLocScheme(eid=eid) or bytearray())
            msgs.extend(hab.makeEndRole(eid=eid, role=kering.Roles.witness) or bytearray())

    for (_, erole, eid), _ in baser.ends.getItemIter(keys=(aid, kering.Roles.mailbox)):
        msgs.extend(hab.loadLocScheme(eid=eid) or bytearray())
        msgs.extend(hab.loadEndRole(cid=aid, eid=eid, role=erole) or bytearray())
    return msgs
