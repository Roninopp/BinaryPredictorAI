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
                'bullish_patterns': [],
                'bearish_patterns': [],
                'total_patterns': 0,
                'confidence_boost': 0,
                'at_key_level': False
            }
        
        self.patterns_detected = []
        self.bullish_patterns = []
        self.bearish_patterns = []
        
        # Get current and previous candles
        idx = -1
        o = opens[idx]
        h = highs[idx]
        l = lows[idx]
        c = closes[idx]
        
        o1 = opens[idx-1] if len(opens) > 1 else o
        h1 = highs[idx-1] if len(highs) > 1 else h
        l1 = lows[idx-1] if len(lows) > 1 else l
        c1 = closes[idx-1] if len(closes) > 1 else c
        
        o2 = opens[idx-2] if len(opens) > 2 else o1
        h2 = highs[idx-2] if len(highs) > 2 else h1
        l2 = lows[idx-2] if len(lows) > 2 else l1
        c2 = closes[idx-2] if len(closes) > 2 else c1
        
        # Check if at key levels
        at_support = False
        at_resistance = False
        
        if support and abs(l - support) / support < 0.002:
            at_support = True
        if resistance and abs(h - resistance) / resistance < 0.002:
            at_resistance = True
        
        # SCAN ALL PATTERNS
        
        # === REVERSAL PATTERNS ===
        self._check_hammer(o, h, l, c, at_support)
        self._check_inverted_hammer(o, h, l, c, at_support)
        self._check_shooting_star(o, h, l, c, at_resistance)
        self._check_hanging_man(o, h, l, c, at_resistance)
        
        # === ENGULFING PATTERNS ===
        self._check_bullish_engulfing(o, c, o1, c1, at_support)
        self._check_bearish_engulfing(o, c, o1, c1, at_resistance)
        
        # === STAR PATTERNS ===
        self._check_morning_star(o, c, o1, c1, o2, c2, at_support)
        self._check_evening_star(o, c, o1, c1, o2, c2, at_resistance)
        self._check_doji_star(o, h, l, c, o1, c1)
        
        # === HARAMI PATTERNS ===
        self._check_bullish_harami(o, c, o1, c1, at_support)
        self._check_bearish_harami(o, c, o1, c1, at_resistance)
        
        # === PIERCING PATTERNS ===
        self._check_piercing_line(o, c, o1, c1, at_support)
        self._check_dark_cloud_cover(o, c, o1, c1, at_resistance)
        
        # === TRIPLE PATTERNS ===
        self._check_three_white_soldiers(o, c, o1, c1, o2, c2)
        self._check_three_black_crows(o, c, o1, c1, o2, c2)
        
        # === DOJI VARIATIONS ===
        self._check_dragonfly_doji(o, h, l, c, at_support)
        self._check_gravestone_doji(o, h, l, c, at_resistance)
        self._check_long_legged_doji(o, h, l, c)
        
        # === SPINNING TOPS ===
        self._check_spinning_top(o, h, l, c)
        
        # === MARUBOZU PATTERNS ===
        self._check_bullish_marubozu(o, h, l, c)
        self._check_bearish_marubozu(o, h, l, c)
        
        # === TWEEZER PATTERNS ===
        self._check_tweezer_bottom(l, l1, c, c1, at_support)
        self._check_tweezer_top(h, h1, c, c1, at_resistance)
        
        # === ON NECK PATTERNS ===
        self._check_on_neck(o, c, o1, c1)
        self._check_in_neck(o, c, o1, c1)
        
        # === KICKER PATTERNS ===
        self._check_bullish_kicker(o, c, o1, c1)
        self._check_bearish_kicker(o, c, o1, c1)
        
        # === THREE INSIDE PATTERNS ===
        self._check_three_inside_up(o, c, o1, c1, o2, c2)
        self._check_three_inside_down(o, c, o1, c1, o2, c2)
        
        # === ABANDONED BABY ===
        self._check_abandoned_baby_bullish(h, l, h1, l1, h2, l2, at_support)
        self._check_abandoned_baby_bearish(h, l, h1, l1, h2, l2, at_resistance)
        
        # Calculate confidence boost
        confidence_boost = 0
        
        # Extra boost if at key levels
        if at_support and len(self.bullish_patterns) > 0:
            confidence_boost += 20
        if at_resistance and len(self.bearish_patterns) > 0:
            confidence_boost += 20
        
        # Pattern count boost
        confidence_boost += len(self.bullish_patterns) * 5
        confidence_boost += len(self.bearish_patterns) * 5
        
        return {
            'bullish_patterns': self.bullish_patterns,
            'bearish_patterns': self.bearish_patterns,
            'total_patterns': len(self.bullish_patterns) + len(self.bearish_patterns),
            'confidence_boost': min(confidence_boost, 50),
            'at_key_level': at_support or at_resistance,
            'at_support': at_support,
            'at_resistance': at_resistance
        }
    
    # === PATTERN DETECTION METHODS ===
    
    def _check_hammer(self, o, h, l, c, at_support):
        """Hammer: Small body, long lower shadow"""
        body = abs(c - o)
        total_range = h - l
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        
        if total_range > 0 and body > 0:
            if (lower_shadow >= 2 * body and 
                upper_shadow <= body * 0.3 and
                c > o):
                pattern = "HAMMER" + (" (AT_SUPPORT)" if at_support else "")
                self.bullish_patterns.append(pattern)
    
    def _check_inverted_hammer(self, o, h, l, c, at_support):
        """Inverted Hammer: Small body, long upper shadow"""
        body = abs(c - o)
        total_range = h - l
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        
        if total_range > 0 and body > 0:
            if (upper_shadow >= 2 * body and
                lower_shadow <= body * 0.3 and
                c > o):
                pattern = "INVERTED_HAMMER" + (" (AT_SUPPORT)" if at_support else "")
                self.bullish_patterns.append(pattern)
    
    def _check_shooting_star(self, o, h, l, c, at_resistance):
        """Shooting Star: Small body, long upper shadow"""
        body = abs(c - o)
        total_range = h - l
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        
        if total_range > 0 and body > 0:
            if (upper_shadow >= 2 * body and
                lower_shadow <= body * 0.3 and
                c < o):
                pattern = "SHOOTING_STAR" + (" (AT_RESISTANCE)" if at_resistance else "")
                self.bearish_patterns.append(pattern)
    
    def _check_hanging_man(self, o, h, l, c, at_resistance):
        """Hanging Man: Like hammer but bearish at top"""
        body = abs(c - o)
        total_range = h - l
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        
        if total_range > 0 and body > 0:
            if (lower_shadow >= 2 * body and
                upper_shadow <= body * 0.3 and
                at_resistance):
                self.bearish_patterns.append("HANGING_MAN (AT_RESISTANCE)")
    
    def _check_bullish_engulfing(self, o, c, o1, c1, at_support):
        """Bullish Engulfing: Large bullish candle engulfs previous bearish"""
        if c > o and c1 < o1:  # Current bullish, previous bearish
            if o < c1 and c > o1:  # Engulfs previous
                pattern = "BULLISH_ENGULFING" + (" (AT_SUPPORT)" if at_support else "")
                self.bullish_patterns.append(pattern)
    
    def _check_bearish_engulfing(self, o, c, o1, c1, at_resistance):
        """Bearish Engulfing: Large bearish candle engulfs previous bullish"""
        if c < o and c1 > o1:  # Current bearish, previous bullish
            if o > c1 and c < o1:  # Engulfs previous
                pattern = "BEARISH_ENGULFING" + (" (AT_RESISTANCE)" if at_resistance else "")
                self.bearish_patterns.append(pattern)
    
    def _check_morning_star(self, o, c, o1, c1, o2, c2, at_support):
        """Morning Star: 3-candle bullish reversal"""
        if (c2 < o2 and  # First: bearish
            abs(c1 - o1) < abs(c2 - o2) * 0.3 and  # Second: small body (star)
            c > o and  # Third: bullish
            c > (o2 + c2) / 2):  # Third closes above midpoint of first
            pattern = "MORNING_STAR" + (" (AT_SUPPORT)" if at_support else "")
            self.bullish_patterns.append(pattern)
    
    def _check_evening_star(self, o, c, o1, c1, o2, c2, at_resistance):
        """Evening Star: 3-candle bearish reversal"""
        if (c2 > o2 and  # First: bullish
            abs(c1 - o1) < abs(c2 - o2) * 0.3 and  # Second: small body (star)
            c < o and  # Third: bearish
            c < (o2 + c2) / 2):  # Third closes below midpoint of first
            pattern = "EVENING_STAR" + (" (AT_RESISTANCE)" if at_resistance else "")
            self.bearish_patterns.append(pattern)
    
    def _check_doji_star(self, o, h, l, c, o1, c1):
        """Doji Star: Indecision pattern"""
        body = abs(c - o)
        total_range = h - l
        
        if total_range > 0 and body / total_range < 0.1:
            if c1 > o1:  # Previous bullish
                self.bearish_patterns.append("DOJI_STAR_BEARISH")
            elif c1 < o1:  # Previous bearish
                self.bullish_patterns.append("DOJI_STAR_BULLISH")
    
    def _check_bullish_harami(self, o, c, o1, c1, at_support):
        """Bullish Harami: Small bullish inside large bearish"""
        if c > o and c1 < o1:  # Current bullish, previous bearish
            if o > c1 and c < o1:  # Inside previous
                pattern = "BULLISH_HARAMI" + (" (AT_SUPPORT)" if at_support else "")
                self.bullish_patterns.append(pattern)
    
    def _check_bearish_harami(self, o, c, o1, c1, at_resistance):
        """Bearish Harami: Small bearish inside large bullish"""
        if c < o and c1 > o1:  # Current bearish, previous bullish
            if o < c1 and c > o1:  # Inside previous
                pattern = "BEARISH_HARAMI" + (" (AT_RESISTANCE)" if at_resistance else "")
                self.bearish_patterns.append(pattern)
    
    def _check_piercing_line(self, o, c, o1, c1, at_support):
        """Piercing Line: Bullish reversal, closes above 50% of previous"""
        if c > o and c1 < o1:  # Current bullish, previous bearish
            if o < c1 and c > (o1 + c1) / 2:
                pattern = "PIERCING_LINE" + (" (AT_SUPPORT)" if at_support else "")
                self.bullish_patterns.append(pattern)
    
    def _check_dark_cloud_cover(self, o, c, o1, c1, at_resistance):
        """Dark Cloud Cover: Bearish reversal, closes below 50% of previous"""
        if c < o and c1 > o1:  # Current bearish, previous bullish
            if o > c1 and c < (o1 + c1) / 2:
                pattern = "DARK_CLOUD_COVER" + (" (AT_RESISTANCE)" if at_resistance else "")
                self.bearish_patterns.append(pattern)
    
    def _check_three_white_soldiers(self, o, c, o1, c1, o2, c2):
        """Three White Soldiers: 3 consecutive bullish candles"""
        if c > o and c1 > o1 and c2 > o2:  # All bullish
            if c > c1 > c2:  # Each closes higher
                self.bullish_patterns.append("THREE_WHITE_SOLDIERS")
    
    def _check_three_black_crows(self, o, c, o1, c1, o2, c2):
        """Three Black Crows: 3 consecutive bearish candles"""
        if c < o and c1 < o1 and c2 < o2:  # All bearish
            if c < c1 < c2:  # Each closes lower
                self.bearish_patterns.append("THREE_BLACK_CROWS")
    
    def _check_dragonfly_doji(self, o, h, l, c, at_support):
        """Dragonfly Doji: Long lower shadow, no upper shadow"""
        body = abs(c - o)
        total_range = h - l
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        
        if total_range > 0 and body / total_range < 0.1:
            if lower_shadow >= total_range * 0.7 and upper_shadow <= total_range * 0.1:
                pattern = "DRAGONFLY_DOJI" + (" (AT_SUPPORT)" if at_support else "")
                self.bullish_patterns.append(pattern)
    
    def _check_gravestone_doji(self, o, h, l, c, at_resistance):
        """Gravestone Doji: Long upper shadow, no lower shadow"""
        body = abs(c - o)
        total_range = h - l
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        
        if total_range > 0 and body / total_range < 0.1:
            if upper_shadow >= total_range * 0.7 and lower_shadow <= total_range * 0.1:
                pattern = "GRAVESTONE_DOJI" + (" (AT_RESISTANCE)" if at_resistance else "")
                self.bearish_patterns.append(pattern)
    
    def _check_long_legged_doji(self, o, h, l, c):
        """Long-Legged Doji: Long shadows both sides"""
        body = abs(c - o)
        total_range = h - l
        
        if total_range > 0 and body / total_range < 0.1:
            upper_shadow = h - max(o, c)
            lower_shadow = min(o, c) - l
            if upper_shadow >= total_range * 0.3 and lower_shadow >= total_range * 0.3:
                self.bullish_patterns.append("LONG_LEGGED_DOJI (REVERSAL)")
    
    def _check_spinning_top(self, o, h, l, c):
        """Spinning Top: Small body, long shadows"""
        body = abs(c - o)
        total_range = h - l
        
        if total_range > 0:
            if 0.1 < body / total_range < 0.3:
                self.bullish_patterns.append("SPINNING_TOP (INDECISION)")
    
    def _check_bullish_marubozu(self, o, h, l, c):
        """Bullish Marubozu: Strong bullish, no shadows"""
        body = abs(c - o)
        total_range = h - l
        
        if total_range > 0 and c > o:
            if body / total_range >= 0.95:
                self.bullish_patterns.append("BULLISH_MARUBOZU (STRONG)")
    
    def _check_bearish_marubozu(self, o, h, l, c):
        """Bearish Marubozu: Strong bearish, no shadows"""
        body = abs(c - o)
        total_range = h - l
        
        if total_range > 0 and c < o:
            if body / total_range >= 0.95:
                self.bearish_patterns.append("BEARISH_MARUBOZU (STRONG)")
    
    def _check_tweezer_bottom(self, l, l1, c, c1, at_support):
        """Tweezer Bottom: Same lows, bullish reversal"""
        if abs(l - l1) / l < 0.001:  # Same lows
            if c > c1:  # Current closes higher
                pattern = "TWEEZER_BOTTOM" + (" (AT_SUPPORT)" if at_support else "")
                self.bullish_patterns.append(pattern)
    
    def _check_tweezer_top(self, h, h1, c, c1, at_resistance):
        """Tweezer Top: Same highs, bearish reversal"""
        if abs(h - h1) / h < 0.001:  # Same highs
            if c < c1:  # Current closes lower
                pattern = "TWEEZER_TOP" + (" (AT_RESISTANCE)" if at_resistance else "")
                self.bearish_patterns.append(pattern)
    
    def _check_on_neck(self, o, c, o1, c1):
        """On Neck: Bearish continuation"""
        if c1 < o1 and c > o:  # Previous bearish, current bullish
            if abs(c - c1) / c < 0.001:  # Closes at same level
                self.bearish_patterns.append("ON_NECK (CONTINUATION)")
    
    def _check_in_neck(self, o, c, o1, c1):
        """In Neck: Bearish continuation"""
        if c1 < o1 and c > o:  # Previous bearish, current bullish
            if c < c1 and c > c1 * 0.995:  # Closes slightly above previous close
                self.bearish_patterns.append("IN_NECK (CONTINUATION)")
    
    def _check_bullish_kicker(self, o, c, o1, c1):
        """Bullish Kicker: Strong gap up reversal"""
        if c1 < o1 and c > o:  # Previous bearish, current bullish
            if o > o1:  # Gap up
                self.bullish_patterns.append("BULLISH_KICKER (STRONG)")
    
    def _check_bearish_kicker(self, o, c, o1, c1):
        """Bearish Kicker: Strong gap down reversal"""
        if c1 > o1 and c < o:  # Previous bullish, current bearish
            if o < o1:  # Gap down
                self.bearish_patterns.append("BEARISH_KICKER (STRONG)")
    
    def _check_three_inside_up(self, o, c, o1, c1, o2, c2):
        """Three Inside Up: Bullish harami + confirmation"""
        if c2 < o2:  # First: bearish
            if c1 > o1 and o1 > c2 and c1 < o2:  # Second: bullish harami
                if c > o and c > c1:  # Third: bullish confirmation
                    self.bullish_patterns.append("THREE_INSIDE_UP")
    
    def _check_three_inside_down(self, o, c, o1, c1, o2, c2):
        """Three Inside Down: Bearish harami + confirmation"""
        if c2 > o2:  # First: bullish
            if c1 < o1 and o1 < c2 and c1 > o2:  # Second: bearish harami
                if c < o and c < c1:  # Third: bearish confirmation
                    self.bearish_patterns.append("THREE_INSIDE_DOWN")
    
    def _check_abandoned_baby_bullish(self, h, l, h1, l1, h2, l2, at_support):
        """Abandoned Baby Bullish: Gap pattern with doji"""
        if l1 > h2 and l > h1:  # Gaps on both sides
            pattern = "ABANDONED_BABY_BULLISH" + (" (AT_SUPPORT)" if at_support else "")
            self.bullish_patterns.append(pattern)
    
    def _check_abandoned_baby_bearish(self, h, l, h1, l1, h2, l2, at_resistance):
        """Abandoned Baby Bearish: Gap pattern with doji"""
        if h1 < l2 and h < l1:  # Gaps on both sides
            pattern = "ABANDONED_BABY_BEARISH" + (" (AT_RESISTANCE)" if at_resistance else "")
            self.bearish_patterns.append(pattern)

# Global scanner instance
pattern_scanner = AdvancedCandlestickScanner()
