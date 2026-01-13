"""
Configure PyTest

Use this module to configure pytest
https://docs.pytest.org/en/latest/pythonpath.html

"""

import json
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from typing import List, Union

import pytest
from hio.base import doing
from hio.help import decking
from keri import core
from keri.app import agenting, delegating, forwarding, grouping, habbing, indirecting, keeping
from keri.app.habbing import HaberyDoer, openHby
from keri.core import coring, eventing, scheming, serdering
from keri.help import helping
from keri.vdr import credentialing, verifying
from keri.vdr.credentialing import Regery


@pytest.fixture()
def mock_helping_now_utc(monkeypatch):
    """
    Replace nowUTC universally with fixed value for testing
    """

    def mock_now_utc():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return helping.fromIso8601('2021-01-01T00:00:00.000000+00:00')

    monkeypatch.setattr(helping, 'nowUTC', mock_now_utc)


def assemble_did_webs_did(domain, aid, port=None, path=None):
    did = f'did:webs:{domain}{port}'
    if port:
        did += f'%3a{port}'
    if path:
        did += f':{path}'
    if aid:
        did += f':{aid}'
    return did


def assemble_did_web_did(domain, aid, port=None, path=None):
    did = f'did:web:{domain}'
    if port:
        did += f'%3a{port}'
    if path:
        did += f':{path}'
    if aid:
        did += f':{aid}'
    return did


class CredentialHelpers:
    """Test helpers for issuing credentials using AID and schema."""

    @staticmethod
    def add_cred_to_aid(
        hby: habbing.Habery,
        hby_doer: HaberyDoer,
        regery: Regery,
        hab: habbing.Hab,
        schema_said: str,
        schema_json: dict,
        subject_data: dict,
        rules_json: dict,
        source: Union[dict, list] = None,
        recp: str = None,
        registry_nonce: str = None,
        private: bool = False,
        private_credential_nonce: str = None,
        private_subject_nonce: str = None,
        additional_deeds: deque = None,
    ):
        """Issues a credential with a given AID using the schema, subject data, rules, edges (source), and recipient (recp)."""
        additional_deeds = additional_deeds or decking.deque(
            []
        )  # To avoid NoneType errors when concatenating with the existing deeds deque
        # Components needed for issuance
        counselor = grouping.Counselor(hby=hby)
        registrar = credentialing.Registrar(hby=hby, rgy=regery, counselor=counselor)
        verifier = verifying.Verifier(hby=hby, reger=regery.reger)
        credentialer = credentialing.Credentialer(hby=hby, rgy=regery, registrar=registrar, verifier=verifier)
        regery_doer = credentialing.RegeryDoer(rgy=regery)

        # set up Doist to run doers
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        deeds = doist.enter(doers=[hby_doer, counselor, registrar, credentialer, regery_doer])

        # Add schema to resolver schema cache
        schemer = scheming.Schemer(
            raw=bytes(json.dumps(schema_json), 'utf-8'), typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256
        )
        cache = scheming.CacheResolver(db=hby.db)
        cache.add(schemer.said, schemer.raw)

        # Create registry
        issuer_reg = regery.makeRegistry(prefix=hab.pre, name=hab.name, noBackers=True, nonce=registry_nonce)
        rseal = eventing.SealEvent(issuer_reg.regk, '0', issuer_reg.regd)._asdict()
        reg_anc = hab.interact(data=[rseal])
        reg_anc_serder = serdering.SerderKERI(raw=bytes(reg_anc))
        registrar.incept(iserder=issuer_reg.vcp, anc=reg_anc_serder)

        while not registrar.complete(pre=issuer_reg.regk, sn=0):
            doist.recur(deeds=deeds + additional_deeds)  # run until registry is incepted
            verifier.processEscrows()

        assert issuer_reg.regk in regery.reger.tevers

        # Create and issue the self-attested credential
        creder = credentialer.create(
            regname=issuer_reg.name,
            recp=recp,
            schema=schema_said,
            source=source,
            rules=rules_json,
            data=subject_data,
            private=private,
            private_credential_nonce=private_credential_nonce,
            private_subject_nonce=private_subject_nonce,
        )

        # Create ACDC issuance and anchor to KEL
        reg_iss_serder = issuer_reg.issue(said=creder.said, dt=creder.attrib['dt'])
        iss_seal = eventing.SealEvent(reg_iss_serder.pre, '0', reg_iss_serder.said)._asdict()
        iss_anc = hab.interact(data=[iss_seal])
        anc_serder = serdering.SerderKERI(raw=iss_anc)
        credentialer.issue(creder, reg_iss_serder)
        registrar.issue(creder, reg_iss_serder, anc_serder)

        while not credentialer.complete(said=creder.said):
            doist.recur(deeds=deeds + additional_deeds)
            verifier.processEscrows()
            regery.processEscrows()

        state = issuer_reg.tever.vcState(vci=creder.said)
        assert state.et == coring.Ilks.iss
        return creder, reg_iss_serder, anc_serder


class WitnessContext:
    """
    An instance of the doers for a witness that enable running a witness as a set of doers with the
    static context manager function `with_witness`. This facilitates debuggable testability of any
    functionality involving witnesses.
    """

    def __init__(self, name: str, hby: habbing.Habery, tcp_port: int = 6632, http_port: int = 6642):
        """
        Initialize the WitnessContext context manager with a witness name and habery.

        Args:
            name (str): The name of the witness.
            hby (habbing.Habery): The habery instance to use.
            tcp_port (int): The TCP port for the witness. Default is 6642.
            http_port (int): The HTTP port for the witness. Default is 6643.
        """
        self.name = name
        self.hby = hby
        ks = keeping.Keeper(name=name, base=hby.base, temp=True, reopen=True)

        aeid = ks.gbls.get('aeid')

        hby_doer = habbing.HaberyDoer(habery=hby)
        doers = [hby_doer]
        doers.extend(indirecting.setupWitness(alias=name, hby=hby, tcpPort=tcp_port, httpPort=http_port))
        self.doers = doers  # store doers for manual Doist.recur control in body of test

    @contextmanager
    @staticmethod
    def with_witness(name, hby, tcp_port=6632, http_port=6642):
        yield WitnessContext(name, hby, tcp_port, http_port)


class HabbingHelpers:
    @staticmethod
    @contextmanager
    def openHab(name='test', base='', salt=None, temp=True, cf=None, **kwa):
        """
        Context manager wrapper for Hab instance.
        Defaults to temporary resources
        Context 'with' statements call .close on exit of 'with' block

        Parameters:
            name(str): name of habitat to create
            base(str): the name used for shared resources i.e. Baser and Keeper The habitat specific config file will be
            in base/name
            salt(bytes): passed to habitat to use for inception raw salt not qb64
            temp(bool): indicates if this uses temporary databases
            cf(Configer): optional configer for loading configuration data
        TODO: replace this openHab fixture with one from KERIpy once https://github.com/WebOfTrust/keripy/pull/1078 is merged.
              this copy was needed in order to pass cf to Habery.makeHab() since the **kwa is not unpacking the cf arg.
        """

        salt = core.Salter(raw=salt).qb64

        with openHby(name=name, base=base, salt=salt, temp=temp, cf=cf) as hby:
            if (hab := hby.habByName(name)) is None:
                hab = hby.makeHab(name=name, icount=1, isith='1', ncount=1, nsith='1', cf=cf, **kwa)

            yield hby, hab

    @staticmethod
    def habery_doers(hby: habbing.Habery):
        """
        Return the list of Doers needed to run a controller using a Doist and the WitnessReceiptor.
        The WitnessReceiptorDoer is used to check whether there are any unprocessed cues so the
        Doist knows when to stop running.

        Useful for running a Controller in a test.
        """
        hby_doer = habbing.HaberyDoer(habery=hby)
        anchorer = delegating.Anchorer(hby=hby, proxy=None)
        postman = forwarding.Poster(hby=hby)
        mbx = indirecting.MailboxDirector(hby=hby, topics=['/receipt', '/replay', '/reply'])
        wit_rcptr_doer = agenting.WitnessReceiptor(hby=hby)
        receiptor = agenting.Receiptor(hby=hby)
        doers = [hby_doer, anchorer, postman, mbx, wit_rcptr_doer, receiptor]
        return doers, hby_doer, wit_rcptr_doer


def self_attested_aliases_cred_subj(domain: str, aid: str, port: str = None, path: str = None):
    """
    Generate test self attested credential data using the domain, AID, port, path, and assembler functions.

    Parameters:
        domain (str): domain for did:webs DID
        aid (str): alias identifier for did:webs DID
        port (str): optional port for did:webs DID
        path (str): optional path for did:webs DID
    """
    return dict(
        d='',
        dt='2025-07-24T16:21:40.802473+00:00',  # using fixed date so ACDC SAID stays the same
        ids=[
            assemble_did_web_did(domain, aid, port, path),
            assemble_did_webs_did(domain, aid, port, path),
            assemble_did_web_did('example.com', aid, None, None),
            assemble_did_web_did('foo.com', aid, None, None),
            assemble_did_webs_did('foo.com', aid, None, None),
        ],
    )


class Schema:
    """
    Using pathlib to load schema and rules files from "tests/schema" using the relative .parent path
    allows tests to be run from any working directory.
    """

    @staticmethod
    def designated_aliases_schema():
        schema_path = Path(__file__).parent / 'schema' / 'designated-aliases-public-schema.json'
        return json.loads(schema_path.read_bytes())

    @staticmethod
    def designated_aliases_rules():
        schema_path = Path(__file__).parent / 'schema' / 'rules' / 'desig-aliases-public-schema-rules.json'
        return json.loads(schema_path.read_bytes())
