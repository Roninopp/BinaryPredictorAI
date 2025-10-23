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
    Attempts implicit authentication and logs all message types.
    """

    def __init__(self, ssid=None):
        self.ssid_param = ssid
        self.ws_url = "wss://chat-po.site/cabinet-client/socket.io/?EIO=4&transport=websocket"
        self.ws = None
        self.thread = None
        self.is_connected = False
        # Assume authenticated might happen implicitly after sending message
        # We will only set this to True if we see candle data arriving, or a specific success message.
        self.is_authenticated = False
        self.data_store = {}
        self.data_lock = threading.Lock()
        self.subscribed_assets = set()
        self.initial_auth_sent = False # Flag to track if auth message has been sent

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
        try:
            # Log raw message for debugging if trace is enabled
            # logger.debug(f"Raw WS Received: {message}")

            if message.startswith('42'): # Socket.IO message with data
                data_part = message[2:]
                try:
                    event_data = json.loads(data_part)
                    event_name = event_data[0]
                    payload = event_data[1] if len(event_data) > 1 else {}

                    # --- ENHANCED LOGGING ---
                    logger.info(f"Received Event: {event_name} | Payload: {payload if len(str(payload)) < 200 else str(payload)[:200] + '...'}")
                    # ------------------------

                    if event_name == "candles":
                        # If we receive candles, we can assume authentication worked
                        if not self.is_authenticated:
                             logger.info("Received candle data - Assuming authentication successful.")
                             self.is_authenticated = True
                        self._handle_candle_data(payload)
                    elif event_name == "auth/success": # Explicit success check
                         logger.info("WebSocket authenticated successfully via 'auth/success' event.")
                         self.is_authenticated = True
                         if not self.subscribed_assets: # Subscribe only if not already done
                            self._resubscribe_assets()
                    elif event_name == "error":
                         logger.error(f"Received WebSocket error event: {payload}")
                         if "auth" in str(payload).lower():
                             self.is_authenticated = False
                             logger.error("Authentication failed via error event.")
                    # Add other known events if necessary

                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from message: {data_part}")
                except Exception as e:
                    logger.error(f"Error processing message payload: {e} - Data: {data_part}")

            elif message.startswith('0'): # Socket.IO connection confirmation
                logger.info("Socket.IO connection established. Sending auth...")
                self.initial_auth_sent = False # Reset flag on new connection
                self._authenticate()
            elif message == '2': # Socket.IO Ping from server
                 try:
                     ws.send('3') # Send Pong back
                     # logger.debug("Sent Pong in response to Ping")
                 except Exception as e:
                     logger.warning(f"Failed to send Pong: {e}")
            elif message.startswith('3'): # Pong received (likely echo of our pong)
                 pass # logger.debug("Received Pong")

        except Exception as e:
            logger.error(f"Error in _on_message: {e} - Message: {message}")

    def _handle_candle_data(self, payload):
        """Parse and store candle data."""
        try:
            candles_list, asset_symbol, period_seconds = [], None, None
            if isinstance(payload, dict) and 'candles' in payload:
                 candles_list, asset_symbol, period_seconds = payload.get('candles', []), payload.get('asset'), payload.get('period')
            elif isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict) and 'a' in payload[0] and 'p' in payload[0]:
                 candles_list, asset_symbol, period_seconds = payload, payload[0]['a'], payload[0]['p']
            if not all([asset_symbol, period_seconds, candles_list]): return

            pair_tf_key = f"{asset_symbol}_{period_seconds}"
            with self.data_lock:
                if pair_tf_key not in self.data_store: self.data_store[pair_tf_key] = deque(maxlen=200)
                new_candles_added = 0
                for candle_data in candles_list:
                    candle = {'timestamp': candle_data.get('t'), 'open': float(candle_data.get('o', 0)), 'high': float(candle_data.get('h', 0)), 'low': float(candle_data.get('l', 0)), 'close': float(candle_data.get('c', 0)), 'volume': float(candle_data.get('v', 0))}
                    if candle['timestamp'] and candle['close'] > 0:
                        if not self.data_store[pair_tf_key] or candle['timestamp'] > self.data_store[pair_tf_key][-1]['timestamp']:
                            self.data_store[pair_tf_key].append(candle); new_candles_added += 1
                        elif candle['timestamp'] == self.data_store[pair_tf_key][-1]['timestamp']: self.data_store[pair_tf_key][-1] = candle
                # if new_candles_added > 0: logger.debug(f"Added {new_candles_added} new candles for {pair_tf_key}")

        except Exception as e: logger.error(f"Error handling candle data: {e} - Payload: {payload}")

    def _on_error(self, ws, error):
        logger.error(f"WebSocket Error: {error}")
        if isinstance(error, (websocket.WebSocketConnectionClosedException, ConnectionResetError, BrokenPipeError)):
             self.is_connected, self.is_authenticated, self.initial_auth_sent = False, False, False
             logger.warning("Connection closed due to error.")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected, self.is_authenticated, self.initial_auth_sent = False, False, False
        logger.info("Attempting to reconnect in 10 seconds...")
        threading.Timer(10.0, self._start_websocket).start()

    def _on_open(self, ws):
        logger.info("WebSocket connection opened.")
        self.is_connected = True
        self.initial_auth_sent = False # Reset flag on successful open

    def _authenticate(self):
         """Send the specific authentication message and attempt immediate resubscribe."""
         if self.ws and self.is_connected and not self.initial_auth_sent:
             try:
                 auth_message = r'42["auth",{"sessionToken":"65cc8b38c60a4487987805d218564b46","uid":"82434257","lang":"en","currentUrl":"cabinet","isChart":1}]'
                 logger.info("Sending sessionToken authentication message...")
                 self.ws.send(auth_message)
                 self.initial_auth_sent = True # Mark as sent
                 # --- TRY RESUBSCRIBING IMMEDIATELY ---
                 logger.info("Attempting to resubscribe assets immediately after sending auth...")
                 # Run resubscribe in a separate thread to avoid blocking message handling
                 threading.Thread(target=self._resubscribe_assets, daemon=True).start()
                 # We still wait for an explicit success message or candle data to set is_authenticated=True
                 # -------------------------------------
             except Exception as e:
                 logger.error(f"Failed to send authentication message: {e}")
                 self.initial_auth_sent = False # Allow retry if sending failed

    def _subscribe_to_asset(self, pair, timeframe):
        # Only subscribe if connected, even if auth isn't confirmed yet (optimistic)
        if self.ws and self.is_connected:
             asset_symbol, period_seconds = self.pair_map.get(pair), self.timeframes_seconds.get(timeframe)
             if not asset_symbol or not period_seconds: return
             pair_tf_key = f"{asset_symbol}_{period_seconds}"
             # Avoid re-sending subscribe if already tracked locally
             if pair_tf_key in self.subscribed_assets: return
             try:
                subscribe_message = f'42["candles/subscribe",{{"asset":"{asset_symbol}","period":{period_seconds}}}]'
                logger.info(f"Sending subscription request for {pair} ({pair_tf_key})...")
                self.ws.send(subscribe_message)
                self.subscribed_assets.add(pair_tf_key) # Track desired subscription
             except Exception as e:
                 logger.error(f"Failed to send subscription message for {pair_tf_key}: {e}")
                 # Remove from subscribed if send failed? Maybe not, rely on resubscribe logic.

    def _resubscribe_assets(self):
        # Only proceed if we think we are connected.
        if not self.is_connected:
            logger.warning("Cannot resubscribe, WebSocket not connected.")
            return

        logger.info("Resubscribing to tracked assets...")
        time.sleep(1) # Brief pause after auth success / connection recovery
        # Create a temporary list of assets we WANT to be subscribed to
        target_subscriptions = self.subscribed_assets.copy()
        # Reset the current known subscriptions (they will be re-added on successful send)
        self.subscribed_assets.clear()

        # Try subscribing to all targets
        for pair_tf_key in target_subscriptions:
             try:
                 asset_symbol, period_seconds_str = pair_tf_key.rsplit('_', 1); period_seconds = int(period_seconds_str)
                 original_pair = next((p for p, s in self.pair_map.items() if s == asset_symbol), None)
                 original_tf = next((tf for tf, s in self.timeframes_seconds.items() if s == period_seconds), None)
                 if original_pair and original_tf:
                      self._subscribe_to_asset(original_pair, original_tf)
                      time.sleep(0.1) # Small delay between subscriptions
             except Exception as e: logger.error(f"Error during resubscription attempt for {pair_tf_key}: {e}")

    def _run_websocket(self):
        while True:
            logger.info(f"Attempting to connect to WebSocket: {self.ws_url}")
            # --- TRACE ENABLED ---
            websocket.enableTrace(True)
            # ---------------------
            self.ws = websocket.WebSocketApp(self.ws_url, on_open=self._on_open, on_message=self._on_message, on_error=self._on_error, on_close=self._on_close)
            try: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=20, ping_timeout=10)
            except Exception as e: logger.error(f"WebSocket run_forever error: {e}")
            # Reset flags on exit from run_forever
            self.is_connected, self.is_authenticated, self.initial_auth_sent = False, False, False
            logger.info("WebSocket connection loop exited. Retrying connection in 10 seconds..."); time.sleep(10)

    def _start_websocket(self):
        with self.data_lock: # Prevent race condition
            if self.thread and self.thread.is_alive(): return
            self.thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.thread.start()
            logger.info("WebSocket connection thread started/restarted.")

    def fetch_real_candles(self, pair, timeframe="5m", limit=100):
        if not (self.thread and self.thread.is_alive()): self._start_websocket(); time.sleep(5)

        # Check connection status first
        if not self.is_connected:
            logger.warning(f"WebSocket not connected. Using fallback for {pair}.")
            return self._get_fallback_data(pair, timeframe, limit)

        asset_symbol, period_seconds = self.pair_map.get(pair), self.timeframes_seconds.get(timeframe)
        if not asset_symbol or not period_seconds: return self._get_fallback_data(pair, timeframe, limit)
        pair_tf_key = f"{asset_symbol}_{period_seconds}"

        # Ensure subscription is attempted
        if pair_tf_key not in self.subscribed_assets:
             logger.info(f"Subscription for {pair_tf_key} not active, attempting now.")
             self._subscribe_to_asset(pair, timeframe)
             time.sleep(1.5) # Allow time for subscription

        # Check authentication status *after* attempting subscription (as receiving data confirms auth)
        if not self.is_authenticated:
            logger.warning(f"WebSocket connected but not authenticated. Using fallback for {pair}.")
            return self._get_fallback_data(pair, timeframe, limit)

        # Proceed to fetch data
        retry_count, max_retries = 0, 3
        while retry_count < max_retries:
            with self.data_lock:
                if pair_tf_key in self.data_store and self.data_store[pair_tf_key]:
                    candles = list(self.data_store[pair_tf_key])[-limit:]
                    if candles:
                        opens, highs, lows, closes, volumes, timestamps = zip(*[(c['open'], c['high'], c['low'], c['close'], c['volume'], c['timestamp']) for c in candles])
                        # Check data freshness before returning
                        if time.time() - timestamps[-1] > (period_seconds * 3):
                             logger.warning(f"Data for {pair_tf_key} seems stale (last: {timestamps[-1]}). Re-subscribing.")
                             # Run resubscribe in thread to avoid blocking fetch? Maybe better to just let retry handle it.
                             # Need to remove from subscribed assets to trigger _subscribe_to_asset again
                             if pair_tf_key in self.subscribed_assets: self.subscribed_assets.remove(pair_tf_key)
                             # Break inner loop, go to retry wait
                             break
                        else:
                            # Data looks good and fresh
                            return {'success': True, 'price': closes[-1], 'opens': list(opens), 'highs': list(highs), 'lows': list(lows), 'closes': list(closes), 'volumes': list(volumes), 'timestamps': list(timestamps), 'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'REAL_WEBSOCKET'}

            # If data wasn't ready or stale, wait and retry
            retry_count += 1
            logger.info(f"Waiting for fresh data {pair_tf_key} (Attempt {retry_count}/{max_retries})..."); time.sleep(2)

        # Fallback if still no data after retries
        logger.error(f"Failed to get fresh real-time data for {pair_tf_key} after retries. Using fallback."); return self._get_fallback_data(pair, timeframe, limit)


    def _get_fallback_data(self, pair, timeframe, limit):
        # Fallback data generation remains the same
        base_prices = {"EUR/USD": 1.0685, "GBP/USD": 1.2644, "AUD/CAD OTC": 0.9085} # Shortened for brevity
        base_price = base_prices.get(pair, 1.0); closes, opens, highs, lows, volumes = [], [], [], [], []; current_price = base_price; tf_seconds = self.timeframes_seconds.get(timeframe, 300)
        for _ in range(limit):
            price_change = (np.random.choice([-1, 0, 1], p=[0.35, 0.30, 0.35]) * 0.0005) + np.random.normal(0, 0.0015); current_price *= (1 + price_change)
            open_price, close_price = current_price * (1 + np.random.normal(0, 0.0003)), current_price * (1 + np.random.normal(0, 0.0003)); high_price, low_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.0008))), min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.0008)))
            opens.append(round(open_price, 5)); highs.append(round(high_price, 5)); lows.append(round(low_price, 5)); closes.append(round(close_price, 5)); volumes.append(int(np.random.uniform(1000, 5000)))
        return {'success': True, 'price': closes[-1], 'opens': opens, 'highs': highs,'lows': lows, 'closes': closes, 'volumes': volumes,'timestamps': [int(time.time()) - (i * tf_seconds) for i in range(limit, 0, -1)],'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'FALLBACK_ENHANCED'}

    def get_market_sentiment(self, pair):
        data = self.fetch_real_candles(pair, timeframe="5m", limit=20)
        if not (data and data['success'] and len(data['closes']) > 1): return {'sentiment': 'NEUTRAL', 'strength': 0}
        try:
            closes = data['closes']; price_change = (closes[-1] - closes[0]) / closes[0] * 100; bullish = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1]); bearish = len(closes) - 1 - bullish
            if price_change > 0.05 and bullish > bearish: sentiment, strength = 'BULLISH', min(int(abs(price_change) * 50), 100)
            elif price_change < -0.05 and bearish > bullish: sentiment, strength = 'BEARISH', min(int(abs(price_change) * 50), 100)
            else: sentiment, strength = 'NEUTRAL', 50
            return {'sentiment': sentiment, 'strength': strength}
        except Exception as e: logger.error(f"Error calculating sentiment for {pair}: {e}"); return {'sentiment': 'NEUTRAL', 'strength': 0}

# Global API Instance
pocket_api = PocketOptionAPI(ssid="placeholder")
