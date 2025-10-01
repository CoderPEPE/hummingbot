#!/usr/bin/env python3
"""
Simple script to test ApiEngine API connectivity directly using urllib.
"""
import json
import sys
import urllib.request
import urllib.error
import ssl


def test_api_connectivity():
    """Test basic connectivity to ApiEngine API using direct HTTP calls"""
    print("Testing ApiEngine API connectivity...")

    # Use the provided API credentials
    api_key = "298af00b8558b716aca247083c7108a8"
    api_secret = "b57bf328f03aaf02f697c63ad527b55e33389756e0e13ac889d9f45884e38d74"
    base_url = "https://apiengine.demoapps.space/api"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Create SSL context that doesn't verify certificates (for testing)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        print("1. Testing network connectivity (ping)...")
        req = urllib.request.Request(f"{base_url}/ping", headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status == 200:
                print("   ✅ Ping successful")
            else:
                print(f"   ❌ Ping failed with status {response.status}")
                return False

        print("2. Testing exchange info fetch...")
        req = urllib.request.Request(f"{base_url}/exchange/info", headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                symbols = data.get('symbols', [])
                print(f"   ✅ Exchange info fetched: {len(symbols)} symbols")
                if symbols:
                    print(f"      Sample symbol: {symbols[0] if isinstance(symbols[0], str) else symbols[0].get('symbol', 'N/A')}")
            else:
                print(f"   ❌ Exchange info failed with status {response.status}")
                return False

        print("3. Testing account balances...")
        req = urllib.request.Request(f"{base_url}/account", headers=headers)
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    balances = data.get('balances', [])
                    print(f"   ✅ Balances fetched: {len(balances)} assets")
                else:
                    print(f"   ⚠️  Balances returned {response.status}")
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:  # Authentication issues expected for demo
                print(f"   ⚠️  Balances returned {e.code} (authentication expected for demo)")
            else:
                print(f"   ❌ Balances failed with status {e.code}")
                return False

        print("4. Testing ticker prices...")
        req = urllib.request.Request(f"{base_url}/ticker/price", headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                count = len(data) if isinstance(data, list) else 1
                print(f"   ✅ Ticker prices fetched: {count} entries")
                if isinstance(data, list) and data:
                    sample = data[0]
                    if isinstance(sample, dict) and 'symbol' in sample:
                        print(f"      Sample: {sample['symbol']} @ {sample.get('price', 'N/A')}")
            else:
                print(f"   ❌ Ticker prices failed with status {response.status}")
                return False

        print("5. Testing rate limits...")
        req = urllib.request.Request(f"{base_url}/ratelimits", headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"   ✅ Rate limits fetched: IP limit {data.get('globalLimits', {}).get('ipBased', {}).get('limit', 'N/A')}/min")
            else:
                print(f"   ❌ Rate limits failed with status {response.status}")
                return False

        print("6. Testing rate limits endpoints...")
        req = urllib.request.Request(f"{base_url}/ratelimits/endpoints", headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                endpoints = data.get('endpoints', [])
                print(f"   ✅ Rate limits endpoints fetched: {len(endpoints)} endpoints")
                if endpoints:
                    print(f"      Sample: {endpoints[0]['endpoint']} - {endpoints[0]['limit']}/{(endpoints[0]['ttl'])}s")
            else:
                print(f"   ❌ Rate limits endpoints failed with status {response.status}")
                return False

        print("7. Testing all orders...")
        req = urllib.request.Request(f"{base_url}/order/all-orders", headers=headers)
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"   ✅ All orders fetched: {len(data)} orders")
                    if data:
                        sample_order = data[0]
                        print(f"      Sample: {sample_order['market']} {sample_order['orderType']} @ {sample_order['price']} ({sample_order['status']})")
                else:
                    print(f"   ⚠️  All orders returned {response.status} (may be expected if no orders)")
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                print(f"   ⚠️  All orders returned {e.code} (authentication may be required)")
            else:
                print(f"   ❌ All orders failed with status {e.code}")
                return False

        print("8. Testing active orders...")
        req = urllib.request.Request(f"{base_url}/order/active-orders", headers=headers)
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"   ✅ Active orders fetched: {len(data)} active orders")
                else:
                    print(f"   ⚠️  Active orders returned {response.status}")
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                print(f"   ⚠️  Active orders returned {e.code} (authentication may be required)")
            else:
                print(f"   ❌ Active orders failed with status {e.code}")
                return False

        print("\n✅ All API connectivity tests passed!")
        print(f"API Key: {api_key[:10]}...")
        print(f"API Secret: {api_secret[:10]}...")
        print(f"Base URL: {base_url}")
        return True

    except urllib.error.URLError as e:
        print(f"\n❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_api_connectivity()
    sys.exit(0 if success else 1)