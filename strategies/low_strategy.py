def generate_low_confidence_signals(price_action, indicators, closes=None, highs=None, lows=None):
    """
    60% Confidence Level - Simple Single Signals
    Updated to match enhanced parameter format
    """
    signals = []
    total_confidence = 0
    action = "HOLD"
    
    # 1. SIMPLE RSI SIGNALS (25 points each)
    if indicators['rsi'] < 30:
        signals.append("RSI_OVERSOLD")
        total_confidence += 25
        action = "CALL"
    elif indicators['rsi'] > 70:
        signals.append("RSI_OVERBOUGHT")
        total_confidence += 25
        action = "PUT"
    
    # 2. SIMPLE EMA CROSSOVER (15 points each)
    if indicators['ema_9'] > indicators['ema_21']:
        signals.append("EMA_BULLISH")
        total_confidence += 15
        if action == "HOLD":
            action = "CALL"
    elif indicators['ema_9'] < indicators['ema_21']:
        signals.append("EMA_BEARISH")
        total_confidence += 15
        if action == "HOLD":
            action = "PUT"
    
    # 3. BASIC PRICE ACTION (20 points each)
    if "BULLISH_ENGULFING" in price_action['price_signals']:
        signals.append("BULLISH_ENGULFING")
        total_confidence += 20
        action = "CALL"
    elif "BEARISH_ENGULFING" in price_action['price_signals']:
        signals.append("BEARISH_ENGULFING")
        total_confidence += 20
        action = "PUT"
    
    # 4. PIN BARS (15 points each)
    if "HAMMER_PINBAR" in price_action['price_signals']:
        signals.append("HAMMER_PINBAR")
        total_confidence += 15
        if action == "HOLD":
            action = "CALL"
    elif "SHOOTING_STAR" in price_action['price_signals']:
        signals.append("SHOOTING_STAR")
        total_confidence += 15
        if action == "HOLD":
            action = "PUT"
    
    return {
        'action': action,
        'confidence': total_confidence,
        'signals': signals,
        'confidence_level': 'LOW',
        'is_tradable': total_confidence >= 50
    }
