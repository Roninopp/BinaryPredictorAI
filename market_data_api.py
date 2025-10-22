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
        # Although ssid is passed, the _authenticate function below uses a hardcoded message
        # In a future version, _authenticate should be modified to use self.ssid dynamically
        self.ssid_param = ssid # Store it just in case, though not used in current _authenticate
        self.ws_url = "wss://chat-po.site/cabinet-client/socket.io/?EIO=4&transport=websocket"
        self.ws = None
        self.thread = None
        self.is_connected = False
        self.is_authenticated = False
        self.data_store = {}
        self.data_lock = threading.Lock()
        self.subscribed_assets = set()

        self.timeframes_seconds = {
            "1m": 60, "5m": 300, "15m": 900, "1h": 3600
        }
        self.pair_map = {
            "AUD/CAD OTC": "AUDCAD_otc", "AUD/USD OTC": "AUDUSD_otc",
            "CAD/JPY OTC": "CADJPY_otc", "CHF/JPY OTC": "CHFJPY_otc",
            "EUR/CHF OTC": "EURCHF_otc", "GBP/AUD OTC": "GBPAUD_otc",
            "NZD/JPY OTC": "NZDJPY_otc", "USD/CHF OTC": "USDCHF_otc",
            "EUR/USD": "EURUSD", "GBP/USD": "GBPUSD",
            "USD/JPY": "USDJPY", "XAU/USD": "XAUUSD",
        }

        self._start_websocket()

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        # logger.debug(f"WS Received: {message}")
        try:
            if message.startswith('42'): # Socket.IO message with data
                data_part = message[2:]
                try:
                    event_data = json.loads(data_part)
                    event_name = event_data[0]
                    payload = event_data[1] if len(event_data) > 1 else {}

                    if event_name == "candles":
                        self._handle_candle_data(payload)
                    elif event_name == "successauth": # Check for successauth event
                         logger.info("WebSocket authenticated successfully via 'successauth' event.")
                         self.is_authenticated = True
                         self._resubscribe_assets()
                    # Add handlers for other events like 'connect_error', 'error' etc.
                    elif event_name == "error":
                         logger.error(f"Received WebSocket error event: {payload}")
                         if "auth" in str(payload).lower(): # Check if it's an auth error
                             self.is_authenticated = False
                             logger.error("Authentication failed. Check SSID/Auth message format.")


                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from message: {data_part}")
                except Exception as e:
                    logger.error(f"Error processing message payload: {e} - Data: {data_part}")

            elif message.startswith('0'): # Socket.IO connection confirmation
                logger.info("Socket.IO connection established. Sending auth...")
                self._authenticate() # Send authentication after connection confirmation
            elif message.startswith('3'): # Socket.IO Pong/Ping check
                 # Send Pong back if needed (some servers require this)
                 # try: ws.send('3') except Exception: pass
                 pass # logger.debug("Received Ping/Pong")
            elif message == '2': # Socket.IO Ping from server
                 try:
                     ws.send('3') # Send Pong back
                     # logger.debug("Sent Pong")
                 except Exception as e:
                     logger.warning(f"Failed to send Pong: {e}")


        except Exception as e:
            logger.error(f"Error in _on_message: {e} - Message: {message}")

    def _handle_candle_data(self, payload):
        """Parse and store candle data."""
        try:
            candles_list = []
            asset_symbol = None
            period_seconds = None

            if isinstance(payload, dict) and 'candles' in payload:
                 candles_list = payload.get('candles', [])
                 asset_symbol = payload.get('asset')
                 period_seconds = payload.get('period')
            elif isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict):
                 candles_list = payload
                 if 'a' in candles_list[0] and 'p' in candles_list[0]:
                    asset_symbol = candles_list[0]['a']
                    period_seconds = candles_list[0]['p']

            if not asset_symbol or not period_seconds or not candles_list:
                return

            pair_tf_key = f"{asset_symbol}_{period_seconds}"

            with self.data_lock:
                if pair_tf_key not in self.data_store:
                    self.data_store[pair_tf_key] = deque(maxlen=200)

                for candle_data in candles_list:
                    candle = {
                        'timestamp': candle_data.get('t'),
                        'open': float(candle_data.get('o', 0)),
                        'high': float(candle_data.get('h', 0)),
                        'low': float(candle_data.get('l', 0)),
                        'close': float(candle_data.get('c', 0)),
                        'volume': float(candle_data.get('v', 0))
                    }
                    if candle['timestamp'] and candle['close'] > 0:
                        if not self.data_store[pair_tf_key] or candle['timestamp'] > self.data_store[pair_tf_key][-1]['timestamp']:
                            self.data_store[pair_tf_key].append(candle)
                        elif candle['timestamp'] == self.data_store[pair_tf_key][-1]['timestamp']:
                             self.data_store[pair_tf_key][-1] = candle


        except Exception as e:
            logger.error(f"Error handling candle data: {e} - Payload: {payload}")


    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        # Don't assume disconnection on all errors, some might be recoverable
        logger.error(f"WebSocket Error: {error}")
        if isinstance(error, (websocket.WebSocketConnectionClosedException, ConnectionResetError, BrokenPipeError)):
             self.is_connected = False
             self.is_authenticated = False
             logger.warning("Connection closed due to error.")
        # Optional: Implement reconnection logic here or in _on_close

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closure."""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        self.is_authenticated = False
        logger.info("Attempting to reconnect in 10 seconds...")
        # Use a timer to avoid blocking if _start_websocket is called immediately
        threading.Timer(10.0, self._start_websocket).start()


    def _on_open(self, ws):
        """Handle WebSocket opening."""
        logger.info("WebSocket connection opened.")
        self.is_connected = True
        # Authentication is triggered by receiving the '0' message from Socket.IO

    def _authenticate(self):
         """Send the specific authentication message captured from the browser."""
         if self.ws and self.is_connected:
             try:
                 # USE THE EXACT MESSAGE YOU COPIED - Use r'...' for raw string
                 auth_message = r'42["auth",{"session":"a:4:{s:10:\"session_id\";s:32:\"6995b9b1954901fe2cfbc3b2250ab256\";s:10:\"ip_address\";s:15:\"223.188.126.208\";s:10:\"user_agent\";s:111:\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36\";s:13:\"last_activity\";i:1761150495;}d08265387ffeaceb16fd0362d3cd843e","isDemo":0,"uid":82434257,"platform":2,"isFastHistory":true,"isOptimized":true}]'
                 logger.info("Sending full authentication message...")
                 self.ws.send(auth_message)
                 # Assume authentication might succeed - wait for 'successauth' or 'error' event
             except Exception as e:
                 logger.error(f"Failed to send authentication message: {e}")

    def _subscribe_to_asset(self, pair, timeframe):
        """Send subscription message for a specific asset and timeframe."""
        if self.ws and self.is_authenticated:
             asset_symbol = self.pair_map.get(pair)
             period_seconds = self.timeframes_seconds.get(timeframe)

             if not asset_symbol or not period_seconds:
                  logger.error(f"Cannot subscribe: Invalid pair '{pair}' or timeframe '{timeframe}'")
                  return

             pair_tf_key = f"{asset_symbol}_{period_seconds}"
             if pair_tf_key in self.subscribed_assets:
                  return

             try:
                # Format likely involves asset and period
                # Example: subscribe to candles for a specific asset and period
                # This format needs verification based on captured browser messages
                subscribe_message = f'42["candles/subscribe",{{"asset":"{asset_symbol}","period":{period_seconds}}}]'
                # Alternate possibility: f'42["subscribe",{{"channel":"candles","asset":"{asset_symbol}","period":{period_seconds}}}]'

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
        # Wait a brief moment after auth success before resubscribing
        time.sleep(1)
        current_subscriptions = self.subscribed_assets.copy()
        self.subscribed_assets.clear()
        with self.data_lock:
            for pair_tf_key in current_subscriptions:
                 try:
                     asset_symbol, period_seconds_str = pair_tf_key.rsplit('_', 1)
                     period_seconds = int(period_seconds_str)
                     original_pair = next((p for p, s in self.pair_map.items() if s == asset_symbol), None)
                     original_tf = next((tf for tf, s in self.timeframes_seconds.items() if s == period_seconds), None)

                     if original_pair and original_tf:
                          self._subscribe_to_asset(original_pair, original_tf)
                     else:
                          logger.warning(f"Could not reverse map key {pair_tf_key} for resubscription.")
                 except Exception as e:
                     logger.error(f"Error during resubscription for {pair_tf_key}: {e}")

    def _run_websocket(self):
        """Run the WebSocket connection loop."""
        while True: # Keep trying to connect
            logger.info(f"Attempting to connect to WebSocket: {self.ws_url}")
            # websocket.enableTrace(True) # Uncomment for extreme debugging
            self.ws = websocket.WebSocketApp(self.ws_url,
                                            on_open=self._on_open,
                                            on_message=self._on_message,
                                            on_error=self._on_error,
                                            on_close=self._on_close)
            try:
                # Disable SSL verification - often needed for unofficial endpoints
                self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=20, ping_timeout=10)
            except Exception as e:
                logger.error(f"WebSocket run_forever error: {e}")

            # If run_forever exits (due to error or close), wait before retrying
            self.is_connected = False
            self.is_authenticated = False
            logger.info("WebSocket connection loop exited. Retrying connection in 10 seconds...")
            time.sleep(10)


    def _start_websocket(self):
        """Start the WebSocket connection in a background thread if not already running."""
        with self.data_lock: # Use lock to prevent race condition starting multiple threads
            if self.thread and self.thread.is_alive():
                # logger.warning("WebSocket thread already running.")
                return

            self.thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.thread.start()
            logger.info("WebSocket connection thread started/restarted.")

    def fetch_real_candles(self, pair, timeframe="5m", limit=100):
        """Fetch candle data from the live WebSocket stream."""
        # Ensure connection attempt has started
        if not self.thread or not self.thread.is_alive():
             self._start_websocket()
             time.sleep(5) # Give it a moment to try connecting

        if not self.is_connected or not self.is_authenticated:
            logger.warning(f"WebSocket not ready (Connected: {self.is_connected}, Authenticated: {self.is_authenticated}). Using fallback for {pair}.")
            return self._get_fallback_data(pair, timeframe, limit)

        asset_symbol = self.pair_map.get(pair)
        period_seconds = self.timeframes_seconds.get(timeframe)

        if not asset_symbol or not period_seconds:
            logger.error(f"Invalid pair or timeframe for fetching: {pair} {timeframe}")
            return self._get_fallback_data(pair, timeframe, limit)

        pair_tf_key = f"{asset_symbol}_{period_seconds}"

        if pair_tf_key not in self.subscribed_assets:
             self._subscribe_to_asset(pair, timeframe)
             time.sleep(1.5) # Allow slightly longer for subscription and first data

        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            with self.data_lock:
                if pair_tf_key in self.data_store and self.data_store[pair_tf_key]:
                    candles = list(self.data_store[pair_tf_key])[-limit:]

                    if not candles:
                        logger.warning(f"No candle data available yet for {pair_tf_key}. Retrying...")
                        # Fall through to retry logic outside the lock
                    else:
                        opens = [c['open'] for c in candles]
                        highs = [c['high'] for c in candles]
                        lows = [c['low'] for c in candles]
                        closes = [c['close'] for c in candles]
                        volumes = [c['volume'] for c in candles]
                        timestamps = [c['timestamp'] for c in candles]

                        # Basic check: Ensure latest timestamp isn't too old
                        if time.time() - timestamps[-1] > (period_seconds * 3): # If data is older than 3 candles
                             logger.warning(f"Data for {pair_tf_key} seems stale (last update: {timestamps[-1]}). Requesting again.")
                             self._subscribe_to_asset(pair, timeframe) # Re-request subscription
                             # Fall through to retry logic
                        else:
                            return {
                                'success': True, 'price': closes[-1],
                                'opens': opens, 'highs': highs, 'lows': lows, 'closes': closes,
                                'volumes': volumes, 'timestamps': timestamps,
                                'pair': pair, 'is_otc': 'OTC' in pair,
                                'data_source': 'REAL_WEBSOCKET'
                            }

            # If data wasn't ready or stale, wait and retry
            retry_count += 1
            logger.info(f"Waiting for data for {pair_tf_key} (Attempt {retry_count}/{max_retries})...")
            time.sleep(2) # Wait longer between retries

        # If still no data after retries, use fallback
        logger.error(f"Failed to get real-time data for {pair_tf_key} after {max_retries} attempts. Using fallback.")
        return self._get_fallback_data(pair, timeframe, limit)


    def _get_fallback_data(self, pair, timeframe, limit):
        """Enhanced fallback with realistic price simulation."""
        # logger.info(f"Using enhanced fallback data for {pair}") # Reduced verbosity
        base_prices = {
            "EUR/USD": 1.0685, "GBP/USD": 1.2644, "USD/JPY": 149.85, "AUD/USD": 0.6534,
            "XAU/USD": 2638.50, "BTC/USD": 97234.00, "AUD/CAD OTC": 0.9085,
            "AUD/USD OTC": 0.6534, "CAD/JPY OTC": 106.45, "CHF/JPY OTC": 169.23,
            "EUR/CHF OTC": 0.9362, "GBP/AUD OTC": 1.9365, "NZD/JPY OTC": 88.42,
            "USD/CHF OTC": 0.8863
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
            opens.append(round(open_price, 5)); highs.append(round(high_price, 5))
            lows.append(round(low_price, 5)); closes.append(round(close_price, 5))
            volumes.append(int(np.random.uniform(1000, 5000)))

        return {
            'success': True, 'price': closes[-1], 'opens': opens, 'highs': highs,
            'lows': lows, 'closes': closes, 'volumes': volumes,
            'timestamps': [int(time.time()) - (i * tf_seconds) for i in range(limit, 0, -1)],
            'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'FALLBACK_ENHANCED'
        }

    def get_market_sentiment(self, pair):
        """Analyze recent price action using WebSocket data."""
        data = self.fetch_real_candles(pair, timeframe="5m", limit=20)
        if not data or not data['success'] or len(data['closes']) < 2:
            return {'sentiment': 'NEUTRAL', 'strength': 0}
        try:
            closes = data['closes']
            price_change = (closes[-1] - closes[0]) / closes[0] * 100
            bullish = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
            bearish = len(closes) - 1 - bullish
            if price_change > 0.05 and bullish > bearish: sentiment, strength = 'BULLISH', min(int(abs(price_change) * 50), 100)
            elif price_change < -0.05 and bearish > bullish: sentiment, strength = 'BEARISH', min(int(abs(price_change) * 50), 100)
            else: sentiment, strength = 'NEUTRAL', 50
            return {'sentiment': sentiment, 'strength': strength}
        except Exception as e:
            logger.error(f"Error calculating sentiment for {pair}: {e}")
            return {'sentiment': 'NEUTRAL', 'strength': 0}

# ==================== Global API Instance ====================
# IMPORTANT: Use the SSID you found earlier.
# In a real app, load this securely, don't hardcode it.
YOUR_SSID = "A44Q_EPGwN98Mx5Ot" # <<< Use your actual SSID from browser

# Initialize the API - it will start connecting in the background
pocket_api = PocketOptionAPI(ssid=YOUR_SSID)

# Add a small delay at startup ONLY IF NEEDED for initial connection.
# The fetch_real_candles function now has internal waits.
# logger.info("Allowing initial connection time...")
# time.sleep(5) # Adjust as needed, or remove if fetch_real_candles handles it
# logger.info("API Initialized.")
