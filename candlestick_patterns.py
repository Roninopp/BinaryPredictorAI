import numpy as np
import logging

logger = logging.getLogger(__name__)

class AdvancedCandlestickScanner:
    """
    Professional 30+ Candlestick Pattern Detection
    Scans for patterns at support/resistance levels
    """
    
    def __init__(self):
        self.patterns_detected = []
        self.bullish_patterns = []
        self.bearish_patterns = []
    
    def scan_all_patterns(self, opens, highs, lows, closes, support=None, resistance=None):
        """
        Scan for ALL 30+ candlestick patterns
        Returns detected patterns with confidence scores
        """
        if len(closes) < 5:
            return {
                'bullish_patterns': [], 'bearish_patterns': [], 'total_patterns': 0,
                'confidence_boost': 0, 'at_key_level': False,
                'at_support': False, 'at_resistance': False
            }
        
        self.bullish_patterns = []
        self.bearish_patterns = []
        
        # Get last 3 candles
        o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
        o1, h1, l1, c1 = opens[-2], highs[-2], lows[-2], closes[-2]
        o2, h2, l2, c2 = opens[-3], highs[-3], lows[-3], closes[-3]
        
        at_support = support and abs(l - support) / support < 0.002 if support else False
        at_resistance = resistance and abs(h - resistance) / resistance < 0.002 if resistance else False
        
        # SINGLE CANDLE PATTERNS
        self._check_hammer(o, h, l, c, at_support)
        self._check_inverted_hammer(o, h, l, c, at_support)
        self._check_shooting_star(o, h, l, c, at_resistance)
        self._check_hanging_man(o, h, l, c, at_resistance)
        self._check_doji_variations(o, h, l, c, at_support, at_resistance)
        self._check_spinning_top(o, h, l, c)
        self._check_marubozu(o, h, l, c)

        # DOUBLE CANDLE PATTERNS
        self._check_engulfing(o, c, o1, c1, at_support, at_resistance)
        self._check_harami(o, c, o1, c1, at_support, at_resistance)
        self._check_piercing_dark_cloud(o, c, o1, c1, at_support, at_resistance)
        self._check_tweezer(l, h, l1, h1, at_support, at_resistance)
        self._check_kicker(o, c, o1, c1)

        # TRIPLE CANDLE PATTERNS
        self._check_morning_evening_star(o, c, o1, c1, o2, c2, at_support, at_resistance)
        self._check_three_soldiers_crows(o, c, o1, c1, o2, c2)
        self._check_three_inside_up_down(o, c, o1, c1, o2, c2)
        self._check_abandoned_baby(h, l, h1, l1, h2, l2, at_support, at_resistance)

        confidence_boost = (len(self.bullish_patterns) + len(self.bearish_patterns)) * 5
        if at_support and self.bullish_patterns: confidence_boost += 20
        if at_resistance and self.bearish_patterns: confidence_boost += 20
        
        return {
            'bullish_patterns': self.bullish_patterns,
            'bearish_patterns': self.bearish_patterns,
            'total_patterns': len(self.bullish_patterns) + len(self.bearish_patterns),
            'confidence_boost': min(confidence_boost, 50),
            'at_key_level': at_support or at_resistance,
            'at_support': at_support,
            'at_resistance': at_resistance
        }
    
    # --- Pattern Detection Methods ---
    def _add_pattern(self, name, p_type, condition=True, level_info=""):
        if condition:
            full_name = f"{name}{level_info}"
            if p_type == 'bullish': self.bullish_patterns.append(full_name)
            else: self.bearish_patterns.append(full_name)

    def _check_hammer(self, o, h, l, c, at_support):
        body = abs(c - o)
        if body > 0:
            lower_shadow = min(o, c) - l
            upper_shadow = h - max(o, c)
            self._add_pattern("HAMMER", 'bullish', lower_shadow >= 2 * body and upper_shadow <= body * 0.3, " (AT_SUPPORT)" if at_support else "")

    def _check_inverted_hammer(self, o, h, l, c, at_support):
        body = abs(c - o)
        if body > 0:
            upper_shadow = h - max(o, c)
            lower_shadow = min(o, c) - l
            self._add_pattern("INVERTED_HAMMER", 'bullish', upper_shadow >= 2 * body and lower_shadow <= body * 0.3, " (AT_SUPPORT)" if at_support else "")
    
    def _check_shooting_star(self, o, h, l, c, at_resistance):
        body = abs(c - o)
        if body > 0 and c < o: # Must be a bearish candle
            upper_shadow = h - max(o, c)
            lower_shadow = min(o, c) - l
            self._add_pattern("SHOOTING_STAR", 'bearish', upper_shadow >= 2 * body and lower_shadow <= body * 0.3, " (AT_RESISTANCE)" if at_resistance else "")

    def _check_hanging_man(self, o, h, l, c, at_resistance):
        body = abs(c - o)
        if body > 0 and c < o: # Must be a bearish candle
            lower_shadow = min(o, c) - l
            upper_shadow = h - max(o, c)
            self._add_pattern("HANGING_MAN", 'bearish', lower_shadow >= 2 * body and upper_shadow <= body * 0.3, " (AT_RESISTANCE)" if at_resistance else "")

    def _check_engulfing(self, o, c, o1, c1, at_support, at_resistance):
        self._add_pattern("BULLISH_ENGULFING", 'bullish', c > o and c1 < o1 and c > o1 and o < c1, " (AT_SUPPORT)" if at_support else "")
        self._add_pattern("BEARISH_ENGULFING", 'bearish', c < o and c1 > o1 and c < o1 and o > c1, " (AT_RESISTANCE)" if at_resistance else "")

    def _check_morning_evening_star(self, o, c, o1, c1, o2, c2, at_support, at_resistance):
        is_morning = (c2 < o2 and abs(c1-o1) < abs(c2-o2)*0.3 and c > o and c > (o2+c2)/2)
        self._add_pattern("MORNING_STAR", 'bullish', is_morning, " (AT_SUPPORT)" if at_support else "")
        is_evening = (c2 > o2 and abs(c1-o1) < abs(c2-o2)*0.3 and c < o and c < (o2+c2)/2)
        self._add_pattern("EVENING_STAR", 'bearish', is_evening, " (AT_RESISTANCE)" if at_resistance else "")

    def _check_doji_variations(self, o, h, l, c, at_support, at_resistance):
        body = abs(c - o)
        total_range = h - l
        if total_range > 0 and body / total_range < 0.1:
            upper_shadow, lower_shadow = h - max(o, c), min(o, c) - l
            self._add_pattern("DRAGONFLY_DOJI", 'bullish', lower_shadow > total_range * 0.7, " (AT_SUPPORT)" if at_support else "")
            self._add_pattern("GRAVESTONE_DOJI", 'bearish', upper_shadow > total_range * 0.7, " (AT_RESISTANCE)" if at_resistance else "")
            self._add_pattern("LONG_LEGGED_DOJI", 'bullish', lower_shadow > total_range * 0.3 and upper_shadow > total_range * 0.3)

    def _check_harami(self, o, c, o1, c1, at_support, at_resistance):
        self._add_pattern("BULLISH_HARAMI", 'bullish', c > o and c1 < o1 and o > c1 and c < o1, " (AT_SUPPORT)" if at_support else "")
        self._add_pattern("BEARISH_HARAMI", 'bearish', c < o and c1 > o1 and o < c1 and c > o1, " (AT_RESISTANCE)" if at_resistance else "")

    def _check_piercing_dark_cloud(self, o, c, o1, c1, at_support, at_resistance):
        self._add_pattern("PIERCING_LINE", 'bullish', c > o and c1 < o1 and o < c1 and c > (o1+c1)/2, " (AT_SUPPORT)" if at_support else "")
        self._add_pattern("DARK_CLOUD_COVER", 'bearish', c < o and c1 > o1 and o > c1 and c < (o1+c1)/2, " (AT_RESISTANCE)" if at_resistance else "")

    def _check_three_soldiers_crows(self, o, c, o1, c1, o2, c2):
        self._add_pattern("THREE_WHITE_SOLDIERS", 'bullish', c > o and c1 > o1 and c2 > o2 and c > c1 > c2)
        self._add_pattern("THREE_BLACK_CROWS", 'bearish', c < o and c1 < o1 and c2 < o2 and c < c1 < c2)

    def _check_spinning_top(self, o, h, l, c):
        body = abs(c-o)
        total_range = h-l
        if total_range > 0 and 0.1 < body / total_range < 0.3:
            self.bullish_patterns.append("SPINNING_TOP") # Neutral but often indicates reversal

    def _check_marubozu(self, o, h, l, c):
        body = abs(c-o)
        total_range = h-l
        if total_range > 0 and body / total_range >= 0.95:
            self._add_pattern("BULLISH_MARUBOZU", 'bullish', c > o)
            self._add_pattern("BEARISH_MARUBOZU", 'bearish', c < o)

    def _check_tweezer(self, l, h, l1, h1, at_support, at_resistance):
        self._add_pattern("TWEEZER_BOTTOM", 'bullish', abs(l - l1) / l < 0.001, " (AT_SUPPORT)" if at_support else "")
        self._add_pattern("TWEEZER_TOP", 'bearish', abs(h - h1) / h < 0.001, " (AT_RESISTANCE)" if at_resistance else "")
        
    def _check_kicker(self, o, c, o1, c1):
        self._add_pattern("BULLISH_KICKER", 'bullish', c1 < o1 and c > o and o > o1)
        self._add_pattern("BEARISH_KICKER", 'bearish', c1 > o1 and c < o and o < o1)

    def _check_three_inside_up_down(self, o, c, o1, c1, o2, c2):
        is_up = c2 < o2 and c1 > o1 and o1 > c2 and c1 < o2 and c > o and c > c1
        self._add_pattern("THREE_INSIDE_UP", 'bullish', is_up)
        is_down = c2 > o2 and c1 < o1 and o1 < c2 and c1 > o2 and c < o and c < c1
        self._add_pattern("THREE_INSIDE_DOWN", 'bearish', is_down)

    def _check_abandoned_baby(self, h, l, h1, l1, h2, l2, at_support, at_resistance):
        self._add_pattern("ABANDONED_BABY_BULLISH", 'bullish', l1 > h2 and l > h1, " (AT_SUPPORT)" if at_support else "")
        self._add_pattern("ABANDONED_BABY_BEARISH", 'bearish', h1 < l2 and h < l1, " (AT_RESISTANCE)" if at_resistance else "")


# Global scanner instance
pattern_scanner = AdvancedCandlestickScanner()
