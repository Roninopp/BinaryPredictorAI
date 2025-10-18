import pandas as pd
import numpy as np
from .ai_enhancements import ai_enhancements

def generate_high_confidence_signals(price_action, indicators, closes, highs, lows, multi_timeframe_data=None):
    """
    80% Confidence Level - ULTIMATE AI-Powered Signals
    Maximum accuracy with multi-factor AI confirmation
    """
    signals = []
    total_confidence = 0
    action = "HOLD"
    
    # Get ALL AI enhancements
    volatility_data = ai_enhancements.calculate_ai_volatility_prediction(closes)
    liquidity_data = ai_enhancements.detect_liquidity_zones(highs, lows, closes)
    momentum_data = ai_enhancements.momentum_acceleration(closes)
    
    # Multi-timeframe confluence if available
    confluence_data = None
    if multi_timeframe_data:
        confluence_data = ai_enhancements.multi_timeframe_confluence(
            multi_timeframe_data.get('1m', {}),
            multi_timeframe_data.get('5m', {}), 
            multi_timeframe_data.get('1h', {})
        )
    
    # RULE 1: TRIPLE CONFIRMATION - RSI + ENGULFING + SUPPORT (60 points)
    if (indicators['rsi'] < 28 and 
        "BULLISH_ENGULFING" in price_action['price_signals'] and
        "AT_SUPPORT" in price_action['price_signals']):
        signals.append("TRIPLE_BULLISH_CONFIRMATION")
        total_confidence += 45
        # AI Volatility + Liquidity boost
        if (volatility_data['volatility_regime'] == "HIGH_VOLATILITY" and
            liquidity_data['near_support']):
            total_confidence += 15
            signals.append("AI_PERFECT_SETUP")
        action = "CALL"
    elif (indicators['rsi'] > 72 and 
          "BEARISH_ENGULFING" in price_action['price_signals'] and
          "AT_RESISTANCE" in price_action['price_signals']):
        signals.append("TRIPLE_BEARISH_CONFIRMATION")
        total_confidence += 45
        if (volatility_data['volatility_regime'] == "HIGH_VOLATILITY" and
            liquidity_data['near_resistance']):
            total_confidence += 15
            signals.append("AI_PERFECT_SETUP")
        action = "PUT"
    
    # RULE 2: PINBAR + EMA + MOMENTUM + AI (55 points)
    if ("HAMMER_PINBAR" in price_action['price_signals'] and
        indicators['ema_9'] > indicators['ema_21'] and
        "ACCELERATING_UP" in momentum_data['momentum_signals']):
        signals.append("PINBAR_EMA_MOMENTUM_BULLISH")
        total_confidence += 40
        # AI Multi-timeframe confluence
        if confluence_data and confluence_data['confluence_score'] >= 20:
            total_confidence += 15
            signals.append("AI_MULTI_TIMEFRAME_CONFLUENCE")
        action = "CALL"
    elif ("SHOOTING_STAR" in price_action['price_signals'] and
          indicators['ema_9'] < indicators['ema_21'] and
          "ACCELERATING_DOWN" in momentum_data['momentum_signals']):
        signals.append("PINBAR_EMA_MOMENTUM_BEARISH")
        total_confidence += 40
        if confluence_data and confluence_data['confluence_score'] >= 20:
            total_confidence += 15
            signals.append("AI_MULTI_TIMEFRAME_CONFLUENCE")
        action = "PUT"
    
    # RULE 3: RSI EXTREME + EMA + LIQUIDITY (50 points)
    if (indicators['rsi'] < 25 and
        indicators['ema_9'] > indicators['ema_21'] and
        liquidity_data['near_support']):
        signals.append("RSI_EXTREME_BULLISH")
        total_confidence += 35
        # AI Strong momentum confirmation
        if momentum_data['momentum_score'] >= 20:
            total_confidence += 15
            signals.append("AI_MOMENTUM_POWER")
        action = "CALL"
    elif (indicators['rsi'] > 75 and
          indicators['ema_9'] < indicators['ema_21'] and
          liquidity_data['near_resistance']):
        signals.append("RSI_EXTREME_BEARISH")
        total_confidence += 35
        if momentum_data['momentum_score'] >= 20:
            total_confidence += 15
            signals.append("AI_MOMENTUM_POWER")
        action = "PUT"
    
    # RULE 4: ULTIMATE AI CONFLUENCE (65 points)
    ai_confluence_score = (
        volatility_data['volatility_score'] + 
        liquidity_data['liquidity_score'] + 
        momentum_data['momentum_score'] +
        (confluence_data['confluence_score'] if confluence_data else 0)
    )
    
    if ai_confluence_score >= 80:
        if (action == "CALL" and 
            indicators['rsi'] < 35 and 
            indicators['ema_9'] > indicators['ema_21']):
            total_confidence += 65
            signals.append("ULTIMATE_AI_BULLISH_CONFLUENCE")
            action = "CALL"
        elif (action == "PUT" and 
              indicators['rsi'] > 65 and 
              indicators['ema_9'] < indicators['ema_21']):
            total_confidence += 65
            signals.append("ULTIMATE_AI_BEARISH_CONFLUENCE")
            action = "PUT"
    
    # FINAL AI QUALITY CHECK
    if action != "HOLD":
        # Deduct points if AI detects poor conditions
        if volatility_data['volatility_regime'] == "LOW_VOLATILITY":
            total_confidence -= 10
            signals.append("AI_LOW_VOL_WARNING")
        if momentum_data['momentum_score'] < 10:
            total_confidence -= 8
            signals.append("AI_WEAK_MOMENTUM_WARNING")
    
    return {
        'action': action,
        'confidence': min(max(total_confidence, 0), 95),  # Ensure between 0-95
        'signals': signals,
        'confidence_level': 'HIGH',
        'is_tradable': total_confidence >= 80,
        'ai_data': {
            'volatility': volatility_data,
            'liquidity': liquidity_data,
            'momentum': momentum_data,
            'confluence': confluence_data,
            'ai_confluence_score': ai_confluence_score
        }
    }
