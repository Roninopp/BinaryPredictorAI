"""
MEDIUM CONFIDENCE STRATEGY (60-75%)
Two indicator confirmations
2-5 minute trades
"""

def generate_medium_confidence_signals(price_action, indicators):
    """
    70% Confidence Level - Double Confirmation
    FIXED: Correct parameter format (only 2 parameters)
    """
    signals = []
    total_confidence = 0
    action = "HOLD"
    reasons = []
    
    # RULE 1: RSI + EMA DOUBLE CONFIRMATION (45 points)
    if indicators['rsi'] < 30 and indicators['ema_9'] > indicators['ema_21']:
        signals.append("RSI_OVERSOLD + EMA_BULLISH")
        reasons.append(f"RSI Oversold ({indicators['rsi']}) + Bullish EMA Trend")
        total_confidence += 45
        action = "CALL"
    elif indicators['rsi'] > 70 and indicators['ema_9'] < indicators['ema_21']:
        signals.append("RSI_OVERBOUGHT + EMA_BEARISH")
        reasons.append(f"RSI Overbought ({indicators['rsi']}) + Bearish EMA Trend")
        total_confidence += 45
        action = "PUT"
    
    # RULE 2: ENGULFING + SUPPORT/RESISTANCE (50 points)
    if ("BULLISH_ENGULFING" in price_action['price_signals'] and 
        "AT_SUPPORT" in price_action['price_signals']):
        signals.append("BULLISH_ENGULFING_AT_SUPPORT")
        reasons.append("Bullish Engulfing at Support Level")
        total_confidence += 50
        action = "CALL"
    elif ("BEARISH_ENGULFING" in price_action['price_signals'] and 
          "AT_RESISTANCE" in price_action['price_signals']):
        signals.append("BEARISH_ENGULFING_AT_RESISTANCE")
        reasons.append("Bearish Engulfing at Resistance Level")
        total_confidence += 50
        action = "PUT"
    
    # RULE 3: PINBAR + EMA TREND (40 points)
    if ("HAMMER_PINBAR" in price_action['price_signals'] and 
        indicators['ema_9'] > indicators['ema_21']):
        signals.append("HAMMER + EMA_BULLISH")
        reasons.append("Hammer Pin Bar + Bullish Trend")
        total_confidence += 40
        action = "CALL"
    elif ("SHOOTING_STAR" in price_action['price_signals'] and 
          indicators['ema_9'] < indicators['ema_21']):
        signals.append("SHOOTING_STAR + EMA_BEARISH")
        reasons.append("Shooting Star + Bearish Trend")
        total_confidence += 40
        action = "PUT"
    
    # RULE 4: RSI EXTREME + PRICE PATTERN (48 points)
    if (indicators['rsi'] < 28 and 
        "BULLISH_ENGULFING" in price_action['price_signals']):
        signals.append("EXTREME_RSI + BULLISH_PATTERN")
        reasons.append(f"Extreme RSI ({indicators['rsi']}) + Bullish Engulfing")
        total_confidence += 48
        action = "CALL"
    elif (indicators['rsi'] > 72 and 
          "BEARISH_ENGULFING" in price_action['price_signals']):
        signals.append("EXTREME_RSI + BEARISH_PATTERN")
        reasons.append(f"Extreme RSI ({indicators['rsi']}) + Bearish Engulfing")
        total_confidence += 48
        action = "PUT"
    
    # RULE 5: MULTIPLE PATTERNS AT KEY LEVEL (35 points)
    bullish_count = sum(1 for sig in price_action['price_signals'] 
                        if 'BULLISH' in sig or 'HAMMER' in sig)
    bearish_count = sum(1 for sig in price_action['price_signals'] 
                        if 'BEARISH' in sig or 'SHOOTING' in sig)
    
    if bullish_count >= 2 and "AT_SUPPORT" in price_action['price_signals']:
        signals.append("MULTIPLE_BULLISH_AT_SUPPORT")
        reasons.append(f"{bullish_count} Bullish Patterns at Support")
        total_confidence += 35
        if action == "HOLD":
            action = "CALL"
    elif bearish_count >= 2 and "AT_RESISTANCE" in price_action['price_signals']:
        signals.append("MULTIPLE_BEARISH_AT_RESISTANCE")
        reasons.append(f"{bearish_count} Bearish Patterns at Resistance")
        total_confidence += 35
        if action == "HOLD":
            action = "PUT"
    
    return {
        'action': action,
        'confidence': min(total_confidence, 78),  # Cap at 78%
        'signals': signals,
        'reasons': reasons,
        'confidence_level': 'MEDIUM',
        'is_tradable': total_confidence >= 60,
        'recommended_expiry': '2-5 minutes'
    }
