from unittest.mock import patch

import pytest
import requests

from dws import ArtifactResolveError
from dws.core import requesting


def test_load_url_with_requests_fails_on_connection_error():
    # request mock
    class MockRequestResponse(object):
        def __init__(self, content, status_code):
            self.content = content
            self.status_code = status_code

    # Mock out the requests library
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection failed')
        mock_get.side_effect = [
            requests.exceptions.ConnectionError('Connection failed'),
            requests.exceptions.ConnectionError('Connection failed'),
        ]
        with pytest.raises(ArtifactResolveError) as excinfo:
            requesting.load_url_with_requests('http://192.0.2.1')
        assert 'Failed to connect to HTTP URL' in str(excinfo.value), 'Expected error message for ArtifactResolveError'

        mock_get.side_effect = Exception('Unexpected error')
        with pytest.raises(ArtifactResolveError) as excinfo:
            requesting.load_url_with_requests('http://192.0.2.1')
        assert 'Failed to load HTTP URL' in str(excinfo.value), 'Expected error message for ArtifactResolveError'

    with patch('requests.get') as mock_get:
        # mock returning a byte array in response.content
        mock_get.return_value.content = b'{"key": "value"}'
        mock_get.return_value.status_code = 200
        result = requesting.load_url_with_requests('http://192.0.2.1')
        assert result == b'{"key": "value"}', 'Expected byte array response from mocked requests.get'

    with patch('requests.get') as mock_get:
        mock_get.side_effect = [
            MockRequestResponse(content=b'', status_code=404),
            MockRequestResponse(content=b'{"key": "value"}', status_code=200),
        ]

        # Test giving HTTP URL tries with HTTPS first, fails, and then falls back to HTTP
        result = requesting.load_url_with_requests('http://192.0.2.1')
        assert result == b'{"key": "value"}', 'Expected byte array response from mocked requests.get after fallback'

        # Test when HTTPS fails and HTTP throws a connection error
        mock_get.side_effect = [
            MockRequestResponse(content=b'', status_code=404),
            requests.exceptions.ConnectionError('Connection failed'),
        ]
        with pytest.raises(ArtifactResolveError) as excinfo:
            requesting.load_url_with_requests('https://example.com')
        assert 'Failed to connect to HTTP URL' in str(excinfo.value), 'Expected error message for ArtifactResolveError'

        # Test when HTTPS fails and HTTP throws a general exception
        mock_get.side_effect = [
            MockRequestResponse(content=b'', status_code=404),
            Exception('Some request error'),
        ]
        with pytest.raises(ArtifactResolveError) as excinfo:
            requesting.load_url_with_requests('https://example.com')
        assert 'Failed to load HTTP URL' in str(excinfo.value), 'Expected error message for ArtifactResolveError'
