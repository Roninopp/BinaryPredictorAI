def generate_medium_confidence_signals(price_action, indicators, closes=None, highs=None, lows=None):
    """
    70% Confidence Level - Two Confirming Signals
    Better accuracy with 2 confirmations
    Updated parameter format for compatibility
    """
    signals = []
    total_confidence = 0
    action = "HOLD"
    
    # RULE 1: RSI + EMA CONFIRMATION
    if indicators['rsi'] < 30 and indicators['ema_9'] > indicators['ema_21']:
        signals.append("RSI_OVERSOLD_EMA_BULLISH")
        total_confidence += 40
        action = "CALL"
    elif indicators['rsi'] > 70 and indicators['ema_9'] < indicators['ema_21']:
        signals.append("RSI_OVERBOUGHT_EMA_BEARISH")
        total_confidence += 40
        action = "PUT"
    
    # RULE 2: ENGULFING + SUPPORT/RESISTANCE
    if ("BULLISH_ENGULFING" in price_action['price_signals'] and 
        "AT_SUPPORT" in price_action['price_signals']):
        signals.append("BULLISH_ENGULFING_AT_SUPPORT")
        total_confidence += 45
        action = "CALL"
    elif ("BEARISH_ENGULFING" in price_action['price_signals'] and 
          "AT_RESISTANCE" in price_action['price_signals']):
        signals.append("BEARISH_ENGULFING_AT_RESISTANCE")
        total_confidence += 45
        action = "PUT"
    
    # RULE 3: PINBAR + EMA CONFIRMATION
    if ("HAMMER_PINBAR" in price_action['price_signals'] and 
        indicators['ema_9'] > indicators['ema_21']):
        signals.append("HAMMER_EMA_BULLISH")
        total_confidence += 35
        action = "CALL"
    elif ("SHOOTING_STAR" in price_action['price_signals'] and 
          indicators['ema_9'] < indicators['ema_21']):
        signals.append("SHOOTING_STAR_EMA_BEARISH")
        total_confidence += 35
        action = "PUT"
    
    # RULE 4: RSI + PRICE ACTION
    if (indicators['rsi'] < 30 and 
        "BULLISH_ENGULFING" in price_action['price_signals']):
        signals.append("RSI_OVERSOLD_BULLISH_ENGULFING")
        total_confidence += 42
        action = "CALL"
    elif (indicators['rsi'] > 70 and 
          "BEARISH_ENGULFING" in price_action['price_signals']):
        signals.append("RSI_OVERBOUGHT_BEARISH_ENGULFING")
        total_confidence += 42
        action = "PUT"
    
    return {
        'action': action,
        'confidence': total_confidence,
        'signals': signals,
        'confidence_level': 'MEDIUM',
        'is_tradable': total_confidence >= 60
    }
