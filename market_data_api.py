import socketio
import threading
import time
import logging
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

class PocketOptionAPI:
    """
    Connects to Pocket Option using the python-socketio library,
    which correctly handles the Socket.IO protocol.
    Includes the latest authentication message.
    """

    def __init__(self):
        # ssl_verify=False might be needed if server uses self-signed cert
        self.sio = socketio.Client(logger=False, engineio_logger=False, ssl_verify=False)
        self.is_connected = False
        self.is_authenticated = False
        self.data_store = {}
        self.data_lock = threading.Lock()
        self.subscribed_assets = set()
        # Define base URL and path separately
        self.ws_base_url = "wss://chat-po.site"
        self.ws_path = "/cabinet-client/socket.io/" # Make sure this path is correct

        self.timeframes_seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}
        self.pair_map = {
            "AUD/CAD OTC": "AUDCAD_otc", "AUD/USD OTC": "AUDUSD_otc",
            "CAD/JPY OTC": "CADJPY_otc", "CHF/JPY OTC": "CHFJPY_otc",
            "EUR/CHF OTC": "EURCHF_otc", "GBP/AUD OTC": "GBPAUD_otc",
            "NZD/JPY OTC": "NZDJPY_otc", "USD/CHF OTC": "USDCHF_otc",
            "EUR/USD": "EURUSD", "GBP/USD": "GBPUSD",
            "USD/JPY": "USDJPY", "XAU/USD": "XAUUSD",
        }

        self._register_handlers()
        self._start_connection()

    def _register_handlers(self):
        @self.sio.event
        def connect():
            logger.info("Socket.IO connection established. Sending auth...")
            self.is_connected = True
            # The actual auth message is now hardcoded in _authenticate
            self._authenticate() # Call authenticate function

        @self.sio.event
        def disconnect():
            logger.warning("Socket.IO disconnected.")
            self.is_connected = False
            self.is_authenticated = False # Reset auth status on disconnect

        # Listen for the specific success event name found in browser
        @self.sio.on('auth/success')
        def on_auth_success(data):
            logger.info(f"Authentication successful via 'auth/success': {data}")
            self.is_authenticated = True
            self._resubscribe_assets() # Subscribe/resubscribe after success

        @self.sio.on('candles')
        def on_candles(data):
            # Implicitly authenticate if we receive candles before auth/success
            if not self.is_authenticated:
                logger.info("Received candle data - implicitly authenticating.")
                self.is_authenticated = True
            self._handle_candle_data(data)

        @self.sio.on('connect_error')
        def on_connect_error(data):
            logger.error(f"Socket.IO connection error: {data}")

        @self.sio.event # Catch generic errors from server
        def error(data):
             logger.error(f"Socket.IO server error event: {data}")
             # Check if it's an auth error specifically
             if isinstance(data, dict) and 'auth' in data.get('message', '').lower():
                 logger.error("Authentication likely failed based on error event.")
                 self.is_authenticated = False


    def _authenticate(self):
         """Send the specific authentication message captured."""
         if self.sio and self.is_connected:
             try:
                 # --- THIS IS THE UPDATED AUTH MESSAGE ---
                 # Use the exact message captured from the browser
                 # It's better to send the event name and payload separately for python-socketio
                 event_name = "auth"
                 payload = {"sessionToken":"65cc8b38c60a4487987805d218564b46","uid":"82434257","lang":"en","currentUrl":"cabinet","isChart":1}
                 # ----------------------------------------
                 logger.info(f"Sending authentication event '{event_name}' with payload...")
                 self.sio.emit(event_name, payload)
                 # Now wait for 'auth/success' or 'error' event in handlers
             except Exception as e:
                 logger.error(f"Failed to send authentication message: {e}")

    def _handle_candle_data(self, payload):
        try:
            asset_symbol = payload.get('asset')
            period_seconds = payload.get('period')
            candles_list = payload.get('candles', [])
            if not all([asset_symbol, period_seconds, candles_list]): return

            pair_tf_key = f"{asset_symbol}_{period_seconds}"
            with self.data_lock:
                if pair_tf_key not in self.data_store: self.data_store[pair_tf_key] = deque(maxlen=200)
                for candle_data in candles_list:
                    candle = {'timestamp': candle_data.get('t'), 'open': float(candle_data.get('o', 0)), 'high': float(candle_data.get('h', 0)), 'low': float(candle_data.get('l', 0)), 'close': float(candle_data.get('c', 0)), 'volume': float(candle_data.get('v', 0))}
                    if candle['timestamp'] and candle['close'] > 0:
                        # Simple append/update logic
                        if not self.data_store[pair_tf_key] or candle['timestamp'] > self.data_store[pair_tf_key][-1]['timestamp']:
                            self.data_store[pair_tf_key].append(candle)
                        elif candle['timestamp'] == self.data_store[pair_tf_key][-1]['timestamp']:
                            self.data_store[pair_tf_key][-1] = candle
        except Exception as e: logger.error(f"Error handling candle data: {e} - Payload: {payload}")


    def _connection_thread(self):
        while True:
            try:
                logger.info(f"Attempting to connect to Socket.IO server: {self.ws_base_url} with path {self.ws_path}")
                self.sio.connect(
                    self.ws_base_url,
                    transports=['websocket'],
                    socketio_path=self.ws_path
                )
                logger.info("Socket.IO connect call completed, entering wait loop.")
                self.sio.wait() # Keep thread alive until disconnected
                logger.info("Socket.IO wait loop finished (disconnected).")
            except socketio.exceptions.ConnectionError as e:
                 logger.error(f"Socket.IO ConnectionError: {e}. Retrying in 10 seconds...")
            except Exception as e:
                logger.error(f"Socket.IO connection failed unexpectedly: {e}. Retrying in 10 seconds...")

            # If connect or wait fails/exits, ensure flags are reset and wait before retrying
            self.is_connected = False
            self.is_authenticated = False
            time.sleep(10)


    def _start_connection(self):
        with self.data_lock:
            if hasattr(self, 'connection_thread') and self.connection_thread.is_alive():
                return
            self.connection_thread = threading.Thread(target=self._connection_thread, daemon=True)
            self.connection_thread.start()
            logger.info("Socket.IO connection thread started/restarted.")

    def _subscribe_to_asset(self, pair, timeframe):
        if self.is_connected and self.is_authenticated: # Only subscribe if authenticated
             asset_symbol = self.pair_map.get(pair)
             period_seconds = self.timeframes_seconds.get(timeframe)
             if not asset_symbol or not period_seconds: return
             pair_tf_key = f"{asset_symbol}_{period_seconds}"
             # Avoid re-sending if already tracking
             # if pair_tf_key in self.subscribed_assets: return
             try:
                subscription_payload = {"asset": asset_symbol, "period": period_seconds}
                # Use the event name captured or guessed from browser
                event_name = "candles/subscribe"
                logger.info(f"Sending subscription event '{event_name}' for {pair} ({pair_tf_key})...")
                self.sio.emit(event_name, subscription_payload)
                self.subscribed_assets.add(pair_tf_key)
             except Exception as e: logger.error(f"Failed to send subscription for {pair}: {e}")
        elif not self.is_connected:
             logger.warning("Cannot subscribe: Socket.IO not connected.")
        else: # Not authenticated
             logger.warning("Cannot subscribe: Socket.IO not authenticated.")


    def _resubscribe_assets(self):
        logger.info("Resubscribing to tracked assets after auth success...")
        time.sleep(1) # Brief pause
        target_subscriptions = self.subscribed_assets.copy()
        # Clear the set so _subscribe_to_asset sends the request again
        self.subscribed_assets.clear()
        for pair_tf_key in target_subscriptions:
             try:
                 asset_symbol, period_seconds_str = pair_tf_key.rsplit('_', 1); period_seconds = int(period_seconds_str)
                 original_pair = next((p for p, s in self.pair_map.items() if s == asset_symbol), None)
                 original_tf = next((tf for tf, s in self.timeframes_seconds.items() if s == period_seconds), None)
                 if original_pair and original_tf:
                     self._subscribe_to_asset(original_pair, original_tf)
                     time.sleep(0.1) # Stagger resubscriptions slightly
             except Exception as e: logger.error(f"Error during resubscription for {pair_tf_key}: {e}")

    def fetch_real_candles(self, pair, timeframe="5m", limit=100):
        # Check connection and authentication status first
        if not self.is_connected or not self.is_authenticated:
            logger.warning(f"Socket.IO not ready (Connected: {self.is_connected}, Authenticated: {self.is_authenticated}). Using fallback for {pair}.")
            return self._get_fallback_data(pair, timeframe, limit)

        asset_symbol, period_seconds = self.pair_map.get(pair), self.timeframes_seconds.get(timeframe)
        if not asset_symbol or not period_seconds: return self._get_fallback_data(pair, timeframe, limit)
        pair_tf_key = f"{asset_symbol}_{period_seconds}"

        # Ensure subscription is active (or attempt it)
        if pair_tf_key not in self.subscribed_assets:
            logger.info(f"Subscription for {pair_tf_key} not marked active, attempting subscribe.")
            self._subscribe_to_asset(pair, timeframe)
            time.sleep(2) # Allow time for potential data arrival after first subscribe

        # Try fetching data from store
        with self.data_lock:
            if pair_tf_key in self.data_store and len(self.data_store[pair_tf_key]) > 0:
                candles = list(self.data_store[pair_tf_key])[-limit:] # Get the most recent 'limit' candles
                # Check data freshness
                latest_timestamp = candles[-1]['timestamp']
                if time.time() - latest_timestamp > (period_seconds * 3): # If data is older than 3 candle periods
                    logger.warning(f"Data for {pair_tf_key} seems stale (last update: {datetime.fromtimestamp(latest_timestamp)}). Using fallback & re-subscribing.")
                    # Clear local subscription status to force re-subscribe next time
                    if pair_tf_key in self.subscribed_assets: self.subscribed_assets.remove(pair_tf_key)
                    # Don't trigger resubscribe here, let next call handle it. Return fallback.
                    return self._get_fallback_data(pair, timeframe, limit)
                else:
                    # Data is available and seems fresh
                    opens, highs, lows, closes, volumes, timestamps = zip(*[(c['open'], c['high'], c['low'], c['close'], c['volume'], c['timestamp']) for c in candles])
                    return {'success': True, 'price': closes[-1], 'opens': list(opens), 'highs': list(highs), 'lows': list(lows), 'closes': list(closes), 'volumes': list(volumes), 'timestamps': list(timestamps), 'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'REAL_WEBSOCKET'}

        # If we reach here, data wasn't in store or was empty
        logger.warning(f"No recent candle data in store for {pair_tf_key} after check. Using fallback.")
        return self._get_fallback_data(pair, timeframe, limit)


    def _get_fallback_data(self, pair, timeframe, limit):
        # (Fallback data generation remains the same)
        base_prices = {"EUR/USD": 1.0685, "AUD/CAD OTC": 0.9085} # Shortened
        base_price = base_prices.get(pair, 1.0); closes, opens, highs, lows, volumes = [], [], [], [], []; current_price = base_price; tf_seconds = self.timeframes_seconds.get(timeframe, 300)
        for _ in range(limit):
            price_change = (np.random.choice([-1, 0, 1], p=[0.35, 0.30, 0.35]) * 0.0005) + np.random.normal(0, 0.0015); current_price *= (1 + price_change)
            open_price, close_price = current_price * (1 + np.random.normal(0, 0.0003)), current_price * (1 + np.random.normal(0, 0.0003)); high_price, low_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.0008))), min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.0008)))
            opens.append(round(open_price, 5)); highs.append(round(high_price, 5)); lows.append(round(low_price, 5)); closes.append(round(close_price, 5)); volumes.append(int(np.random.uniform(1000, 5000)))
        return {'success': True, 'price': closes[-1], 'opens': opens, 'highs': highs,'lows': lows, 'closes': closes, 'volumes': volumes,'timestamps': [int(time.time()) - (i * tf_seconds) for i in range(limit, 0, -1)],'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'FALLBACK_ENHANCED'}

    def get_market_sentiment(self, pair):
        # (Market sentiment logic remains the same)
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
pocket_api = PocketOptionAPI()
