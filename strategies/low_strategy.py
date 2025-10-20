"""
LOW CONFIDENCE STRATEGY (50-60%)
Single indicator confirmation
Quick 1-3 minute trades
"""

def generate_low_confidence_signals(price_action, indicators):
    """
    60% Confidence Level - Simple Single Signals
    FIXED: Correct parameter format (only 2 parameters)
    """
    signals = []
    total_confidence = 0
    action = "HOLD"
    reasons = []
    
    # 1. RSI EXTREME SIGNALS (30 points)
    if indicators['rsi'] < 30:
        signals.append("RSI_OVERSOLD")
        reasons.append(f"RSI Oversold at {indicators['rsi']}")
        total_confidence += 30
        action = "CALL"
    elif indicators['rsi'] > 70:
        signals.append("RSI_OVERBOUGHT")
        reasons.append(f"RSI Overbought at {indicators['rsi']}")
        total_confidence += 30
        action = "PUT"
    
    # 2. EMA TREND (20 points)
    if indicators['ema_9'] > indicators['ema_21']:
        signals.append("EMA_BULLISH_TREND")
        reasons.append("EMA 9 above EMA 21 (Bullish)")
        total_confidence += 20
        if action == "HOLD":
            action = "CALL"
    elif indicators['ema_9'] < indicators['ema_21']:
        signals.append("EMA_BEARISH_TREND")
        reasons.append("EMA 9 below EMA 21 (Bearish)")
        total_confidence += 20
        if action == "HOLD":
            action = "PUT"
    
    # 3. PRICE ACTION PATTERNS (25 points each)
    if "BULLISH_ENGULFING" in price_action['price_signals']:
        signals.append("BULLISH_ENGULFING")
        reasons.append("Bullish Engulfing Pattern")
        total_confidence += 25
        action = "CALL"
    elif "BEARISH_ENGULFING" in price_action['price_signals']:
        signals.append("BEARISH_ENGULFING")
        reasons.append("Bearish Engulfing Pattern")
        total_confidence += 25
        action = "PUT"
    
    # 4. SUPPORT/RESISTANCE (15 points)
    if "AT_SUPPORT" in price_action['price_signals']:
        signals.append("NEAR_SUPPORT")
        reasons.append("Price at Support Level")
        total_confidence += 15
        if action == "HOLD":
            action = "CALL"
    elif "AT_RESISTANCE" in price_action['price_signals']:
        signals.append("NEAR_RESISTANCE")
        reasons.append("Price at Resistance Level")
        total_confidence += 15
        if action == "HOLD":
            action = "PUT"
    
    # 5. PIN BARS (20 points)
    if "HAMMER_PINBAR" in price_action['price_signals']:
        signals.append("HAMMER_PINBAR")
        reasons.append("Hammer Pin Bar (Bullish Reversal)")
        total_confidence += 20
        if action == "HOLD":
            action = "CALL"
    elif "SHOOTING_STAR" in price_action['price_signals']:
        signals.append("SHOOTING_STAR")
        reasons.append("Shooting Star (Bearish Reversal)")
        total_confidence += 20
        if action == "HOLD":
            action = "PUT"
    
    return {
        'action': action,
        'confidence': min(total_confidence, 65),  # Cap at 65%
        'signals': signals,
        'reasons': reasons,
        'confidence_level': 'LOW',
        'is_tradable': total_confidence >= 50,
        'recommended_expiry': '1-3 minutes'
    }
