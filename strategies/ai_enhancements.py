import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class AIEnhancements:
    def __init__(self):
        self.volatility_history = {}
        self.liquidity_zones = {}
    
    def calculate_ai_volatility_prediction(self, closes, period=20):
        """AI-powered volatility forecasting"""
        prices = pd.Series(closes)
        
        # Historical volatility
        returns = np.log(prices / prices.shift(1))
        hist_volatility = returns.rolling(window=period).std() * np.sqrt(365) * 100
        
        # Volatility regime detection
        current_vol = hist_volatility.iloc[-1] if not hist_volatility.isna().iloc[-1] else 15.0
        avg_vol = hist_volatility.mean() if not hist_volatility.isna().all() else 15.0
        
        # AI Volatility Prediction
        if current_vol > avg_vol * 1.3:
            vol_regime = "HIGH_VOLATILITY"
            vol_score = 25
        elif current_vol < avg_vol * 0.7:
            vol_regime = "LOW_VOLATILITY" 
            vol_score = 15
        else:
            vol_regime = "NORMAL_VOLATILITY"
            vol_score = 20
            
        return {
            'volatility_regime': vol_regime,
            'volatility_score': vol_score,
            'current_volatility': round(current_vol, 2),
            'prediction': "EXPECT_PRICE_SURGE" if vol_regime == "HIGH_VOLATILITY" else "STABLE_MOVEMENT"
        }
    
    def detect_liquidity_zones(self, highs, lows, closes, lookback=50):
        """Smart money liquidity zone detection"""
        prices = pd.Series(closes)
        
        # Identify significant highs and lows
        significant_highs = []
        significant_lows = []
        
        for i in range(2, len(highs)-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                significant_highs.append(highs[i])
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                significant_lows.append(lows[i])
        
        # Calculate liquidity zones (support/resistance clusters)
        if significant_highs:
            resistance_zone = np.mean(significant_highs[-3:]) if len(significant_highs) >= 3 else np.mean(highs[-10:])
        else:
            resistance_zone = np.mean(highs[-10:])
            
        if significant_lows:
            support_zone = np.mean(significant_lows[-3:]) if len(significant_lows) >= 3 else np.mean(lows[-10:])
        else:
            support_zone = np.mean(lows[-10:])
        
        current_price = closes[-1]
        
        # Liquidity proximity scoring
        resistance_distance = abs(resistance_zone - current_price) / current_price
        support_distance = abs(support_zone - current_price) / current_price
        
        liquidity_score = 0
        if resistance_distance < 0.002:  # 0.2% from resistance
            liquidity_score += 20
        if support_distance < 0.002:     # 0.2% from support
            liquidity_score += 20
            
        return {
            'liquidity_support': round(support_zone, 4),
            'liquidity_resistance': round(resistance_zone, 4),
            'liquidity_score': liquidity_score,
            'near_support': support_distance < 0.002,
            'near_resistance': resistance_distance < 0.002
        }
    
    def multi_timeframe_confluence(self, data_1m, data_5m, data_1h):
        """AI Multi-timeframe alignment analysis"""
        confluence_score = 0
        signals = []
        
        # Extract trends from different timeframes
        trend_1m = "BULLISH" if data_1m['closes'][-1] > data_1m['closes'][-10] else "BEARISH"
        trend_5m = "BULLISH" if data_5m['closes'][-1] > data_5m['closes'][-10] else "BEARISH" 
        trend_1h = "BULLISH" if data_1h['closes'][-1] > data_1h['closes'][-10] else "BEARISH"
        
        # Confluence scoring
        if trend_1m == trend_5m == trend_1h:
            confluence_score += 30
            signals.append("STRONG_TREND_CONFLUENCE")
        elif trend_1m == trend_5m:
            confluence_score += 20
            signals.append("MEDIUM_TREND_CONFLUENCE")
        elif trend_5m == trend_1h:
            confluence_score += 15
            signals.append("LONGER_TERM_CONFLUENCE")
            
        return {
            'confluence_score': confluence_score,
            'confluence_signals': signals,
            'trend_alignment': f"1m:{trend_1m} 5m:{trend_5m} 1h:{trend_1h}"
        }
    
    def momentum_acceleration(self, closes, period=14):
        """Advanced momentum detection with acceleration"""
        prices = pd.Series(closes)
        
        # Rate of Change (ROC)
        roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        current_roc = roc.iloc[-1] if not roc.isna().iloc[-1] else 0
        
        # Momentum acceleration (ROC of ROC)
        roc_roc = ((roc - roc.shift(5)) / roc.shift(5)) * 100 if not roc.isna().all() else 0
        acceleration = roc_roc.iloc[-1] if not pd.isna(roc_roc.iloc[-1]) else 0
        
        momentum_score = 0
        momentum_signals = []
        
        if abs(current_roc) > 2.0:  # Strong momentum
            momentum_score += 20
            momentum_signals.append("STRONG_MOMENTUM")
            
        if acceleration > 10:  # Accelerating momentum
            momentum_score += 15
            momentum_signals.append("ACCELERATING_UP")
        elif acceleration < -10:
            momentum_score += 15  
            momentum_signals.append("ACCELERATING_DOWN")
            
        return {
            'momentum_score': momentum_score,
            'momentum_signals': momentum_signals,
            'rate_of_change': round(current_roc, 2),
            'acceleration': round(acceleration, 2)
        }

# Global AI instance
ai_enhancements = AIEnhancements()
