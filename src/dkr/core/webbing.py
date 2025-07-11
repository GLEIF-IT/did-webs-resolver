# -*- encoding: utf-8 -*-
"""
dkr.core.webbing module

"""

from dkr.core.ends.did_webs_resource_end import DIDWebsResourceEnd
from dkr.core.ends.keri_cesr_resource_end import KeriCesrResourceEnd


def setup(app, hby):
    """Set up web app endpoints to serve configured KERI AIDs as `did:web` DIDs

    Parameters:
        app (App): Falcon app to register endpoints against
        hby (Habery): Database environment for exposed KERI AIDs
    """

    app.add_route(f'/{{aid}}/did.json', DIDWebsResourceEnd(hby))
    app.add_route(f'/{{aid}}/keri.cesr', KeriCesrResourceEnd(hby))
