# -*- encoding: utf-8 -*-
"""
dkr.core.didding module

"""

import itertools
import json
import math
import re
from base64 import urlsafe_b64encode
from functools import reduce

from keri.app import habbing, oobiing
from keri.core import coring
from keri.help import helping
from keri.vdr import credentialing, verifying

from dkr import log_name, ogler

logger = ogler.getLogger(log_name)

DID_KERI_RE = re.compile(r'\Adid:keri:(?P<aid>[^:]+)\Z', re.IGNORECASE)
DID_WEBS_RE = re.compile(
    r'\Adid:web(s)?:(?P<domain>[^%:]+)(?:%3a(?P<port>\d+))?(?::(?P<path>.+?))?(?::(?P<aid>[^:]+))\Z', re.IGNORECASE
)

DID_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DID_TIME_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')

DES_ALIASES_SCHEMA = 'EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5'

DID_RES_META_FIELD = 'didResolutionMetadata'
DD_META_FIELD = 'didDocumentMetadata'
DD_FIELD = 'didDocument'
VMETH_FIELD = 'verificationMethod'


def parseDIDKeri(did):
    """
    Parse a did:keri DID with regex to return the AID

    Returns:
        str: AID extracted from the did:keri DID
    """
    match = DID_KERI_RE.match(did)
    if match is None:
        raise ValueError(f'{did} is not a valid did:keri DID')

    aid = match.group('aid')

    try:
        _ = coring.Prefixer(qb64=aid)
    except Exception as e:
        raise ValueError(f'{aid} is an invalid AID')

    return aid


def parseDIDWebs(did):
    """
    Parse a did:webs DID with regex to return the domain, port, path, and AID

    Returns:
        (str, str, str, str): domain, port, path, AID
    """
    match = DID_WEBS_RE.match(did)
    if match is None:
        raise ValueError(f'{did} is not a valid did:web(s) DID')

    domain, port, path, aid = match.group('domain', 'port', 'path', 'aid')

    try:
        _ = coring.Prefixer(qb64=aid)
    except Exception as e:
        raise ValueError(f'{aid} is an invalid AID')

    return domain, port, path, aid


def generateJsonWebKeyVM(pubkey, did, kid, x):
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
        controller=did,
        publicKeyJwk=dict(kid=f'{kid}', kty='OKP', crv='Ed25519', x=f'{x}'),
    )


def generateVerificationMethods(verfers, thold, did, aid):
    """
    Generate a verification method for each public key (Verfer) from the source key state.
    Multiple verfers implies a multisig DID, a single verfer implies a single key DID.

    Parameters:
        kever (Kever): The Kever instance containing the verfers.
        did (str): The DID to associate with the verification methods.

    Returns:
        list: A list of verification methods in the format required for a DID document.
    """
    # for each public key (Verfer) in the Kever, generate a verification method
    vms = []
    for idx, verfer in enumerate(verfers):
        kid = verfer.qb64
        x = urlsafe_b64encode(verfer.raw).rstrip(b'=').decode('utf-8')
        vms.append(generateJsonWebKeyVM(kid, did, kid, x))

    # Handle multi-key or multisig AID cases
    if isinstance(thold, int):
        if thold > 1:
            conditions = [vm.get('id') for vm in vms]
            vms.append(generateThresholdProof2022(aid, did, thold, conditions))
    elif isinstance(thold, list):
        vms.append(generateWeightedThresholdProof(thold, verfers, vms, did, aid))
    return vms


def generateThresholdProof2022(aid, did, thold, conditions):
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
        controller=did,
        threshold=thold,
        conditionThreshold=conditions,
    )


def generateWeightedThresholdProof2022(aid, did, threshold, conditions):
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
        controller=did,
        threshold=threshold,
        conditionWeightedThreshold=conditions,
    )


def generateWeightedThresholdProof(thold, verfers, vms, did, aid):
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
    return generateWeightedThresholdProof2022(aid, did, threshold, conditions)


def genDidDocument(did, vms, serviceEndpoints, alsoKnownAs):
    """
    Generate a basic DID document structure.

    DID document properties:
    - id: The DID itself
    - verificationMethod: A list of verification methods derived from the Kever's verfers
    - service: A list of service endpoints derived from the hab's fetchRoleUrls and fetchWitnessUrls methods
    - alsoKnownAs: A list of designated aliases for the AID

    Parameters:
        did (str): The DID to include in the document.
        vms (list): A list of verification methods.
        serviceEndpoints (list): A list of service endpoints.
        alsoKnownAs (list): A list of alternative identifiers.

    Returns:
        dict: A basic DID document structure.
    """
    return dict(id=did, verificationMethod=vms, service=serviceEndpoints, alsoKnownAs=alsoKnownAs)


def genDidResolutionResult(witnessList, seqNo, equivalentIds, did, vms, servEnds, akaIds):
    """
    Generate a DID resolution result structure.

    Parameters:
        witnessList (list): A list of witnesses AIDs
        seqNo (int): The sequence number of the latest KEL event for the AID generating the DID document.
        equivalentIds (list): A list of equivalent IDs.
        did (str): The DID to include in the document.
        vms (list): A list of verification methods.
        servEnds (list): A list of service endpoints.
        akaIds (list): A list of alternative identifiers.

    Returns:
        dict: A DID resolution result structure containing the DID document, resolution metadata, and document metadata.
    """
    return dict(
        didDocument=genDidDocument(did, vms, servEnds, akaIds),
        didResolutionMetadata=dict(contentType='application/did+json', retrieved=helping.nowUTC().strftime(DID_TIME_FORMAT)),
        didDocumentMetadata=dict(
            witnesses=witnessList,
            versionId=f'{seqNo}',
            equivalentId=equivalentIds,
        ),
    )


def generateDIDDoc(hby: habbing.Habery, did, aid, oobi=None, meta=False, reg_name=None):
    """
    Generates a DID document for the given DID and AID using the provided OOBI and metadata.

    The DID document will have one of the following structures:
    - If `meta` is True:
      - didDocument: The DID document itself (see genDidDocument for structure)
      - didResolutionMetadata: Metadata about the DID resolution process
      - didDocumentMetadata: Additional metadata about the DID document
    if `meta` is False:
    - didDocument: The DID document itself (see genDidDocument for structure)

    Parameters:
        hby (habbing.Habery): The habery instance containing the necessary data.
        did (str): The DID to generate the document for.
        aid (str): The AID associated with the DID.
        oobi (str, optional): An OOBI identifier to resolve. Defaults to None.
        meta (bool, optional): If True, include metadata in the response. Defaults to False.
        reg_name (str, optional): The name of the registry for credentials. Defaults to None.

    Returns:
        dict of DID document structure; DID document, metadata and resolution metadata or just the DID document
    """
    if (did and aid) and not did.endswith(aid):
        raise ValueError(f'{did} does not end with {aid}')
    logger.debug(
        f'Generating DID document for\n\t{did}'
        f'\nwith aid\n\t{aid}'
        f'\nusing oobi\n\t{oobi}'
        f'\nand metadata\n\t{meta}'
        f'\nregistry name for creds\n\t{reg_name}'
    )

    hab = None
    if aid in hby.habs:
        hab = hby.habs[aid]

    if oobi is not None:
        obr = hby.db.roobi.get(keys=(oobi,))
        if obr is None or obr.state == oobiing.Result.failed:
            msg = dict(msg=f'OOBI resolution for did {did} failed.')
            data = json.dumps(msg)
            return data.encode('utf-8')

    kever = None
    if aid in hby.kevers:
        kever = hby.kevers[aid]
    else:
        raise ValueError(f'unknown {aid}')

    vms = generateVerificationMethods(kever.verfers, kever.tholder.thold, did, aid)

    witnessList = []
    for idx, eid in enumerate(kever.wits):
        for (tid, scheme), loc in hby.db.locs.getItemIter(keys=(eid,)):
            witnessList.append(dict(idx=idx, scheme=scheme, url=loc.url))

    servEnds = []
    if hab and hasattr(hab, 'fetchRoleUrls'):
        ends = hab.fetchRoleUrls(cid=aid)
        servEnds.extend(addEnds(ends))
        ends = hab.fetchWitnessUrls(cid=aid)
        servEnds.extend(addEnds(ends))

    equivIds = []
    akaIds = []
    for s in designatedAliases(hby, aid, reg_name=reg_name):
        if s.startswith('did:webs'):
            equivIds.append(s)
        akaIds.append(s)

    if meta is True:
        return genDidResolutionResult(
            witnessList=witnessList,
            seqNo=kever.sner.num,
            equivalentIds=equivIds,
            did=did,
            vms=vms,
            servEnds=servEnds,
            akaIds=akaIds,
        )
    else:
        return genDidDocument(did, vms, servEnds, akaIds)


def toDidWeb(diddoc):
    if diddoc:
        diddoc['id'] = diddoc['id'].replace('did:webs', 'did:web')
        for verificationMethod in diddoc['verificationMethod']:
            verificationMethod['controller'] = verificationMethod['controller'].replace('did:webs', 'did:web')
        return diddoc


def fromDidWeb(diddoc):
    # Log the original state of the DID and controller
    logger.debug(f'fromDidWeb() called with id: {diddoc["id"]}')
    initial_controller = diddoc['verificationMethod'][0]['controller']
    logger.debug(f'Initial controller in fromDidWeb: {initial_controller}')

    # Apply the replacement only if necessary
    if 'did:web' in diddoc['id'] and 'did:webs' not in diddoc['id']:
        diddoc['id'] = diddoc['id'].replace('did:web', 'did:webs')
        logger.debug(f'Updated id in fromDidWeb: {diddoc["id"]}')

    for verificationMethod in diddoc['verificationMethod']:
        if 'did:web' in verificationMethod['controller'] and 'did:webs' not in verificationMethod['controller']:
            verificationMethod['controller'] = verificationMethod['controller'].replace('did:web', 'did:webs')
            logger.debug(f'Updated controller in fromDidWeb: {verificationMethod["controller"]}')

    return diddoc


def designatedAliases(hby: habbing.Habery, aid: str, reg_name: str = None):
    """
    Returns the credentialer for the des-aliases schema, or None if it doesn't exist.
    """
    da_ids = []
    if aid in hby.habs:
        if reg_name is None:
            reg_name = hby.habs[aid].name
        rgy = credentialing.Regery(hby=hby, name=reg_name)
        vry = verifying.Verifier(hby=hby, reger=rgy.reger)

        saids = rgy.reger.issus.get(keys=aid)
        scads = rgy.reger.schms.get(keys=DES_ALIASES_SCHEMA)
        # self-attested, there is no issuee, and schmea is designated aliases
        saids = [saider for saider in saids if saider.qb64 in [saider.qb64 for saider in scads]]

        creds = rgy.reger.cloneCreds(saids, hby.habs[aid].db)

        for idx, cred in enumerate(creds):
            sad = cred['sad']
            status = cred['status']
            if status['et'] == 'iss' or status['et'] == 'bis':
                da_ids.append(sad['a']['ids'])

    return list(itertools.chain.from_iterable(da_ids))


def addEnds(ends):
    def process_role(role):
        return reduce(lambda rs, eids: rs + process_eids(eids, role), ends.getall(role), [])

    def process_eids(eids, role):
        return reduce(lambda es, eid: es + process_eid(eid, eids[eid], role), eids, [])

    def process_eid(eid, val, role):
        v = dict(id=f'#{eid}/{role}', type=role, serviceEndpoint={proto: f'{host}' for proto, host in val.items()})
        return [v]

    return reduce(lambda emit, role: emit + process_role(role), ends, [])
