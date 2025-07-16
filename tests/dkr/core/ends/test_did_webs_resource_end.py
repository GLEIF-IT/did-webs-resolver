import falcon
import pytest
from keri.app import habbing
from mockito import mock, unstub, when

from dkr.core import didding
from dkr.core.ends.did_webs_resource_end import DIDWebsResourceEnd


def test_did_web_resource_end_on_get():
    req = mock(falcon.Request)
    rep = mock(falcon.Response)
    hby = mock(habbing.Habery)
    hby.kevers = {'test_aid': mock()}

    req.path = '/test_aid/did.json'
    req.host = 'example.com'
    req.port = 80

    when(didding).generate_did_doc(hby, 'did:web:example.com:test_aid', 'test_aid').thenReturn({'mocked': 'data'})

    resource = DIDWebsResourceEnd(hby)
    resource.on_get(req, rep, 'test_aid')

    assert rep.status == falcon.HTTP_200
    assert rep.content_type == 'application/json'
    assert rep.data == b'{\n  "mocked": "data"\n}'

    unstub()


def test_did_web_resource_end_on_get_odd_port():
    req = mock(falcon.Request)
    rep = mock(falcon.Response)
    hby = mock(habbing.Habery)
    hby.kevers = {'test_aid': mock()}

    req.path = '/test_aid/did.json'
    req.host = 'example.com'
    req.port = 42

    when(didding).generate_did_doc(hby, 'did:web:example.com%3A42:test_aid', 'test_aid').thenReturn({'mocked': 'data'})

    resource = DIDWebsResourceEnd(hby)
    resource.on_get(req, rep, 'test_aid')

    assert rep.status == falcon.HTTP_200
    assert rep.content_type == 'application/json'
    assert rep.data == b'{\n  "mocked": "data"\n}'

    unstub()


def test_did_web_resource_end_on_get_bad_path():
    req = mock(falcon.Request)
    rep = mock(falcon.Response)
    hby = mock(habbing.Habery)
    hby.kevers = {'test_aid': mock()}

    req.path = '/test_aid/bad.path'

    resource = DIDWebsResourceEnd(hby)

    with pytest.raises(falcon.HTTPBadRequest) as e:
        resource.on_get(req, rep, 'test_aid')

    assert isinstance(e.value, falcon.HTTPBadRequest)

    unstub()


def test_did_web_resource_end_on_get_bad_aid():
    req = mock(falcon.Request)
    rep = mock(falcon.Response)
    hby = mock(habbing.Habery)
    hby.kevers = {'test_aid': mock()}

    req.path = '/bad_aid/did.json'

    resource = DIDWebsResourceEnd(hby)

    with pytest.raises(falcon.HTTPNotFound) as e:
        resource.on_get(req, rep, 'bad_aid')

    assert isinstance(e.value, falcon.HTTPNotFound)

    unstub()
