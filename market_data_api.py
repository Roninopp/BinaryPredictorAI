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
    """

    def __init__(self):
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.is_connected = False
        self.is_authenticated = False
        self.data_store = {}
        self.data_lock = threading.Lock()
        self.subscribed_assets = set()
        self.ws_url = "wss://chat-po.site/cabinet-client/socket.io/?EIO=4&transport=websocket"

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
            auth_payload = {"sessionToken":"65cc8b38c60a4487987805d218564b46","uid":"82434257","lang":"en","currentUrl":"cabinet","isChart":1}
            self.sio.emit("auth", auth_payload)

        @self.sio.event
        def disconnect():
            logger.warning("Socket.IO disconnected.")
            self.is_connected = False
            self.is_authenticated = False

        @self.sio.on('auth/success')
        def on_auth_success(data):
            logger.info(f"Authentication successful: {data}")
            self.is_authenticated = True
            self._resubscribe_assets()

        @self.sio.on('candles')
        def on_candles(data):
            if not self.is_authenticated:
                logger.info("Received candle data - implicitly authenticating.")
                self.is_authenticated = True
            self._handle_candle_data(data)

        @self.sio.on('connect_error')
        def on_connect_error(data):
            logger.error(f"Socket.IO connection error: {data}")

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
                        if not self.data_store[pair_tf_key] or candle['timestamp'] > self.data_store[pair_tf_key][-1]['timestamp']:
                            self.data_store[pair_tf_key].append(candle)
                        elif candle['timestamp'] == self.data_store[pair_tf_key][-1]['timestamp']:
                            self.data_store[pair_tf_key][-1] = candle
        except Exception as e: logger.error(f"Error handling candle data: {e} - Payload: {payload}")

    def _connection_thread(self):
        while True:
            try:
                logger.info("Attempting to connect to Socket.IO server...")
                self.sio.connect(self.ws_url, transports=['websocket'])
                self.sio.wait()
            except Exception as e:
                logger.error(f"Socket.IO connection failed: {e}. Retrying in 10 seconds...")
                time.sleep(10)

    def _start_connection(self):
        thread = threading.Thread(target=self._connection_thread, daemon=True)
        thread.start()
        logger.info("Socket.IO connection thread started.")

    def _subscribe_to_asset(self, pair, timeframe):
        if self.is_connected:
             asset_symbol = self.pair_map.get(pair)
             period_seconds = self.timeframes_seconds.get(timeframe)
             if not asset_symbol or not period_seconds: return
             pair_tf_key = f"{asset_symbol}_{period_seconds}"
             if pair_tf_key in self.subscribed_assets: return
             try:
                subscription_payload = {"asset": asset_symbol, "period": period_seconds}
                logger.info(f"Sending subscription request for {pair}...")
                self.sio.emit("candles/subscribe", subscription_payload)
                self.subscribed_assets.add(pair_tf_key)
             except Exception as e: logger.error(f"Failed to send subscription for {pair}: {e}")

    def _resubscribe_assets(self):
        logger.info("Resubscribing to tracked assets...")
        time.sleep(1)
        target_subscriptions = self.subscribed_assets.copy()
        self.subscribed_assets.clear()
        for pair_tf_key in target_subscriptions:
             try:
                 asset_symbol, period_seconds_str = pair_tf_key.rsplit('_', 1); period_seconds = int(period_seconds_str)
                 original_pair = next((p for p, s in self.pair_map.items() if s == asset_symbol), None)
                 original_tf = next((tf for tf, s in self.timeframes_seconds.items() if s == period_seconds), None)
                 if original_pair and original_tf: self._subscribe_to_asset(original_pair, original_tf)
             except Exception as e: logger.error(f"Error during resubscription for {pair_tf_key}: {e}")

    def fetch_real_candles(self, pair, timeframe="5m", limit=100):
        if not self.is_connected or not self.is_authenticated:
            logger.warning(f"Socket.IO not ready (Connected: {self.is_connected}, Authenticated: {self.is_authenticated}). Using fallback.")
            return self._get_fallback_data(pair, timeframe, limit)

        asset_symbol, period_seconds = self.pair_map.get(pair), self.timeframes_seconds.get(timeframe)
        if not asset_symbol or not period_seconds: return self._get_fallback_data(pair, timeframe, limit)
        pair_tf_key = f"{asset_symbol}_{period_seconds}"

        if pair_tf_key not in self.subscribed_assets:
            self._subscribe_to_asset(pair, timeframe); time.sleep(2)

        with self.data_lock:
            if pair_tf_key in self.data_store and len(self.data_store[pair_tf_key]) > 0:
                candles = list(self.data_store[pair_tf_key])[-limit:]
                opens, highs, lows, closes, volumes, timestamps = zip(*[(c['open'], c['high'], c['low'], c['close'], c['volume'], c['timestamp']) for c in candles])
                return {'success': True, 'price': closes[-1], 'opens': list(opens), 'highs': list(highs), 'lows': list(lows), 'closes': list(closes), 'volumes': list(volumes), 'timestamps': list(timestamps), 'pair': pair, 'is_otc': 'OTC' in pair, 'data_source': 'REAL_WEBSOCKET'}
        
        logger.warning(f"No candle data in store for {pair}. Using fallback.")
        return self._get_fallback_data(pair, timeframe, limit)

    def _get_fallback_data(self, pair, timeframe, limit):
        base_prices = {"EUR/USD": 1.0685, "AUD/CAD OTC": 0.9085}
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
pocket_api = PocketOptionAPI()
