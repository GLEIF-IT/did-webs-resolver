import io
import json
import logging
import os
from unittest.mock import Mock, patch

import falcon
import pytest
from hio.base import doing
from keri import core
from keri.app import configing, habbing, oobiing
from keri.vdr import credentialing
from mockito import mock

from dws.core import artifacting, didding, generating, resolving
from dws.core.ends import DID_JSON, KERI_CESR
from dws.core.resolving import RequestLoggerMiddleware
from tests import conftest
from tests.conftest import CredentialHelpers, HabbingHelpers, WitnessContext, self_attested_aliases_cred_subj


def test_artifact_generation_creates_expected_artifacts():
    salt = b'0AAB_Fidf5WeZf6VFc53IxVw'
    registry_nonce = '0ADV24br-aaezyRTB-oUsZJE'

    # set up witness config
    wit_salt = core.Salter(raw=b'abcdef0123456789').qb64
    wit_cf = configing.Configer(name='wil', temp=False, reopen=True, clear=False)
    wit_cf_dict = {
        'dt': '2022-01-20T12:57:59.823350+00:00',
        'wil': {'dt': '2022-01-20T12:57:59.823350+00:00', 'curls': ['tcp://127.0.0.1:6633/', 'http://127.0.0.1:6643/']},
    }
    wit_cf.put(wit_cf_dict)
    wil_oobi = 'http://127.0.0.1:6643/oobi/BKH72-JtJiyIgvFA9YAZW4FCrYwICboCb6STGzJwFEv0/controller?name=Wil&tag=witness'

    # Config of the AID controller keystore who is having their did:webs or did:keri artifacts resolved
    rb_cf = configing.Configer(name='red_book', temp=False, reopen=True, clear=False)
    rb_cf.put({'dt': '2022-01-20T12:57:59.823350+00:00', 'iurls': [wil_oobi]})

    # Open the witness Habery and Hab, feed it into the witness setup, and then create the AID controller Habery and Hab
    with (
        HabbingHelpers.openHab(salt=bytes(wit_salt, 'utf-8'), name='wil', transferable=False, temp=True, cf=wit_cf) as (
            wit_hby,
            wit_hab,
        ),
        WitnessContext.with_witness(name='wil', hby=wit_hby, tcp_port=6633, http_port=6643) as wil_wit,
        habbing.openHab(salt=salt, name='red_book', transferable=True, temp=True, cf=rb_cf) as (rb_hby, rb_hab),
    ):
        wil_pre = 'BKH72-JtJiyIgvFA9YAZW4FCrYwICboCb6STGzJwFEv0'
        tock = 0.03125
        doist = doing.Doist(limit=0.0, tock=tock, real=True)
        # Doers and deeds for witness wil
        wit_deeds = doist.enter(doers=wil_wit.doers)

        # Resolve OOBI
        oobiery = oobiing.Oobiery(hby=rb_hby)
        authn = oobiing.Authenticator(hby=rb_hby)
        oobiery_deeds = doist.enter(doers=oobiery.doers + authn.doers)
        while not oobiery.hby.db.roobi.get(keys=(wil_oobi,)):
            doist.recur(deeds=wit_deeds + oobiery_deeds)
            rb_hby.kvy.processEscrows()  # process any escrows from witness receipts
        print(f'Resolved OOBI: {wil_oobi} to {oobiery.hby.db.roobi.get(keys=(wil_oobi,))}')

        # Doers and deeds for the page Hab and Habery
        rb_doers, hby_doer, wit_rcptr_doer = HabbingHelpers.habery_doers(hby=rb_hby)
        rb_deeds = doist.enter(doers=rb_doers)

        page_hab = rb_hby.makeHab(name='page', isith='1', icount=1, toad=1, wits=[wil_pre])

        # Waiting for witness receipts...
        wit_rcptr_doer.msgs.append(dict(pre=page_hab.pre))
        while not wit_rcptr_doer.cues:
            doist.recur(deeds=wit_deeds + rb_deeds)

        # Prepare the DID artifact stream using self-attested credentials
        aid = 'EJg2UL2kSzFV_Akd9ISAvgOUFDKcBxpDO3OZDIbSIjGe'  # page_hab.pre
        host = '127.0.0.1'
        port = f'7677'
        did_path = 'dws'
        meta = True
        did_webs_did = f'did:webs:{host}%3A{port}:{did_path}:{aid}?meta=true'  # did:webs:127.0.0.1%3A7677:dws:EPTCU0Yge3UDk4bsTWtUhiNJjPDZlW88qRQvJpZ53WRV?meta=true

        # Expects the test to be run from the root of the repository
        regery = credentialing.Regery(hby=rb_hby, name=rb_hby.name, temp=rb_hby.temp)
        schema_json = conftest.Schema.designated_aliases_schema()
        rules_json = conftest.Schema.designated_aliases_rules()
        subject_data = self_attested_aliases_cred_subj(host, aid, port, did_path)
        CredentialHelpers.add_cred_to_aid(
            hby=rb_hby,
            hby_doer=hby_doer,
            regery=regery,
            hab=page_hab,
            schema_said='EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5',  # Designated Aliases Public Schema
            schema_json=schema_json,
            subject_data=subject_data,
            rules_json=rules_json,
            recp=None,  # No recipient for self-attested credential
            registry_nonce=registry_nonce,
            additional_deeds=wit_deeds + rb_deeds,
        )

        # get keri.cesr
        reger = regery.reger
        keri_cesr = bytearray()
        # self.retrieve_kel_via_oobi() # not currently used; an alternative to relying on a local KEL keystore
        keri_cesr.extend(artifacting.gen_kel_cesr(rb_hab, aid))  # add KEL CESR stream
        keri_cesr.extend(artifacting.gen_loc_schemes_cesr(rb_hab, aid))
        keri_cesr.extend(artifacting.gen_des_aliases_cesr(page_hab, reger, aid))

        did_webs_diddoc = didding.generate_did_doc(rb_hby, rgy=regery, did=did_webs_did, aid=aid, meta=meta)

        # Run the DIDArtifactGenerator to generate the artifacts
        output_dir = './tests/artifact_output_dir'
        did_art_gen = generating.DIDArtifactGenerator(
            name=rb_hby.name,
            base=rb_hby.base,
            bran=None,
            hby=rb_hby,
            hby_doer=hby_doer,
            regery=regery,
            did=did_webs_did,
            meta=meta,
            output_dir=output_dir,
            verbose=True,
            cf=rb_cf,
        )
        doist.do([did_art_gen])
        assert os.path.exists(f'{output_dir}/{aid}/{DID_JSON}')
        assert os.path.exists(f'{output_dir}/{aid}/{KERI_CESR}')
        assert (
            did_art_gen.did_json[didding.DD_FIELD] == didding.to_did_web(diddoc=did_webs_diddoc, meta=meta)[didding.DD_FIELD]
        ), 'DID document does not match the expected structure'
        assert did_art_gen.keri_cesr == keri_cesr

        with open(f'{output_dir}/{aid}/{DID_JSON}', 'r') as did_file:
            did_json = json.load(did_file)
            assert did_json == didding.to_did_web(diddoc=did_webs_diddoc, meta=meta)

        with open(f'{output_dir}/{aid}/{KERI_CESR}', 'rb') as cesr_file:
            keri_cesr_data = cesr_file.read()
            assert keri_cesr_data == keri_cesr

        assert resolving.diff_dicts(did_webs_diddoc, did_json), 'DID document does not match the expected structure'

        # And test a failed verification by having one be meta=True and one be meta=False

        did_webs_diddoc = didding.generate_did_doc(rb_hby, rgy=regery, did=did_webs_did, aid=aid, meta=True)
        did_webs_diddoc[didding.DD_FIELD] = {f'{didding.VMETH_FIELD}': {}}  # break the diddoc
        result, dd_expected = resolving.verify(did_art_gen.did_json, did_webs_diddoc, meta=True)
        assert not result, 'Verification should fail when meta is True but did document is generated with meta=False'


def test_did_art_genr_with_empty_hby_creates_hby():
    hby_mock = mock(habbing.Habery)
    hby_mock.db = mock()
    hby_doer_mock = mock(habbing.HaberyDoer)
    rgy_mock = mock(credentialing.Regery)
    with patch('dws.core.habs.get_habery_and_doer') as mock_get_habery_and_doer:
        mock_get_habery_and_doer.return_value = hby_mock, hby_doer_mock
        gen = generating.DIDArtifactGenerator(
            name='test_resolver', base='test_base', bran=None, did='fake:did', regery=rgy_mock
        )
        assert gen.hby == hby_mock, 'Expected KeriResolver to create a new Habery instance'
        assert hby_doer_mock in gen.doers, 'Expected KeriResolver to add HaberyDoer to its doers'


@pytest.fixture
def mock_req():
    req = Mock(spec=falcon.Request)
    req.method = 'POST'
    req.url = '/test'
    req.headers = {'Content-Type': 'application/json'}
    req.content_length = 10
    req.stream = io.BytesIO(b'{"key": "value"}')  # Mock stream for body read
    req.env = {'wsgi.input': req.stream, 'CONTENT_LENGTH': '10'}
    return req


@pytest.fixture
def mock_resp():
    return Mock(spec=falcon.Response)


def test_request_logger_middleware_on_debug(mock_req, mock_resp):
    """
    Test that the request logger middleware logs requests when debug is enabled.
    """
    middleware = RequestLoggerMiddleware()

    with (
        patch('dws.core.resolving.logger.isEnabledFor') as mock_enabled,
        patch('dws.core.resolving.logger.debug') as mock_debug,
    ):
        mock_enabled.return_value = True  # Force enabled path

        middleware.process_request(mock_req, mock_resp)

        mock_enabled.assert_called_with(logging.DEBUG)
        mock_debug.assert_called_with('Request body    : %s', '{"key": "value"}')  # Or '<empty>' if no body
        assert mock_req.env['wsgi.input'].read() == b'{"key": "value"}'  # Reset worked
        assert mock_req.env['CONTENT_LENGTH'] == '16'  # Updated to actual len
