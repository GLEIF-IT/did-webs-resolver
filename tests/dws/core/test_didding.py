# -*- encoding: utf-8 -*-
"""
tests.core.didding module

"""

import os
import sys
from unittest.mock import patch

import pytest
from hio.help.hicting import Mict
from keri.app import habbing
from keri.core import coring, eventing, serdering
from keri.db import basing, koming, subing
from keri.vdr import credentialing, verifying
from mockito import mock, unstub, when

from dws import DidWebsError, UnknownAID
from dws.core import didding, didkeri

sys.path.append(os.path.join(os.path.dirname(__file__)))

wdid = 'did:webs:127.0.0.1:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
did = 'did:webs:127.0.0.1:ECCoHcHP1jTAW8Dr44rI2kWzfF71_U0sZwvV-J_q4YE7'


def test_parse_keri_did():
    # Valid did:keri DID
    did = 'did:keri:EKW4IEkAZ8VQ_ADXbtRsSOQ_Gk0cRxp6U4qKSr4Eb8zg'
    aid, query = didding.parse_did_keri(did)
    assert aid == 'EKW4IEkAZ8VQ_ADXbtRsSOQ_Gk0cRxp6U4qKSr4Eb8zg'

    # Invalid AID in did:keri
    did = 'did:keri:Gk0cRxp6U4qKSr4Eb8zg'

    with pytest.raises(ValueError) as e:
        _, _ = didding.parse_did_keri(did)

    assert isinstance(e.value, ValueError)
    assert str(e.value) == 'Gk0cRxp6U4qKSr4Eb8zg is an invalid AID'

    non_matching_dids = [
        'did:keri:example:extra',
        'did:keri:',
        'did:keri:example:123',
        'did:keri:example:extra:more',
        'did:keri:example:extra:evenmore',
    ]

    for did in non_matching_dids:
        with pytest.raises(ValueError):
            didding.parse_did_keri(did)

        assert isinstance(e.value, ValueError)

    with pytest.raises(ValueError) as e:
        didding.generate_did_doc(hby=mock(), rgy=mock(), did='did:keri:', aid='EKW4IEkAZ8VQ_ADXbtRsSOQ_Gk0cRxp6U4qKSr4Eb8zg')


def test_parse_webs_did():
    with pytest.raises(ValueError) as e:
        did = 'did:example'
        didding.parse_did_webs(did)
    assert str(e.value) == f'{did} is not a valid did:web(s) DID'

    with pytest.raises(ValueError) as e:
        did = 'did:webs:127.0.0.1:1234567'
        domain, port, path, aid, query = didding.parse_did_webs(did)

    assert isinstance(e.value, ValueError)
    assert str(e.value) == '1234567 is an invalid AID'

    did = 'did:webs:127.0.0.1:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did)
    assert '127.0.0.1' == domain
    assert None == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port url should be url encoded with %3a according to the spec
    did_port_bad = 'did:webs:127.0.0.1:7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_port = 'did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port should be url encoded with %3a according to the spec
    did_port_path_bad = 'did:webs:127.0.0.1:7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port_path_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676:my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port is properly url encoded with %3a according to the spec
    did_port_path = 'did:webs:127.0.0.1%3a7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port_path)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert 'my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_path = 'did:webs:127.0.0.1:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_path)
    assert '127.0.0.1' == domain
    assert None == port
    assert 'my:path' == path
    assert aid, 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'


def test_parse_web_did():
    with pytest.raises(ValueError) as e:
        did = 'did:web:127.0.0.1:1234567'
        domain, port, path, aid, query = didding.parse_did_webs(did)

    assert isinstance(e.value, ValueError)

    did = 'did:web:127.0.0.1:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did)
    assert '127.0.0.1' == domain
    assert None == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port url should be url encoded with %3a according to the spec
    did_port_bad = 'did:web:127.0.0.1:7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_port = 'did:web:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port should be url encoded with %3a according to the spec
    did_port_path_bad = 'did:web:127.0.0.1:7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port_path_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676:my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port is properly url encoded with %3a according to the spec
    did_port_path = 'did:web:127.0.0.1%3a7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_port_path)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert 'my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_path = 'did:web:127.0.0.1:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid, query = didding.parse_did_webs(did_path)
    assert '127.0.0.1' == domain
    assert None == port
    assert 'my:path' == path
    assert aid, 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'


def test_generate_did_doc_bad_aid():
    hby = mock()
    rgy = mock()
    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HD'

    with pytest.raises(ValueError) as e:
        didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid)

    assert isinstance(e.value, ValueError)
    assert str(e.value) == (
        'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4 does '
        'not contain AID EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HD'
    )


def test_generate_did_doc_unknown_aid():
    hby = mock()
    hab = mock()
    hab_db = mock()
    kever = mock()
    db = mock()
    roobi = mock()
    rgy = mock()

    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    hab.name = 'test_hab'
    hab.db = hab_db
    hby.habs = {aid: hab}
    db.roobi = roobi
    hby.db = db
    hby.kevers = {'a different aid': kever}

    with pytest.raises(UnknownAID) as e:
        didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid)

    assert isinstance(e.value, UnknownAID)
    assert (
        str(e.value)
        == 'Unknown AID EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4 found in did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    )


def role_urls_fixture():
    return Mict(
        [
            (
                'controller',
                Mict(
                    [
                        (
                            'BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX',
                            Mict(
                                [
                                    ('http', 'http://localhost:8080/witness/wok'),
                                    ('tcp', 'tcp://localhost:8080/witness/wok'),
                                ]
                            ),
                        )
                    ]
                ),
            )
        ]
    )


def witness_urls_fixture():
    return Mict(
        [
            (
                'witness',
                Mict(
                    [
                        (
                            'BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX',
                            Mict([('http', 'http://localhost:8080/witness/wok')]),
                        )
                    ]
                ),
            )
        ]
    )


def test_generate_did_doc_single_sig():
    hby = mock()
    hby.name = 'test_hby'
    hab = mock()
    hab_db = mock()
    kever = mock()
    verfer = mock()
    tholder = mock()
    db = mock()
    locs = mock()

    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    hab.name = 'test_hab'
    hab.db = hab_db
    hab.delpre = None
    hby.habs = {aid: hab}
    sner = mock()
    sner.num = 0
    kever.sner = sner
    hby.kevers = {aid: kever}
    verfer.raw = bytearray()
    verfer.qb64 = 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K'
    kever.verfers = [verfer]
    tholder.thold = None
    kever.tholder = tholder
    db.locs = locs
    hby.db = db
    wits = []
    kever.wits = wits

    loc = basing.LocationRecord(url='tcp://127.0.0.1:5634/')
    when(db.locs).getItemIter(keys=(aid,)).thenReturn([((aid, 'some_key'), loc)])

    when(hab).fetchRoleUrls(cid=aid).thenReturn(role_urls_fixture())
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(witness_urls_fixture())

    rgy = mock()
    issus = mock()
    schms = mock()
    rgy.reger = mock()
    rgy.reger.issus = issus
    rgy.reger.schms = schms
    vry = mock()

    when(credentialing).Regery(hby=hby, name=hby.name).thenReturn(rgy)
    when(verifying).Verifier(hby=hby, reger=rgy.reger).thenReturn(vry)

    when(rgy.reger.issus).get(keys=aid).thenReturn([])
    when(rgy.reger.issus).get(keys=aid).thenReturn([])

    when(rgy.reger).cloneCreds([], hab_db).thenReturn([])

    diddoc = didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid)

    assert diddoc == {
        'id': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
        'verificationMethod': [
            {
                'id': '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                'type': 'JsonWebKey',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'publicKeyJwk': {
                    'kid': 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                    'kty': 'OKP',
                    'crv': 'Ed25519',
                    'x': '',
                },
            }
        ],
        'service': [
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/controller',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok', 'tcp': 'tcp://localhost:8080/witness/wok'},
                'type': 'controller',
            },
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/witness',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
                'type': 'witness',
            },
        ],
        'alsoKnownAs': [],
    }

    unstub()


def test_generate_did_doc_single_sig_with_designated_alias(mock_helping_now_utc):
    hby = mock()
    hby.name = 'test_hby'
    hab = mock()
    hab_db = mock()
    kever = mock()
    verfer = mock()
    tholder = mock()
    db = mock()
    locs = mock()

    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    hab.name = 'test_hab'
    hab.db = hab_db
    hab.delpre = None
    hby.habs = {aid: hab}
    sner = mock()
    sner.num = 0
    kever.sner = sner
    hby.kevers = {aid: kever}
    verfer.raw = bytearray()
    verfer.qb64 = 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K'
    kever.verfers = [verfer]
    tholder.thold = None
    kever.tholder = tholder
    db.locs = locs
    hby.db = db
    wits = []
    kever.wits = wits

    loc = basing.LocationRecord(url='tcp://127.0.0.1:5634/')
    when(db.locs).getItemIter(keys=(aid,)).thenReturn([((aid, 'some_key'), loc)])

    when(hab).fetchRoleUrls(cid=aid).thenReturn(role_urls_fixture())
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(witness_urls_fixture())

    rgy = mock()
    issus = mock()
    schms = mock()
    rgy.reger = mock()
    rgy.reger.issus = issus
    rgy.reger.schms = schms
    vry = mock()

    when(credentialing).Regery(hby=hby, name=hby.name).thenReturn(rgy)
    when(verifying).Verifier(hby=hby, reger=rgy.reger).thenReturn(vry)

    cred1 = mock({'qb64': 'cred_1_qb64'}, coring.Saider)
    cred2 = mock({'qb64': 'cred_2_qb64'}, coring.Saider)
    when(rgy.reger.issus).get(keys=aid).thenReturn([cred1, cred2])
    when(rgy.reger.schms).get(keys='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5').thenReturn([cred1, cred2])

    cloned_cred1 = {'sad': {'a': {'ids': ['designated_id_1']}}, 'status': {'et': 'iss'}}
    cloned_cred2 = {
        'sad': {'a': {'ids': ['did:webs:foo:designated_id_2', 'designated_id_2_but_different']}},
        'status': {'et': 'bis'},
    }
    when(rgy.reger).cloneCreds([cred1, cred2], hab_db).thenReturn([cloned_cred1, cloned_cred2])

    diddoc = didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid)
    assert diddoc == {
        'id': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
        'verificationMethod': [
            {
                'id': '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                'type': 'JsonWebKey',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'publicKeyJwk': {
                    'kid': 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                    'kty': 'OKP',
                    'crv': 'Ed25519',
                    'x': '',
                },
            }
        ],
        'service': [
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/controller',
                'type': 'controller',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok', 'tcp': 'tcp://localhost:8080/witness/wok'},
            },
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/witness',
                'type': 'witness',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
            },
        ],
        'alsoKnownAs': ['designated_id_1', 'did:webs:foo:designated_id_2', 'designated_id_2_but_different'],
    }

    unstub()

    loc = basing.LocationRecord(url='tcp://127.0.0.1:5634/')
    when(db.locs).getItemIter(keys=(aid,)).thenReturn([((aid, 'some_key'), loc)])

    when(hab).fetchRoleUrls(cid=aid).thenReturn(role_urls_fixture())
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(witness_urls_fixture())
    when(credentialing).Regery(hby=hby, name=hby.name).thenReturn(rgy)
    when(verifying).Verifier(hby=hby, reger=rgy.reger).thenReturn(vry)

    cred1 = mock({'qb64': 'cred_1_qb64'}, coring.Saider)
    cred2 = mock({'qb64': 'cred_2_qb64'}, coring.Saider)
    when(rgy.reger.issus).get(keys=aid).thenReturn([cred1, cred2])
    when(rgy.reger.schms).get(keys='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5').thenReturn([cred1, cred2])

    cloned_cred1 = {'sad': {'a': {'ids': ['designated_id_1']}}, 'status': {'et': 'iss'}}
    cloned_cred2 = {
        'sad': {'a': {'ids': ['did:webs:foo:designated_id_2', 'designated_id_2_but_different']}},
        'status': {'et': 'bis'},
    }
    when(rgy.reger).cloneCreds([cred1, cred2], hab_db).thenReturn([cloned_cred1, cloned_cred2])

    diddoc = didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid, meta=True)
    assert diddoc == {
        'didDocument': {
            'id': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
            'verificationMethod': [
                {
                    'id': '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                    'type': 'JsonWebKey',
                    'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                    'publicKeyJwk': {
                        'kid': 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                        'kty': 'OKP',
                        'crv': 'Ed25519',
                        'x': '',
                    },
                }
            ],
            'service': [
                {
                    'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/controller',
                    'type': 'controller',
                    'serviceEndpoint': {
                        'http': 'http://localhost:8080/witness/wok',
                        'tcp': 'tcp://localhost:8080/witness/wok',
                    },
                },
                {
                    'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/witness',
                    'type': 'witness',
                    'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
                },
            ],
            'alsoKnownAs': ['designated_id_1', 'did:webs:foo:designated_id_2', 'designated_id_2_but_different'],
        },
        'didResolutionMetadata': {'contentType': 'application/did+json', 'retrieved': '2021-01-01T00:00:00Z'},
        'didDocumentMetadata': {'witnesses': [], 'versionId': '0', 'equivalentId': ['did:webs:foo:designated_id_2']},
    }


def test_generate_did_doc_single_sig_meta(mock_helping_now_utc):
    hby = mock()
    hby.name = 'test_hby'
    hab = mock()
    hab_db = mock()
    kever = mock()
    verfer = mock()
    tholder = mock()
    db = mock()
    locs = mock()

    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    hab.name = 'test_hab'
    hab.db = hab_db
    hab.delpre = None
    hby.habs = {aid: hab}
    sner = mock()
    sner.num = 0
    kever.sner = sner
    hby.kevers = {aid: kever}
    verfer.raw = bytearray()
    verfer.qb64 = 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K'
    kever.verfers = [verfer]
    tholder.thold = None
    kever.tholder = tholder
    db.locs = locs
    hby.db = db
    kever.wits = ['witness1', 'witness2']

    loc = basing.LocationRecord(url='tcp://127.0.0.1:5632/')
    when(db.locs).getItemIter(keys=('witness1',)).thenReturn([(('witness1', 'some_key_witness1'), loc)])
    loc = basing.LocationRecord(url='tcp://127.0.0.1:5633/')
    when(db.locs).getItemIter(keys=('witness2',)).thenReturn([(('witness2', 'some_key_witness2'), loc)])
    loc = basing.LocationRecord(url='tcp://127.0.0.1:5634/')
    when(db.locs).getItemIter(keys=(aid,)).thenReturn([((aid, 'some_key'), loc)])

    when(hab).fetchRoleUrls(cid=aid).thenReturn(role_urls_fixture())
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(witness_urls_fixture())

    rgy = mock()
    issus = mock()
    schms = mock()
    rgy.reger = mock()
    rgy.reger.issus = issus
    rgy.reger.schms = schms
    vry = mock()

    when(credentialing).Regery(hby=hby, name=hby.name).thenReturn(rgy)
    when(verifying).Verifier(hby=hby, reger=rgy.reger).thenReturn(vry)

    when(rgy.reger.issus).get(keys=aid).thenReturn([])
    when(rgy.reger.issus).get(keys=aid).thenReturn([])

    when(rgy.reger).cloneCreds([], hab_db).thenReturn([])

    diddoc = didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid, meta=True)

    assert diddoc == {
        'didDocument': {
            'id': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
            'verificationMethod': [
                {
                    'id': '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                    'type': 'JsonWebKey',
                    'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                    'publicKeyJwk': {
                        'kid': 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                        'kty': 'OKP',
                        'crv': 'Ed25519',
                        'x': '',
                    },
                }
            ],
            'service': [
                {
                    'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/controller',
                    'type': 'controller',
                    'serviceEndpoint': {
                        'http': 'http://localhost:8080/witness/wok',
                        'tcp': 'tcp://localhost:8080/witness/wok',
                    },
                },
                {
                    'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/witness',
                    'type': 'witness',
                    'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
                },
            ],
            'alsoKnownAs': [],
        },
        'didResolutionMetadata': {'contentType': 'application/did+json', 'retrieved': '2021-01-01T00:00:00Z'},
        'didDocumentMetadata': {
            'witnesses': [
                {'idx': '0', 'scheme': 'some_key_witness1', 'url': 'tcp://127.0.0.1:5632/'},
                {'idx': '1', 'scheme': 'some_key_witness2', 'url': 'tcp://127.0.0.1:5633/'},
            ],
            'versionId': '0',
            'equivalentId': [],
        },
    }

    unstub()


def test_generate_did_doc_multi_sig():
    hby = mock()
    hby.name = 'test_hby'
    hab = mock()
    hab_db = mock()
    kever = mock()
    verfer = mock()
    verfer_multi = mock()
    tholder = mock()
    db = mock()
    locs = mock()

    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    hab.name = 'test_hab'
    hab.delpre = None
    hab.db = hab_db
    hby.habs = {aid: hab}
    sner = mock()
    sner.num = 0
    kever.sner = sner
    hby.kevers = {aid: kever}
    verfer.raw = bytearray()
    verfer.qb64 = 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K'
    verfer_multi.raw = bytearray()
    verfer_multi.qb64 = 'DOZlWGPfDHLMf62zSFzE8thHmnQUOgA3_Y-KpOyF9ScG'
    kever.verfers = [verfer, verfer_multi]
    tholder.thold = 2
    kever.tholder = tholder
    db.locs = locs
    hby.db = db
    wits = []
    kever.wits = wits

    loc = basing.LocationRecord(url='tcp://127.0.0.1:5634/')
    when(db.locs).getItemIter(keys=(aid,)).thenReturn([((aid, 'some_key'), loc)])

    when(hab).fetchRoleUrls(cid=aid).thenReturn(role_urls_fixture())
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(witness_urls_fixture())

    rgy = mock()
    issus = mock()
    schms = mock()
    rgy.reger = mock()
    rgy.reger.issus = issus
    rgy.reger.schms = schms
    vry = mock()

    when(credentialing).Regery(hby=hby, name=hby.name).thenReturn(rgy)
    when(verifying).Verifier(hby=hby, reger=rgy.reger).thenReturn(vry)

    when(rgy.reger.issus).get(keys=aid).thenReturn([])
    when(rgy.reger.issus).get(keys=aid).thenReturn([])

    when(rgy.reger).cloneCreds([], hab_db).thenReturn([])

    diddoc = didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid)

    assert diddoc == {
        'id': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
        'verificationMethod': [
            {
                'id': '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                'type': 'JsonWebKey',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'publicKeyJwk': {
                    'kid': 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                    'kty': 'OKP',
                    'crv': 'Ed25519',
                    'x': '',
                },
            },
            {
                'id': '#DOZlWGPfDHLMf62zSFzE8thHmnQUOgA3_Y-KpOyF9ScG',
                'type': 'JsonWebKey',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'publicKeyJwk': {
                    'kid': 'DOZlWGPfDHLMf62zSFzE8thHmnQUOgA3_Y-KpOyF9ScG',
                    'kty': 'OKP',
                    'crv': 'Ed25519',
                    'x': '',
                },
            },
            {
                'id': '#EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'type': 'ConditionalProof2022',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'threshold': 2,
                'conditionThreshold': [
                    '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                    '#DOZlWGPfDHLMf62zSFzE8thHmnQUOgA3_Y-KpOyF9ScG',
                ],
            },
        ],
        'service': [
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/controller',
                'type': 'controller',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok', 'tcp': 'tcp://localhost:8080/witness/wok'},
            },
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/witness',
                'type': 'witness',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
            },
        ],
        'alsoKnownAs': [],
    }

    unstub()

    kever.tholder = coring.Tholder(sith=['1/2', '1/2'])

    when(db.locs).getItemIter(keys=(aid,)).thenReturn([((aid, 'some_key'), loc)])

    when(hab).fetchRoleUrls(cid=aid).thenReturn(role_urls_fixture())
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(witness_urls_fixture())
    when(credentialing).Regery(hby=hby, name=hby.name).thenReturn(rgy)
    when(verifying).Verifier(hby=hby, reger=rgy.reger).thenReturn(vry)

    when(rgy.reger.issus).get(keys=aid).thenReturn([])
    when(rgy.reger.issus).get(keys=aid).thenReturn([])

    when(rgy.reger).cloneCreds([], hab_db).thenReturn([])

    diddoc = didding.generate_did_doc(hby=hby, rgy=rgy, did=did, aid=aid)

    assert diddoc == {
        'id': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
        'verificationMethod': [
            {
                'id': '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                'type': 'JsonWebKey',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'publicKeyJwk': {
                    'kid': 'DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K',
                    'kty': 'OKP',
                    'crv': 'Ed25519',
                    'x': '',
                },
            },
            {
                'id': '#DOZlWGPfDHLMf62zSFzE8thHmnQUOgA3_Y-KpOyF9ScG',
                'type': 'JsonWebKey',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'publicKeyJwk': {
                    'kid': 'DOZlWGPfDHLMf62zSFzE8thHmnQUOgA3_Y-KpOyF9ScG',
                    'kty': 'OKP',
                    'crv': 'Ed25519',
                    'x': '',
                },
            },
            {
                'id': '#EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'type': 'ConditionalProof2022',
                'controller': 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4',
                'threshold': 1.0,
                'conditionWeightedThreshold': [
                    {'condition': '#DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K', 'weight': 1},
                    {'condition': '#DOZlWGPfDHLMf62zSFzE8thHmnQUOgA3_Y-KpOyF9ScG', 'weight': 1},
                ],
            },
        ],
        'service': [
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/controller',
                'type': 'controller',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok', 'tcp': 'tcp://localhost:8080/witness/wok'},
            },
            {
                'id': '#BKVb58uITf48YoMPz8SBOTVwLgTO9BY4oEXRPoYIOErX/witness',
                'type': 'witness',
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
            },
        ],
        'alsoKnownAs': [],
    }

    unstub()


def test_to_did_web():
    diddoc = {'id': 'did:webs:example:123', 'verificationMethod': [{'controller': 'did:webs:example:123'}]}

    from dws.core.didding import to_did_web

    result = to_did_web(diddoc)

    assert result['id'] == 'did:web:example:123'
    assert result['verificationMethod'][0]['controller'] == 'did:web:example:123'

    with pytest.raises(DidWebsError) as excinfo:
        to_did_web(None)
    assert str(excinfo.value) == 'Cannot convert empty diddoc to did:web'

    unstub()


def test_from_did_web():
    diddoc = {'id': 'did:web:example:123', 'verificationMethod': [{'controller': 'did:web:example:123'}]}

    from dws.core.didding import from_did_web

    result = from_did_web(diddoc)

    # Verify the changes
    assert result['id'] == 'did:webs:example:123'
    assert result['verificationMethod'][0]['controller'] == 'did:webs:example:123'

    with pytest.raises(ValueError) as excinfo:
        from_did_web(diddoc, meta=True)
    assert str(excinfo.value) == f"Expected '{didding.DD_FIELD}' in did.json when indicating resolution metadata in use."

    unstub()


def test_from_did_web_no_change():
    diddoc = {'id': 'did:webs:example:123', 'verificationMethod': [{'controller': 'did:webs:example:123'}]}

    from dws.core.didding import from_did_web

    result = from_did_web(diddoc)

    assert result['id'] == 'did:webs:example:123'
    assert result['verificationMethod'][0]['controller'] == 'did:webs:example:123'

    unstub()


def test_parse_did_webs_no_match_raises():
    did = 'did:webs:example:123'
    with pytest.raises(ValueError) as excinfo:
        didding.parse_did_webs(did)
        assert str(excinfo.value) == f'{did} is not a valid did:web(s) DID'


def test_parse_query_string_false_param():
    query_string = '?param1=value1&param2=false'
    result = didding.parse_query_string(query_string)
    assert result == {'param1': 'value1', 'param2': False}


def test_parse_query_string_with_int_parse_as_int():
    query_string = '?param1=value1&param2=42'
    result = didding.parse_query_string(query_string)
    assert result == {'param1': 'value1', 'param2': 42}


def test_re_encode_invalid_did_webs_invalid_aid_raises():
    invalid_aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk'
    # it is invalidly encoded because it has an unencoded colon after the domain instead of the percent-encoded %3A string.
    invl_did_invl_aid = f'did:webs:127.0.0.1:7676:{invalid_aid}'
    with pytest.raises(ValueError) as excinfo:
        didding.re_encode_invalid_did_webs(invl_did_invl_aid)
        assert str(excinfo.value) == f'{invl_did_invl_aid} is an invalid AID'


def test_re_encode_valid_did_webs_did_returns_original_did():
    valid_did = 'did:webs:example.com%3A8443:my:path:components:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4?meta=true'
    result = didding.re_encode_invalid_did_webs(valid_did)
    assert result == valid_did, f'Expected {valid_did}, but got {result}'


def test_re_encode_invalid_did_non_webs_raises():
    invalid_did = 'did:example:123'
    with pytest.raises(ValueError) as excinfo:
        didding.re_encode_invalid_did_webs(invalid_did)
        assert str(excinfo.value) == f'{invalid_did} is not an invalidly encoded did:web(s) DID'


def test_re_encode_invalid_did_webs_did_adds_domain_port_path_aid_query_parts():
    domain = 'example.com'
    port = '8080'
    path = 'some:path:for:did'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    query = '?meta=True'
    # it is invalidly encoded because it has an unencoded colon after the domain instead of the percent-encoded %3A string.
    invalidly_encoded_did = f'did:webs:{domain}:{port}:{path}:{aid}{query}'
    expected_did = f'did:webs:{domain}%3A{port}:{path}:{aid}{query}'
    result = didding.re_encode_invalid_did_webs(invalidly_encoded_did)
    assert result == expected_did, f'Expected {expected_did}, but got {result}'
    assert domain in result, 'Domain should be present in the result'
    assert port in result, 'Port should be present in the result'
    assert path in result, 'Path should be present in the result'
    assert aid in result, 'AID should be present in the result'
    assert query in result, 'Query should be present in the result'
    assert result.startswith('did:webs:'), "Result should start with 'did:webs:'"
    assert result.count(':') == 7, 'Result should have exactly 7 colons'
    assert '%3A' in result, "Result should contain the encoded colon '%3A' after the domain"


def test_re_encode_invalid_did_raises_for_non_did_webs_or_keri_did():
    non_did_webs_did = 'did:example:123'
    with pytest.raises(ValueError) as excinfo:
        didding.re_encode_invalid_did(non_did_webs_did)
        assert str(excinfo.value) == f'{non_did_webs_did} is not a valid did:webs or did:keri DID'


def test_re_encode_invalid_did_encodes_did_webs_did():
    invalidly_encoded_did = (
        f'did:webs:example.com:1234:my:path:components:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4?meta=true'
    )
    expected_did = f'did:webs:example.com%3A1234:my:path:components:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4?meta=true'
    result = didding.re_encode_invalid_did(invalidly_encoded_did)
    assert result == expected_did, f'Expected {expected_did}, but got {result}'


def test_re_encode_invalid_did_encodes_did_keri_did():
    did_keri_did = f'did:keri:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    result = didding.re_encode_invalid_did(did_keri_did)
    assert result == did_keri_did, f'Expected {did_keri_did}, but got {result}'


def test_did_keri_regex_match_parses_query():
    aid = 'EEdpe-yqftH2_FO1-luoHvaiShK4y_E2dInrRQ2_2X5v'
    query = '?meta=true&oobi=http%3A//127.0.0.1%3A6642/oobi/EEdpe-yqftH2_FO1-luoHvaiShK4y_E2dInrRQ2_2X5v/witness/BPwwr5VkI1b7ZA2mVbzhLL47UPjsGBX4WeO6WRv6c7H-'
    did_keri_did = f'did:keri:{aid}{query}'
    matched_aid, matched_query = didding.parse_did_keri(did_keri_did)
    assert matched_aid is not None, f'Expected AID to be parsed, but got {aid}'
    assert matched_query is not None, f'Expected query to be parsed, but got {query}'
    assert matched_aid == aid, f'Expected matched AID to be {aid}, but got {matched_aid}'
    assert matched_query == query, f'Expected matched query to be {query}, but got {matched_query}'


def test_requote_did_re_encodes_improperly_url_encoded_dids():
    invalidly_encoded_did = (
        f'did%3Awebs%3Aexample.com%3A8443%3Amy%3Apath%3Acomponents%3AEKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4?meta=true'
    )
    expected_did = f'did:webs:example.com%3A8443:my:path:components:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4?meta=true'
    requoted_did = didding.requote(invalidly_encoded_did)
    assert requoted_did == expected_did, f'Expected {expected_did}, but got {requoted_did}'


def test_extract_desg_alias_from_cred_rev_status_returns_none():
    cred = {
        'sad': {'a': {'ids': ['did:webs:foo:designated_id_2', 'designated_id_2_but_different']}},
        'status': {'et': 'rev'},
    }
    assert None == didding.extract_desg_alias_from_cred(cred), 'Expected None for revocation status'


def test_keri_resolver_with_empty_hby_creates_hby():
    hby_mock = mock(habbing.Habery)
    hby_mock.db = mock(basing.Baser)
    hby_doer_mock = mock(habbing.HaberyDoer)
    rgy_mock = mock(credentialing.Regery)
    with patch('dws.core.habs.get_habery_and_doer') as mock_get_habery_and_doer:
        mock_get_habery_and_doer.return_value = hby_mock, hby_doer_mock
        resolver = didkeri.KeriResolver(did='fake:did', name='test_resolver', base='test_base', rgy=rgy_mock)
        assert resolver.hby == hby_mock, 'Expected KeriResolver to create a new Habery instance'
        assert hby_doer_mock in resolver.doers, 'Expected KeriResolver to add HaberyDoer to its doers'


def test_designated_aliases_generation_returns_creds_when_non_local_aid():
    hby = mock(habbing.Habery)
    hby.db = mock(basing.Baser)
    hby.habs = {}
    rgy = mock(credentialing.Regery)
    rgy.reger = mock(credentialing.Reger)
    rgy.reger.issus = mock(subing.CesrDupSuber)
    rgy.reger.schms = mock(subing.CesrDupSuber)

    test_saider = coring.Saider(qb64='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5')

    when(rgy.reger.issus).get(keys='test_aid').thenReturn([test_saider])
    when(rgy.reger.schms).get(keys='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5').thenReturn([test_saider])
    when(rgy.reger).cloneCreds([test_saider], hby.db).thenReturn([])
    da = didding.gen_designated_aliases(hby, rgy, 'test_aid')
    assert da == [], 'Expected empty list for designated aliases when no credentials are found'


def test_generate_did_doc_with_delegator_shows_service_delegator_section():
    pass


def test_gen_delegation_service_generates_correctly():
    seal_evt = dict(i='delegate_aid', s='0', d='delegate_aid')
    mockSealSerder = mock(serdering.SerderKERI)
    mockSealSerder.sad = {'a': [{'d': 'delegator_aid'}]}

    hby = mock(habbing.Habery)
    hby.db = mock(basing.Baser)
    hby.db.roobi = mock(koming.Komer)
    when(hby.db).fetchLastSealingEventByEventSeal(pre='delegator_aid', seal=seal_evt).thenReturn(mockSealSerder)
    oobi = 'http://example.com/oobi/delegate_aid'
    obr = basing.OobiRecord(cid='delegator_aid')
    when(hby.db.roobi).getItemIter().thenReturn([((oobi,), obr)])

    assert didding.gen_delegation_service(hby=hby, pre='delegate_aid', delpre='delegator_aid')


def test_gen_delegation_service_no_oobi_returns_none():
    seal_evt = dict(i='delegate_aid', s='0', d='delegate_aid')
    mockSealSerder = mock(serdering.SerderKERI)
    mockSealSerder.sad = {'a': [{'d': 'delegator_aid'}]}

    hby = mock(habbing.Habery)
    hby.db = mock(basing.Baser)
    hby.db.roobi = mock(koming.Komer)
    when(hby.db).fetchLastSealingEventByEventSeal(pre='delegator_aid', seal=seal_evt).thenReturn(mockSealSerder)
    when(hby.db.roobi).getItemIter().thenReturn([])

    assert didding.gen_delegation_service(hby=hby, pre='delegate_aid', delpre='delegator_aid') == []


def test_gen_service_endpoints_when_del_serv_end_is_none_does_not_include_delegator_service():
    aid = 'delegate_aid'
    seal_evt = dict(i='delegate_aid', s='0', d='delegate_aid')
    mockSealSerder = mock(serdering.SerderKERI)
    mockSealSerder.sad = {'a': [{'d': 'delegator_aid'}]}

    hby = mock(habbing.Habery)
    hby.db = mock(basing.Baser)
    hby.db.roobi = mock(koming.Komer)
    when(hby.db).fetchLastSealingEventByEventSeal(pre='delegator_aid', seal=seal_evt).thenReturn(mockSealSerder)
    when(hby.db.roobi).getItemIter().thenReturn([])

    hab = mock(habbing.Hab)
    kever = mock(eventing.Kever)
    when(hab).fetchRoleUrls(cid=aid).thenReturn(role_urls_fixture())
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(witness_urls_fixture())

    serv_endpoints = didding.gen_service_endpoints(hby=hby, hab=hab, kever=kever, aid='delegate_aid')
    assert len(serv_endpoints) > 0, 'Service endpoints should not be empty'
    assert 'DelegatorOOBI' not in [service['type'] for service in serv_endpoints], 'Delegator service should not be included'
