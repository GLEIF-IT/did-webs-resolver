import json
import os
import tempfile
import threading
import urllib.parse
from collections import deque
from unittest.mock import MagicMock, Mock, patch

import falcon
import pytest
from falcon import testing
from hio.base import doing
from keri import core, kering
from keri.app import agenting, configing, delegating, forwarding, grouping, habbing, indirecting, notifying, oobiing
from keri.core import coring, eventing, scheming, serdering
from keri.db import basing
from keri.db.basing import dbdict
from keri.peer import exchanging
from keri.vdr import credentialing, verifying
from mockito import mock, when

from dws import ArtifactResolveError, log_name, ogler, set_log_level
from dws.core import artifacting, didding, generating, requesting, resolving
from dws.core.didkeri import KeriResolver
from dws.core.ends import monitoring
from tests import conftest, keri_api
from tests.conftest import CredentialHelpers, HabbingHelpers, WitnessContext, self_attested_aliases_cred_subj
from tests.keri_api import HabHelpers


def test_health_end():
    """Simple test to demonstrate Falcon HTTP endpoint testing."""
    app = resolving.falcon_app()
    app.add_route('/health', monitoring.HealthEnd())

    client = testing.TestClient(app=app)

    rep = client.simulate_get('/health')
    assert rep.status == falcon.HTTP_200
    assert rep.content_type == falcon.MEDIA_JSON
    assert 'Health is okay' in rep.text


def test_resolver_with_witnesses():
    """
    This test spins up an actual witness and performs proper, receipted inception and credential
    issuance for an end-to-end integration test of the universal resolver endpoints.

    It also includes the delegator for the AID controller to ensure the service section of the did document shows the delegator OOBI
    """
    # setting log level to DEBUG so that it triggers the debug logging branch in the RequestLoggerMiddleware
    logger = ogler.getLogger(log_name)
    set_log_level('DEBUG', logger)

    delegator_salt = b'0ABaQTNARS1U1u7VhP0mnEKz'
    delegate_salt = b'0AAB_Fidf5WeZf6VFc53IxVw'
    resolver_salt = b'0AAl3nvsqKGyKHp2Hz9wLy9t'
    registry_nonce = '0ADV24br-aaezyRTB-oUsZJE'
    wit_salt = core.Salter(raw=b'abcdef0123456789').qb64

    # Witness config
    wit_cf = configing.Configer(name='wan', temp=False, reopen=True, clear=False)
    wit_cf.put(
        json.loads("""{
      "dt": "2022-01-20T12:57:59.823350+00:00",
      "wan": {
        "dt": "2022-01-20T12:57:59.823350+00:00",
        "curls": ["tcp://127.0.0.1:6632/", "http://127.0.0.1:6642/"]}}""")
    )
    wan_oobi = 'http://127.0.0.1:6642/oobi/BPwwr5VkI1b7ZA2mVbzhLL47UPjsGBX4WeO6WRv6c7H-/controller?name=Wan&tag=witness'

    aid_conf = f"""{{
        "dt": "2022-01-20T12:57:59.823350+00:00",
        "iurls": [\"{wan_oobi}\"]}}"""
    # Config of the Delegator
    delegator_cf = configing.Configer(name='delegator', temp=False, reopen=True, clear=False)
    delegator_cf.put(json.loads(aid_conf))

    # Config of the AID controller keystore who is having their did:webs or did:keri artifacts resolved
    delegate_cf = configing.Configer(name='delegate', temp=False, reopen=True, clear=False)
    delegate_cf.put(json.loads(aid_conf))

    # Open the witness Habery and Hab, feed it into the witness setup, and then create the delegate and AID controller Haberies and Habs
    with (
        HabbingHelpers.openHab(salt=bytes(wit_salt, 'utf-8'), name='wan', transferable=False, temp=True, cf=wit_cf) as (
            wit_hby,
            wit_hab,
        ),
        WitnessContext.with_witness(name='wan', hby=wit_hby) as wan_wit,
        habbing.openHby(salt=delegate_salt, name='delegator', temp=True, cf=delegator_cf) as del_hby,
        habbing.openHby(salt=delegate_salt, name='delegate', temp=True, cf=delegate_cf) as dgt_hby,
        habbing.openHab(salt=resolver_salt, name='resolver', transferable=True, temp=True, cf=None) as (
            resolver_hby,
            resolver_hab,
        ),
    ):
        wan_pre = 'BPwwr5VkI1b7ZA2mVbzhLL47UPjsGBX4WeO6WRv6c7H-'
        tock = 0.03125
        doist = doing.Doist(limit=0.0, tock=tock, real=True)
        # Doers and deeds for witness wan
        wit_deeds: deque = doist.enter(doers=wan_wit.doers)

        # Introduce the witness to each of the delegator and delegate Haberies

        # Have the Delegator Hab Resolve Wan's witness OOBI
        del_oobiery = oobiing.Oobiery(hby=del_hby)
        del_authn = oobiing.Authenticator(hby=del_hby)
        del_oobiery_deeds = doist.enter(doers=del_oobiery.doers + del_authn.doers)
        while not del_oobiery.hby.db.roobi.get(keys=(wan_oobi,)):
            doist.recur(deeds=wit_deeds + del_oobiery_deeds)
            del_hby.kvy.processEscrows()  # process any escrows from witness receipts

        # Have Delegate Hab Resolve Wan's witness OOBI
        oobiery = oobiing.Oobiery(hby=dgt_hby)
        authn = oobiing.Authenticator(hby=dgt_hby)
        oobiery_deeds = doist.enter(doers=oobiery.doers + authn.doers)
        while not oobiery.hby.db.roobi.get(keys=(wan_oobi,)):
            doist.recur(deeds=wit_deeds + oobiery_deeds)
            dgt_hby.kvy.processEscrows()  # process any escrows from witness receipts

        # Set up the Doers (deeds) for the delegator and delegate

        # Doers and deeds for the delegator's Hab and Habery
        del_hby_doer = habbing.HaberyDoer(habery=del_hby)
        del_anchorer = delegating.Anchorer(hby=del_hby, proxy=None)
        del_postman = forwarding.Poster(hby=del_hby)
        del_exc = exchanging.Exchanger(hby=del_hby, handlers=[])
        del_notifier = notifying.Notifier(hby=del_hby)
        delegating.loadHandlers(hby=del_hby, exc=del_exc, notifier=del_notifier)
        del_mbx = indirecting.MailboxDirector(hby=del_hby, topics=['/receipt', '/replay', '/reply', '/delegate'], exc=del_exc)
        del_wit_rcptr_doer = agenting.WitnessReceiptor(hby=del_hby)
        del_receiptor = agenting.Receiptor(hby=del_hby)
        del_doers = [del_hby_doer, del_anchorer, del_postman, del_mbx, del_wit_rcptr_doer, del_receiptor]
        del_deeds: deque = doist.enter(doers=del_doers)

        # Doers and deeds for the dgt_aid Hab and Habery
        dgt_hby_doer = habbing.HaberyDoer(habery=dgt_hby)
        dgt_anchorer = delegating.Anchorer(hby=dgt_hby, proxy=None)
        dgt_postman = forwarding.Poster(hby=dgt_hby)
        dgt_exc = exchanging.Exchanger(hby=dgt_hby, handlers=[])
        dgt_notifier = notifying.Notifier(hby=dgt_hby)
        delegating.loadHandlers(hby=dgt_hby, exc=dgt_exc, notifier=dgt_notifier)
        dgt_mbx = indirecting.MailboxDirector(hby=dgt_hby, topics=['/receipt', '/replay', '/reply', '/delegate'], exc=dgt_exc)
        dgt_wit_rcptr_doer = agenting.WitnessReceiptor(hby=dgt_hby)
        dgt_receiptor = agenting.Receiptor(hby=dgt_hby)
        dgt_doers = [dgt_hby_doer, dgt_anchorer, dgt_postman, dgt_mbx, dgt_wit_rcptr_doer, dgt_receiptor]
        dgt_deeds: deque = doist.enter(doers=dgt_doers)

        # Incept delegator Hab
        del_hab = del_hby.makeHab(name='delegator', isith='1', icount=1, toad=1, wits=[wan_pre])
        del_wit_rcptr_doer.msgs.append(dict(pre=del_hab.pre))
        while not del_wit_rcptr_doer.cues:
            doist.recur(deeds=wit_deeds + del_deeds)

        # Incept delegate proxy Hab
        pxy_hab = dgt_hby.makeHab(name='proxy', isith='1', icount=1, toad=1, wits=[wan_pre])
        dgt_wit_rcptr_doer.msgs.append(dict(pre=pxy_hab.pre))
        while not dgt_wit_rcptr_doer.cues:
            doist.recur(deeds=wit_deeds + dgt_deeds)

        # Get Delegator OOBI and resolve with Delegate
        del_oobi = HabHelpers.generate_oobi(hby=del_hby, alias='delegator', role=kering.Roles.witness)
        HabHelpers.resolve_wit_oobi(doist, wit_deeds, dgt_hby, del_oobi, alias='delegator')

        proxy_oobi = HabHelpers.generate_oobi(hby=dgt_hby, alias='proxy', role=kering.Roles.witness)
        HabHelpers.resolve_wit_oobi(doist, wit_deeds, del_hby, proxy_oobi, alias='proxy')

        # begin delegated inception- single sig
        dgt_hab = dgt_hby.makeHab(name='delegate', delpre=del_hab.pre, isith='1', icount=1, toad=1, wits=[wan_pre])
        dipper = keri_api.Dipper(
            hby=dgt_hby, hab=dgt_hab, proxy='proxy'
        )  # proxy is named "delegate" since that is what the openHab helper received
        dip_sealer = keri_api.DipSealer(hby=del_hby, hab=del_hab, witRcptrDoer=del_wit_rcptr_doer)
        delegation_deeds: deque = doist.enter(doers=[dipper, dip_sealer])
        while not dipper.done:
            doist.recur(deeds=wit_deeds + del_deeds + dgt_deeds + delegation_deeds)

        # Waiting for witness receipts...
        dgt_wit_rcptr_doer.msgs.append(dict(pre=dgt_hab.pre))
        while not dgt_wit_rcptr_doer.cues:
            doist.recur(deeds=wit_deeds + dgt_deeds)

        # Wait for delegation request to show up for delegator
        while not HabHelpers.has_delegables(del_hby.db):
            doist.recur(deeds=wit_deeds + del_deeds + dgt_deeds)
            # del_hby.kvy.processEscrows()  # process any escrows from witness receipts
            # dgt_hby.kvy.processEscrows()  # process any escrows from witness receipts
        print('found delegable events')
        print(HabHelpers.has_delegables(del_hby.db))

        # now perform did:webs and did:keri resolution with an OOBI to test it.
        aid = 'EHUi8qUknNeLBYtZ_tUwuLjlaRm-srp2PqVBO5YEJ4PA'  # dgt_hab.pre
        host = '127.0.0.1'
        port = f'7677'
        did_path = 'dws'
        meta = True
        # fmt: off
        did_webs_did = f'did:webs:{host}%3A{port}:{did_path}:{aid}?meta=true'  # did:webs:127.0.0.1%3A7677:dws:'EHUi8qUknNeLBYtZ_tUwuLjlaRm-srp2PqVBO5YEJ4PA'?meta=true
        did_keri_did = f'did:keri:{aid}'                                       # did:keri:'EHUi8qUknNeLBYtZ_tUwuLjlaRm-srp2PqVBO5YEJ4PA'
        did_json_url = f'http://{host}:{port}/{did_path}/{aid}/did.json'       # http://127.0.0.1:7677/dws/'EHUi8qUknNeLBYtZ_tUwuLjlaRm-srp2PqVBO5YEJ4PA'/did.json?meta=true
        keri_cesr_url = f'http://{host}:{port}/{did_path}/{aid}/keri.cesr'     # http://127.0.0.1:7677/dws/'EHUi8qUknNeLBYtZ_tUwuLjlaRm-srp2PqVBO5YEJ4PA'/keri.cesr
        # fmt: on

        schema_json = conftest.Schema.designated_aliases_schema()
        rules_json = conftest.Schema.designated_aliases_rules()
        subject_data = self_attested_aliases_cred_subj(host, aid, port, did_path)
        regery = credentialing.Regery(hby=dgt_hby, name=dgt_hby.name, temp=dgt_hby.temp)
        CredentialHelpers.add_cred_to_aid(
            hby=dgt_hby,
            hby_doer=dgt_hby_doer,
            hab=dgt_hab,
            regery=regery,
            schema_said='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5',  # Designated Aliases Public Schema
            schema_json=schema_json,
            subject_data=subject_data,
            rules_json=rules_json,
            recp=None,  # No recipient for self-attested credential
            registry_nonce=registry_nonce,
            additional_deeds=wit_deeds + dgt_deeds,
        )

        # get keri.cesr
        reger = regery.reger
        keri_cesr = bytearray()
        keri_cesr.extend(artifacting.gen_kel_cesr(dgt_hab, aid))  # add KEL CESR stream
        keri_cesr.extend(artifacting.gen_loc_schemes_cesr(dgt_hab, aid))
        keri_cesr.extend(artifacting.gen_des_aliases_cesr(dgt_hab, reger, aid))

        did_webs_diddoc = didding.generate_did_doc(dgt_hby, rgy=regery, did=did_webs_did, aid=aid, meta=meta)
        assert did_webs_diddoc[didding.DD_FIELD]['alsoKnownAs'] != [], 'alsoKnownAs field should contain designated aliases'

        # generate DID artifacts and store them locally so I can resolve them.
        output_dir = f'./tests/artifact_output_dir/{did_path}'
        did_art_gen = generating.DIDArtifactGenerator(
            name=dgt_hby.name,
            base=dgt_hby.base,
            bran=None,
            hby=dgt_hby,
            hby_doer=dgt_hby_doer,
            regery=regery,
            did=did_webs_did,
            meta=meta,
            output_dir=output_dir,
            verbose=True,
            cf=delegate_cf,
        )
        doist.do([did_art_gen])

        # Start up a universal resolver to test that resolution works
        resolver_regery = credentialing.Regery(hby=resolver_hby, name=resolver_hby.name, temp=resolver_hby.temp)
        resolver_oobiery = oobiing.Oobiery(hby=resolver_hby)
        resolver_doers = resolving.setup_resolver(
            resolver_hby,
            resolver_regery,
            resolver_oobiery,
            http_port=7677,
            static_files_dir='./tests/artifact_output_dir/',
            did_path='',  # don't need to specify 'dws' as did_path here because the directory structure already has a 'dws' subdir being served from '/'
            keypath=None,
            certpath=None,
            cafilepath=None,
        )
        resolver_deeds = doist.enter(doers=resolver_doers)
        client, client_doer = requesting.create_http_client(method='GET', url=f'{did_json_url}')
        resolution_deed = doist.enter(doers=[client_doer])
        while client.responses is None or len(client.responses) == 0:
            doist.recur(deeds=dgt_deeds + resolver_deeds + resolution_deed)
        resp = client.respond()
        resp_body = bytes(resp.body)
        did_webs_diddoc[didding.DD_FIELD] = didding.to_did_web(did_webs_diddoc[didding.DD_FIELD])
        assert did_webs_diddoc[didding.DD_FIELD] == json.loads(resp_body.decode('utf-8'))[didding.DD_FIELD], (
            'DID Document does not match expected output'
        )

        # Resolve did:keri with OOBI fails to resolve (OOBI parameter not currently supported)
        controller_oobi = f'http://127.0.0.1:6642/oobi/{aid}/witness/{wan_pre}'
        did_keri_did = f'{did_keri_did}?meta=true&oobi={urllib.parse.quote(controller_oobi)}'
        did_keri_url = f'http://{host}:{7677}/1.0/identifiers/{did_keri_did}'

        # Separate witness thread so it can respond to the OOBI request without blocking this main
        # test thread
        def run_witness_other_thread(event: threading.Event):
            wit_doist = doing.Doist(limit=0.0, tock=tock, real=True)
            while not event.is_set():
                wit_doist.recur(deeds=wit_deeds)

        stop_event = threading.Event()
        wit_thread = threading.Thread(target=run_witness_other_thread, args=(stop_event,))
        wit_thread.start()

        client, client_doer = requesting.create_http_client(method='GET', url=did_keri_url)
        resolution_deed = doist.enter(doers=[client_doer])
        while client.responses is None or len(client.responses) == 0:
            doist.recur(deeds=dgt_deeds + resolver_deeds + resolution_deed)
        stop_event.set()  # end witness thread since response is received
        wit_thread.join()  # clean up the witness thread

        rep = client.respond()
        resp_body = json.loads(rep.body)
        # Expected did doc
        resolver_regery = credentialing.Regery(hby=resolver_hby, name=resolver_hby.name, temp=resolver_hby.temp)
        exp_did_keri_diddoc = didding.generate_did_doc(resolver_hby, rgy=resolver_regery, did=did_keri_did, aid=aid, meta=meta)
        assert rep.status == 200
        assert resp_body[didding.DD_FIELD] == exp_did_keri_diddoc[didding.DD_FIELD], (
            f'actual and expected did doc did not match for did:keri DID: {did_keri_did}'
        )

        # resolve did:dud fails as invalid did
        did_dud = 'did:dud:invalid'
        did_dud_url = f'http://{host}:{7677}/1.0/identifiers/{did_dud}'
        client, client_doer = requesting.create_http_client(method='GET', url=did_dud_url)
        resolution_deed = doist.enter(doers=[client_doer])
        while client.responses is None or len(client.responses) == 0:
            doist.recur(deeds=dgt_deeds + resolver_deeds + resolution_deed)
        rep = client.respond()
        assert rep.status == 400
        resp_body = json.loads(rep.body)
        assert resp_body['error'] == f'invalid DID: {urllib.parse.quote(did_dud)}'

        # Test resolving did:keri did from Habery that doesn't know about it triggers OOBI resolution
        with habbing.openHab(salt=resolver_salt, name='other', transferable=True, temp=True, cf=None) as (
            other_hby,
            other_hab,
        ):
            # Start witness thread in background to respond to OOBI requests
            stop_event = threading.Event()
            wit_thread = threading.Thread(target=run_witness_other_thread, args=(stop_event,))
            wit_thread.start()

            # get did:keri resolver ready and run it
            other_regery = credentialing.Regery(hby=other_hby, name=other_hby.name, temp=other_hby.temp)
            KeriResolver.TimeoutOOBIResolve = 10.0  # set timeout back to 10 seconds for this test
            keri_resolver = KeriResolver(did=did_keri_did, meta=False, verbose=False, hby=other_hby, rgy=other_regery)
            other_doist = doing.Doist(limit=5.0, tock=0.03125, real=True)
            other_doist.do([keri_resolver])

            stop_event.set()
            wit_thread.join()
            exp_did_doc = didding.generate_did_doc(hby=other_hby, rgy=other_regery, did=did_keri_did, aid=aid, meta=False)
            assert keri_resolver.result is not None, 'KeriResolver did not return a result'
            assert keri_resolver.result == exp_did_doc, 'KeriResolver result did not match expected DID Document'

        # Test resolving did:keri did from Habery that doesn't know about with bad OOBI triggers timeout
        with habbing.openHab(salt=resolver_salt, name='another', transferable=True, temp=True, cf=None) as (
            another_hby,
            another_hab,
        ):
            did_keri_did = f'did:keri:{aid}'
            bad_controller_oobi = f'http://127.0.0.1:6646/oobi/{aid}/witness/{wan_pre}'
            bad_did_keri_did = f'{did_keri_did}?meta=true&oobi={urllib.parse.quote(bad_controller_oobi)}'
            # Start witness thread in background to respond to OOBI requests
            stop_event = threading.Event()
            wit_thread = threading.Thread(target=run_witness_other_thread, args=(stop_event,))
            wit_thread.start()

            # get did:keri resolver ready and run it
            another_regery = credentialing.Regery(hby=another_hby, name=another_hby.name, temp=another_hby.temp)
            KeriResolver.TimeoutOOBIResolve = 0.1  # set timeout to 1 second for this test
            keri_resolver = KeriResolver(did=bad_did_keri_did, meta=False, verbose=False, hby=another_hby, rgy=another_regery)
            other_doist = doing.Doist(limit=10.0, tock=0.03125, real=True)
            with pytest.raises(kering.KeriError) as exc_info:
                other_doist.do([keri_resolver])
            assert 'resolution timed out' in str(exc_info.value), 'KeriResolver did not raise timeout error as expected'

            stop_event.set()
            try:
                wit_thread.join()
            except Exception as e:
                pass  # ignore any witness thread join exceptions
            assert 'error' in keri_resolver.result, 'KeriResolver did not return an error result'
            assert 'resolution timed out' in keri_resolver.result['error'], (
                'KeriResolver result did not contain expected timeout error'
            )
    # reset log level for other tests
    set_log_level('INFO', logger)


def test_artifact_server_hosts_artifacts():
    # test using the dynamic artifact server allows retrieval of did.json and keri.cesr
    aid_salt = b'0ACuuzf-aYxlda5fB6HzsEfP'
    resolver_salt = b'0ADzZCSm8LTeyIiYWW1pg1gr'

    wit_name = 'wes'
    wit_aid = 'BJ2nSXbH8aH8jSdkjpq-ZU-hPTa4DJWx5OoJTZUe4WJP'  # determine by running once and hardcoding it here
    wit_tcp = 6635
    wit_http = 6645
    wit_salt = core.Salter(raw=b'abcdef012345678X').qb64
    wit_cf = configing.Configer(name='wes', temp=False, reopen=True, clear=False)
    wit_cf.put(
        json.loads(f"""{{
          "dt": "2022-01-20T12:57:59.823350+00:00",
          "{wit_name}": {{
            "dt": "2022-01-20T12:57:59.823350+00:00",
            "curls": ["tcp://127.0.0.1:{wit_tcp}/", "http://127.0.0.1:{wit_http}/"]}}}}""")
    )
    wit_oobi = f'http://127.0.0.1:{wit_http}/oobi/{wit_aid}/controller?name={wit_name}&tag=witness'

    # Config of the AID controller keystore who is having their did:webs or did:keri artifacts resolved
    ctlr_name = 'ada'
    ctlr_cf = configing.Configer(name=ctlr_name, temp=False, reopen=True, clear=False)
    ctlr_cf.put(
        json.loads(f"""{{
                  "dt": "2022-01-20T12:57:59.823350+00:00",
                  "iurls": [
                    "http://127.0.0.1:{wit_http}/oobi/{wit_aid}/controller?name={wit_name}&tag=witness"
                  ]}}""")
    )
    ctlr_aid_name = 'ada_aid1'

    # Open the witness Habery and Hab, feed it into the witness setup, and then create the AID controller Habery and Hab
    with (
        HabbingHelpers.openHab(salt=bytes(wit_salt, 'utf-8'), name=wit_name, transferable=False, temp=True, cf=wit_cf) as (
            wit_hby,
            wit_hab,
        ),
        WitnessContext.with_witness(name=wit_name, hby=wit_hby, http_port=wit_http, tcp_port=wit_tcp) as wit_ctx,
        habbing.openHab(salt=aid_salt, name=ctlr_name, transferable=True, temp=True, cf=ctlr_cf) as (ctlr_hby, ctlr_hab),
    ):
        tock = 0.03125
        doist = doing.Doist(limit=0.0, tock=tock, real=True)
        # Doers and deeds for witness wan
        wit_deeds = doist.enter(doers=wit_ctx.doers)

        # Have Cracker Hab Resolve Wan's witness OOBI
        ctlr_oobiery = oobiing.Oobiery(hby=ctlr_hby)
        authn = oobiing.Authenticator(hby=ctlr_hby)
        oobiery_deeds = doist.enter(doers=ctlr_oobiery.doers + authn.doers)
        while not ctlr_oobiery.hby.db.roobi.get(keys=(wit_oobi,)):
            doist.recur(deeds=wit_deeds + oobiery_deeds)
            ctlr_hby.kvy.processEscrows()  # process any escrows from witness receipts
        print(f'Resolved OOBI: {wit_oobi} to {ctlr_oobiery.hby.db.roobi.get(keys=(wit_oobi,))}')

        ctlr_hby_doer = habbing.HaberyDoer(habery=ctlr_hby)
        rgy = credentialing.Regery(hby=ctlr_hby, name=ctlr_hby.name, base=ctlr_hby.base, temp=ctlr_hby.temp)
        anchorer = delegating.Anchorer(hby=ctlr_hby, proxy=None)
        postman = forwarding.Poster(hby=ctlr_hby)
        mbx = indirecting.MailboxDirector(hby=ctlr_hby, topics=['/receipt', '/replay', '/reply'])
        wit_rcptr_doer = agenting.WitnessReceiptor(hby=ctlr_hby)
        receiptor = agenting.Receiptor(hby=ctlr_hby)
        ctlr_doers = [ctlr_hby_doer, anchorer, postman, mbx, wit_rcptr_doer, receiptor]
        ctlr_deeds = doist.enter(doers=ctlr_doers)

        ctlr_aid1_hab = ctlr_hby.makeHab(name=ctlr_aid_name, isith='1', icount=1, toad=1, wits=[wit_aid])

        # Waiting for witness receipts...
        wit_rcptr_doer.msgs.append(dict(pre=ctlr_aid1_hab.pre))
        while not wit_rcptr_doer.cues:
            doist.recur(deeds=wit_deeds + ctlr_deeds)

        # set up dynamic artifact server doers and load keri.cesr and did.json artifacts
        aid = 'EDKswKm3X0gxReQewbLjBbPzXPD67KsrLq0tI6kJU3sQ'  # ctlr_aid1_hab.pre
        artifact_svr_doers = artifacting.dyn_artifact_svr_doers(
            hby=ctlr_hby, rgy=rgy, alias=ctlr_aid_name, http_port=7678, meta=False
        )

        def run_artifact_server_other_thread(event: threading.Event):
            """
            Run the artifact server in a separate thread to allow it to serve artifacts while the test runs.
            """
            artifact_doist = doing.Doist(limit=0.0, tock=tock, real=True)
            deeds = artifact_doist.enter(doers=artifact_svr_doers + [ctlr_hby_doer])
            while not event.is_set():
                artifact_doist.recur(deeds=deeds)

        stop_event = threading.Event()
        art_svr_thread = threading.Thread(target=run_artifact_server_other_thread, args=(stop_event,))
        art_svr_thread.start()

        # perform did.json request
        did_json_url = f'http://127.0.0.1:{7678}/{aid}/did.json'
        client, client_doer = requesting.create_http_client(method='GET', url=did_json_url)
        did_json_deeds = doist.enter(doers=[client_doer])
        while client.responses is None or len(client.responses) == 0:
            doist.recur(deeds=did_json_deeds)

        rep = client.respond()
        assert rep.status == 200, f'Expected 200 for did.json artifact: {did_json_url}'
        resp_body = json.loads(rep.body)
        assert 'verificationMethod' in resp_body, 'Expected verificationMethod in did.json response'
        assert 'id' in resp_body, 'Expected id in did.json response'
        assert resp_body['id'] == f'did:web:127.0.0.1%3A7678:{aid}'

        # perform keri.cesr request, reusing the artifact server thread from above
        keri_cesr_url = f'http://127.0.0.1:{7678}/{aid}/keri.cesr'
        client, client_doer = requesting.create_http_client(method='GET', url=keri_cesr_url)
        keri_cesr_deeds = doist.enter(doers=[client_doer])
        while client.responses is None or len(client.responses) == 0:
            doist.recur(deeds=keri_cesr_deeds)

        rep = client.respond()
        assert rep.status == 200, f'Expected 200 for keri.cesr artifact: {keri_cesr_url}'
        resp_body = rep.body
        assert len(resp_body) > 0, 'Expected non-empty keri.cesr response'

        stop_event.set()  # end artifact server thread since response is received
        art_svr_thread.join()  # clean up the artifact server thread


def test_resolution_failure():
    # TODO rework and reenable this test
    # test a resolution failure
    # UniversalResolverResource.TimeoutArtifactResolution = 0.1  # set timeout to 1 second for this test
    # unknown_did_webs_did = f'did:webs:{host}%3A{7678}:{did_path}:EEdpe-yqftH2_FO1-luoHvaiShK4y_E2dInrRQ2_2X5X'  # Invalid AID
    # did_webs_url = f'http://{host}:{7677}/1.0/identifiers/{unknown_did_webs_did}'
    #
    # cracker_static_doers = resolving.setup_resolver(
    #     ck_hab,
    #     regery,
    #     oobiery,
    #     http_port=7678,
    #     static_files_dir='./tests/artifact_output_dir',
    #     did_path='dws',
    #     keypath=None,
    #     certpath=None,
    #     cafilepath=None,
    # )
    # cracker_static_deeds = doist.enter(doers=cracker_static_doers)
    #
    # def run_static_server_other_thread(event: threading.Event):
    #     wit_doist = doing.Doist(limit=0.0, tock=tock, real=True)
    #     while not event.is_set():
    #         wit_doist.recur(deeds=cracker_static_deeds)
    #
    # stop_event = threading.Event()
    # resolver_thread = threading.Thread(target=run_static_server_other_thread, args=(stop_event,))
    # resolver_thread.start()
    #
    # client, client_doer = requesting.create_http_client(method='GET', url=did_webs_url)
    # resolution_deed = doist.enter(doers=[client_doer])
    # while client.responses is None or len(client.responses) == 0:
    #     doist.recur(deeds=resolver_deeds + resolution_deed)
    # stop_event.set()  # end witness thread since response is received
    # resolver_thread.join()  # clean up the witness thread
    #
    # rep = client.respond()
    # assert rep.status == 417, f'Expected 417 for unknown did:webs DID: {unknown_did_webs_did}'
    # resp_body = json.loads(rep.body)
    # assert 'error' in resp_body, 'Expected error in response body for unknown did:webs DID'
    # assert 'Failed to load URL' in resp_body['error'], f'Expected error message for unknown did:webs DID: {unknown_did_webs_did}'
    # # UniversalResolverResource.TimeoutArtifactResolution = 5.0  # reset timeout
    pass


def test_compare_dicts_returns_differences_when_present():
    """
    Tests the compare_dicts function to ensure it correctly identifies differences between two dictionaries.
    """
    # different values are detected
    exp = {'key1': 'value1', 'key2': 'value2'}
    act = {'key1': 'value1', 'key2': 'different_value'}

    diff = resolving.diff_dicts(exp, act)
    assert diff == [('key2', 'value2', 'different_value')], 'Differences not identified correctly'

    # missing values are detected
    exp = {'key1': 'value1', 'key2': 'value2'}
    act = {'key1': 'value1'}

    diff = resolving.diff_dicts(exp, act)
    assert diff == [('key2', 'value2', None)], 'Differences not identified correctly when keys are missing'

    # nested structures are compared correctly
    exp = {'key1': 'value1', 'key2': {'key3': 'value2'}}
    act = {'key1': 'value1', 'key2': 'different_value'}

    diff = resolving.diff_dicts(exp, act)
    assert diff == [('key2', {'key3': 'value2'}, 'different_value')], (
        'Differences not identified correctly for nested structures'
    )

    # actual having a dictionary when not expected is detected
    exp = {'key1': 'value1', 'key2': 'value2'}
    act = {'key1': 'value1', 'key2': {'key3': 'different_value'}}

    diff = resolving.diff_dicts(exp, act)
    assert diff == [('key2', 'value2', {'key3': 'different_value'})], (
        'Differences not identified correctly for nested structures'
    )

    # extra attributes in actual detected
    exp = {'key1': 'value1', 'key2': 'value2'}
    act = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}

    diff = resolving.diff_dicts(exp, act)
    assert diff == [('key3', None, 'value3')], 'Differences not identified correctly for extra attributes in actual'

    # detects when actual is not a dict yet expected is
    exp = {}
    act = []

    diff = resolving.diff_dicts(exp, act)
    assert diff == [('', exp, None)], 'Differences not identified correctly when actual is not a dict but expected is'

    # detects when expected is a list of dicts and compares properly
    exp = [{'key1': 'value1', 'key2': 'value2'}, {'key3': 'value3', 'key4': 'value4'}]
    act = [{'key1': 'value1', 'key2': 'value2'}, {'key3': 'value3', 'key4': 'value4'}]
    diff = resolving.diff_dicts(exp, act)
    assert diff == [[], []], 'Differences should be empty when both lists of dicts are equal'

    # detects when non-list, non-dict expected does not equal actual
    exp = 0.123
    act = 'asdf'
    diff = resolving.diff_dicts(exp, act)
    assert diff == [('', exp, act)], 'Differences not identified correctly when expected is a non-list, non-dict type'

    # detects when comparing lists and the length of expected and actual differ
    exp = [1, 2, 3]
    act = [1, 2]
    diff = resolving.diff_dicts(exp, act)
    assert diff == [('', exp, act)], 'Differences not identified correctly when comparing lists of different lengths'


def test_get_serve_dir():
    with tempfile.TemporaryDirectory() as temp_static:
        dir = resolving.get_serve_dir(temp_static, 'dws')
        assert dir == temp_static + '/dws', 'Serve directory path is incorrect'

    cwd = os.getcwd()
    dir = resolving.get_serve_dir('static', 'dws')
    assert dir == os.path.join(cwd, 'static', 'dws'), 'Serve directory path is incorrect when using relative path'

    with tempfile.TemporaryDirectory() as temp_did_doc_dir:
        dir = resolving.get_serve_dir(None, temp_did_doc_dir)
        assert dir == temp_did_doc_dir, 'Serve directory path should match the provided directory when no static path is given'


def test_resolver_with_did_webs_did_returns_correct_doc():
    """
    Tests generation of both did:webs and did:keri DID Documents and a CESR stream for the did:webs DID.
    Uses static salt, registry nonce, and ACDC datetimestamp for deterministic results.
    """
    salt = b'0ACB-gtnUTQModt9u_UC3LFQ'
    registry_nonce = '0AC-D5XhLUkO-ODnrJMSRPqv'
    with habbing.openHab(salt=salt, name='water', transferable=True, temp=True) as (hby, hab):
        hby_doer = habbing.HaberyDoer(habery=hby)
        aid = 'EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU'
        host = '127.0.0.1'
        port = f'7677'
        did_path = 'dws'
        meta = False
        # fmt: off
        did_webs_did = f'did:webs:{host}%3A{port}:{did_path}:{aid}'         # did:webs:127.0.0.1%3A7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU
        did_keri_did = f'did:keri:{aid}'                                    # did:keri:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU
        did_json_url = f'https://{host}:{port}/{did_path}/{aid}/did.json'    # http://127.0.0.1:7677/dws/EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU/did.json
        keri_cesr_url = f'https://{host}:{port}/{did_path}/{aid}/keri.cesr'  # http://127.0.0.1:7677/dws/EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU/keri.cesr
        # fmt: on

        # Components needed for issuance
        regery = credentialing.Regery(hby=hby, name=hab.name, temp=hby.temp)
        counselor = grouping.Counselor(hby=hby)
        registrar = credentialing.Registrar(hby=hby, rgy=regery, counselor=counselor)
        verifier = verifying.Verifier(hby=hby, reger=regery.reger)
        credentialer = credentialing.Credentialer(hby=hby, rgy=regery, registrar=registrar, verifier=verifier)
        regery_doer = credentialing.RegeryDoer(rgy=regery)

        # set up Doist to run doers
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        deeds = doist.enter(doers=[hby_doer, counselor, registrar, credentialer, regery_doer])

        # Add schema to resolver schema cache
        raw_schema = conftest.Schema.designated_aliases_schema()
        schemer = scheming.Schemer(
            raw=bytes(json.dumps(raw_schema), 'utf-8'), typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256
        )
        cache = scheming.CacheResolver(db=hby.db)
        cache.add(schemer.said, schemer.raw)

        # Create registry for designated aliases credential

        issuer_reg = regery.makeRegistry(prefix=hab.pre, name=hab.name, noBackers=True, nonce=registry_nonce)
        rseal = eventing.SealEvent(issuer_reg.regk, '0', issuer_reg.regd)._asdict()
        reg_anc = hab.interact(data=[rseal])
        reg_anc_serder = serdering.SerderKERI(raw=bytes(reg_anc))
        registrar.incept(iserder=issuer_reg.vcp, anc=reg_anc_serder)

        while not registrar.complete(pre=issuer_reg.regk, sn=0):
            doist.recur(deeds=deeds)  # run until registry is incepted

        assert issuer_reg.regk in regery.reger.tevers

        # Create and issue the self-attested credential
        credSubject = self_attested_aliases_cred_subj(host, aid, port, did_path)
        rules_json = conftest.Schema.designated_aliases_rules()
        creder = credentialer.create(
            regname=issuer_reg.name,
            recp=None,
            schema='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5',  # Designated Aliases Public Schema
            source=None,
            rules=rules_json,
            data=credSubject,
            private=False,
            private_credential_nonce=None,
            private_subject_nonce=None,
        )

        # Create ACDC issuance and anchor to KEL
        reg_iss_serder = issuer_reg.issue(said=creder.said, dt=creder.attrib['dt'])
        iss_seal = eventing.SealEvent(reg_iss_serder.pre, '0', reg_iss_serder.said)._asdict()
        iss_anc = hab.interact(data=[iss_seal])
        anc_serder = serdering.SerderKERI(raw=iss_anc)
        credentialer.issue(creder, reg_iss_serder)
        registrar.issue(creder, reg_iss_serder, anc_serder)

        while not credentialer.complete(said=creder.said):
            doist.recur(deeds=deeds)
            verifier.processEscrows()

        state = issuer_reg.tever.vcState(vci=creder.said)
        assert state.et == coring.Ilks.iss

        # get the keri.cesr and did.json for later verification
        reger = regery.reger
        keri_cesr = bytearray()
        keri_cesr.extend(artifacting.gen_kel_cesr(hab, aid))  # add KEL CESR stream
        keri_cesr.extend(artifacting.gen_loc_schemes_cesr(hab, aid))
        keri_cesr.extend(artifacting.gen_des_aliases_cesr(hab, reger, aid))

        did_webs_diddoc = didding.generate_did_doc(hby, rgy=regery, did=did_webs_did, aid=aid, meta=meta)

        # Mock load_url to return the did.json and keri.cesr content
        def mock_load_url(url, timeout=None):
            if url == did_json_url:
                # whitespace added for readability - this is just bytes and the whitespace does not impact the actual content
                # fmt: off
                return (
                    b'{'
                    b'"id": "did:webs:127.0.0.1%3A7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                    b'"verificationMethod": [{'
                        b'"id": "#DHfhTX8nqUdiU2yw5gnx3dFguwAPiR0SzK4I9ugjRoRF", '
                        b'"type": "JsonWebKey", '
                        b'"controller": "did:webs:127.0.0.1%3A7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                        b'"publicKeyJwk": {'
                            b'"kid": "DHfhTX8nqUdiU2yw5gnx3dFguwAPiR0SzK4I9ugjRoRF", '
                            b'"kty": "OKP", '
                            b'"crv": "Ed25519", '
                            b'"x": "d-FNfyepR2JTbLDmCfHd0WC7AA-JHRLMrgj26CNGhEU"}}], '
                    b'"service": [], '
                    b'"alsoKnownAs": ['
                        b'"did:web:127.0.0.1%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                        b'"did:webs:127.0.0.17677%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                        b'"did:web:example.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                        b'"did:web:foo.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                        b'"did:webs:foo.comNone:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU"]}'
                )
                # fmt: on
            elif url == keri_cesr_url:
                # whitespace added for readability - this is just bytes and the whitespace does not impact the actual content
                # fmt: off
                return (
                    bytearray(
                        b'{'
                        b'"v":"KERI10JSON00012b_","t":"icp",'
                        b'"d":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                        b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                        b'"s":"0",'
                        b'"kt":"1","k":["DHfhTX8nqUdiU2yw5gnx3dFguwAPiR0SzK4I9ugjRoRF"],'
                        b'"nt":"1","n":["EDklD8WWC8ks7U-pdxI_hoftybqLVRTj3KJK70jkq6Ha"],'
                        b'"bt":"0","b":[],"c":[],"a":[]}'
                        b'-VAn-AABAAAVeuv7YV_mWaMsye6tH5-G1x58jyJyPJtNePHS3u6vn5UYMlWBFzShMSabVqAtRvW8YW18uEhEGOaZ-cGkcE0J-EAB0AAAAAAAAAAAAAAAAAAAAAAA1AAG2025-07-29T19c40c43d405620p00c00'
                        b'{'
                        b'"v":"KERI10JSON00013a_","t":"ixn",'
                        b'"d":"EHZquNk1-N_KYQJcdXy_jym_YnwlzvdC_6YmGKp6VvIN",'
                        b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                        b'"s":"1","p":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                        b'"a":[{"i":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb","s":"0","d":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb"}]}'
                        b'-VAn-AABAAAfWrHVECbYrHe5hBQnIdgbbwmNPUO4VFsV0HG9zSwmbA-Qc7PqkQCD3IAZ_CnP5RrV2R_MgeYZtFu7PPwdWw0J-EAB0AAAAAAAAAAAAAAAAAAAAAAB1AAG2025-07-29T19c40c43d430980p00c00'
                        b'{'
                        b'"v":"KERI10JSON00013a_","t":"ixn",'
                        b'"d":"EEy7aFHQPBagfqW4MatcUVRVN7yJfft-3RhTzgZvN3Pf",'
                        b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                        b'"s":"2","p":"EHZquNk1-N_KYQJcdXy_jym_YnwlzvdC_6YmGKp6VvIN",'
                        b'"a":[{"i":"EAKC8atqn7nuqB7Iqv_FohuGJz6l3ZhWsISbkQFD522D","s":"0","d":"EHFeHZKRISML75268kN2XvkFueHu-mXj3YZAWU8aQxQQ"}]}'
                        b'-VAn-AABAADnenNyGDisXGeZdQCLSzXl9QoYgBxi7cdYw3baY5ukUonbnIQnUBFBsCqPVvrp_dNibpTPVOWtJSDYNglDTKIH-EAB0AAAAAAAAAAAAAAAAAAAAAAC1AAG2025-07-29T19c40c43d456239p00c00'
                        b'{"v":"KERI10JSON0000ff_","t":"vcp",'
                        b'"d":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb",'
                        b'"i":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb",'
                        b'"ii":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                        b'"s":"0","c":["NB"],"bt":"0","b":[],"n":"0AC-D5XhLUkO-ODnrJMSRPqv"}'
                        b'-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAABEHZquNk1-N_KYQJcdXy_jym_YnwlzvdC_6YmGKp6VvIN'
                        b'{"v":"KERI10JSON0000ed_","t":"iss",'
                        b'"d":"EHFeHZKRISML75268kN2XvkFueHu-mXj3YZAWU8aQxQQ",'
                        b'"i":"EAKC8atqn7nuqB7Iqv_FohuGJz6l3ZhWsISbkQFD522D",'
                        b'"s":"0","ri":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb","dt":"2025-07-24T16:21:40.802473+00:00"}'
                        b'-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAACEEy7aFHQPBagfqW4MatcUVRVN7yJfft-3RhTzgZvN3Pf'
                        b'{"v":"ACDC10JSON0005f4_",'
                        b'"d":"EAKC8atqn7nuqB7Iqv_FohuGJz6l3ZhWsISbkQFD522D",'
                        b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                        b'"ri":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb",'
                        b'"s":"EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5",'
                        b'"a":{'
                            b'"d":"EP75lC-MDk8br72V7r5hxY1S7E7U4pgnsGX2WmGyLPxs",'
                            b'"dt":"2025-07-24T16:21:40.802473+00:00",'
                            b'"ids":['
                                b'"did:web:127.0.0.1%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                                b'"did:webs:127.0.0.17677%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                                b'"did:web:example.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                                b'"did:web:foo.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                                b'"did:webs:foo.comNone:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU"]},'
                        b'"r":{"d":"EEVTx0jLLZDQq8a5bXrXgVP0JDP7j8iDym9Avfo8luLw",'
                            b'"aliasDesignation":{'
                                b'"l":"The issuer of this ACDC designates the identifiers in the ids field as the only allowed namespaced aliases of the issuer\'s AID."},'
                            b'"usageDisclaimer":{'
                                b'"l":"This attestation only asserts designated aliases of the controller of the AID, that the AID controlled namespaced alias has been designated by the controller. It does not assert that the controller of this AID has control over the infrastructure or anything else related to the namespace other than the included AID."},'
                            b'"issuanceDisclaimer":{'
                                b'"l":"All information in a valid and non-revoked alias designation assertion is accurate as of the date specified."},'
                            b'"termsOfUse":{'
                                b'"l":"Designated aliases of the AID must only be used in a manner consistent with the expressed intent of the AID controller."}}}'
                        b'-VA0-FABEMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU0AAAAAAAAAAAAAAAAAAAAAAAEMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU-AABAAC29a0oQ7ML0dKq_MNsEUElt7d49KH2-folu9qiHztbLbtHfAU5O1X99TbnExPncL8uW2_mVD9ChYk5fZOK-eMO')
                )
                # fmt: on
            else:
                raise ValueError(f'Unexpected URL: {url}')

        app = resolving.falcon_app()
        oobiery = oobiing.Oobiery(hby=hby)
        resolver_end = resolving.UniversalResolverResource(hby=hby, rgy=regery, oobiery=oobiery, load_url=mock_load_url)
        app.add_route('/1.0/identifiers/{did}', resolver_end)
        client = testing.TestClient(app=app)

        encoded_did_webs = urllib.parse.quote(
            did_webs_did
        )  # to simulate what HIO does to the DID with urllib.parse.quote in Server.buildEnviron

        # Verify did:webs DID doc
        did_webs_response = client.simulate_get(f'/1.0/identifiers/{encoded_did_webs}')

        assert did_webs_response.content_type == 'application/did+ld+json', 'Content-Type should be application/did+ld+json'
        response_diddoc = json.loads(did_webs_response.content)
        assert response_diddoc == did_webs_diddoc, 'did:webs response did document does not match expected diddoc'

        # Verify did:keri DID doc
        encoded_did_keri = urllib.parse.quote(
            did_keri_did
        )  # to simulate what HIO does to the DID with urllib.parse.quote in Server.buildEnviron
        did_keri_response = client.simulate_get(f'/1.0/identifiers/{encoded_did_keri}')

        assert did_keri_response.content_type == 'application/did+ld+json', 'Content-Type should be application/did+ld+json'
        response_diddoc = json.loads(did_keri_response.content)
        did_keri_diddoc = didding.generate_did_doc(hby, rgy=regery, did=did_keri_did, aid=aid, meta=meta)
        assert response_diddoc == did_keri_diddoc, 'did:keri response did document does not match expected diddoc'


def test_universal_resolver_resource_on_get_error_cases():
    # Some error test cases for the UniversalResolverResource
    salt = b'0ACB-gtnUTQModt9u_UC3LFQ'
    registry_nonce = '0AC-D5XhLUkO-ODnrJMSRPqv'
    with habbing.openHab(salt=salt, name='water', transferable=True, temp=True) as (hby, hab):
        hby_doer = habbing.HaberyDoer(habery=hby)
        aid = 'EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU'
        host = '127.0.0.1'
        port = f'7677'
        did_path = 'dws'
        meta = False
        # fmt: off
        did_webs_did = f'did:webs:{host}%3A{port}:{did_path}:{aid}'         # did:webs:127.0.0.1%3A7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU
        did_keri_did = f'did:keri:{aid}'                                    # did:keri:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU
        did_json_url = f'https://{host}:{port}/{did_path}/{aid}/did.json'    # http://127.0.0.1:7677/dws/EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU/did.json
        keri_cesr_url = f'https://{host}:{port}/{did_path}/{aid}/keri.cesr'  # http://127.0.0.1:7677/dws/EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU/keri.cesr
        # fmt: on

        regery = credentialing.Regery(hby=hby, name=hab.name, temp=hby.temp)

        # Mock load_url to return the did.json and keri.cesr content
        def mock_load_url(url, timeout=None):
            if url == did_json_url:
                return bytearray()
            elif url == keri_cesr_url:
                return bytearray()
            else:
                raise ValueError(f'Unexpected URL: {url}')

        app = resolving.falcon_app()
        oobiery = oobiing.Oobiery(hby=hby)
        resolver_end = resolving.UniversalResolverResource(hby=hby, rgy=regery, oobiery=oobiery, load_url=mock_load_url)
        app.add_route('/1.0/identifiers/{did}', resolver_end)
        client = testing.TestClient(app=app)

        # must use on_get directly to simulate executing the request from outside of HIO so it acts
        # like getting mangled by HIO's use of urllib.parse.quote (PEP 3333 compliance)
        did = 'did%3Awebs%3A127.0.0.1%3A1234567'
        rep = mock(falcon.Response)
        resolver_end.on_get(mock(), rep, did)
        assert rep.status == falcon.HTTP_400, 'Expected HTTP 400 Bad Request for invalid DID'
        assert rep.content_type == 'application/json', 'Content-Type should be application/problem+json'
        assert rep.media == {'message': f'invalid DID: {did}', 'error': '1234567 is an invalid AID'}

        # Get with no DID returns error
        rep = client.simulate_get(f'/1.0/identifiers/')
        assert rep.status == falcon.HTTP_400, 'Expected HTTP 400 Not Found for missing DID parameter'
        assert rep.content.decode() == json.dumps({'error': "invalid resolution request body, 'did' is required"})


def test_resolver_with_metadata_returns_correct_doc():
    """
    Tests generation of both did:webs and did:keri DID Documents and a CESR stream for the did:webs DID with metadata.
    Uses static salt, registry nonce, and ACDC datetimestamp for deterministic results.
    """
    salt = b'0ACB-gtnUTQModt9u_UC3LFQ'
    registry_nonce = '0AC-D5XhLUkO-ODnrJMSRPqv'
    with habbing.openHab(salt=salt, name='water', transferable=True, temp=True) as (hby, hab):
        hby_doer = habbing.HaberyDoer(habery=hby)
        aid = 'EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU'
        host = '127.0.0.1'
        port = f'7677'
        did_path = 'dws'
        meta = True
        # fmt: off
        did_webs_did = f'did:webs:{host}%3A{port}:{did_path}:{aid}?meta=true'         # did:webs:127.0.0.1%3A7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU?meta=true
        did_keri_did = f'did:keri:{aid}'                                    # did:keri:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU
        did_json_url = f'https://{host}:{port}/{did_path}/{aid}/did.json?meta=true'    # http://127.0.0.1:7677/dws/EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU/did.json?meta=true
        keri_cesr_url = f'https://{host}:{port}/{did_path}/{aid}/keri.cesr'            # http://127.0.0.1:7677/dws/EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU/keri.cesr
        # fmt: on

        regery = credentialing.Regery(hby=hby, name=hab.name, temp=hby.temp)
        schema_json = conftest.Schema.designated_aliases_schema()
        rules_json = conftest.Schema.designated_aliases_rules()
        subject_data = self_attested_aliases_cred_subj(host, aid, port, did_path)
        CredentialHelpers.add_cred_to_aid(
            hby=hby,
            hby_doer=hby_doer,
            regery=regery,
            hab=hab,
            schema_said='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5',  # Designated Aliases Public Schema
            schema_json=schema_json,
            subject_data=subject_data,
            rules_json=rules_json,
            recp=None,  # No recipient for self-attested credential
            registry_nonce=registry_nonce,
        )

        did_webs_diddoc = didding.generate_did_doc(hby, rgy=regery, did=did_webs_did, aid=aid, meta=meta)

        # Mock load_url to return the did.json and keri.cesr content
        def mock_load_url(url, timeout=None):
            if url == did_json_url:
                # whitespace added for readability - this is just bytes and the whitespace does not impact the actual content
                # fmt: off
                return (
                    b'{'
                    b'"didDocument": {'
                        b'"id": "did:webs:127.0.0.1%3A7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU?meta=true", '
                        b'"verificationMethod": [{'
                            b'"id": "#DHfhTX8nqUdiU2yw5gnx3dFguwAPiR0SzK4I9ugjRoRF", '
                            b'"type": "JsonWebKey", '
                            b'"controller": "did:webs:127.0.0.1%3A7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                            b'"publicKeyJwk": {'
                                b'"kid": "DHfhTX8nqUdiU2yw5gnx3dFguwAPiR0SzK4I9ugjRoRF", '
                                b'"kty": "OKP", '
                                b'"crv": "Ed25519", '
                                b'"x": "d-FNfyepR2JTbLDmCfHd0WC7AA-JHRLMrgj26CNGhEU"}}], '
                        b'"service": [], '
                        b'"alsoKnownAs": ['
                            b'"did:web:127.0.0.1%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                            b'"did:webs:127.0.0.17677%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                            b'"did:web:example.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                            b'"did:web:foo.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                            b'"did:webs:foo.comNone:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU"]}, '
                    b'"didResolutionMetadata": {'
                        b'"contentType": "application/did+json", '
                        b'"retrieved": "2025-07-29T20:40:30Z"}, '
                    b'"didDocumentMetadata": {'
                        b'"witnesses": [], '
                        b'"versionId": "2", '
                        b'"equivalentId": ['
                            b'"did:webs:127.0.0.17677%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU", '
                            b'"did:webs:foo.comNone:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU"]}}'
                )
                # fmt: on
            elif url == keri_cesr_url:
                # whitespace added for readability - this is just bytes and the whitespace does not impact the actual content
                return (
                    b'{"v":"KERI10JSON00012b_","t":"icp",'
                    b'"d":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"s":"0",'
                    b'"kt":"1","k":["DHfhTX8nqUdiU2yw5gnx3dFguwAPiR0SzK4I9ugjRoRF"],'
                    b'"nt":"1","n":["EDklD8WWC8ks7U-pdxI_hoftybqLVRTj3KJK70jkq6Ha"],'
                    b'"bt":"0","b":[],"c":[],"a":[]}'
                    b'-VAn-AABAAAVeuv7YV_mWaMsye6tH5-G1x58jyJyPJtNePHS3u6vn5UYMlWBFzShMSabVqAtRvW8YW18uEhEGOaZ-cGkcE0J-EAB0AAAAAAAAAAAAAAAAAAAAAAA1AAG2025-07-24T16c27c22d019596p00c00'
                    b'{"v":"KERI10JSON00013a_","t":"ixn",'
                    b'"d":"EHZquNk1-N_KYQJcdXy_jym_YnwlzvdC_6YmGKp6VvIN",'
                    b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"s":"1","p":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"a":[{"i":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb","s":"0","d":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb"}]}'
                    b'-VAn-AABAAAfWrHVECbYrHe5hBQnIdgbbwmNPUO4VFsV0HG9zSwmbA-Qc7PqkQCD3IAZ_CnP5RrV2R_MgeYZtFu7PPwdWw0J-EAB0AAAAAAAAAAAAAAAAAAAAAAB1AAG2025-07-24T16c27c22d043008p00c00'
                    b'{"v":"KERI10JSON00013a_","t":"ixn",'
                    b'"d":"EEy7aFHQPBagfqW4MatcUVRVN7yJfft-3RhTzgZvN3Pf",'
                    b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"s":"2","p":"EHZquNk1-N_KYQJcdXy_jym_YnwlzvdC_6YmGKp6VvIN",'
                    b'"a":[{"i":"EAKC8atqn7nuqB7Iqv_FohuGJz6l3ZhWsISbkQFD522D","s":"0","d":"EHFeHZKRISML75268kN2XvkFueHu-mXj3YZAWU8aQxQQ"}]}'
                    b'-VAn-AABAADnenNyGDisXGeZdQCLSzXl9QoYgBxi7cdYw3baY5ukUonbnIQnUBFBsCqPVvrp_dNibpTPVOWtJSDYNglDTKIH-EAB0AAAAAAAAAAAAAAAAAAAAAAC1AAG2025-07-24T16c53c32d268075p00c00'
                    b'{"v":"KERI10JSON0000ff_","t":"vcp",'
                    b'"d":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb",'
                    b'"i":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb",'
                    b'"ii":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"s":"0","c":["NB"],"bt":"0","b":[],"n":"0AC-D5XhLUkO-ODnrJMSRPqv"}'
                    b'-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAABEHZquNk1-N_KYQJcdXy_jym_YnwlzvdC_6YmGKp6VvIN'
                    b'{"v":"KERI10JSON0000ed_","t":"iss",'
                    b'"d":"EHFeHZKRISML75268kN2XvkFueHu-mXj3YZAWU8aQxQQ",'
                    b'"i":"EAKC8atqn7nuqB7Iqv_FohuGJz6l3ZhWsISbkQFD522D",'
                    b'"s":"0","ri":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb","dt":"2025-07-24T16:21:40.802473+00:00"}'
                    b'-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAACEEy7aFHQPBagfqW4MatcUVRVN7yJfft-3RhTzgZvN3Pf'
                    b'{"v":"ACDC10JSON0005f4_",'
                    b'"d":"EAKC8atqn7nuqB7Iqv_FohuGJz6l3ZhWsISbkQFD522D",'
                    b'"i":"EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"ri":"EK_yp-mT-9YFKVqyUnqAN0CXUd6cxUGeIvem5I0A8TLb",'
                    b'"s":"EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5",'
                    b'"a":{'
                    b'"d":"EP75lC-MDk8br72V7r5hxY1S7E7U4pgnsGX2WmGyLPxs",'
                    b'"dt":"2025-07-24T16:21:40.802473+00:00",'
                    b'"ids":['
                    b'"did:web:127.0.0.1%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"did:webs:127.0.0.17677%3a7677:dws:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"did:web:example.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"did:web:foo.com:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU",'
                    b'"did:webs:foo.comNone:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU"]},'
                    b'"r":{'
                    b'"d":"EEVTx0jLLZDQq8a5bXrXgVP0JDP7j8iDym9Avfo8luLw",'
                    b'"aliasDesignation":{"l":"The issuer of this ACDC designates the identifiers in the ids field as the only allowed namespaced aliases of the issuer\'s AID."},'
                    b'"usageDisclaimer":{"l":"This attestation only asserts designated aliases of the controller of the AID, that the AID controlled namespaced alias has been designated by the controller. It does not assert that the controller of this AID has control over the infrastructure or anything else related to the namespace other than the included AID."},'
                    b'"issuanceDisclaimer":{"l":"All information in a valid and non-revoked alias designation assertion is accurate as of the date specified."},'
                    b'"termsOfUse":{"l":"Designated aliases of the AID must only be used in a manner consistent with the expressed intent of the AID controller."}}}'
                    b'-VA0-FABEMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU0AAAAAAAAAAAAAAAAAAAAAAAEMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU-AABAAC29a0oQ7ML0dKq_MNsEUElt7d49KH2-folu9qiHztbLbtHfAU5O1X99TbnExPncL8uW2_mVD9ChYk5fZOK-eMO'
                )
            else:
                raise ValueError(f'Unexpected URL: {url}')

        app = resolving.falcon_app()
        oobiery = oobiing.Oobiery(hby=hby)
        resolver_end = resolving.UniversalResolverResource(hby=hby, rgy=regery, oobiery=oobiery, load_url=mock_load_url)
        app.add_route('/1.0/identifiers/{did}', resolver_end)
        client = testing.TestClient(app=app)

        encoded_did_webs = urllib.parse.quote(
            did_webs_did
        )  # to simulate what HIO does to the DID with urllib.parse.quote in Server.buildEnviron

        # Verify did:webs DID doc
        did_webs_response = client.simulate_get(f'/1.0/identifiers/{encoded_did_webs}')

        assert did_webs_response.content_type == 'application/did-resolution', 'Content-Type should be application/did+ld+json'
        response_diddoc = json.loads(did_webs_response.content)[didding.DD_FIELD]
        did_webs_diddoc = did_webs_diddoc[didding.DD_FIELD]
        assert response_diddoc == did_webs_diddoc, 'did:webs response did document does not match expected diddoc'

        # Verify did:keri DID doc
        encoded_did_keri = urllib.parse.quote(
            did_keri_did
        )  # to simulate what HIO does to the DID with urllib.parse.quote in Server.buildEnviron
        did_keri_response = client.simulate_get(f'/1.0/identifiers/{encoded_did_keri}')

        assert did_keri_response.content_type == 'application/did+ld+json', 'Content-Type should be application/did+ld+json'
        response_diddoc = json.loads(did_keri_response.content)
        did_keri_diddoc = didding.generate_did_doc(hby, rgy=regery, did=did_keri_did, aid=aid, meta=False)
        assert response_diddoc == did_keri_diddoc, 'did:keri response did document does not match expected diddoc'


def test_resolver_with_did_keri_resolve_returns_correct_doc():
    salt = b'0ACB-gtnUTQModt9u_UC3LFQ'
    with habbing.openHab(salt=salt, name='water', transferable=True, temp=True) as (hby, hab):
        hby_doer = habbing.HaberyDoer(habery=hby)
        rgy = credentialing.Regery(hby=hby, name=hby.name, base=hby.base, temp=hby.temp)
        aid = 'EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU'
        meta = True
        did_keri_did = f'did:keri:{aid}'  # did:keri:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU

        expected_doc = didding.generate_did_doc(hby, rgy=rgy, did=did_keri_did, aid=aid, meta=meta)

        # Run the did:keri resolver and verify it returns the expected DID doc
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        keri_resolver = KeriResolver(did=did_keri_did, meta=meta, verbose=True, hby=hby, rgy=rgy)
        doist.do([keri_resolver])
        assert keri_resolver.result == expected_doc, 'KeriResolver did not return the expected DID document'

        # with an invalid did:keri DID
        keri_resolver = KeriResolver(did='did:keri:invalid', meta=meta, verbose=True, hby=hby, rgy=rgy)
        with pytest.raises(ValueError) as excinfo:
            doist.do([keri_resolver])
        assert str(excinfo.value) == 'invalid is an invalid AID'


def test_resolve_error_conditions():
    hby = mock()
    rgy = mock()
    with patch('dws.core.resolving.get_dws_artifacts') as mock_get_artifacts:
        mock_get_artifacts.side_effect = ArtifactResolveError('Failed to resolve artifacts')
        result, err = resolving.resolve(hby, rgy, 'did:webs:example.com:EEdpe-yqftH2_FO1-luoHvaiShK4y_E2dInrRQ2_2X5v')
        assert not result, 'Expected result to be False for resolution failure'
        assert err == {'error': 'Failed to resolve artifacts'}, 'Expected error message for resolution failure'

        mock_get_artifacts.side_effect = Exception('Unexpected error')
        result, err = resolving.resolve(hby, rgy, 'did:webs:example.com:EEdpe-yqftH2_FO1-luoHvaiShK4y_E2dInrRQ2_2X5v')
        assert not result, 'Expected result to be False for unexpected error'


def test_resolve_meta_true_yet_no_returned_metadata_wraps_in_meta():
    """
    Tests the branch where metadata is requested yet the retrieved did.json document does not contain metadata
    so the document is wrapped in metadata.
    """
    aid = 'EBFn5ge82EQwxp9eeje-UMEXF-v-3dlfbdVMX_PNjSft'
    hby = mock(habbing.Habery)
    hby.db = mock(basing.Baser)
    rgy = mock(credentialing.Regery)
    hby.kevers = dbdict()
    kever = mock(eventing.Kever)
    hby.kevers[aid] = kever
    kever.sner = mock(serdering.SerderKERI)
    kever.sner.num = 0

    did = 'did:webs:127.0.0.1%3A7676:dws:EBFn5ge82EQwxp9eeje-UMEXF-v-3dlfbdVMX_PNjSft'
    did_doc = b"""{
        "id": "did:webs:127.0.0.1%3A7676:dws:EBFn5ge82EQwxp9eeje-UMEXF-v-3dlfbdVMX_PNjSft",
        "verificationMethod": [
          {
            "id": "#DLocH0g8QYMUqaxn7UcxQbiy-vp5m_1LQY4DsHu0CRrw",
            "type": "JsonWebKey",
            "controller": "did:webs:127.0.0.1%3A7676:dws:EBFn5ge82EQwxp9eeje-UMEXF-v-3dlfbdVMX_PNjSft",
            "publicKeyJwk": {
              "kid": "DLocH0g8QYMUqaxn7UcxQbiy-vp5m_1LQY4DsHu0CRrw",
              "kty": "OKP",
              "crv": "Ed25519",
              "x": "uhwfSDxBgxSprGftRzFBuLL6-nmb_UtBjgOwe7QJGvA"
            }
          }
        ],
        "service": [],
        "alsoKnownAs": []
      }"""
    keri_cesr = b''
    with (
        patch('dws.core.resolving.get_dws_artifacts') as mock_get_artifacts,
        patch('dws.core.resolving.save_cesr') as mock_save_cesr,
        # patch('dws.core.didding.from_did_web') as mock_from_did_web,
        patch('dws.core.resolving.get_generated_did_doc') as mock_get_gen_did_doc,
        patch('dws.core.resolving.verify') as mock_verify,
        patch('dws.core.didding.get_equiv_aka_ids') as mock_get_equiv_aka_ids,
        patch('dws.core.didding.get_witness_list') as mock_get_witness_list,
    ):
        mock_get_witness_list.return_value = []
        mock_get_equiv_aka_ids.return_value = [], []

        # Mock the return value to simulate no metadata
        mock_get_artifacts.return_value = (aid, did_doc, keri_cesr)

        wrapped_dd = resolving.wrap_metadata(json.loads(did_doc.decode()), did, aid, hby, rgy)
        dd_actual = didding.from_did_web(wrapped_dd, True)

        mock_get_gen_did_doc.return_value = {}
        mock_verify.return_value = True, {}

        result, err = resolving.resolve(hby, rgy, did, meta=True)

        mock_verify.assert_called_once_with({}, dd_actual, meta=True)


def test_save_cesr_aid_not_in_kevers_raises():
    # Mock out the get item call
    hby = MagicMock()
    hby.psr = mock()
    mydict = {}
    hby.kevers = MagicMock()
    hby.kevers.__getitem__.side_effect = mydict.get
    rgy = mock(credentialing.Regery)
    rgy.reger = mock(credentialing.Reger)

    kc_res = b''
    aid = 'EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU'
    when(hby.kevers).__getitem__(aid).thenReturn([])
    with pytest.raises(kering.KeriError) as excinfo:
        resolving.save_cesr(hby, rgy, kc_res, aid)


def test_tls_falcon_server_keypath_present_returns_server_tls():
    app = Mock(spec=falcon.App)
    mock_servant = MagicMock()
    with patch('hio.core.tcp.ServerTls') as mock_tls, patch('hio.core.http.Server') as mock_server:
        mock_tls.return_value = mock_servant

        resolving.tls_falcon_server(app, 10, 'path', 'path', 'path')
        mock_tls.assert_called_once_with(
            certify=False,
            keypath='path',
            certpath='path',
            cafilepath='path',
            port=10,
        )
        mock_server.assert_called_once_with(port=10, app=app, servant=mock_servant)

    with patch('hio.core.http.Server') as mock_server:
        server = resolving.tls_falcon_server(app, 10, None, None, None)
        mock_server.assert_called_once_with(port=10, app=app, servant=None)


def test_resolution_failure_with_mocks():
    hby = mock()
    rgy = mock()
    oobiery = mock()
    load_url = mock()
    with patch('dws.core.resolving.resolve') as mock_resolve:
        mock_resolve.return_value = False, {}
        resolver = resolving.UniversalResolverResource(hby=hby, rgy=rgy, oobiery=oobiery, load_url=load_url)
        req = mock()
        req.params = {}
        rep = mock(falcon.Response)
        req.get_header = lambda x: 'application/did-resolution' if x == 'Accept' else None
        resolver.on_get(req, rep, 'did:webs:example.com:EEdpe-yqftH2_FO1-luoHvaiShK4y_E2dInrRQ2_2X5v?meta=true')
        assert rep.status == falcon.HTTP_417, 'Expected HTTP 417 Expectation Failed for resolution failure'


def test_resolve_did_keri_error_cases():
    hby = mock()
    hby.kevers = dbdict()
    rgy = mock()
    did = 'did:keri:EMkO5tGOSTSGY13mdljkFaSuUWBpvGMbdYTGV_7LAXhU'
    result, err = resolving.resolve_did_keri(hby, rgy, did)
    assert not result, 'Expected result to be False for invalid did:keri'
    assert err == {'error': f'Unknown AID, cannot resolve DID {did}'}
