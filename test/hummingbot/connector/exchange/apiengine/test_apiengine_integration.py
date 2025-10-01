import asyncio
import unittest
from decimal import Decimal

from hummingbot.connector.exchange.apiengine.apiengine_exchange import ApiEngineExchange


class ApiEngineIntegrationTests(unittest.TestCase):
    """
    Integration tests for ApiEngine connector using real API credentials.
    These tests verify that the connector can successfully communicate with the API.
    """

    def setUp(self):
        # Use the provided API credentials
        self.api_key = "298af00b8558b716aca247083c7108a8"
        self.api_secret = "b57bf328f03aaf02f697c63ad527b55e33389756e0e13ac889d9f45884e38d74"
        self.trading_pairs = ["BTC-USDT"]  # Test with a common pair

        self.exchange = ApiEngineExchange(
            apiengine_api_key=self.api_key,
            apiengine_api_secret=self.api_secret,
            trading_pairs=self.trading_pairs,
            trading_required=True
        )

    def async_run_with_timeout(self, coroutine, timeout: float = 30):
        """Helper to run async functions with timeout"""
        ret = asyncio.get_event_loop().run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def test_exchange_initialization(self):
        """Test that the exchange initializes correctly"""
        self.assertEqual(self.exchange.name, "apiengine")
        self.assertEqual(self.exchange.api_key, self.api_key)
        self.assertEqual(self.exchange.secret_key, self.api_secret)
        self.assertEqual(self.exchange._trading_pairs, self.trading_pairs)

    def test_network_check(self):
        """Test network connectivity to the API"""
        try:
            network_status = self.async_run_with_timeout(self.exchange.check_network())
            self.assertTrue(network_status)
        except Exception as e:
            self.fail(f"Network check failed: {e}")

    def test_get_all_pairs_prices(self):
        """Test fetching all trading pairs prices"""
        try:
            prices = self.async_run_with_timeout(self.exchange.get_all_pairs_prices())
            self.assertIsInstance(prices, list)
            # Check if we got some price data
            if len(prices) > 0:
                self.assertIn("symbol", prices[0])
                self.assertIn("price", prices[0])
        except Exception as e:
            self.fail(f"Failed to get pairs prices: {e}")

    def test_update_trading_rules(self):
        """Test fetching and updating trading rules"""
        try:
            self.async_run_with_timeout(self.exchange._update_trading_rules())
            # Check if trading rules were loaded
            self.assertGreater(len(self.exchange.trading_rules), 0)
        except Exception as e:
            self.fail(f"Failed to update trading rules: {e}")

    def test_update_balances(self):
        """Test fetching account balances"""
        try:
            self.async_run_with_timeout(self.exchange._update_balances())
            # Check if balances were loaded (may be empty for new accounts)
            self.assertIsInstance(self.exchange._account_balances, dict)
        except Exception as e:
            self.fail(f"Failed to update balances: {e}")

    def test_get_last_traded_price(self):
        """Test getting last traded price for a trading pair"""
        try:
            for pair in self.trading_pairs:
                price = self.async_run_with_timeout(self.exchange._get_last_traded_price(pair))
                self.assertIsInstance(price, float)
                self.assertGreater(price, 0)
        except Exception as e:
            self.fail(f"Failed to get last traded price: {e}")

    def test_exchange_symbol_mapping(self):
        """Test symbol mapping functionality"""
        try:
            # First update trading rules to populate symbol mappings
            self.async_run_with_timeout(self.exchange._update_trading_rules())

            for pair in self.trading_pairs:
                symbol = self.async_run_with_timeout(self.exchange.exchange_symbol_associated_to_pair(pair))
                self.assertIsInstance(symbol, str)
                self.assertNotEqual(symbol, "")

                # Test reverse mapping
                reverse_pair = self.async_run_with_timeout(self.exchange.trading_pair_associated_to_exchange_symbol(symbol))
                self.assertEqual(reverse_pair, pair)
        except Exception as e:
            self.fail(f"Symbol mapping test failed: {e}")

    def test_supported_order_types(self):
        """Test that supported order types are properly defined"""
        order_types = self.exchange.supported_order_types()
        self.assertIsInstance(order_types, list)
        self.assertGreater(len(order_types), 0)

    def test_connector_properties(self):
        """Test various connector properties"""
        self.assertIsInstance(self.exchange.name, str)
        self.assertIsInstance(self.exchange.client_order_id_prefix, str)
        self.assertIsInstance(self.exchange.client_order_id_max_length, int)
        self.assertGreater(self.exchange.client_order_id_max_length, 0)


if __name__ == '__main__':
    unittest.main()