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

    def __init__(self, ssid=None):
        self.ssid_param = ssid
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
        try:
            if message.startswith('42'): # Socket.IO message with data
                data_part = message[2:]
                try:
                    event_data = json.loads(data_part)
                    event_name = event_data[0]
                    payload = event_data[1] if len(event_data) > 1 else {}

                    if event_name == "candles":
                        self._handle_candle_data(payload)
                    elif event_name == "auth/success":
                         logger.info("WebSocket authenticated successfully via 'auth/success' event.")
                         self.is_authenticated = True
                         self._resubscribe_assets()
                    elif event_name == "error":
                         logger.error(f"Received WebSocket error event: {payload}")
                         if "auth" in str(payload).lower():
                             self.is_authenticated = False
                             logger.error("Authentication failed. Check sessionToken/Auth message format.")

                except json.JSONDecodeError:
                    logger.warning(f"Could not decode JSON from message: {data_part}")
                except Exception as e:
                    logger.error(f"Error processing message payload: {e} - Data: {data_part}")

            elif message.startswith('0'): # Socket.IO connection confirmation
                logger.info("Socket.IO connection established. Sending auth...")
                self._authenticate()
            elif message == '2': # Socket.IO Ping from server
                 try:
                     ws.send('3') # Send Pong back
                 except Exception as e:
                     logger.warning(f"Failed to send Pong: {e}")

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
                for candle_data in candles_list:
                    candle = {'timestamp': candle_data.get('t'), 'open': float(candle_data.get('o', 0)), 'high': float(candle_data.get('h', 0)), 'low': float(candle_data.get('l', 0)), 'close': float(candle_data.get('c', 0)), 'volume': float(candle_data.get('v', 0))}
                    if candle['timestamp'] and candle['close'] > 0:
                        if not self.data_store[pair_tf_key] or candle['timestamp'] > self.data_store[pair_tf_key][-1]['timestamp']: self.data_store[pair_tf_key].append(candle)
                        elif candle['timestamp'] == self.data_store[pair_tf_key][-1]['timestamp']: self.data_store[pair_tf_key][-1] = candle
        except Exception as e: logger.error(f"Error handling candle data: {e} - Payload: {payload}")

    def _on_error(self, ws, error):
        logger.error(f"WebSocket Error: {error}")
        if isinstance(error, (websocket.WebSocketConnectionClosedException, ConnectionResetError, BrokenPipeError)):
             self.is_connected, self.is_authenticated = False, False
             logger.warning("Connection closed due to error.")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected, self.is_authenticated = False, False
        logger.info("Attempting to reconnect in 10 seconds...")
        threading.Timer(10.0, self._start_websocket).start()

    def _on_open(self, ws):
        logger.info("WebSocket connection opened.")
        self.is_connected = True

    def _authenticate(self):
         if self.ws and self.is_connected:
             try:
                 auth_message = r'42["auth",{"sessionToken":"65cc8b38c60a4487987805d218564b46","uid":"82434257","lang":"en","currentUrl":"cabinet","isChart":1}]'
                 logger.info("Sending sessionToken authentication message...")
                 self.ws.send(auth_message)
             except Exception as e: logger.error(f"Failed to send authentication message: {e}")

    def _subscribe_to_asset(self, pair, timeframe):
        if self.ws and self.is_authenticated:
             asset_symbol, period_seconds = self.pair_map.get(pair), self.timeframes_seconds.get(timeframe)
             if not asset_symbol or not period_seconds: return
             pair_tf_key = f"{asset_symbol}_{period_seconds}"
             if pair_tf_key in self.subscribed_assets: return
             try:
                subscribe_message = f'42["candles/subscribe",{{"asset":"{asset_symbol}","period":{period_seconds}}}]'
                logger.info(f"Subscribing to {pair} ({asset_symbol}) - {timeframe} ({period_seconds}s)...")
                self.ws.send(subscribe_message)
                self.subscribed_assets.add(pair_tf_key)
             except Exception as e: logger.error(f"Failed to send subscription message for {pair_tf_key}: {e}")

    def _resubscribe_assets(self):
        logger.info("Resubscribing to tracked assets..."); time.sleep(1)
        current_subscriptions, self.subscribed_assets = self.subscribed_assets.copy(), set()
        with self.data_lock:
            for pair_tf_key in current_subscriptions:
                 try:
                     asset_symbol, period_seconds_str = pair_tf_key.rsplit('_', 1); period_seconds = int(period_seconds_str)
                     original_pair = next((p for p, s in self.pair_map.items() if s == asset_symbol), None)
                     original_tf = next((tf for tf, s in self.timeframes_seconds.items() if s == period_seconds), None)
                     if original_pair and original_tf: self._subscribe_to_asset(original_pair, original_tf)
                 except Exception as e: logger.error(f"Error during resubscription for {pair_tf_key}: {e}")

    def _run_websocket(self):
        while True:
            logger.info(f"Attempting to connect to WebSocket: {self.ws_url}")
            # --- THIS IS THE EDITED LINE ---
            websocket.enableTrace(True)
            # ---------------------------------
            self.ws = websocket.WebSocketApp(self.ws_url, on_open=self._on_open, on_message=self._on_message, on_error=self._on_error, on_close=self._on_close)
            try: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=20, ping_timeout=10)
            except Exception as e: logger.error(f"WebSocket run_forever error: {e}")
            self.is_connected, self.is_authenticated = False, False
            logger.info("WebSocket connection loop exited. Retrying connection in 10 seconds..."); time.sleep(10)

    def _start_websocket(self):
        with self.data_lock:
            if self.thread and self.thread.is_alive(): return
            self.thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.thread.start()
            logger.info("WebSocket connection thread started/restarted.")

    def fetch_real_candles(self, pair, timeframe="5m", limit=100):
        if not (self.thread and self.thread.is_alive()): self._start_websocket(); time.sleep(5)
        if not self.is_connected or not self.is_authenticated:
            logger.warning(f"WebSocket not ready (Connected: {self.is_connected}, Authenticated: {self.is_authenticated}). Using fallback for {pair}.")
            return self._get_fallback_data(pair, timeframe, limit)

        asset_symbol, period_seconds = self.pair_map.get(pair), self.timeframes_seconds.get(timeframe)
        if not asset_symbol or not period_seconds: return self._get_fallback_data(pair, timeframe, limit)
        pair_tf_key = f"{asset_symbol}_{period_seconds}"
        if pair_tf_key not in self.subscribed_assets: self._subscribe_to_asset(pair, timeframe); time.sleep(1.5)

        retry_count, max_retries = 0, 3
        while retry_count < max_retries:
            with self.data_lock:
                if pair_tf_key in self.data_store and self.data_store[pair_tf_key]:
                    candles = list(self.data_store[pair_tf_key])[-limit:]
                    if candles:
                        opens, highs, lows, closes, volumes, timestamps = zip(*[(c['open'], c['high'], c['low'], c['close'], c['volume'], c['timestamp']) for c in candles])
                        if time.time() - timestamps[-1] > (period_seconds * 3): logger.warning(f"Data for {pair_tf_key} seems stale. Re-subscribing."); self._subscribe_to_asset(pair, timeframe)
                        else: return {'success': True, 'price': closes[-1], 'opens': list(opens), 'highs': list(highs), 'lows': list(lows), 'closes': list(closes), 'volumes': list(volumes), 'timestamps': list(timestamps), 'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'REAL_WEBSOCKET'}
            retry_count += 1; logger.info(f"Waiting for data {pair_tf_key} (Attempt {retry_count}/{max_retries})..."); time.sleep(2)
        return self._get_fallback_data(pair, timeframe, limit)

    def _get_fallback_data(self, pair, timeframe, limit):
        base_prices = {"EUR/USD": 1.0685, "GBP/USD": 1.2644, "AUD/CAD OTC": 0.9085}
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
