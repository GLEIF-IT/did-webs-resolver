from hio.help import hicting
from keri import kering
from keri.app import configing, habbing, keeping
from keri.app.cli.common import existing
from keri.core import eventing
from keri.db import basing

from dws import log_name, ogler

logger = ogler.getLogger(log_name)


def get_habery_configer(name: str | None, base: str | None, head_dir_path: str | None, temp: bool = False):
    """Get the Configer for the Habery if name provide otherwise return None."""
    if name is not None:
        return configing.Configer(name=name, base=base, headDirPath=head_dir_path, temp=temp, reopen=True, clear=False)
    return None


def get_auth_encryption_aid(name: str, base: str, temp: bool = False):
    """Get the Authentication and Encryption Identifier (AEID) from the Keeper."""
    ks = keeping.Keeper(name=name, base=base, temp=temp, reopen=True)
    aeid = ks.gbls.get('aeid')
    ks.close()  # to avoid LMDB reader table locks
    return aeid


def get_habery_and_doer(
    name: str | None, base: str | None, bran: str | None, cf: configing.Configer = None, temp: bool = False
) -> (habbing.Habery, habbing.HaberyDoer):
    """Get the Habery and its Doer respecting any existing AEID."""
    aeid = get_auth_encryption_aid(name, base, temp)
    if aeid is None:
        hby = habbing.Habery(name=name, base=base, bran=bran, cf=cf, temp=temp)
    else:
        hby = existing.setupHby(name=name, base=base, bran=bran, cf=cf, temp=temp)
    return hby, habbing.HaberyDoer(habery=hby)


def fetch_urls(baser: basing.Baser, eid: str, scheme: str = '') -> hicting.Mict:
    """
    Returns:
        hicting.Mict: urls keyed by scheme for given endpoint identifier (eid). Assumes that user
            independently verifies that the eid is allowed for a given cid and role.
            If url is empty then does not return.

    Parameters:
        baser (basing.Baser): The Baser instance to fetch URLs from.
        eid (str): The endpoint identifier (eid) to fetch URLs for.
        scheme (str): The scheme to filter URLs by. Defaults to an empty string, which means no filtering.
    """
    urls = []
    for keys, loc in baser.locs.getItemIter(keys=(eid, scheme)):
        logger.debug(f'Fetched URL: {loc.url} for eid: {eid}, scheme: {scheme} with keys: {keys}')
        if loc.url:
            urls.append((keys[1], loc.url))
    return hicting.Mict(urls)


def get_role_urls(baser: basing.Baser, kever: eventing.Kever, scheme: str = ''):
    """
    Gets all witness role URLs in a given database for the witnesses in a Kever, filterable by scheme.

    A subset of the habbing.BaseHab.fetchRoleUrls method from KERIpy.

    Parameters:
        baser (basing.Baser): The Baser instance to fetch URLs from.
        kever (eventing.Kever): The Kever instance containing the witnesses.
        scheme (str): The scheme to filter URLs by. Defaults to an empty string, which means no filtering.
    """
    rurls = hicting.Mict()
    for eid in kever.wits:
        surls = fetch_urls(baser, eid, scheme=scheme)
        if surls:
            rurls.add(kering.Roles.witness, hicting.Mict([(eid, surls)]))
    return rurls
