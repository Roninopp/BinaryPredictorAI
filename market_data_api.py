import websocket
import threading
import time
import json
import logging
import ssl
from collections import deque
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class PocketOptionAPI:
    """
    Connects to Pocket Option via WebSocket for real-time data.
    Uses unofficial WebSocket connection based on browser inspection.
    """

    def __init__(self, ssid):
        self.ssid = ssid
        # Use the WebSocket URL found via Developer Tools
        self.ws_url = "wss://chat-po.site/cabinet-client/socket.io/?EIO=4&transport=websocket"
        self.ws = None
        self.thread = None
        self.is_connected = False
        self.is_authenticated = False
        self.data_store = {}  # Stores recent candles {pair_tf: deque([candle])}
        self.data_lock = threading.Lock()
        self.subscribed_assets = set() # Keep track of subscribed assets {pair_tf}

        # Timeframe conversion (seconds) - needed for subscription
        self.timeframes_seconds = {
            "1m": 60, "5m": 300, "15m": 900, "1h": 3600
        }
        # Pair mapping (if needed for subscription message format)
        self.pair_map = {
             # OTC Pairs
            "AUD/CAD OTC": "AUDCAD_otc", "AUD/USD OTC": "AUDUSD_otc",
            "CAD/JPY OTC": "CADJPY_otc", "CHF/JPY OTC": "CHFJPY_otc",
            "EUR/CHF OTC": "EURCHF_otc", "GBP/AUD OTC": "GBPAUD_otc",
            "NZD/JPY OTC": "NZDJPY_otc", "USD/CHF OTC": "USDCHF_otc",
             # Regular Pairs (adjust as needed)
            "EUR/USD": "EURUSD", "GBP/USD": "GBPUSD",
            "USD/JPY": "USDJPY", "XAU/USD": "XAUUSD",
        }

        self._start_websocket()

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        # logger.debug(f"WS Received: {message}")
        try:
            # Socket.IO messages often start with numbers (e.g., '42[...]')
            if message.startswith('42'):
                data_part = message[2:] # Remove the '42' prefix
                try:
                    event_data = json.loads(data_part)
                    event_name = event_data[0]
                    payload = event_data[1]

                    if event_name == "candles":
                        self._handle_candle_data(payload)
                    elif event_name == "auth_success": # Hypothetical success event
                         logger.info("WebSocket authenticated successfully.")
                         self.is_authenticated = True
                         # Resubscribe to assets after successful auth/reconnect
                         self._resubscribe_assets()
                    # Add handlers for other relevant events if needed

                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from message: {data_part}")
                except Exception as e:
                    logger.error(f"Error processing message payload: {e} - Data: {data_part}")

            elif message.startswith('0'): # Socket.IO connection confirmation
                logger.info("Socket.IO connection established. Sending auth...")
                self._authenticate()
            elif message.startswith('3'): # Socket.IO Pong
                pass # logger.debug("Received Pong")


        except Exception as e:
            logger.error(f"Error in _on_message: {e} - Message: {message}")

    def _handle_candle_data(self, payload):
        """Parse and store candle data."""
        try:
            # Assuming payload format is like: {'asset': 'AUDCAD_otc', 'period': 300, 'candles': [...]}
            # Or sometimes: [{'t': ts, 'o': o, 'h': h, 'l': l, 'c': c, 'v': v, 'a': asset, 'p': period}, ...]
            candles_list = []
            asset_symbol = None
            period_seconds = None

            # Handle different possible payload structures
            if isinstance(payload, dict) and 'candles' in payload:
                 candles_list = payload.get('candles', [])
                 asset_symbol = payload.get('asset')
                 period_seconds = payload.get('period')
            elif isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict):
                 # Assuming list of candle dicts, potentially with asset/period inside each
                 candles_list = payload
                 if 'a' in candles_list[0] and 'p' in candles_list[0]: # Asset/Period per candle
                    asset_symbol = candles_list[0]['a']
                    period_seconds = candles_list[0]['p']


            if not asset_symbol or not period_seconds or not candles_list:
                # logger.warning(f"Received candle data in unexpected format or missing info: {payload}")
                return

            pair_tf_key = f"{asset_symbol}_{period_seconds}"

            with self.data_lock:
                if pair_tf_key not in self.data_store:
                    self.data_store[pair_tf_key] = deque(maxlen=200) # Store last 200 candles

                for candle_data in candles_list:
                     # Adapt keys based on actual received data ('t', 'o', 'h', 'l', 'c', 'v')
                    candle = {
                        'timestamp': candle_data.get('t'),
                        'open': float(candle_data.get('o', 0)),
                        'high': float(candle_data.get('h', 0)),
                        'low': float(candle_data.get('l', 0)),
                        'close': float(candle_data.get('c', 0)),
                        'volume': float(candle_data.get('v', 0))
                    }
                    if candle['timestamp'] and candle['close'] > 0: # Basic validation
                        # Avoid duplicates and ensure order (simple approach)
                        if not self.data_store[pair_tf_key] or candle['timestamp'] > self.data_store[pair_tf_key][-1]['timestamp']:
                            self.data_store[pair_tf_key].append(candle)
                        elif candle['timestamp'] == self.data_store[pair_tf_key][-1]['timestamp']:
                             # Update the last candle if timestamp matches (real-time update)
                             self.data_store[pair_tf_key][-1] = candle


        except Exception as e:
            logger.error(f"Error handling candle data: {e} - Payload: {payload}")


    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket Error: {error}")
        self.is_connected = False
        self.is_authenticated = False
        # Optional: Implement reconnection logic here or in _on_close

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closure."""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        self.is_authenticated = False
        # Simple Reconnection Strategy
        logger.info("Attempting to reconnect in 5 seconds...")
        time.sleep(5)
        self._start_websocket() # Try to restart the connection


    def _on_open(self, ws):
        """Handle WebSocket opening."""
        logger.info("WebSocket connection opened.")
        self.is_connected = True
        # Authentication might happen after receiving the '0' message from Socket.IO

    def _authenticate(self):
         """Send authentication message using SSID."""
         if self.ws and self.is_connected:
             try:
                 # Format based on common Socket.IO/PocketOption patterns
                 # May need 'isDemo', 'uid' etc. depending on server requirements
                 auth_message = f'42["auth",{{"session":"{self.ssid}"}}]'
                 logger.info("Sending authentication message...")
                 self.ws.send(auth_message)
             except Exception as e:
                 logger.error(f"Failed to send authentication message: {e}")

    def _subscribe_to_asset(self, pair, timeframe):
        """Send subscription message for a specific asset and timeframe."""
        if self.ws and self.is_authenticated: # Only subscribe if authenticated
             asset_symbol = self.pair_map.get(pair)
             period_seconds = self.timeframes_seconds.get(timeframe)

             if not asset_symbol or not period_seconds:
                  logger.error(f"Cannot subscribe: Invalid pair '{pair}' or timeframe '{timeframe}'")
                  return

             pair_tf_key = f"{asset_symbol}_{period_seconds}"
             if pair_tf_key in self.subscribed_assets:
                  # logger.debug(f"Already subscribed to {pair_tf_key}")
                  return

             try:
                # This message format is a GUESS - needs verification
                # Might be 'subscribe_candles', 'get_candles', etc.
                subscribe_message = f'42["subscribe",{{"asset":"{asset_symbol}","period":{period_seconds}}}]'
                # Alternate guess: f'42["get_candles",{{"asset":"{asset_symbol}","period":{period_seconds}, "limit": 100}}]'

                logger.info(f"Subscribing to {pair} ({asset_symbol}) - {timeframe} ({period_seconds}s)...")
                self.ws.send(subscribe_message)
                self.subscribed_assets.add(pair_tf_key)
             except Exception as e:
                 logger.error(f"Failed to send subscription message for {pair_tf_key}: {e}")
        elif not self.is_connected:
             logger.warning(f"Cannot subscribe to {pair} {timeframe}: WebSocket not connected.")
        elif not self.is_authenticated:
             logger.warning(f"Cannot subscribe to {pair} {timeframe}: WebSocket not authenticated.")


    def _resubscribe_assets(self):
        """Resubscribe to all previously tracked assets after reconnection."""
        logger.info("Resubscribing to tracked assets...")
        current_subscriptions = self.subscribed_assets.copy() # Avoid modifying set during iteration
        self.subscribed_assets.clear() # Clear old set, _subscribe_to_asset will re-add them
        with self.data_lock: # Ensure data_store keys match reality
            for pair_tf_key in current_subscriptions:
                 try:
                     # Need to reverse map the key back to pair/timeframe
                     asset_symbol, period_seconds_str = pair_tf_key.rsplit('_', 1)
                     period_seconds = int(period_seconds_str)
                     # Find original pair name and timeframe string
                     original_pair = next((p for p, s in self.pair_map.items() if s == asset_symbol), None)
                     original_tf = next((tf for tf, s in self.timeframes_seconds.items() if s == period_seconds), None)

                     if original_pair and original_tf:
                          # Use a small delay if needed when resubscribing many assets
                          # time.sleep(0.1)
                          self._subscribe_to_asset(original_pair, original_tf)
                     else:
                          logger.warning(f"Could not reverse map key {pair_tf_key} for resubscription.")
                 except Exception as e:
                     logger.error(f"Error during resubscription for {pair_tf_key}: {e}")

    def _run_websocket(self):
        """Run the WebSocket connection loop."""
        logger.info(f"Attempting to connect to WebSocket: {self.ws_url}")
        self.ws = websocket.WebSocketApp(self.ws_url,
                                         on_open=self._on_open,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close)
        # Disable SSL verification if needed (use carefully)
        # self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        # Enable trace for debugging
        # websocket.enableTrace(True)
        self.ws.run_forever()


    def _start_websocket(self):
        """Start the WebSocket connection in a background thread."""
        if self.thread and self.thread.is_alive():
             logger.warning("WebSocket thread already running.")
             return

        self.thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.thread.start()
        logger.info("WebSocket connection thread started.")

    def fetch_real_candles(self, pair, timeframe="5m", limit=100):
        """
        Fetch candle data from the live WebSocket stream.
        """
        if not self.is_connected or not self.is_authenticated:
            logger.warning(f"WebSocket not ready (Connected: {self.is_connected}, Authenticated: {self.is_authenticated}). Using fallback for {pair}.")
            return self._get_fallback_data(pair, timeframe, limit)

        asset_symbol = self.pair_map.get(pair)
        period_seconds = self.timeframes_seconds.get(timeframe)

        if not asset_symbol or not period_seconds:
            logger.error(f"Invalid pair or timeframe for fetching: {pair} {timeframe}")
            return self._get_fallback_data(pair, timeframe, limit) # Use fallback if invalid

        pair_tf_key = f"{asset_symbol}_{period_seconds}"

        # Ensure subscription is active for this asset/timeframe
        if pair_tf_key not in self.subscribed_assets:
             self._subscribe_to_asset(pair, timeframe)
             # Wait a moment for data to potentially arrive after subscription
             time.sleep(1)


        with self.data_lock:
            if pair_tf_key in self.data_store and self.data_store[pair_tf_key]:
                # Get the last 'limit' candles from the deque
                candles = list(self.data_store[pair_tf_key])[-limit:]

                if not candles:
                     logger.warning(f"No candle data available yet for {pair_tf_key}. Using fallback.")
                     return self._get_fallback_data(pair, timeframe, limit)

                # Format data as expected by the rest of the bot
                opens = [c['open'] for c in candles]
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                closes = [c['close'] for c in candles]
                volumes = [c['volume'] for c in candles]
                timestamps = [c['timestamp'] for c in candles]

                return {
                    'success': True,
                    'price': closes[-1],
                    'opens': opens, 'highs': highs, 'lows': lows, 'closes': closes,
                    'volumes': volumes, 'timestamps': timestamps,
                    'pair': pair, 'is_otc': 'OTC' in pair,
                    'data_source': 'REAL_WEBSOCKET'
                }
            else:
                logger.warning(f"No data in store for {pair_tf_key}. Using fallback.")
                return self._get_fallback_data(pair, timeframe, limit)


    def _get_fallback_data(self, pair, timeframe, limit):
        """Enhanced fallback with realistic price simulation."""
        logger.info(f"Using enhanced fallback data for {pair}")
        # ... (Keep your existing fallback data generation logic here) ...
        # Base prices (close to real market values)
        base_prices = {
            "EUR/USD": 1.0685, "GBP/USD": 1.2644, "USD/JPY": 149.85,
            "AUD/USD": 0.6534, "XAU/USD": 2638.50, "BTC/USD": 97234.00,
            "AUD/CAD OTC": 0.9085, "AUD/USD OTC": 0.6534,
            "CAD/JPY OTC": 106.45, "CHF/JPY OTC": 169.23,
            "EUR/CHF OTC": 0.9362, "GBP/AUD OTC": 1.9365,
            "NZD/JPY OTC": 88.42, "USD/CHF OTC": 0.8863
        }
        base_price = base_prices.get(pair, 1.0)
        closes, opens, highs, lows, volumes = [], [], [], [], []
        current_price = base_price
        tf_seconds = self.timeframes_seconds.get(timeframe, 300)

        for _ in range(limit):
            trend = np.random.choice([-1, 0, 1], p=[0.35, 0.30, 0.35])
            volatility = np.random.normal(0, 0.0015)
            price_change = (trend * 0.0005) + volatility
            current_price *= (1 + price_change)

            open_price = current_price * (1 + np.random.normal(0, 0.0003))
            close_price = current_price * (1 + np.random.normal(0, 0.0003))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.0008)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.0008)))

            opens.append(round(open_price, 5))
            highs.append(round(high_price, 5))
            lows.append(round(low_price, 5))
            closes.append(round(close_price, 5))
            volumes.append(int(np.random.uniform(1000, 5000)))

        return {
            'success': True, 'price': closes[-1], 'opens': opens, 'highs': highs,
            'lows': lows, 'closes': closes, 'volumes': volumes,
            'timestamps': [int(time.time()) - (i * tf_seconds) for i in range(limit, 0, -1)],
            'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'FALLBACK_ENHANCED'
        }

    def get_market_sentiment(self, pair):
        """Analyze recent price action for market sentiment using WebSocket data."""
        # Use fetch_real_candles to get data, it handles WS or fallback
        data = self.fetch_real_candles(pair, timeframe="5m", limit=20)

        if not data or not data['success'] or len(data['closes']) < 2:
            return {'sentiment': 'NEUTRAL', 'strength': 0}

        try:
            closes = data['closes']
            price_change = (closes[-1] - closes[0]) / closes[0] * 100
            bullish_candles = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
            bearish_candles = len(closes) - 1 - bullish_candles

            if price_change > 0.05 and bullish_candles > bearish_candles:
                sentiment, strength = 'BULLISH', min(int(abs(price_change) * 50), 100)
            elif price_change < -0.05 and bearish_candles > bullish_candles:
                sentiment, strength = 'BEARISH', min(int(abs(price_change) * 50), 100)
            else:
                sentiment, strength = 'NEUTRAL', 50

            return {'sentiment': sentiment, 'strength': strength}

        except Exception as e:
            logger.error(f"Error calculating sentiment for {pair}: {e}")
            return {'sentiment': 'NEUTRAL', 'strength': 0}

# ==================== Global API Instance ====================
# IMPORTANT: Replace YOUR_SSID_HERE with your actual Session ID
# In a real app, load this securely, don't hardcode it.
YOUR_SSID = "A44Q_EPGwN98Mx5Ot" # <<< YOUR ACTUAL SSID HERE

pocket_api = PocketOptionAPI(ssid=YOUR_SSID)

# Optional: Add a small delay to allow WebSocket connection to establish
# logger.info("Waiting a few seconds for WebSocket connection...")
# time.sleep(5)
# logger.info("Ready.")
