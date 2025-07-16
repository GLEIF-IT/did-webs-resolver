# -*- encoding: utf-8 -*-
"""
tests.core.didding module

"""

import os
import sys

import pytest
from hio.help.hicting import Mict
from keri.app import oobiing
from keri.core import coring
from keri.db import basing
from keri.vdr import credentialing, verifying
from mockito import mock, unstub, when

from dkr.core import didding

sys.path.append(os.path.join(os.path.dirname(__file__)))

wdid = 'did:webs:127.0.0.1:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
did = 'did:webs:127.0.0.1:ECCoHcHP1jTAW8Dr44rI2kWzfF71_U0sZwvV-J_q4YE7'


def test_parse_keri_did():
    # Valid did:keri DID
    did = 'did:keri:EKW4IEkAZ8VQ_ADXbtRsSOQ_Gk0cRxp6U4qKSr4Eb8zg'
    aid = didding.parse_did_keri(did)
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


def test_parse_webs_did():
    with pytest.raises(ValueError) as e:
        did = 'did:webs:127.0.0.1:1234567'
        domain, port, path, aid = didding.parse_did_webs(did)

    assert isinstance(e.value, ValueError)
    assert str(e.value) == '1234567 is an invalid AID'

    did = 'did:webs:127.0.0.1:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did)
    assert '127.0.0.1' == domain
    assert None == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port url should be url encoded with %3a according to the spec
    did_port_bad = 'did:webs:127.0.0.1:7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_port = 'did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port should be url encoded with %3a according to the spec
    did_port_path_bad = 'did:webs:127.0.0.1:7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port_path_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676:my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port is properly url encoded with %3a according to the spec
    did_port_path = 'did:webs:127.0.0.1%3a7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port_path)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert 'my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_path = 'did:webs:127.0.0.1:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_path)
    assert '127.0.0.1' == domain
    assert None == port
    assert 'my:path' == path
    assert aid, 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'


def test_parse_web_did():
    with pytest.raises(ValueError) as e:
        did = 'did:web:127.0.0.1:1234567'
        domain, port, path, aid = didding.parse_did_webs(did)

    assert isinstance(e.value, ValueError)

    did = 'did:web:127.0.0.1:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did)
    assert '127.0.0.1' == domain
    assert None == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port url should be url encoded with %3a according to the spec
    did_port_bad = 'did:web:127.0.0.1:7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_port = 'did:web:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert None == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port should be url encoded with %3a according to the spec
    did_port_path_bad = 'did:web:127.0.0.1:7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port_path_bad)
    assert '127.0.0.1' == domain
    assert None == port
    assert '7676:my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    # port is properly url encoded with %3a according to the spec
    did_port_path = 'did:web:127.0.0.1%3a7676:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_port_path)
    assert '127.0.0.1' == domain
    assert '7676' == port
    assert 'my:path' == path
    assert aid == 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'

    did_path = 'did:web:127.0.0.1:my:path:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'
    domain, port, path, aid = didding.parse_did_webs(did_path)
    assert '127.0.0.1' == domain
    assert None == port
    assert 'my:path' == path
    assert aid, 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'


def test_generate_did_doc_bad_ends_with():
    hby = mock()
    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HD'

    with pytest.raises(ValueError) as e:
        didding.generate_did_doc(hby=hby, aid=aid, did=did)

    assert isinstance(e.value, ValueError)
    assert str(e.value) == (
        'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4 does '
        'not end with EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HD'
    )


def test_generate_did_doc_unknown_aid():
    hby = mock()
    hab = mock()
    hab_db = mock()
    kever = mock()
    db = mock()
    roobi = mock()

    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    hab.name = 'test_hab'
    hab.db = hab_db
    hby.habs = {aid: hab}
    db.roobi = roobi
    hby.db = db
    hby.kevers = {'a different aid': kever}

    with pytest.raises(ValueError) as e:
        didding.generate_did_doc(hby=hby, aid=aid, did=did)

    assert isinstance(e.value, ValueError)
    assert str(e.value) == 'unknown EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'


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

    when(hab).fetchRoleUrls(cid=aid).thenReturn(
        Mict(
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
    )
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(
        Mict(
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
    )

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

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did)

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

    when(hab).fetchRoleUrls(cid=aid).thenReturn(
        Mict(
            [
                (
                    'controller',
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
    )
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(
        Mict(
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
    )

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

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did)
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
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
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

    when(hab).fetchRoleUrls(cid=aid).thenReturn(
        Mict(
            [
                (
                    'controller',
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
    )
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(
        Mict(
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
    )
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

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did, meta=True)
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
                    'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
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

    when(hab).fetchRoleUrls(cid=aid).thenReturn(
        Mict(
            [
                (
                    'controller',
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
    )
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(
        Mict(
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
    )

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

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did, meta=True)

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
                    'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
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
                {'idx': 0, 'scheme': 'some_key_witness1', 'url': 'tcp://127.0.0.1:5632/'},
                {'idx': 1, 'scheme': 'some_key_witness2', 'url': 'tcp://127.0.0.1:5633/'},
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

    when(hab).fetchRoleUrls(cid=aid).thenReturn(
        Mict(
            [
                (
                    'controller',
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
    )
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(
        Mict(
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
    )

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

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did)

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
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
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

    when(hab).fetchRoleUrls(cid=aid).thenReturn(
        Mict(
            [
                (
                    'controller',
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
    )
    when(hab).fetchWitnessUrls(cid=aid).thenReturn(
        Mict(
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
    )
    when(credentialing).Regery(hby=hby, name=hby.name).thenReturn(rgy)
    when(verifying).Verifier(hby=hby, reger=rgy.reger).thenReturn(vry)

    when(rgy.reger.issus).get(keys=aid).thenReturn([])
    when(rgy.reger.issus).get(keys=aid).thenReturn([])

    when(rgy.reger).cloneCreds([], hab_db).thenReturn([])

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did)

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
                'serviceEndpoint': {'http': 'http://localhost:8080/witness/wok'},
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


def test_generate_did_doc_single_sig_with_oobi():
    hby = mock()
    hab = mock()
    hab_db = mock()
    db = mock()
    roobi = mock()

    did = 'did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    aid = 'EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4'
    hab.name = 'test_hab'
    hab.db = hab_db
    hby.habs = {aid: hab}
    db.roobi = roobi
    hby.db = db

    when(hby.db.roobi).get(keys=('with_oobi',)).thenReturn(None)

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did, oobi='with_oobi')

    assert (
        diddoc
        == b'{"msg": "OOBI resolution for did did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4 failed."}'
    )
    unstub()

    obr = basing.OobiRecord(state=oobiing.Result.failed)
    when(hby.db.roobi).get(keys=('with_oobi_2',)).thenReturn(obr)

    diddoc = didding.generate_did_doc(hby=hby, aid=aid, did=did, oobi='with_oobi_2')

    assert (
        diddoc
        == b'{"msg": "OOBI resolution for did did:web:127.0.0.1%3A7676:EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4 failed."}'
    )

    unstub()


def test_to_did_web():
    diddoc = {'id': 'did:webs:example:123', 'verificationMethod': [{'controller': 'did:webs:example:123'}]}

    from dkr.core.didding import to_did_web

    result = to_did_web(diddoc)

    assert result['id'] == 'did:web:example:123'
    assert result['verificationMethod'][0]['controller'] == 'did:web:example:123'

    unstub()


def test_from_did_web():
    diddoc = {'id': 'did:web:example:123', 'verificationMethod': [{'controller': 'did:web:example:123'}]}

    from dkr.core.didding import from_did_web

    result = from_did_web(diddoc)

    # Verify the changes
    assert result['id'] == 'did:webs:example:123'
    assert result['verificationMethod'][0]['controller'] == 'did:webs:example:123'

    unstub()


def test_from_did_web_no_change():
    diddoc = {'id': 'did:webs:example:123', 'verificationMethod': [{'controller': 'did:webs:example:123'}]}

    from dkr.core.didding import from_did_web

    result = from_did_web(diddoc)

    assert result['id'] == 'did:webs:example:123'
    assert result['verificationMethod'][0]['controller'] == 'did:webs:example:123'

    unstub()
