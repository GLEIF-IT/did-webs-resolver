# -*- encoding: utf-8 -*-
"""
dws.core.didding module

"""

import itertools
import json
import math
import re
import urllib.parse
from base64 import urlsafe_b64encode
from functools import reduce

from keri import kering
from keri.app import habbing
from keri.core import coring
from keri.core.eventing import Kever, Kevery
from keri.db.basing import Baser
from keri.help import helping
from keri.vdr import credentialing

from dws import DidWebsError, UnknownAID, log_name, ogler
from dws.core import habs, oobiing

logger = ogler.getLogger(log_name)

DID_KERI_RE = re.compile(
    pattern=r'\Adid:keri:'
    r'(?:(?P<aid>[^:?]+))'
    r'(?P<query>\?.*)?\Z',
    flags=re.IGNORECASE,
)
DID_WEBS_RE = re.compile(
    pattern=r'\Adid:web(s)?:'
    r'(?P<domain>[^%:]+)'
    r'(?:%3a(?P<port>\d+))?'
    r'(?::(?P<path>.+?))?'
    r'(?::(?P<aid>[^:?]+))'
    r'(?P<query>\?.*)?\Z',
    flags=re.IGNORECASE,
)
DID_WEBS_UNENCODED_PORT_RE = re.compile(
    pattern=r'\Adid:web(s)?:'
    r'(?P<domain>[^%:]+)'
    r'(?::(?P<port>\d+))?'
    r'(?::(?P<path>.+?))?'
    r'(?::(?P<aid>[^:?]+))'
    r'(?P<query>\?.*)?\Z',
    flags=re.IGNORECASE,
)

DID_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DID_TIME_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')

DES_ALIASES_SCHEMA = 'EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5'

DID_RES_META_FIELD = 'didResolutionMetadata'
DD_META_FIELD = 'didDocumentMetadata'
DD_FIELD = 'didDocument'
VMETH_FIELD = 'verificationMethod'


def parse_did_keri(did):
    """
    Parse a did:keri DID with regex to return the AID

    Returns:
        str: AID extracted from the did:keri DID
    """
    match = DID_KERI_RE.match(did)
    if match is None:
        raise ValueError(f'{did} is not a valid did:keri DID')

    aid = match.group('aid')
    query = match.group('query')

    try:
        _ = coring.Prefixer(qb64=aid)
    except Exception as e:
        raise ValueError(f'{aid} is an invalid AID')

    return aid, query


def parse_did_webs(did: str):
    """
    Parse a did:webs DID with regex to return the domain, port, path, and AID

    Returns:
        (str, str, str, str, str): domain, port, path, AID
    """
    match = DID_WEBS_RE.match(did)
    if match is None:
        raise ValueError(f'{did} is not a valid did:web(s) DID')

    domain, port, path, aid, query = match.group('domain', 'port', 'path', 'aid', 'query')

    try:
        _ = coring.Prefixer(qb64=aid)
    except Exception as e:
        raise ValueError(f'{aid} is an invalid AID')

    return domain, port, path, aid, query


def parse_query_string(query: str) -> dict:
    if not query or query == '?':
        return {}
    query = query.lstrip('?')
    parsed = urllib.parse.parse_qs(query)
    result = {}
    for key, values in parsed.items():
        value = values[0] if values else ''
        if value.lower() == 'true':
            result[key] = True
        elif value.lower() == 'false':
            result[key] = False
        else:
            try:
                result[key] = int(value)
            except ValueError:
                result[key] = value
    return result


def re_encode_invalid_did_webs(did: str):
    match = DID_WEBS_UNENCODED_PORT_RE.match(did)
    if match is None:
        match = DID_WEBS_RE.match(did)
        if match is not None:
            return did  # already encoded correctly
        raise ValueError(f'{did} is not an invalidly encoded did:web(s) DID')

    domain, port, path, aid, query = match.group('domain', 'port', 'path', 'aid', 'query')

    if aid:
        try:
            _ = coring.Prefixer(qb64=aid)
        except Exception as e:
            raise ValueError(f'{aid} is an invalid AID')

    encoded = f'did:webs:{domain}'
    if port:
        encoded += f'%3A{port}'
    if path:
        encoded += f':{path}'
    if aid:
        encoded += f':{aid}'
    if query:
        encoded += f'{query}'
    return encoded


def requote(encoded_did: str):
    """
    Due to compliance with PEP3333 in PR 38 to HIO (https://github.com/ioflo/hio/pull/38) the
    WSGI container for the Falcon server URL encodes the URL path which means that  the did:webs and did:keri
    DIDs must be URL decoded, broken apart, and then re-encoded to ensure they are valid for resolution.

    This specific attribute of the WSGI environment uses urllib.parse.quote to encode the path, so we need to decode it
    environ['PATH_INFO'] = quote(requestant.path)
    """
    if encoded_did.lower().startswith('did%3awebs') or encoded_did.lower().startswith('did%3akeri'):
        # The DID is incorrectly fully URL-encoded, happens with some WSGI servers, so must decode and re-encode it
        # this happens in Falcon
        did = urllib.parse.unquote(encoded_did)
        did = re_encode_invalid_did(did)
        return did
    else:
        return encoded_did


def re_encode_invalid_did(did: str):
    """
    Parse a did:webs DID with regex to return the domain, port, path, and AID.
    This version does not URL-encode the port.

    Returns:
        (str, str, str, str): domain, port, path, AID
    """
    if did.startswith('did:webs:'):
        return re_encode_invalid_did_webs(did)
    elif did.startswith('did:keri:'):  # included for completion's sake and uniformity when parsing DIDs
        aid, query = parse_did_keri(did)
        return f'did:keri:{aid}{query if query else ""}'
    else:
        raise ValueError(f'{did} is not a valid did:webs or did:keri DID')


def generate_json_web_key_vm(pubkey, did, kid, x):
    """
    Generate a JSON Web Key (JWK) verification method for a given public key.

    Parameters:
        pubkey (str): The public key identifier (e.g., a Verfer's qb64).
        did (str): The DID to associate with the verification method.
        kid (str): The key ID for the JWK.
        x (str): The base64url-encoded public key value.
    """
    return dict(
        id=f'#{pubkey}',
        type='JsonWebKey',
        controller=strip_query(did),
        publicKeyJwk=dict(kid=f'{kid}', kty='OKP', crv='Ed25519', x=f'{x}'),
    )


def strip_query(did: str):
    if did.startswith('did:webs:') or did.startswith('did:web:'):
        domain, port, path, aid, query = parse_did_webs(did=did)
        if query is None or query == '':
            return did
        return f'did:webs:{domain}%3A{port}:{path}:{aid}'
    else:
        return did  # for did:keri


def generate_verification_methods(verfers, thold, did, aid):
    """
    Generate a verification method for each public key (Verfer) from the source key state.
    Multiple verfers implies a multisig DID, a single verfer implies a single key DID.

    Parameters:
        verfers (list[core.Verfer]): A list of Verfer instances representing the public keys.
        thold (int or list): The signing threshold, possibly multisig. If an integer, it indicates a simple multisig DID.
        did (str): The DID to associate with the verification methods.
        aid (str): The AID to associate with the verification methods.

    Returns:
        list: A list of verification methods in the format required for a DID document.
    """
    # for each public key (Verfer) in the Kever, generate a verification method
    vms = []
    for idx, verfer in enumerate(verfers):
        kid = verfer.qb64
        x = urlsafe_b64encode(verfer.raw).rstrip(b'=').decode('utf-8')
        vms.append(generate_json_web_key_vm(kid, did, kid, x))

    # Handle multi-key or multisig AID cases
    if isinstance(thold, int):
        if thold > 1:
            conditions = [vm.get('id') for vm in vms]
            vms.append(generate_threshold_proof2022(aid, did, thold, conditions))
    elif isinstance(thold, list):
        vms.append(generate_weighted_threshold_proof(thold, verfers, vms, did, aid))
    return vms


def generate_threshold_proof2022(aid, did, thold, conditions):
    """
    Generate a ConditionalProof2022 verification method for a multisig DID.

    Parameters:
        aid (str): The controlling AID to associate with the conditional proof.
        did (str): The DID to associate with the conditional proof.
        thold (int): The multisig signing threshold.
        conditions (list): List of condition verification method IDs.

    Returns:
        dict: A ConditionalProof2022 verification method
    """
    return dict(
        id=f'#{aid}',
        type='ConditionalProof2022',
        controller=strip_query(did),
        threshold=thold,
        conditionThreshold=conditions,
    )


def generate_weighted_threshold_proof2022(aid, did, threshold, conditions):
    """
    Generate a ConditionalProof2022 verification method for a multisig DID with weighted conditions.

    Parameters:
        aid (str): The controlling AID to associate with the conditional proof.
        did (str): The DID to associate with the conditional proof.
        threshold (float): The multisig signing threshold.
        conditions (list): List of condition verification method IDs with weights.

    Returns:
        dict: A ConditionalProof2022 verification method with weighted conditions.
    """
    return dict(
        id=f'#{aid}',
        type='ConditionalProof2022',
        controller=strip_query(did),
        threshold=threshold,
        conditionWeightedThreshold=conditions,
    )


def generate_weighted_threshold_proof(thold, verfers, vms, did, aid):
    """
    Compute the weighted threshold proof for a multisig DID based on the provided fraction threshold
     weights and public keys (Verfers).

    Parameters:
        thold (list): A list of fractions representing the threshold weights.
        verfers (list[core.Verfer]): A list of Verfer instances representing the public keys.
        vms (list): A list of verification methods already generated for the public keys.
        did (str): The DID to associate with the weighted threshold proof.
        aid (str): The controlling AID to associate with the weighted threshold proof.
    """
    lcd = int(math.lcm(*[fr.denominator for fr in thold[0]]))
    threshold = float(lcd / 2)
    numerators = [int(fr.numerator * lcd / fr.denominator) for fr in thold[0]]
    conditions = []
    for idx, verfer in enumerate(verfers):
        conditions.append(dict(condition=vms[idx]['id'], weight=numerators[idx]))
    return generate_weighted_threshold_proof2022(aid, did, threshold, conditions)


def gen_did_document(did, verification_methods, service_endpoints, also_known_as):
    """
    Generate a basic DID document structure.

    DID document properties:
    - id: The DID itself
    - verificationMethod: A list of verification methods derived from the Kever's verfers
    - service: A list of service endpoints derived from the hab's fetchRoleUrls and fetchWitnessUrls methods
    - alsoKnownAs: A list of designated aliases for the AID

    Parameters:
        did (str): The DID to include in the document.
        verification_methods (list): A list of verification methods.
        service_endpoints (list): A list of service endpoints.
        also_known_as (list): A list of alternative identifiers.

    Returns:
        dict: A basic DID document structure.
    """
    return dict(id=did, verificationMethod=verification_methods, service=service_endpoints, alsoKnownAs=also_known_as)


def gen_did_resolution_result(did_doc, witness_list, seq_no, equivalent_ids):
    """
    Generate a DID resolution result structure.

    Parameters:
        did_doc (dict): The DID document to include in the resolution result.
        witness_list (list): A list of witnesses AIDs
        seq_no (int): The sequence number of the latest KEL event for the AID generating the DID document.
        equivalent_ids (list): A list of equivalent IDs.

    Returns:
        dict: A DID resolution result structure containing the DID document, resolution metadata, and document metadata.
    """
    return dict(
        didDocument=did_doc,
        didResolutionMetadata=dict(contentType='application/did+json', retrieved=helping.nowUTC().strftime(DID_TIME_FORMAT)),
        didDocumentMetadata=dict(
            witnesses=witness_list,
            versionId=f'{seq_no}',
            equivalentId=equivalent_ids,
        ),
    )


def get_witness_list(baser: Baser, kever: Kever):
    witness_list = []
    for idx, eid in enumerate(kever.wits):
        for (tid, scheme), loc in baser.locs.getItemIter(keys=(eid,)):
            witness_list.append(dict(idx=str(idx), scheme=scheme, url=loc.url))
    return witness_list


def get_equiv_aka_ids(did: str, aid: str, hby: habbing.Habery, rgy: credentialing.Regery):
    equiv_ids = []
    aka_ids = []
    if did.startswith('did:webs') or did.startswith('did:web'):
        for s in gen_designated_aliases(hby, rgy, aid):
            if s.startswith('did:webs'):
                equiv_ids.append(s)
            aka_ids.append(s)
    return equiv_ids, aka_ids


def generate_did_doc(hby: habbing.Habery, rgy: credentialing.Regery, did, aid, meta=False):
    """
    Generates a DID document for the given DID and AID.

    The DID document will have one of the following structures:
    - If `meta` is True:
      - didDocument: The DID document itself (see genDidDocument for structure)
      - didResolutionMetadata: Metadata about the DID resolution process
      - didDocumentMetadata: Additional metadata about the DID document
    if `meta` is False:
    - didDocument: The DID document itself (see genDidDocument for structure)

    Parameters:
        hby (habbing.Habery): The habery instance containing the necessary data.
        rgy (credentialing.Regery): The Regery instance for the credential and registry data.
        did (str): The DID to generate the document for.
        aid (str): The AID associated with the DID.
        meta (bool, optional): If True, include metadata in the response. Defaults to False.

    Returns:
        dict of DID document structure; DID document, metadata and resolution metadata or just the DID document
    """
    if did.startswith('did:webs') or did.startswith('did:web'):
        _domain, _port, _path, parsed_aid, _query = parse_did_webs(did=did)
        if (did and aid) and parsed_aid != aid:
            raise ValueError(f'{did} does not contain AID {aid}')
    if did.startswith('did:keri'):
        aid, query = parse_did_keri(did=did)
        did = f'did:keri:{aid}'  # strip of query for did doc generation as is not needed. OOBI should be resolved by now.
    logger.debug(f'Generating DID document for\n\t{did}\nwith aid\n\t{aid}\nand metadata\n\t{meta}')

    hab: habbing.Hab | None = None
    if aid in hby.habs:
        hab = hby.habs[aid]

    kever = None
    if aid in hby.kevers:
        kever = hby.kevers[aid]
    else:
        raise UnknownAID(aid, did)

    verification_methods = generate_verification_methods(kever.verfers, kever.tholder.thold, did, aid)
    service_endpoints = gen_service_endpoints(hby, hab, kever, aid)
    equiv_ids, aka_ids = get_equiv_aka_ids(did, aid, hby, rgy)

    did_doc = gen_did_document(did, verification_methods, service_endpoints, aka_ids)
    if meta is True:
        return gen_did_resolution_result(
            did_doc=did_doc,
            witness_list=get_witness_list(hby.db, kever),
            seq_no=kever.sner.num,
            equivalent_ids=equiv_ids,
        )
    else:
        return did_doc


def to_did_web(diddoc: dict, meta=False):
    """
    Convert DID schemes for did.json DID document from did:webs did:web.

    If metadata is present then the didDocument field is replaced with the converted DID document.
    """
    if not diddoc:
        raise DidWebsError('Cannot convert empty diddoc to did:web')
    if meta:
        replaced = diddoc_to_did_web(diddoc[DD_FIELD])
        diddoc[DD_FIELD] = replaced
        return diddoc
    else:
        return diddoc_to_did_web(diddoc)


def diddoc_to_did_web(diddoc: dict):
    """Converts all did:webs DIDs in the 'id' property and verification method 'controller' properties to did:web"""
    diddoc['id'] = diddoc['id'].replace('did:webs', 'did:web')
    for verificationMethod in diddoc['verificationMethod']:
        verificationMethod['controller'] = verificationMethod['controller'].replace('did:webs', 'did:web')
    return diddoc


def diddoc_to_did_webs(diddoc: dict):
    """Converts all did:web DIDs in the 'id' property and verification method 'controller' properties to did:webs"""
    # Apply the replacement only if necessary
    if 'did:web' in diddoc['id'] and 'did:webs' not in diddoc['id']:
        diddoc['id'] = diddoc['id'].replace('did:web', 'did:webs')
        logger.debug(f'Updated id in fromDidWeb: {diddoc["id"]}')

    for verificationMethod in diddoc['verificationMethod']:
        if 'did:web' in verificationMethod['controller'] and 'did:webs' not in verificationMethod['controller']:
            verificationMethod['controller'] = verificationMethod['controller'].replace('did:web', 'did:webs')
            logger.debug(f'Updated controller in fromDidWeb: {verificationMethod["controller"]}')

    return diddoc


def from_did_web(did_json: dict, meta: bool = False):
    """
    Convert DID schemes in did.json DID document from did:web to did:webs.

    If metadata is present then the didDocument field is replaced with the converted DID document.
    """
    # Log the original state of the DID and controller
    if meta and DD_FIELD not in did_json:
        logger.debug(f'DID resolution metadata did not contain {DD_FIELD}:\n{json.dumps(did_json, indent=2)}')
        raise ValueError(f"Expected '{DD_FIELD}' in did.json when indicating resolution metadata in use.")
    diddoc = did_json[DD_FIELD] if meta else did_json
    initial_controller = diddoc['verificationMethod'][0]['controller']
    # id = diddoc["id"] if not meta else did_json[DD_FIELD]["id"]
    if not meta:
        converted_did_doc = diddoc_to_did_webs(diddoc)
        diddoc = converted_did_doc
    else:
        initial_controller = diddoc['verificationMethod'][0]['controller']
        converted_did_doc = diddoc_to_did_webs(diddoc)
        did_json[DD_FIELD] = converted_did_doc
        diddoc = did_json
    return diddoc


def extract_desg_alias_from_cred(cred: dict) -> str | None:
    """
    Extract the 'ids' property from the designated aliases ACDC credential.
    This is specific to the current designated aliases schema.
    """
    sad = cred['sad']
    status = cred['status']
    if status['et'] == 'iss' or status['et'] == 'bis':
        return sad['a']['ids']
    return None


def gen_designated_aliases(hby: habbing.Habery, rgy: credentialing.Regery, aid: str, schema: str = DES_ALIASES_SCHEMA):
    """
    Searches the entire Regery database for non-revoked, self-attested designated alias ACDCs by schema and
    returns a list of designated alias IDs using their `a.ids` field.

    Parameters:
        hby (habbing.Habery): The Habery instance containing the Regery.
        rgy (credentialing.Regery): The Regery instance for credential and registry data.
        aid (str): The AID prefix to retrieve the ACDCs for.
        schema (str): The schema to use to select the target ACDC from the local registry. Default is DES_ALIASES_SCHEMA.

    Returns:
        list: A list of designated alias IDs (a.ids) from self-attested ACDCs.
    """
    da_ids = []
    saids = rgy.reger.issus.get(keys=aid)
    scads = rgy.reger.schms.get(keys=schema)  # get credentials by schema
    # self-attested schema, and scehma is designated aliases
    saids = [saider for saider in saids if saider.qb64 in [saider.qb64 for saider in scads]]
    if not saids:
        return da_ids
    if aid in hby.habs:
        # if aid is in a hab in the local habery then get self issued ACDCS
        creds = rgy.reger.cloneCreds(saids, hby.habs[aid].db)
    else:
        # otherwise if AID is just in kevers and is non-local, get creds issued by the AID in the DID
        creds = rgy.reger.cloneCreds(saids, hby.db)
    da_ids = [extract_desg_alias_from_cred(cred) for _, cred in enumerate(creds)]
    return list(itertools.chain.from_iterable(da_ids))


def gen_service_endpoints(hby: habbing.Habery, hab: habbing.Hab, kever: Kever, aid: str):
    """Generate service endpoints including both witness and delegation service endpoints."""
    serv_ends = []
    # TODO: move Location Scheme and Endpoint Role Authorization to dedicated function
    if hab and hasattr(hab, 'fetchRoleUrls'):
        ends = hab.fetchRoleUrls(cid=aid)
        serv_ends.extend(add_ends(ends))
        ends = hab.fetchWitnessUrls(cid=aid)
        serv_ends.extend(add_ends(ends))
    else:
        ends = habs.get_role_urls(baser=hby.db, kever=kever)
        serv_ends.extend(add_ends(ends))

    if hasattr(hab, 'delpre') and hab.delpre is not None:
        del_serv_end = gen_delegation_service(hby=hby, pre=hab.pre, delpre=hab.delpre)
        serv_ends.extend(del_serv_end)
    return serv_ends


def add_ends(ends):
    def process_role(role):
        return reduce(lambda rs, eids: rs + process_eids(eids, role), ends.getall(role), [])

    def process_eids(eids, role):
        return reduce(lambda es, eid: es + process_eid(eid, eids[eid], role), eids, [])

    def process_eid(eid, val, role):
        v = dict(id=f'#{eid}/{role}', type=role, serviceEndpoint={proto: f'{host}' for proto, host in val.items()})
        return [v]

    return reduce(lambda emit, role: emit + process_role(role), ends, [])


def gen_delegation_service(hby: habbing.Habery, pre: str, delpre: str):
    """Returns an array of delegation service endpoints for the delegator AID."""
    seal = dict(i=pre, s='0', d=pre)
    dserder = hby.db.fetchLastSealingEventByEventSeal(pre=delpre, seal=seal)
    approval_evt_digest = dserder.sad['a'][0]['d']
    del_oobi = oobiing.get_resolved_oobi(hby=hby, pre=delpre)
    if del_oobi is None:
        logger.error(f'No resolved OOBI found for delegate AID {delpre} for delegator AID {pre}')
        return []
    return [dict(id=approval_evt_digest, type='DelegatorOOBI', serviceEndpoint=del_oobi)]
