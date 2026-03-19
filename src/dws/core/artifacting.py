import json
import os

import vgate
from hio.core import http
from keri import kering
from keri.app import habbing, signing
from keri.app.habbing import Hab, Habery
from keri.core.serdering import SerderACDC
from keri.vdr import credentialing, viring
from keri.vdr.credentialing import Regery
from keri.vdr.viring import Reger

from dws import UnknownAID, log_name, ogler
from dws.core import didding, ends, resolving, webbing
from dws.core.didding import DES_ALIASES_SCHEMA

logger = ogler.getLogger(log_name)


def gen_kel_cesr(hab: habbing.Hab, pre: str) -> bytearray:
    """Return a bytearray of the CESR stream of all KEL events for a given prefix."""
    return hab.replay(pre=pre)


def make_keri_cesr_path(output_dir: str, aid: str):
    """Create keri.cesr enclosing dir, and any intermediate dirs, if not existing"""
    kc_dir_path = os.path.join(output_dir, aid)
    if not os.path.exists(kc_dir_path):
        logger.debug(f'Creating directory for KERI CESR events: {kc_dir_path}')
        os.makedirs(kc_dir_path)
    return os.path.join(kc_dir_path)


def write_keri_cesr_file(output_dir: str, aid: str, keri_cesr: bytearray):
    """Write the keri.cesr file to output path, making any enclosing directories"""
    kc_file_path = make_keri_cesr_path(output_dir, aid)
    kc_file_path = os.path.join(kc_file_path, ends.KERI_CESR)
    with open(kc_file_path, 'w') as kcf:
        tmsg = keri_cesr.decode('utf-8')
        logger.debug(f'Writing CESR events to {kc_file_path}: \n{tmsg}')
        kcf.write(tmsg)


def get_self_issued_acdcs(aid: str, reger: credentialing.Reger, schema: str = didding.DES_ALIASES_SCHEMA):
    """Get self issued ACDCs filtered by schema"""
    creds_issued = reger.issus.get(keys=aid)
    creds_by_schema = reger.schms.get(keys=schema.encode('utf-8'))

    # self-attested, there is no issuee, and schema is designated aliases
    return [
        cred_issued
        for cred_issued in creds_issued
        if cred_issued.qb64 in [cred_by_schm.qb64 for cred_by_schm in creds_by_schema]
    ]


def gen_tel_cesr(reger: viring.Reger, evt_pre: str) -> bytearray:
    """Get the CESR stream of TEL events for a given registry."""
    msgs = bytearray()
    for msg in reger.clonePreIter(pre=evt_pre):
        msgs.extend(msg)
    return msgs


def gen_acdc_cesr(hab: Hab, reger: Reger, creder: SerderACDC) -> bytearray:
    """
    Add the CESR stream of the self attestation ACDCs for the given AID including signatures
    and their anchors to their source KELs.
    """
    arr = bytearray()
    (prefixer, seqner, saider) = reger.cancs.get(keys=(creder.said,))
    arr.extend(bytearray(signing.serialize(creder, prefixer, seqner, saider)))
    return arr


def gen_des_aliases_cesr(hab: Hab, reger: Reger, aid: str, schema: str = DES_ALIASES_SCHEMA) -> bytearray:
    """
    Select a specific ACDC from the local registry (Regery), if it exists, to generate the
    CESR stream
    Args:
        hab: The local Hab to use for generating the CESR stream
        aid: AID prefix to retrieve the ACDC for
        reger: The Regery to use for retrieving the ACDC
        schema: the schema to use to select the target ACDC from the local registry

    Returns:
        bytearray: CESR stream of locally stored ACDC events for the specified AID and schema
    """
    # self-attested, there is no issuee, and schema is designated aliases
    local_creds = get_self_issued_acdcs(aid, reger, schema)

    cesr_bytes = bytearray()
    for cred in local_creds:
        creder, *_ = reger.cloneCred(said=cred.qb64)
        cesr_bytes.extend(add_cred_cesr_bytes(creder, hab, reger))
    return cesr_bytes


def add_cred_cesr_bytes(creder: SerderACDC, hab: Hab, reger: Reger) -> bytearray:
    """Add one ACDC credential bytes to the CESR stream"""
    creder_bytes = bytearray()
    creder_bytes.extend(gen_tel_cesr(reger, creder.regi))
    creder_bytes.extend(gen_tel_cesr(reger, creder.said))
    creder_bytes.extend(gen_acdc_cesr(hab, reger, creder))
    return creder_bytes


def get_witness_loc_scheme_bytes(hab: habbing.Hab, wit_prefixes: list[str], scheme: str = '') -> bytearray:
    """Gets the witness location scheme records from the local hab database as a bytearray."""
    msgs = bytearray()
    for eid in wit_prefixes:
        loc_scheme_msg = hab.loadLocScheme(eid=eid, scheme=scheme)
        logger.debug(f'Found witness location scheme message for eid {eid}: {loc_scheme_msg}')
        msgs.extend(loc_scheme_msg if loc_scheme_msg else bytearray())
        end_role_msg = hab.loadEndRole(cid=eid, eid=eid, role=kering.Roles.controller)
        logger.debug(f'Found witness endpoint role message for eid {eid}: {end_role_msg}')
        msgs.extend(end_role_msg if end_role_msg else bytearray())
    return msgs


def get_agent_loc_scheme_bytes(hab: habbing.Hab, aid: str, scheme: str = '') -> bytearray:
    """Gets the agent location scheme records from the local hab database as a bytearray."""
    msgs = bytearray()
    for (_, erole, eid), _ in hab.db.ends.getItemIter(keys=(aid, kering.Roles.agent)):
        # Get the location scheme message for the agent
        loc_scheme_msg = hab.loadLocScheme(eid=eid, scheme=scheme)
        logger.debug(f'Found agent location scheme message for eid {eid}: {loc_scheme_msg}')
        msgs.extend(loc_scheme_msg if loc_scheme_msg else bytearray())
        # Get the endpoint role message for the agent
        end_role_msg = hab.loadEndRole(cid=aid, eid=eid, role=erole)
        logger.debug(f'Found agent endpoint role message for eid {eid}: {end_role_msg}')
        msgs.extend(end_role_msg if end_role_msg else bytearray())
    return msgs


def get_mailbox_loc_scheme_endrole_bytes(hab: habbing.Hab, aid: str, scheme: str = '') -> bytearray:
    """Gets the mailbox location scheme and endpoint role records from the local hab database as a bytearray."""
    msgs = bytearray()
    for (_, erole, eid), _ in hab.db.ends.getItemIter(keys=(aid, kering.Roles.mailbox)):
        # Get the location scheme message for the mailbox
        loc_scheme_msg = hab.loadLocScheme(eid=eid)
        logger.debug(f'Found mailbox location scheme message for eid {eid}: {loc_scheme_msg}')
        msgs.extend(loc_scheme_msg if loc_scheme_msg else bytearray())
        # Get the endpoint role message for the mailbox
        end_role_msg = hab.loadEndRole(cid=aid, eid=eid, role=erole)
        logger.debug(f'Found mailbox endpoint role message for eid {eid}: {end_role_msg}')
        msgs.extend(end_role_msg if end_role_msg else bytearray())
    return msgs


def gen_loc_schemes_cesr(hab: habbing.Hab, aid: str, role: str = None, scheme='') -> bytearray:
    """
    Generates a CESR stream of all location scheme record reply 'rpy' messages for a given AID based on
    the witness location scheme and endpoint role records in the local Hab's database.

    Returns:
        bytearray: CESR stream of location scheme and endpoint role records for the given AID and role.

    Parameters:
        hab (habbing.Hab): The local Hab to use for generating the CESR stream.
        aid (str): The AID prefix to retrieve the location schemes for.
        role (str): The role of the endpoint, e.g., witness, agent, mailbox. Defaults to None.
        scheme (str): The scheme to filter the location schemes by. Defaults to an empty string.
    """
    kever = hab.kevers[aid]
    msgs = bytearray()
    # Get witness location schemes and endpoint roles
    if not role or role == kering.Roles.witness:
        msgs.extend(get_witness_loc_scheme_bytes(hab, kever.wits, scheme=scheme))
    # Get agent and mailbox location schemes and endpoint roles
    if not role or role == kering.Roles.agent:  # in preparation for working with KERIA agents
        msgs.extend(get_agent_loc_scheme_bytes(hab, aid, scheme=scheme))
    # Get mailbox location schemes and endpoint roles
    if not role or role == kering.Roles.mailbox:
        msgs.extend(get_mailbox_loc_scheme_endrole_bytes(hab, aid, scheme=scheme))
    return msgs


def make_did_json_path(output_dir: str, aid: str):
    """Create the directory (and any intermediate directories in the given path) if it doesn't already exist"""
    dd_dir_path = os.path.join(output_dir, aid)
    if not os.path.exists(dd_dir_path):
        os.makedirs(dd_dir_path)
    return dd_dir_path


def write_did_json_file(dd_dir_path: str, diddoc: dict, meta: bool = False):
    """save did.json to a file at output_dir/{aid}/{AID}.json"""
    dd_file_path = os.path.join(dd_dir_path, f'{ends.DID_JSON}')
    with open(dd_file_path, 'w') as ddf:
        json.dump(didding.to_did_web(diddoc, meta), ddf)


def generate_artifacts(hby: Habery, rgy: Regery, did: str, meta: bool = False, output_dir: str = '.'):
    domain, port, path, aid, query = didding.parse_did_webs(did)

    # generate did doc
    try:
        did_json = didding.generate_did_doc(hby, rgy, did=did, aid=aid, meta=meta)
    except UnknownAID as e:
        logger.error(f'Failed to generate DID document for {did}: {e}')
        raise e
    # Create the directory (and any intermediate directories in the given path) if it doesn't already exist
    dd_dir_path = make_did_json_path(output_dir, aid)
    write_did_json_file(dd_dir_path, did_json, meta)

    logger.info(f'Generating CESR event stream data from local Habery keystore')
    hab = hby.habs[aid]
    reger = rgy.reger
    keri_cesr = bytearray()
    keri_cesr.extend(gen_kel_cesr(hab, aid))  # add KEL CESR stream
    keri_cesr.extend(gen_loc_schemes_cesr(hab, aid))  # add witness location schemes
    keri_cesr.extend(gen_des_aliases_cesr(hab, reger, aid))  # add designated aliases TELs and ACDCs
    write_keri_cesr_file(output_dir, aid, keri_cesr)

    return did_json, keri_cesr


def dyn_artifact_svr_doers(
    hby, rgy, alias: str, http_port, did_path=None, meta=False, keypath=None, certpath=None, cafilepath=None
):
    """
    Parameters:
        hby (habbing.Habery): identifier database environment
        rgy (credentialing.Regery): Doer for the identifier database environment
        alias (str): alias for the KERI AID to dynamically generate and serve did:webs and did:keri artifacts for.
        http_port (int): external port to listen on for HTTP messages
        meta (bool): whether to include metadata in the DID document, default is False
        did_path (str): path segment of the did:webs URL to host the did:webs artifacts on, disabled if None
        keypath (str | None): path to the TLS private key file, default is None (disabled)
        certpath (str | None): path to the TLS certificate file, default is None (disabled)
        cafilepath (str | None): path to the CA certificate file, default is None (disabled)
    Returns:
        list: list of Doers to run in the Tymist
    """
    doers = []
    app = resolving.falcon_app()
    webbing.load_endpoints(app, hby=hby, rgy=rgy, did_path=did_path, meta=meta)
    voodoers = vgate.setup(hby=hby, alias=alias)
    server = resolving.tls_falcon_server(app, http_port, keypath, certpath, cafilepath)
    http_server_doer = http.ServerDoer(server=server)
    doers.extend([http_server_doer])
    doers += voodoers
    return doers
