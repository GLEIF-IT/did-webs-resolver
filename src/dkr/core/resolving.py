# -*- encoding: utf-8 -*-
"""
dkr.core.serving module

"""

import json
import os
import queue

import falcon
import requests
from hio.base import doing
from hio.core import http
from keri.app import directing, habbing

from dkr import log_name, ogler
from dkr.app.cli.commands.did.keri.resolve import KeriResolver
from dkr.core import didding, ends

logger = ogler.getLogger(log_name)


def get_sources(did: str, resq: queue.Queue = None):
    logger.info(f'Parsing DID {did}')
    domain, port, path, aid = didding.parse_did_webs(did=did)

    opt_port = f':{port}' if port is not None else ''
    opt_path = f'/{path.replace(":", "/")}' if path is not None else ''
    base_url = f'http://{domain}{opt_port}{opt_path}/{aid}'

    # Load the did doc
    dd_url = f'{base_url}/{ends.DID_JSON}'
    logger.info(f'Loading DID Doc from {dd_url}')
    dd_res = load_url(dd_url, resq=resq)
    logger.debug(f'Got DID doc: {dd_res.content.decode("utf-8")}')

    # Load the KERI CESR
    kc_url = f'{base_url}/{ends.KERI_CESR}'
    logger.info(f'Loading KERI CESR from {kc_url}')
    kc_res = load_url(kc_url, resq=resq)
    logger.debug(f'Got KERI CESR: {kc_res.content.decode("utf-8")}')

    if resq is not None:
        resq.put(aid)
        resq.put(dd_res)
        resq.put(kc_res)
    return aid, dd_res, kc_res


def save_cesr(hby: habbing.Habery, kc_res: requests.Response, aid: str = None):
    logger.info('Saving KERI CESR to hby: %s', kc_res.content.decode('utf-8'))
    hby.psr.parse(ims=bytearray(kc_res.content))
    if aid:
        assert aid in hby.kevers, f'KERI CESR parsing failed, KERI AID {aid} not found in habery'


def compare_did_docs(
    hby: habbing.Habery, did: str, aid: str, meta: bool, dd_res: requests.Response, kc_res: requests.Response
):
    dd = didding.generate_did_doc(hby, did=did, aid=aid, oobi=None, meta=meta)
    if meta:
        dd[didding.DD_META_FIELD]['didDocUrl'] = dd_res.url
        dd[didding.DD_META_FIELD]['keriCesrUrl'] = kc_res.url

    dd_actual = didding.from_did_web(json.loads(dd_res.content.decode('utf-8')), meta)
    logger.debug(f'Got DID Doc: {dd_actual}')

    return dd, dd_actual


def error_resolution_response(meta: bool, error_message: str):
    """
    Generate an error response for DID resolution.
    """
    didresult = dict()
    didresult[didding.DD_FIELD] = None
    if didding.DID_RES_META_FIELD not in didresult:
        didresult[didding.DID_RES_META_FIELD] = dict()
    didresult[didding.DID_RES_META_FIELD]['error'] = 'notVerified'
    didresult[didding.DID_RES_META_FIELD]['errorMessage'] = error_message
    result = didresult
    return result


def verify(dd_expected: dict, dd_actual: dict, meta: bool = False) -> (bool, dict):
    """
    Verify the DID document against the KERI event stream.

    Returns:
         tuple(bool, dict): (verified, dd) where verified is a boolean indicating verification status
    """
    dd_exp = dd_expected
    if didding.DD_FIELD in dd_exp:
        dd_exp = dd_expected[didding.DD_FIELD]
    # TODO verify more than verificationMethod
    verified = _verify_did_docs(dd_exp[didding.VMETH_FIELD], dd_actual[didding.VMETH_FIELD])

    if verified:
        logger.info(f'DID document verified')
        return (True, dd_expected[didding.DD_FIELD]) if meta else (True, dd_expected)
    else:
        logger.info(f'DID document verification failed')
        return (
            False,
            error_resolution_response(
                meta=meta, error_message='The DID document could not be verified against the KERI event stream'
            ),
        )


def _verify_did_docs(expected, actual):
    # TODO determine what to do with BADA RUN things like services (witnesses) etc.
    if (
        expected != actual
    ):  # Python != and == perform a deep object value comparison; this is not reference equality, it is value equality
        differences = _compare_dicts(expected, actual)
        logger.error(f'Differences found in DID Doc verification: {differences}')
        return False
    else:
        return True


def _compare_dicts(expected, actual, path=''):
    """Recursively compare two dictionaries and return differences."""
    logger.error(f'Comparing dictionaries:\nexpected:\n{expected}\n \nand\n \nactual:\n{actual}')
    differences = []

    if isinstance(expected, dict):
        for k in expected.keys():
            # Construct current path
            current_path = f'{path}.{k}' if path else k
            logger.error(f'Comparing key {current_path}')

            # Key not present in the actual dictionary
            if k not in actual:
                differences.append((current_path, expected[k], None))
                logger.error(f'Key {current_path} not found in the actual dictionary')
                continue

            # If value in expected is a dictionary but not in actual
            if isinstance(expected[k], dict) and not isinstance(actual[k], dict):
                differences.append((current_path, expected[k], actual[k]))
                logger.error(f'{current_path} is a dictionary in expected, but not in actual')
                continue

            # If value in actual is a dictionary but not in expected
            if isinstance(actual[k], dict) and not isinstance(expected[k], dict):
                differences.append((current_path, expected[k], actual[k]))
                logger.error(f'{current_path} is a dictionary in actual, but not in expected')
                continue

            # If value is another dictionary, recurse
            if isinstance(expected[k], dict) and isinstance(actual[k], dict):
                differences.append(_compare_dicts(expected[k], actual[k], current_path))
            # Compare non-dict values
            elif expected[k] != actual[k]:
                differences.append((current_path, expected[k], actual[k]))
                logger.error(f'Different values for key {current_path}: {expected[k]} (expected) vs. {actual[k]} (actual)')

        if isinstance(actual, dict):
            # Check for keys in actual that are not present in expected
            for k in actual.keys():
                current_path = f'{path}.{k}' if path else k
                if k not in expected:
                    differences.append((current_path, None, actual[k]))
                    logger.error(f'Key {current_path} not found in the expected dictionary')
        else:
            differences.append((path, expected, None))
            logger.error(f'Expecting actual did document to contain dictionary {expected}')
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            differences.append((path, expected, actual))
            logger.error(f'Expected list {expected} and actual list {actual} are not the same length')
        else:
            for i in range(len(expected)):
                differences.append(_compare_dicts(expected[i], actual[i], path))
    else:
        if expected != actual:
            differences.append((path, expected, actual))
            logger.error(f'Different values for key {path}: {expected} (expected) vs. {actual} (actual)')
    return differences


def resolve(hby, did, meta=False, resq: queue.Queue = None):
    """Resolve a did:webs DID and returl the verification result."""
    aid, dd_res, kc_res = get_sources(did=did, resq=resq)
    save_cesr(hby=hby, kc_res=kc_res, aid=aid)
    dd, dd_actual = compare_did_docs(hby=hby, did=did, aid=aid, meta=meta, dd_res=dd_res, kc_res=kc_res)
    return verify(dd, dd_actual, meta=meta)


# # Test with the provided dictionaries
# expected_dict = {
#     'id': 'did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
#     'verificationMethod': [{'id': 'did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha#key-0', 'type': 'Ed25519VerificationKey2020', 'controller': 'did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha', 'publicKeyMultibase': 'z2fD7Rmbbggzwa4SNpYKWi6csiiUcVeyUTgGzDtMrqC7b'}]
# }

# actual_dict = {
#     "id": "did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
#     "verificationMethod": [{
#         "id": "did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha#key-0",
#         "type": "Ed25519VerificationKey2020",
#         "controller": "did:webs:127.0.0.1%3a7676:BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
#         "publicKeyMultibase": "z2fD7Rmbbggzwa4SNpYKWi6csiiUcVeyUTgGzDtMrqC7b"
#     }]
# }

# compare_dicts(expected_dict, actual_dict)


def setup(hby, hby_doer, oobiery, *, http_port, cf=None, static_files_dir='dws'):
    """Setup serving package and endpoints

    Parameters:
        hby (Habery): identifier database environment
        hby_doer (HaberyDoer): Doer for the identifier database environment
        oobiery (Oobiery): OOBI management environment
        http_port (int): external port to listen on for HTTP messages
        cf (Configer): configuration object for the serving package
        static_files_dir (str): directory to serve static files from, default is 'dws'
    Returns:
        list: list of Doers to run in the Tymist
    """
    logger.info(f'Setting up Resolver HTTP server Doers on port {http_port}')
    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*', allow_credentials='*', expose_headers=['cesr-attachment', 'cesr-date', 'content-type']
        )
    )

    server = http.Server(port=http_port, app=app)
    http_server_doer = http.ServerDoer(server=server)

    load_ends(app, hby=hby, hby_doer=hby_doer, oobiery=oobiery, static_files_dir=static_files_dir)

    doers = [http_server_doer]

    return doers


def load_ends(app, *, hby, hby_doer, oobiery, static_files_dir):
    # Set up static file serving for did.json and keri.cesr files
    did_doc_dir = hby.cf.get().get('did.doc.dir', 'dws')
    if not os.path.isabs(did_doc_dir):
        did_doc_dir = os.path.join(os.path.abspath(static_files_dir), did_doc_dir)
    if not os.path.isabs(did_doc_dir):
        did_doc_dir = os.path.join(os.getcwd(), did_doc_dir)
    logger.info(f'Serving static files from {did_doc_dir}')
    app.add_static_route('/dws', did_doc_dir)

    resolve_end = ResolveResource(hby=hby, hby_doer=hby_doer, oobiery=oobiery)
    app.add_route('/1.0/identifiers/{did}', resolve_end)
    app.add_route('/health', ends.HealthEnd())
    return [resolve_end]


class ResolveResource(doing.DoDoer):
    """
    Resource for resolving did:webs and did:keri DIDs
    """

    def __init__(self, hby, hby_doer, oobiery):
        """Create Endpoints for discovery and resolution of OOBIs

        Parameters:
            hby (Habery): identifier database environment
            hby_doer (HaberyDoer): Doer for the identifier database environment
            oobiery (Oobiery): OOBI management environment
        """
        self.hby = hby
        self.hby_doer = hby_doer
        self.oobiery = oobiery

        super(ResolveResource, self).__init__(doers=[])

    def on_get(self, req, rep, did, meta=False):
        """
        Handle GET requests to resolve a DID by its identifier (KERI AID).

        Parameters:
            req (falcon.Request): The HTTP request object.
            rep (falcon.Response): The HTTP response object.
            did (str): The DID to resolve.
            meta (bool): If True, include metadata in the DID document resolution.
        """
        # did = urllib.parse.unquote(did)
        logger.info(f'Request to resolve did: {did}')

        if did is None:
            rep.status = falcon.HTTP_400
            rep.content_type = 'application/json'
            rep.media = {'error': "invalid resolution request body, 'did' is required"}
            return

        if 'oobi' in req.params:
            oobi = req.params['oobi']
            logger.info(f'From parameters {req.params} got oobi: {oobi}')
        else:
            oobi = None

        if did.startswith('did:webs'):
            data = resolve(hby=self.hby, did=did, meta=meta)
        elif did.startswith('did:keri'):
            resolver = KeriResolver(hby=self.hby, hby_doer=self.hby_doer, oobiery=self.oobiery, did=did, oobi=oobi, meta=meta)
            directing.runController(doers=[resolver], expire=0.0)
            data = resolver.result
        else:
            rep.status = falcon.HTTP_400
            rep.media = {'error': "invalid 'did'"}
            return

        rep.status = falcon.HTTP_200
        rep.set_header('Content-Type', 'application/did+ld+json')
        rep.body = data

        return


def load_file(file_path):
    # Read the file in binary mode
    with open(file_path, 'rb') as file:
        msgs = file.read()
        return msgs


def load_json_file(file_path):
    # Read the file in binary mode
    with open(file_path, 'r', encoding='utf-8') as file:
        msgs = json.load(file)
        return msgs


def load_url(url: str, resq: queue.Queue = None):
    response = requests.get(url=url)
    # Ensure the request was successful
    response.raise_for_status()
    # Convert the content to a bytearray
    if resq is not None:
        resq.put(response)
    return response


def split_cesr(s, char):
    # Find the last occurrence of the character
    index = s.rfind(char)

    # If the character is not found, return the whole string and an empty string
    if index == -1:
        return s, ''

    json_str = s[: index + 1]
    # quote escaped starts with single quote and double quote and the split will lose the closing single/double quote
    if json_str.startswith('"'):
        json_str = json_str + '"'

    cesr_sig = s[index + 1 :]
    if cesr_sig.endswith('"'):
        cesr_sig = '"' + json_str

    # Split the string into two parts
    return json_str, cesr_sig
