import json

import pytest
from hio.base import doing

from dws import ArtifactResolveError
from dws.core import requesting


def test_load_url_with_hio():
    url = 'https://weboftrust.github.io/oobi/EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5/'
    resp = requesting.load_url_with_hio_clienter(url)
    assert resp is not None, 'Response should not be None'

    resp = requesting.load_url_with_hio(url)
    assert resp is not None, 'Response should not be None'


def test_load_url_with_hio_invalid_url_throws():
    invalid_url = 'http://invalid-url:123456789:://??##@@'
    with pytest.raises(ValueError) as exc_info:
        requesting.load_url_with_hio(invalid_url)
    assert 'Port could not be cast' in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        requesting.load_url_with_hio_clienter(invalid_url)
    assert 'Port could not be cast' in str(exc_info.value)


def test_create_http_client_with_body_encodes():
    url = 'http://192.0.2.1/api'
    body = json.dumps({'key': 'value'})
    headers = {'Content-Type': 'application/json'}
    client, client_doer = requesting.create_http_client('POST', url, body=body, headers=headers)
    assert client is not None
    assert client.requests[0]['body'] == body.encode('utf-8'), 'Body should be encoded to bytes'

    doist = doing.Doist(limit=0.1, tock=0.03125, real=True)
    clienter = requesting.HTTPClienter()
    clienter.always = False
    clienter.tymth = doist.tymen()  # share the Doist tymth with the Clienter
    client = clienter.request('POST', url, body=body, headers=headers)
    assert client is not None
    assert client.requests[0]['body'] == body.encode('utf-8'), 'Body should be encoded to bytes'


def test_load_url_with_hio_timeout_causes_hio_error():
    # Use RFC 5737 TEST-NET address (192.0.2.0/24) - not routed, connection hangs.
    # example.com responds quickly (404), causing intermittent test failure.
    bad_url = 'http://192.0.2.1/oobi/EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5/'
    with pytest.raises(ArtifactResolveError) as exc_info:
        requesting.load_url_with_hio(bad_url, timeout=0.1)
    assert 'Failed to load URL' in str(exc_info.value), 'Should raise HioError on timeout'

    # requesting.load_url_with_hio_clienter(bad_url, timeout=1.0)
    with pytest.raises(ArtifactResolveError) as exc_info:
        requesting.load_url_with_hio_clienter(bad_url, timeout=0.1)
    assert 'Failed to load URL' in str(exc_info.value), 'Should raise HioError on timeout'
