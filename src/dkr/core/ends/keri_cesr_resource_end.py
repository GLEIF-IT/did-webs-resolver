# -*- encoding: utf-8 -*-
"""
dkr.core.webbing module

"""

import falcon
from keri import kering
from keri.core import serdering

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

        content = bytearray()
        for msg in self.hby.db.clonePreIter(pre=aid):
            content.extend(msg)

        # TODO add in ACDC and TEL artifacts for designated aliases

        hab = self.hby.habs[aid]

        msgs = bytearray()
        for eid in hab.kever.wits:
            if eid == aid:
                pass
            else:
                msgs.extend(hab.loadLocScheme(eid=eid) or bytearray())
                msgs.extend(hab.makeEndRole(eid=eid, role=kering.Roles.witness) or bytearray())

        for (_, erole, eid), _ in self.hby.db.ends.getItemIter(keys=(aid, kering.Roles.mailbox)):
            msgs.extend(hab.loadLocScheme(eid=eid) or bytearray())
            msgs.extend(hab.loadEndRole(cid=aid, eid=eid, role=erole) or bytearray())

        content.extend(msgs)
        rep.status = falcon.HTTP_200
        rep.content_type = CESR_MIME
        rep.data = content
