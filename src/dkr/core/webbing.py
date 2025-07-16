# -*- encoding: utf-8 -*-
"""
dkr.core.webbing module

"""

from dkr.core import ends


def setup(app, hby):
    """Set up web app endpoints to serve configured KERI AIDs as `did:web` DIDs

    Parameters:
        app (App): Falcon app to register endpoints against
        hby (Habery): Database environment for exposed KERI AIDs
    """
    app.add_route('/health', ends.HealthEnd())
    app.add_route(f'/{{aid}}/did.json', ends.DIDWebsResourceEnd(hby))
    app.add_route(f'/{{aid}}/keri.cesr', ends.KeriCesrResourceEnd(hby))
