import pandas as pd
import numpy as np
from .ai_enhancements import ai_enhancements

def generate_medium_confidence_signals(price_action, indicators, closes, highs, lows):
    """
    70% Confidence Level - AI Enhanced Two-Signal Confirmation
    Better accuracy with AI-powered confirmations
    """
    signals = []
    total_confidence = 0
    action = "HOLD"
    
    # Get AI enhancements
    volatility_data = ai_enhancements.calculate_ai_volatility_prediction(closes)
    liquidity_data = ai_enhancements.detect_liquidity_zones(highs, lows, closes)
    momentum_data = ai_enhancements.momentum_acceleration(closes)
    
    # RULE 1: RSI + EMA CONFIRMATION + AI Volatility (45 points)
    if indicators['rsi'] < 30 and indicators['ema_9'] > indicators['ema_21']:
        signals.append("RSI_OVERSOLD_EMA_BULLISH")
        total_confidence += 35
        # AI Volatility boost
        if volatility_data['volatility_regime'] == "HIGH_VOLATILITY":
            total_confidence += 10
            signals.append("AI_HIGH_VOL_CONFIRMATION")
        action = "CALL"
    elif indicators['rsi'] > 70 and indicators['ema_9'] < indicators['ema_21']:
        signals.append("RSI_OVERBOUGHT_EMA_BEARISH")
        total_confidence += 35
        if volatility_data['volatility_regime'] == "HIGH_VOLATILITY":
            total_confidence += 10
            signals.append("AI_HIGH_VOL_CONFIRMATION")
        action = "PUT"
    
    # RULE 2: ENGULFING + SUPPORT/RESISTANCE + AI Liquidity (50 points)
    if ("BULLISH_ENGULFING" in price_action['price_signals'] and 
        "AT_SUPPORT" in price_action['price_signals']):
        signals.append("BULLISH_ENGULFING_AT_SUPPORT")
        total_confidence += 35
        # AI Liquidity confirmation
        if liquidity_data['near_support']:
            total_confidence += 15
            signals.append("AI_LIQUIDITY_CONFIRMATION")
        action = "CALL"
    elif ("BEARISH_ENGULFING" in price_action['price_signals'] and 
          "AT_RESISTANCE" in price_action['price_signals']):
        signals.append("BEARISH_ENGULFING_AT_RESISTANCE")
        total_confidence += 35
        if liquidity_data['near_resistance']:
            total_confidence += 15
            signals.append("AI_LIQUIDITY_CONFIRMATION")
        action = "PUT"
    
    # RULE 3: PINBAR + EMA + AI Momentum (40 points)
    if ("HAMMER_PINBAR" in price_action['price_signals'] and 
        indicators['ema_9'] > indicators['ema_21']):
        signals.append("HAMMER_EMA_BULLISH")
        total_confidence += 25
        # AI Momentum confirmation
        if "ACCELERATING_UP" in momentum_data['momentum_signals']:
            total_confidence += 15
            signals.append("AI_MOMENTUM_CONFIRMATION")
        action = "CALL"
    elif ("SHOOTING_STAR" in price_action['price_signals'] and 
          indicators['ema_9'] < indicators['ema_21']):
        signals.append("SHOOTING_STAR_EMA_BEARISH")
        total_confidence += 25
        if "ACCELERATING_DOWN" in momentum_data['momentum_signals']:
            total_confidence += 15
            signals.append("AI_MOMENTUM_CONFIRMATION")
        action = "PUT"
    
    # RULE 4: RSI + PRICE ACTION + AI Multi-confirmation (45 points)
    if (indicators['rsi'] < 30 and 
        "BULLISH_ENGULFING" in price_action['price_signals']):
        signals.append("RSI_OVERSOLD_BULLISH_ENGULFING")
        total_confidence += 30
        # AI Multi-factor boost
        if (liquidity_data['near_support'] and 
            volatility_data['volatility_regime'] == "HIGH_VOLATILITY"):
            total_confidence += 15
            signals.append("AI_MULTI_CONFIRMATION")
        action = "CALL"
    elif (indicators['rsi'] > 70 and 
          "BEARISH_ENGULFING" in price_action['price_signals']):
        signals.append("RSI_OVERBOUGHT_BEARISH_ENGULFING")
        total_confidence += 30
        if (liquidity_data['near_resistance'] and 
            volatility_data['volatility_regime'] == "HIGH_VOLATILITY"):
            total_confidence += 15
            signals.append("AI_MULTI_CONFIRMATION")
        action = "PUT"
    
    # AI BONUS: Strong confluence (20 points)
    ai_bonus = volatility_data['volatility_score'] + liquidity_data['liquidity_score'] + momentum_data['momentum_score']
    if ai_bonus >= 40 and action != "HOLD":
        total_confidence += 20
        signals.append("AI_STRONG_CONFLUENCE")
    
    return {
        'action': action,
        'confidence': min(total_confidence, 95),
        'signals': signals,
        'confidence_level': 'MEDIUM',
        'is_tradable': total_confidence >= 70,
        'ai_data': {
            'volatility': volatility_data,
            'liquidity': liquidity_data,
            'momentum': momentum_data,
            'ai_bonus_score': ai_bonus
        }
    }
