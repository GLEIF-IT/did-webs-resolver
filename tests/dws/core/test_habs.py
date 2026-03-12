import random
import string
from unittest.mock import MagicMock

from hio.help import Mict
from keri.app import habbing
from keri.core import signing
from keri.core.eventing import Kever
from keri.db.basing import Baser, LocationRecord

from dws.core import habs
from dws.core.habs import fetch_urls, get_role_urls


def test_habs():
    # generate a random 6 character string
    cf = habs.get_habery_configer(name=None, base='', head_dir_path=None, temp=True)
    assert cf is None
    cf = habs.get_habery_configer(name='test_habs', base='', head_dir_path=None, temp=True)
    assert cf is not None

    aeid = habs.get_auth_encryption_aid(name='test_habs', base='', temp=True)
    assert aeid is None  # Habery has not been created yet
    random_name = (''.join(random.choices(string.ascii_uppercase + string.digits, k=6))) + '1'

    # tests the already existing case - needs to set temp=False to check for existing files
    #   WARNING: this makes the test somewhat  flaky
    salt = signing.Salter().qb64
    salt = salt.replace('-', '')
    habbing.Habery(name=random_name, base='', bran=salt, temp=False)
    hby, hby_doer = habs.get_habery_and_doer(name=random_name, base='', bran=salt, cf=cf, temp=False)
    assert hby is not None
    assert hby_doer is not None

    # use random name to avoid LMDB lock table conflicts
    random_name = (''.join(random.choices(string.ascii_uppercase + string.digits, k=6))) + '2'
    hby, hby_doer = habs.get_habery_and_doer(name=random_name, base='', bran=None, cf=cf, temp=True)
    assert hby is not None
    assert hby_doer is not None


def test_fetch_urls_and_get_role_urls_when_empty_loc_url_then_returns_empty_results():
    baser = MagicMock(spec=Baser)
    baser.locs = MagicMock()
    baser.locs.getItemIter = MagicMock()

    eid = 'myeid'
    scheme = 'http'
    locScheme = LocationRecord(url=None)
    urls = [((eid, scheme), locScheme)]
    baser.locs.getItemIter.return_value = urls
    fetched = fetch_urls(baser, eid, scheme)
    assert fetched == Mict([])

    kever = MagicMock(spec=Kever)
    kever.wits = ['myeid']
    role_urls = get_role_urls(baser, kever, scheme)
    assert role_urls == Mict([])
