import falcon
import pytest
from keri import kering
from keri.app import habbing
from keri.core import eventing
from keri.db import basing, koming, subing
from keri.vdr import credentialing
from mockito import mock, when

from dws.core import didding
from dws.core.artifacting import gen_loc_schemes_cesr
from dws.core.ends.keri_cesr_resource_end import KeriCesrResourceEnd


def test_keri_cesr_resource_end_on_get_single_sig():
    req = mock(falcon.Request)
    rep = mock(falcon.Response)
    hby = mock(habbing.Habery)

    hab = mock()
    hab.kever = mock()
    kever = mock(eventing.Kever)
    kever.wits = ['BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha']
    hab.kevers = {'test_aid': kever}
    # hab.kever.wits = ['BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha']

    hby.db = mock()
    hby.db.ends = mock()
    hby.name = 'test_hab'
    hby.base = 'test_base'
    hby.habs = {'test_aid': hab}
    hby.kvy = mock()
    hby.kevers = {'test_aid': mock()}

    hab.db = mock(basing.Baser)
    hab.db.ends = mock(koming.Komer)

    rgy = mock(credentialing.Regery)
    rgy.reger = mock(credentialing.Reger)
    rgy.reger.issus = mock(subing.CesrDupSuber)
    rgy.reger.schms = mock(subing.CesrDupSuber)
    when(rgy.reger.issus).get(keys='test_aid').thenReturn([])
    when(rgy.reger.schms).get(keys=didding.DES_ALIASES_SCHEMA.encode()).thenReturn([])

    req.path = '/test_aid/keri.cesr'

    mock_serder_raw = bytearray(
        b'{'
        b'"v":"KERI10JSON0001b7_","t":"icp",'
        b'"d":"EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",'
        b'"i":"EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",'
        b'"s":"0",'
        b'"kt":"1","k":["DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K"],'
        b'"nt":"1","n":["EHlpcaxffvtcpoUUMTc6tpqAVtb2qnOYVk_3HRsZ34PH"],'
        b'"bt":"2","b":["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM","BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"],'
        b'"c":[],"a":[]}'
        b'-VBq-AABAABpDqK4TQytiWO_S-2VvfigdPs6T2pEWPfbgqy7DzYhakD9EmW-wGGa7i5VoF7Re8pkCCLIAO35_BtZOfNV4WIA-BADAADBrKDUOPHm9IFvg_EeEmMMzAvXB4xu6MdnzTohJkeK3Ome__5IWtnWZmXRYyIYau5BPqVXM9RptPc2DCmDg2wKABDrSZ3pVsK7DNlSS_fcT3QO3adZyhcIxcWiJUc5dYsHlEu-A3AVu8nkqXLeYXqE9Z_JKTJen-GfHU3tVp16GPIEACDUzCmXCwY-E6bCbz7umsvnvBS2MS83-03CbCuZ3DZN1GQLlH-A3bUKlhabdqjYW56JtifgcljgGvN7mJk8oa8P-EAB0AAAAAAAAAAAAAAAAAAAAAAA1AAG2025-03-18T17c57c24d927822p00c00'
    )

    # when(hby.db).clonePreIter(pre='test_aid').thenReturn(mock_serder_raw)
    when(hab).replay(pre='test_aid').thenReturn(mock_serder_raw)

    when(hab).loadLocScheme(eid='BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha', scheme='').thenReturn(
        bytearray(
            b'{'
            b'"v":"KERI10JSON0000fa_","t":"rpy",'
            b'"d":"ELSHJwBjsy41VvikaWd5cSC5hoooONVeVsImCzjzBQWP",'
            b'"dt":"2022-01-20T12:57:59.823350+00:00",'
            b'"r":"/loc/scheme",'
            b'"a":{"eid":"BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"http","url":"http://127.0.0.1:5642/"}}'
            b'-VAi-CABBBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha0BDRY23xEjEXaAJs7jPJt6uyxK8N2apNJitvn9mo0q4Gh8p7Pf2bAEp1Ufed5l0FdlLxV-Z2sMO8D7wVtA-m_QEM'
            b'{'
            b'"v":"KERI10JSON0000f8_","t":"rpy",'
            b'"d":"EBwDJvb5oW2SgwNfDK8Ib-NiljgBt4uK1bDjW3QztBPr",'
            b'"dt":"2022-01-20T12:57:59.823350+00:00",'
            b'"r":"/loc/scheme",'
            b'"a":{"eid":"BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"tcp","url":"tcp://127.0.0.1:5632/"}}'
            b'-VAi-CABBBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha0BCsK_YJIDH8djf5ncLs0VPJ1In104Hiu1392AlIMVFhmIxDP6gxgzMtklcOIyhQwRe7Mvgjniynjdv95iTCPWEL'
        )
    )
    when(hab).loadEndRole(
        cid='BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
        eid='BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
        role=kering.Roles.controller,
    ).thenReturn(
        bytearray(
            b'{'
            b'"v":"KERI10JSON000113_","t":"rpy",'
            b'"d":"EC-u2taS5Z0YZT18XvV8cPnFDJVNjm6B7j_vZbeMBKHF",'
            b'"dt":"2025-03-21T14:33:26.196052+00:00",'
            b'"r":"/end/role/add",'
            b'"a":{"cid":"EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4","role":"witness","eid":"BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"}}'
            b'-VA0-FABEKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk40AAAAAAAAAAAAAAAAAAAAAAAEKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4-AABAAAsb68BJ6XGB77xP37tPiDjZOd6oB4nxshznxz6GMy1dTmvpi5yltfvTpBNLZQYlhpRzUI3K0GD_4DNTiUldHAL'
        )
    )
    when(hab.db.ends).getItemIter(keys=('test_aid', kering.Roles.agent)).thenReturn([])

    when(hab.db.ends).getItemIter(keys=('test_aid', kering.Roles.mailbox)).thenReturn(
        [((None, 'mailbox', 'BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'), None)]
    )
    when(hab).loadLocScheme(eid='BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha').thenReturn(
        bytearray(
            b'{"r":"/loc/scheme","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"tcp","url":"tcp://127.0.0.1:5632/"}}'
        )
    )
    when(hab).loadEndRole(
        cid='test_aid', eid='BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha', role=kering.Roles.mailbox
    ).thenReturn(
        bytearray(
            b'{"r":"/end/role/add","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","role":"mailbox","cid":"test_aid"}}'
        )
    )

    resource = KeriCesrResourceEnd(hby, rgy)
    resource.on_get(req, rep, 'test_aid')

    assert rep.status == falcon.HTTP_200
    assert rep.content_type == 'application/cesr'
    assert (
        rep.data == b'{'
        b'"v":"KERI10JSON0001b7_","t":"icp",'
        b'"d":"EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",'
        b'"i":"EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",'
        b'"s":"0",'
        b'"kt":"1","k":["DHGb2qY9WwZ1sBnC9Ip0F-M8QjTM27ftI-3jTGF9mc6K"],'
        b'"nt":"1","n":["EHlpcaxffvtcpoUUMTc6tpqAVtb2qnOYVk_3HRsZ34PH"],'
        b'"bt":"2","b":["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM","BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"],'
        b'"c":[],"a":[]}'
        b'-VBq-AABAABpDqK4TQytiWO_S-2VvfigdPs6T2pEWPfbgqy7DzYhakD9EmW-wGGa7i5VoF7Re8pkCCLIAO35_BtZOfNV4WIA-BADAADBrKDUOPHm9IFvg_EeEmMMzAvXB4xu6MdnzTohJkeK3Ome__5IWtnWZmXRYyIYau5BPqVXM9RptPc2DCmDg2wKABDrSZ3pVsK7DNlSS_fcT3QO3adZyhcIxcWiJUc5dYsHlEu-A3AVu8nkqXLeYXqE9Z_JKTJen-GfHU3tVp16GPIEACDUzCmXCwY-E6bCbz7umsvnvBS2MS83-03CbCuZ3DZN1GQLlH-A3bUKlhabdqjYW56JtifgcljgGvN7mJk8oa8P-EAB0AAAAAAAAAAAAAAAAAAAAAAA1AAG2025-03-18T17c57c24d927822p00c00'
        b'{"v":"KERI10JSON0000fa_","t":"rpy",'
        b'"d":"ELSHJwBjsy41VvikaWd5cSC5hoooONVeVsImCzjzBQWP",'
        b'"dt":"2022-01-20T12:57:59.823350+00:00",'
        b'"r":"/loc/scheme",'
        b'"a":{"eid":"BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"http","url":"http://127.0.0.1:5642/"}}'
        b'-VAi-CABBBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha0BDRY23xEjEXaAJs7jPJt6uyxK8N2apNJitvn9mo0q4Gh8p7Pf2bAEp1Ufed5l0FdlLxV-Z2sMO8D7wVtA-m_QEM'
        b'{"v":"KERI10JSON0000f8_","t":"rpy",'
        b'"d":"EBwDJvb5oW2SgwNfDK8Ib-NiljgBt4uK1bDjW3QztBPr",'
        b'"dt":"2022-01-20T12:57:59.823350+00:00",'
        b'"r":"/loc/scheme",'
        b'"a":{"eid":"BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"tcp","url":"tcp://127.0.0.1:5632/"}}'
        b'-VAi-CABBBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha0BCsK_YJIDH8djf5ncLs0VPJ1In104Hiu1392AlIMVFhmIxDP6gxgzMtklcOIyhQwRe7Mvgjniynjdv95iTCPWEL'
        b'{"v":"KERI10JSON000113_","t":"rpy",'
        b'"d":"EC-u2taS5Z0YZT18XvV8cPnFDJVNjm6B7j_vZbeMBKHF",'
        b'"dt":"2025-03-21T14:33:26.196052+00:00",'
        b'"r":"/end/role/add",'
        b'"a":{"cid":"EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4","role":"witness","eid":"BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"}}'
        b'-VA0-FABEKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk40AAAAAAAAAAAAAAAAAAAAAAAEKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4-AABAAAsb68BJ6XGB77xP37tPiDjZOd6oB4nxshznxz6GMy1dTmvpi5yltfvTpBNLZQYlhpRzUI3K0GD_4DNTiUldHAL'
        b'{"r":"/loc/scheme","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"tcp","url":"tcp://127.0.0.1:5632/"}}'
        b'{"r":"/end/role/add","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","role":"mailbox","cid":"test_aid"}}'
    )


def test_gen_loc_schemes_cesr_with_mailbox_role_skips_agent():
    hab = mock()
    hab.kever = mock()
    kever = mock(eventing.Kever)
    hab.kevers = {'test_aid': kever}
    # hab.kever.wits = ['BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha']

    hab.db = mock(basing.Baser)
    hab.db.ends = mock(koming.Komer)

    when(hab.db.ends).getItemIter(keys=('test_aid', kering.Roles.mailbox)).thenReturn(
        [((None, 'mailbox', 'BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'), None)]
    )

    when(hab).loadLocScheme(eid='BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha').thenReturn(
        bytearray(
            b'{"r":"/loc/scheme","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"tcp","url":"tcp://127.0.0.1:5632/"}}'
        )
    )

    when(hab).loadEndRole(
        cid='test_aid', eid='BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha', role=kering.Roles.mailbox
    ).thenReturn(
        bytearray(
            b'{"r":"/end/role/add","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","role":"mailbox","cid":"test_aid"}}'
        )
    )
    loc_scheme_cesr = gen_loc_schemes_cesr(hab, 'test_aid', role=kering.Roles.mailbox)
    assert (
        loc_scheme_cesr
        == b'{"r":"/loc/scheme","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","scheme":"tcp","url":"tcp://127.0.0.1:5632/"}}'
        b'{"r":"/end/role/add","a":{"eid":"BDilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha","role":"mailbox","cid":"test_aid"}}'
    )


def test_keri_cesr_resource_end_on_get_bad_path():
    req = mock(falcon.Request)
    rep = mock(falcon.Response)
    hby = mock(habbing.Habery)
    hby.name = 'test_hab'
    hby.base = 'test_base'
    hby.kvy = mock()
    hby.db = mock()
    hby.kevers = {'test_aid': mock()}

    rgy = mock(credentialing.Regery)

    req.path = '/test_aid/bad.path'

    resource = KeriCesrResourceEnd(hby, rgy)

    with pytest.raises(falcon.HTTPBadRequest) as e:
        resource.on_get(req, rep, 'test_aid')

    assert isinstance(e.value, falcon.HTTPBadRequest)


def test_keri_cesr_resource_end_on_get_bad_aid():
    req = mock(falcon.Request)
    rep = mock(falcon.Response)
    hby = mock(habbing.Habery)
    hby.name = 'test_hab'
    hby.base = 'test_base'
    hby.kvy = mock()
    hby.db = mock()
    hby.kevers = {'test_aid': mock()}

    rgy = mock(credentialing.Regery)

    req.path = '/bad_aid/keri.cesr'

    resource = KeriCesrResourceEnd(hby, rgy)

    with pytest.raises(falcon.HTTPNotFound) as e:
        resource.on_get(req, rep, 'bad_aid')

    assert isinstance(e.value, falcon.HTTPNotFound)
