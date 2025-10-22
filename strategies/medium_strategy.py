"""
MEDIUM CONFIDENCE STRATEGY (60-75%)
Two indicator confirmations
2-5 minute trades
"""

def generate_medium_confidence_signals(price_action, indicators):
    """
    70% Confidence Level - Double Confirmation
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
    if (("HAMMER" in ' '.join(price_action['price_signals'])) and 
        indicators['ema_9'] > indicators['ema_21']):
        signals.append("HAMMER + EMA_BULLISH")
        reasons.append("Hammer Pin Bar + Bullish Trend")
        total_confidence += 40
        action = "CALL"
    elif (("SHOOTING_STAR" in ' '.join(price_action['price_signals'])) and 
          indicators['ema_9'] < indicators['ema_21']):
        signals.append("SHOOTING_STAR + EMA_BEARISH")
        reasons.append("Shooting Star + Bearish Trend")
        total_confidence += 40
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
