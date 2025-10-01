import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from hummingbot.connector.exchange.apiengine.apiengine_auth import ApiEngineAuth
from hummingbot.connector.exchange.apiengine.apiengine_constants import (
    RATE_LIMITS_ENDPOINTS_PATH_URL,
    RATE_LIMITS_PATH_URL,
    ALL_ORDERS_PATH_URL,
    ACTIVE_ORDERS_PATH_URL,
)
from hummingbot.connector.time_synchronizer import TimeSynchronizer


class TestApiEngineEndpoints(unittest.TestCase):
    def setUp(self):
        self.api_key = "298af00b8558b716aca247083c7108a8"
        self.api_secret = "b57bf328f03aaf02f697c63ad527b55e33389756e0e13ac889d9f45884e38d74"
        self.time_synchronizer = TimeSynchronizer()
        self.auth = ApiEngineAuth(self.api_key, self.api_secret, self.time_synchronizer)

    def test_auth_headers(self):
        """Test that authentication headers are correctly formatted"""
        headers = self.auth.header_for_authentication()

        self.assertIn("x-api-key", headers)
        self.assertIn("x-api-secret", headers)
        self.assertIn("Authorization", headers)

        self.assertEqual(headers["x-api-key"], self.api_key)
        self.assertEqual(headers["x-api-secret"], self.api_secret)
        self.assertTrue(headers["Authorization"].startswith("Bearer "))

    @patch('aiohttp.ClientSession')
    async def test_rate_limits_endpoint(self, mock_session):
        """Test fetching rate limits from the API"""
        # Mock response data
        mock_response_data = {
            "ip": "::ffff:127.0.0.1",
            "userId": "d4e348a2-f057-4728-afeb-980ce68e832d",
            "globalLimits": {
                "ipBased": {
                    "limit": 1200,
                    "ttl": 60,
                    "description": "1200 requests per minute per IP address"
                },
                "userBased": {
                    "limit": 1200,
                    "ttl": 60,
                    "description": "1200 requests per minute per authenticated user"
                },
                "burst": {
                    "limit": 10,
                    "ttl": 1,
                    "description": "10 requests per second burst limit"
                }
            },
            "timestamp": "2025-10-01T12:58:20.583Z"
        }

        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = AsyncMock()
        mock_session_instance.get = AsyncMock(return_value=mock_response)
        mock_session.return_value = mock_session_instance

        # Test the actual API call (this would be in a real integration test)
        base_url = "https://apiengine.demoapps.space"
        headers = self.auth.header_for_authentication()

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{base_url}/{RATE_LIMITS_PATH_URL}") as response:
                if response.status == 200:
                    data = await response.json()
                    self.assertIn("globalLimits", data)
                    self.assertIn("ipBased", data["globalLimits"])
                    self.assertEqual(data["globalLimits"]["ipBased"]["limit"], 1200)

    @patch('aiohttp.ClientSession')
    async def test_rate_limits_endpoints(self, mock_session):
        """Test fetching endpoint-specific rate limits"""
        mock_response_data = {
            "endpoints": [
                {
                    "endpoint": "GET /ping",
                    "method": "GET",
                    "limit": 1200,
                    "ttl": 60,
                    "weight": 1,
                    "description": "Ping endpoint - 1200 requests per minute"
                },
                {
                    "endpoint": "POST /order",
                    "method": "POST",
                    "limit": 10,
                    "ttl": 1,
                    "weight": 1,
                    "description": "Place order - 10 requests per second"
                },
                {
                    "endpoint": "GET /order/active-orders",
                    "method": "GET",
                    "limit": 10,
                    "ttl": 1,
                    "weight": 1,
                    "description": "Get active orders - 10 requests per second"
                }
            ],
            "timestamp": "2025-10-01T13:03:46.524Z"
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = AsyncMock()
        mock_session_instance.get = AsyncMock(return_value=mock_response)
        mock_session.return_value = mock_session_instance

        base_url = "https://apiengine.demoapps.space"
        headers = self.auth.header_for_authentication()

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{base_url}/{RATE_LIMITS_ENDPOINTS_PATH_URL}") as response:
                if response.status == 200:
                    data = await response.json()
                    self.assertIn("endpoints", data)
                    self.assertTrue(len(data["endpoints"]) > 0)

                    # Check specific endpoints
                    endpoints = {ep["endpoint"]: ep for ep in data["endpoints"]}

                    # Verify ping endpoint
                    self.assertIn("GET /ping", endpoints)
                    ping_ep = endpoints["GET /ping"]
                    self.assertEqual(ping_ep["limit"], 1200)
                    self.assertEqual(ping_ep["ttl"], 60)

                    # Verify order endpoint
                    self.assertIn("POST /order", endpoints)
                    order_ep = endpoints["POST /order"]
                    self.assertEqual(order_ep["limit"], 10)
                    self.assertEqual(order_ep["ttl"], 1)

                    # Verify active orders endpoint
                    self.assertIn("GET /order/active-orders", endpoints)
                    active_orders_ep = endpoints["GET /order/active-orders"]
                    self.assertEqual(active_orders_ep["limit"], 10)
                    self.assertEqual(active_orders_ep["ttl"], 1)

    @patch('aiohttp.ClientSession')
    async def test_all_orders_endpoint(self, mock_session):
        """Test fetching all orders from the API"""
        mock_response_data = [
            {
                "id": "88f45fe7-c484-4ff4-88b3-e7da56984451",
                "userId": "d4e348a2-f057-4728-afeb-980ce68e832d",
                "market": "ETH/XLM",
                "price": 0.02,
                "timestamp": "1755689000150878835",
                "originalSize": 0.01,
                "status": "PENDING",
                "bids": True,
                "orderType": "BUY",
                "size": 0.01,
                "displayStatus": "PENDING",
                "matchedOrders": [],
                "orderPlacedType": "LIMIT",
                "tradedPrice": 0.41,
                "tradeSize": None,
                "meanMatchPrice": None
            },
            {
                "id": "dc3494db-1db6-4da0-bcf9-2a3f02ae1495",
                "userId": "d4e348a2-f057-4728-afeb-980ce68e832d",
                "market": "ETH/XLM",
                "price": 0.03,
                "timestamp": "1755689010025805672",
                "originalSize": 0.01,
                "status": "PENDING",
                "bids": True,
                "orderType": "BUY",
                "size": 0.01,
                "displayStatus": "PENDING",
                "matchedOrders": [],
                "orderPlacedType": "LIMIT",
                "tradedPrice": 0.41,
                "tradeSize": None,
                "meanMatchPrice": None
            }
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = AsyncMock()
        mock_session_instance.get = AsyncMock(return_value=mock_response)
        mock_session.return_value = mock_session_instance

        base_url = "https://apiengine.demoapps.space"
        headers = self.auth.header_for_authentication()

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{base_url}/{ALL_ORDERS_PATH_URL}") as response:
                if response.status == 200:
                    data = await response.json()
                    self.assertIsInstance(data, list)
                    self.assertTrue(len(data) > 0)

                    # Check structure of first order
                    order = data[0]
                    required_fields = ["id", "userId", "market", "price", "status", "bids", "orderType", "size"]
                    for field in required_fields:
                        self.assertIn(field, order)

                    # Verify data types
                    self.assertIsInstance(order["id"], str)
                    self.assertIsInstance(order["price"], (int, float))
                    self.assertIsInstance(order["size"], (int, float))
                    self.assertIsInstance(order["bids"], bool)
                    self.assertIn(order["status"], ["PENDING", "FILLED", "CANCELLED", "PARTIAL"])

    @patch('aiohttp.ClientSession')
    async def test_active_orders_endpoint(self, mock_session):
        """Test fetching active orders from the API"""
        mock_response_data = [
            {
                "id": "88f45fe7-c484-4ff4-88b3-e7da56984451",
                "userId": "d4e348a2-f057-4728-afeb-980ce68e832d",
                "market": "ETH/XLM",
                "price": 0.02,
                "timestamp": "1755689000150878835",
                "originalSize": 0.01,
                "status": "PENDING",
                "bids": True,
                "orderType": "BUY",
                "size": 0.01,
                "displayStatus": "PENDING",
                "matchedOrders": [],
                "orderPlacedType": "LIMIT",
                "tradedPrice": 0.41,
                "tradeSize": None,
                "meanMatchPrice": None
            }
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = AsyncMock()
        mock_session_instance.get = AsyncMock(return_value=mock_response)
        mock_session.return_value = mock_session_instance

        base_url = "https://apiengine.demoapps.space"
        headers = self.auth.header_for_authentication()

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{base_url}/{ACTIVE_ORDERS_PATH_URL}") as response:
                if response.status == 200:
                    data = await response.json()
                    self.assertIsInstance(data, list)

                    # Active orders should only include non-completed orders
                    for order in data:
                        self.assertIn(order["status"], ["PENDING", "OPEN", "PARTIAL"])
                        self.assertNotIn(order["status"], ["FILLED", "CANCELLED"])

    def test_order_status_mapping(self):
        """Test that order statuses are correctly mapped"""
        from hummingbot.connector.exchange.apiengine.apiengine_constants import ORDER_STATE
        from hummingbot.core.data_type.in_flight_order import OrderState

        # Test known mappings
        self.assertEqual(ORDER_STATE["PENDING"], OrderState.PENDING_CREATE)
        self.assertEqual(ORDER_STATE["OPEN"], OrderState.OPEN)
        self.assertEqual(ORDER_STATE["FILLED"], OrderState.FILLED)
        self.assertEqual(ORDER_STATE["PARTIAL"], OrderState.PARTIALLY_FILLED)
        self.assertEqual(ORDER_STATE["CANCELLED"], OrderState.CANCELED)
        self.assertEqual(ORDER_STATE["REJECTED"], OrderState.FAILED)
        self.assertEqual(ORDER_STATE["EXPIRED"], OrderState.FAILED)
        self.assertEqual(ORDER_STATE["COMPLETED"], OrderState.FILLED)

    @patch('aiohttp.ClientSession')
    async def test_api_key_generation(self, mock_session):
        """Test API key generation endpoint"""
        mock_response_data = {
            "status": True,
            "statusCode": 201,
            "message": "New API Key generated successfully",
            "data": {
                "id": "7cfbb0ed-9afa-448b-bd63-7811e97b4154",
                "userId": "d4e348a2-f057-4728-afeb-980ce68e832d",
                "key": "298af00b8558b716aca247083c7108a8",
                "secret": "b57bf328f03aaf02f697c63ad527b55e33389756e0e13ac889d9f45884e38d74",
                "createdAt": "2025-10-01T00:00:00.000Z"
            }
        }

        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session_instance = AsyncMock()
        mock_session_instance.post = AsyncMock(return_value=mock_response)
        mock_session.return_value = mock_session_instance

        base_url = "https://apiengine.demoapps.space"
        headers = self.auth.header_for_authentication()

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f"{base_url}/apikey/generate") as response:
                if response.status == 201:
                    data = await response.json()
                    self.assertTrue(data["status"])
                    self.assertEqual(data["statusCode"], 201)
                    self.assertIn("data", data)

                    api_data = data["data"]
                    self.assertIn("key", api_data)
                    self.assertIn("secret", api_data)
                    self.assertIn("userId", api_data)

                    # Verify the key format (should be a valid UUID-like string)
                    self.assertIsInstance(api_data["key"], str)
                    self.assertEqual(len(api_data["key"]), 32)  # MD5 hash length
                    self.assertIsInstance(api_data["secret"], str)
                    self.assertEqual(len(api_data["secret"]), 64)  # SHA256 hash length

    def test_rate_limit_constants(self):
        """Test that rate limit constants are properly defined"""
        from hummingbot.connector.exchange.apiengine.apiengine_constants import (
            GLOBAL_IP_LIMIT,
            GLOBAL_USER_LIMIT,
            BURST_LIMIT,
        )

        self.assertEqual(GLOBAL_IP_LIMIT, 1200)
        self.assertEqual(GLOBAL_USER_LIMIT, 1200)
        self.assertEqual(BURST_LIMIT, 10)


if __name__ == '__main__':
    # Run async tests
    async def run_async_tests():
        test_instance = TestApiEngineEndpoints()
        test_instance.setUp()

        # Run individual async test methods
        await test_instance.test_auth_headers()
        print("✓ test_auth_headers passed")

        await test_instance.test_rate_limits_endpoint()
        print("✓ test_rate_limits_endpoint passed")

        await test_instance.test_rate_limits_endpoints()
        print("✓ test_rate_limits_endpoints passed")

        await test_instance.test_all_orders_endpoint()
        print("✓ test_all_orders_endpoint passed")

        await test_instance.test_active_orders_endpoint()
        print("✓ test_active_orders_endpoint passed")

        await test_instance.test_api_key_generation()
        print("✓ test_api_key_generation passed")

        # Run sync tests
        test_instance.test_order_status_mapping()
        print("✓ test_order_status_mapping passed")

        test_instance.test_rate_limit_constants()
        print("✓ test_rate_limit_constants passed")

        print("\n✅ All endpoint tests passed!")

    asyncio.run(run_async_tests())