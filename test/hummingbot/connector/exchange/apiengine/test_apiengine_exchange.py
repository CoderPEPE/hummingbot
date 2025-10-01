import asyncio
import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from aioresponses import aioresponses

from hummingbot.connector.exchange.apiengine import apiengine_constants as CONSTANTS, apiengine_web_utils as web_utils
from hummingbot.connector.exchange.apiengine.apiengine_exchange import ApiEngineExchange
from hummingbot.connector.test_support.exchange_connector_test import AbstractExchangeConnectorTests
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState


class ApiEngineExchangeTests(AbstractExchangeConnectorTests.ExchangeConnectorTests):

    @property
    def all_symbols_url(self):
        return web_utils.public_rest_url(path_url=CONSTANTS.EXCHANGE_INFO_PATH_URL, domain=self.exchange._domain)

    @property
    def latest_prices_url(self):
        url = web_utils.public_rest_url(path_url=CONSTANTS.TICKER_PRICE_CHANGE_PATH_URL, domain=self.exchange._domain)
        url = f"{url}?symbol={self.exchange_symbol_for_tokens(self.base_asset, self.quote_asset)}"
        return url

    @property
    def network_status_url(self):
        url = web_utils.public_rest_url(CONSTANTS.PING_PATH_URL, domain=self.exchange._domain)
        return url

    @property
    def trading_rules_url(self):
        url = web_utils.public_rest_url(CONSTANTS.EXCHANGE_INFO_PATH_URL, domain=self.exchange._domain)
        return url

    @property
    def order_creation_url(self):
        url = web_utils.private_rest_url(CONSTANTS.ORDER_PATH_URL, domain=self.exchange._domain)
        return url

    @property
    def balance_url(self):
        url = web_utils.private_rest_url(CONSTANTS.ACCOUNTS_PATH_URL, domain=self.exchange._domain)
        return url

    @property
    def all_symbols_request_mock_response(self):
        return {
            "symbols": [
                {
                    "symbol": self.exchange_symbol_for_tokens(self.base_asset, self.quote_asset),
                    "status": "TRADING",
                    "baseAsset": self.base_asset,
                    "quoteAsset": self.quote_asset,
                    "minOrderSize": "0.0001",
                    "tickSize": "0.0001",
                    "stepSize": "0.0001",
                    "minNotional": "0.0001"
                }
            ]
        }

    @property
    def latest_prices_request_mock_response(self):
        return {
            "symbol": self.exchange_symbol_for_tokens(self.base_asset, self.quote_asset),
            "price": str(self.expected_latest_price),
        }

    @property
    def network_status_request_successful_mock_response(self):
        return {}

    @property
    def trading_rules_request_mock_response(self):
        return {
            "symbols": [
                {
                    "symbol": self.exchange_symbol_for_tokens(self.base_asset, self.quote_asset),
                    "status": "TRADING",
                    "baseAsset": self.base_asset,
                    "quoteAsset": self.quote_asset,
                    "minOrderSize": "0.001",
                    "tickSize": "0.000001",
                    "stepSize": "0.001",
                    "minNotional": "0.001"
                }
            ]
        }

    @property
    def order_creation_request_successful_mock_response(self):
        return {
            "id": self.expected_exchange_order_id,
            "userId": "testUserId",
            "market": self.trading_pair,
            "type": "LIMIT",
            "bid": True,
            "size": 1.0,
            "price": 10000.0,
            "currency": self.quote_asset,
            "status": "pending",
            "createdAt": "2025-01-01T00:00:00.000Z"
        }

    @property
    def balance_request_mock_response_for_base_and_quote(self):
        return {
            "balances": [
                {
                    "currency": self.base_asset,
                    "available": "10.0",
                    "total": "15.0"
                },
                {
                    "currency": self.quote_asset,
                    "available": "2000",
                    "total": "2000"
                }
            ]
        }

    @property
    def expected_latest_price(self):
        return 9999.9

    @property
    def expected_supported_order_types(self):
        return [OrderType.LIMIT, OrderType.MARKET]

    @property
    def expected_trading_rule(self):
        return TradingRule(
            trading_pair=self.trading_pair,
            min_order_size=Decimal(self.trading_rules_request_mock_response["symbols"][0]["minOrderSize"]),
            min_price_increment=Decimal(self.trading_rules_request_mock_response["symbols"][0]["tickSize"]),
            min_base_amount_increment=Decimal(self.trading_rules_request_mock_response["symbols"][0]["stepSize"]),
            min_notional_size=Decimal(self.trading_rules_request_mock_response["symbols"][0]["minNotional"]),
        )

    @property
    def expected_exchange_order_id(self):
        return "test-order-123"

    def exchange_symbol_for_tokens(self, base_token: str, quote_token: str) -> str:
        return f"{base_token}-{quote_token}"

    def create_exchange_instance(self):
        return ApiEngineExchange(
            apiengine_api_key="testApiKey",
            apiengine_api_secret="testSecret",
            trading_pairs=[self.trading_pair],
        )

    def validate_auth_credentials_present(self, request_call):
        request_headers = request_call.kwargs["headers"]
        self.assertIn("Authorization", request_headers)
        self.assertEqual("Bearer testApiKey", request_headers["Authorization"])

    def validate_order_creation_request(self, order: InFlightOrder, request_call):
        request_data = json.loads(request_call.kwargs["data"])
        self.assertEqual(order.trading_pair, request_data["market"])
        self.assertEqual(order.trade_type == TradeType.BUY, request_data["bid"])
        self.assertEqual(float(order.amount), request_data["size"])
        self.assertEqual(float(order.price), request_data["price"])

    def validate_order_cancelation_request(self, order: InFlightOrder, request_call):
        # For ApiEngine, cancel is DELETE to /orders/{order_id}
        pass  # URL validation is done in the test framework

    def validate_order_status_request(self, order: InFlightOrder, request_call):
        # For ApiEngine, status is GET to /orders/{order_id}
        pass  # URL validation is done in the test framework

    def validate_trades_request(self, order: InFlightOrder, request_call):
        # For ApiEngine, trades are GET to /myTrades
        pass  # URL validation is done in the test framework

    def configure_successful_cancelation_response(self, order: InFlightOrder, mock_api: aioresponses, callback=None) -> str:
        url = web_utils.private_rest_url(f"{CONSTANTS.ORDER_PATH_URL}/{order.exchange_order_id}", domain=self.exchange._domain)
        response = {"status": "cancelled", "success": True}
        mock_api.delete(url, body=json.dumps(response), callback=callback)
        return url

    def configure_erroneous_cancelation_response(self, order: InFlightOrder, mock_api: aioresponses, callback=None) -> str:
        url = web_utils.private_rest_url(f"{CONSTANTS.ORDER_PATH_URL}/{order.exchange_order_id}", domain=self.exchange._domain)
        mock_api.delete(url, status=400, callback=callback)
        return url

    def configure_completely_filled_order_status_response(self, order: InFlightOrder, mock_api: aioresponses, callback=None) -> str:
        url = web_utils.private_rest_url(f"{CONSTANTS.ORDER_PATH_URL}/{order.exchange_order_id}", domain=self.exchange._domain)
        response = self._order_status_request_completely_filled_mock_response(order=order)
        mock_api.get(url, body=json.dumps(response), callback=callback)
        return url

    def configure_canceled_order_status_response(self, order: InFlightOrder, mock_api: aioresponses, callback=None) -> str:
        url = web_utils.private_rest_url(f"{CONSTANTS.ORDER_PATH_URL}/{order.exchange_order_id}", domain=self.exchange._domain)
        response = self._order_status_request_canceled_mock_response(order=order)
        mock_api.get(url, body=json.dumps(response), callback=callback)
        return url

    def configure_open_order_status_response(self, order: InFlightOrder, mock_api: aioresponses, callback=None) -> str:
        url = web_utils.private_rest_url(f"{CONSTANTS.ORDER_PATH_URL}/{order.exchange_order_id}", domain=self.exchange._domain)
        response = self._order_status_request_open_mock_response(order=order)
        mock_api.get(url, body=json.dumps(response), callback=callback)
        return url

    def configure_partially_filled_order_status_response(self, order: InFlightOrder, mock_api: aioresponses, callback=None) -> str:
        url = web_utils.private_rest_url(f"{CONSTANTS.ORDER_PATH_URL}/{order.exchange_order_id}", domain=self.exchange._domain)
        response = self._order_status_request_partially_filled_mock_response(order=order)
        mock_api.get(url, body=json.dumps(response), callback=callback)
        return url

    def _order_status_request_completely_filled_mock_response(self, order: InFlightOrder):
        return {
            "id": order.exchange_order_id,
            "userId": "testUserId",
            "market": order.trading_pair,
            "status": "filled",
            "size": float(order.amount),
            "price": float(order.price),
            "createdAt": "2025-01-01T00:00:00.000Z",
            "updatedAt": "2025-01-01T00:00:01.000Z"
        }

    def _order_status_request_canceled_mock_response(self, order: InFlightOrder):
        return {
            "id": order.exchange_order_id,
            "userId": "testUserId",
            "market": order.trading_pair,
            "status": "cancelled",
            "size": float(order.amount),
            "price": float(order.price),
            "createdAt": "2025-01-01T00:00:00.000Z",
            "updatedAt": "2025-01-01T00:00:01.000Z"
        }

    def _order_status_request_open_mock_response(self, order: InFlightOrder):
        return {
            "id": order.exchange_order_id,
            "userId": "testUserId",
            "market": order.trading_pair,
            "status": "open",
            "size": float(order.amount),
            "price": float(order.price),
            "createdAt": "2025-01-01T00:00:00.000Z",
            "updatedAt": "2025-01-01T00:00:01.000Z"
        }

    def _order_status_request_partially_filled_mock_response(self, order: InFlightOrder):
        return {
            "id": order.exchange_order_id,
            "userId": "testUserId",
            "market": order.trading_pair,
            "status": "partially_filled",
            "size": float(order.amount),
            "price": float(order.price),
            "createdAt": "2025-01-01T00:00:00.000Z",
            "updatedAt": "2025-01-01T00:00:01.000Z"
        }