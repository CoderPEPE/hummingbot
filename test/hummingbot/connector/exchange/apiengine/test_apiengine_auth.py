import asyncio
from unittest import TestCase
from unittest.mock import MagicMock

from typing_extensions import Awaitable

from hummingbot.connector.exchange.apiengine.apiengine_auth import ApiEngineAuth
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest


class ApiEngineAuthTests(TestCase):

    def setUp(self) -> None:
        self._api_key = "testApiKey"
        self._secret = "testSecret"

    def async_run_with_timeout(self, coroutine: Awaitable, timeout: float = 1):
        ret = asyncio.get_event_loop().run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def test_rest_authenticate(self):
        mock_time_provider = MagicMock()
        mock_time_provider.time.return_value = 1234567890.000

        auth = ApiEngineAuth(api_key=self._api_key, secret_key=self._secret, time_provider=mock_time_provider)
        request = RESTRequest(method=RESTMethod.GET, is_auth_required=True)
        configured_request = self.async_run_with_timeout(auth.rest_authenticate(request))

        expected_header = {"Authorization": f"Bearer {self._api_key}"}
        self.assertEqual(expected_header, configured_request.headers)

    def test_rest_authenticate_with_data(self):
        mock_time_provider = MagicMock()
        mock_time_provider.time.return_value = 1234567890.000

        auth = ApiEngineAuth(api_key=self._api_key, secret_key=self._secret, time_provider=mock_time_provider)
        request = RESTRequest(method=RESTMethod.POST, data={"test": "data"}, is_auth_required=True)
        configured_request = self.async_run_with_timeout(auth.rest_authenticate(request))

        expected_header = {"Authorization": f"Bearer {self._api_key}"}
        self.assertEqual(expected_header, configured_request.headers)
        self.assertEqual({"test": "data"}, configured_request.data)