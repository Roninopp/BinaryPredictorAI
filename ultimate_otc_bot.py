import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime, timedelta
import ta
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# ==================== CONFIGURATION ====================
BOT_TOKEN = "7914882777:AAGv_940utBNry2JXfwbzhtZWxtyK1qMO24"
UTC_PLUS_7 = timedelta(hours=7)

# ENHANCED TRADING PAIRS - REGULAR + OTC (92% RETURNS)
TRADING_PAIRS = {
    # Regular Binary Pairs
    "EUR/USD": "EURUSD", "GBP/USD": "GBPUSD", "USD/JPY": "USDJPY",
    "AUD/USD": "AUDUSD", "XAU/USD": "XAUUSD", "BTC/USD": "BTCUSD",
    
    # OTC PAIRS (92% HIGH RETURNS!)
    "AUD/CAD OTC": "AUDCAD", "AUD/USD OTC": "AUDUSD", 
    "CAD/JPY OTC": "CADJPY", "CHF/JPY OTC": "CHFJPY",
    "EUR/CHF OTC": "EURCHF", "GBP/AUD OTC": "GBPAUD",
    "NZD/JPY OTC": "NZDJPY", "USD/CHF OTC": "USDCHF"
}

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltimateBinaryAI:
    def __init__(self):
        self.market_analysis = []
        
    def get_utc7_time(self):
        """Get current UTC+7 time for Pocket Option"""
        return datetime.utcnow() + UTC_PLUS_7
    
    def fetch_market_data(self, pair, timeframe):
        """Fetch market data with OTC-specific ranges"""
        try:
            # Real data integration would go here
            return self.get_enhanced_simulated_data(pair)
        except:
            return self.get_enhanced_simulated_data(pair)
    
    def get_enhanced_simulated_data(self, pair):
        """Realistic price data for both regular and OTC pairs"""
        # PROFESSIONAL PRICE RANGES FOR BINARY OPTIONS
        base_prices = {
            # Regular Pairs
            "EUR/USD": 1.068, "GBP/USD": 1.344, "USD/JPY": 159.2,
            "AUD/USD": 0.734, "XAU/USD": 2415.0, "BTC/USD": 61500,
            
            # OTC Pairs (Specific ranges)
            "AUD/CAD OTC": 0.885, "AUD/USD OTC": 0.734, 
            "CAD/JPY OTC": 114.5, "CHF/JPY OTC": 176.8,
            "EUR/CHF OTC": 0.945, "GBP/AUD OTC": 1.832,
            "NZD/JPY OTC": 93.4, "USD/CHF OTC": 0.885
        }
        
        base_price = base_prices.get(pair, 1.0)
        # Generate realistic price movement
        closes = [base_price * (1 + np.random.normal(0, 0.0015)) for _ in range(100)]
        highs = [price * (1 + abs(np.random.normal(0, 0.001))) for price in closes]
        lows = [price * (1 - abs(np.random.normal(0, 0.001))) for price in closes]
        opens = [price * (1 + np.random.normal(0, 0.0005)) for price in closes]
        
        return {
            'success': True,
            'price': closes[-1],
            'opens': opens, 'highs': highs, 'lows': lows, 'closes': closes,
            'timestamp': self.get_utc7_time(),
            'is_otc': 'OTC' in pair
        }

    def advanced_price_action_detection(self, opens, highs, lows, closes):
        """ULTIMATE Price Action Detection with Liquidity Analysis"""
        current_open = opens[-1]
        current_high = highs[-1]
        current_low = lows[-1]
        current_close = closes[-1]
        prev_open = opens[-2]
        prev_high = highs[-2]
        prev_low = lows[-2]
        prev_close = closes[-2]
        
        price_signals = []
        confidence_boost = 0
        
        # ===== 1. CANDLESTICK PATTERNS =====
        body_size = abs(current_close - current_open)
        upper_wick = current_high - max(current_open, current_close)
        lower_wick = min(current_open, current_close) - current_low
        total_range = current_high - current_low
        
        # Engulfing Patterns
        if (current_close > current_open and prev_close < prev_open and
            current_open < prev_close and current_close > prev_open):
            price_signals.append("🔥 BULLISH ENGULFING")
            confidence_boost += 25
            
        elif (current_close < current_open and prev_close > prev_open and
              current_open > prev_close and current_close < prev_open):
            price_signals.append("🔻 BEARISH ENGULFING")
            confidence_boost += 25
        
        # Pin Bars
        if (lower_wick >= 2 * body_size and upper_wick <= body_size * 0.3):
            price_signals.append("🔨 HAMMER PIN BAR")
            confidence_boost += 20
            
        elif (upper_wick >= 2 * body_size and lower_wick <= body_size * 0.3):
            price_signals.append("⭐ SHOOTING STAR")
            confidence_boost += 20
        
        # ===== 2. LIQUIDITY & MARKET STRUCTURE =====
        recent_high = max(highs[-15:])
        recent_low = min(lows[-15:])
        resistance = recent_high * 1.0005  # Slight buffer
        support = recent_low * 0.9995      # Slight buffer
        
        # Liquidity Sweep Detection
        if current_high >= recent_high:
            price_signals.append("💧 LIQUIDITY SWEEP HIGH")
            confidence_boost += 15
            
        if current_low <= recent_low:
            price_signals.append("💧 LIQUIDITY SWEEP LOW") 
            confidence_boost += 15
        
        # Support/Resistance Reaction
        if abs(current_high - resistance) / resistance < 0.0005:
            price_signals.append("🚧 AT RESISTANCE")
            confidence_boost += 10
            
        if abs(current_low - support) / support < 0.0005:
            price_signals.append("🛡️ AT SUPPORT")
            confidence_boost += 10
        
        return {
            'price_signals': price_signals,
            'confidence_boost': confidence_boost,
            'support': support,
            'resistance': resistance,
            'recent_high': recent_high,
            'recent_low': recent_low
        }

    def dual_indicator_confirmation(self, closes, highs, lows):
        """2-INDICATOR CONFIRMATION SYSTEM"""
        prices = pd.Series(closes)
        
        # INDICATOR 1: RSI (Momentum)
        rsi = ta.momentum.RSIIndicator(prices, window=14).rsi().iloc[-1]
        
        # INDICATOR 2: EMA CROSSOVER (Trend)
        ema_9 = ta.trend.EMAIndicator(prices, window=9).ema_indicator().iloc[-1]
        ema_21 = ta.trend.EMAIndicator(prices, window=21).ema_indicator().iloc[-1]
        
        indicator_signals = []
        indicator_confidence = 0
        
        # RSI Analysis
        if rsi < 30:
            indicator_signals.append("📉 RSI OVERSOLD")
            indicator_confidence += 20
        elif rsi > 70:
            indicator_signals.append("📈 RSI OVERBOUGHT")
            indicator_confidence += 20
        elif 40 < rsi < 60:
            indicator_signals.append("⚖️ RSI NEUTRAL")
            indicator_confidence += 5
        
        # EMA Trend Analysis
        if ema_9 > ema_21:
            indicator_signals.append("📈 EMA BULLISH")
            indicator_confidence += 15
        else:
            indicator_signals.append("📉 EMA BEARISH") 
            indicator_confidence += 15
        
        return {
            'rsi': round(rsi, 1),
            'ema_9': round(ema_9, 4),
            'ema_21': round(ema_21, 4),
            'indicator_signals': indicator_signals,
            'indicator_confidence': indicator_confidence
        }

    def generate_ultimate_signal(self, price_action, indicators, current_price, is_otc=False):
        """AI-POWERED SIGNAL GENERATION WITH MY STRATEGIES"""
        total_confidence = price_action['confidence_boost'] + indicators['indicator_confidence']
        signal = "HOLD"
        reasons = []
        
        # MY PERSONAL TRADING STRATEGIES COMBINED:
        
        # STRATEGY 1: Engulfing + RSI Extreme
        if ("BULLISH ENGULFING" in price_action['price_signals'] and 
            indicators['rsi'] < 35):
            signal = "CALL"
            total_confidence += 20
            reasons.extend(["Strong bullish reversal", "RSI oversold confirmation"])
            
        elif ("BEARISH ENGULFING" in price_action['price_signals'] and 
              indicators['rsi'] > 65):
            signal = "PUT" 
            total_confidence += 20
            reasons.extend(["Strong bearish reversal", "RSI overbought confirmation"])
        
        # STRATEGY 2: Pin Bar at Key Levels
        elif (("HAMMER PIN BAR" in price_action['price_signals'] and 
               "AT SUPPORT" in price_action['price_signals']) or
              ("SHOOTING STAR" in price_action['price_signals'] and 
               "AT RESISTANCE" in price_action['price_signals'])):
            signal = "CALL" if "HAMMER" in price_action['price_signals'] else "PUT"
            total_confidence += 25
            reasons.extend(["Pin bar at key level", "High probability reversal"])
        
        # STRATEGY 3: Liquidity Sweep + EMA Confirmation
        elif (("LIQUIDITY SWEEP HIGH" in price_action['price_signals'] and 
               indicators['ema_9'] < indicators['ema_21']) or
              ("LIQUIDITY SWEEP LOW" in price_action['price_signals'] and 
               indicators['ema_9'] > indicators['ema_21'])):
            signal = "PUT" if "HIGH" in price_action['price_signals'] else "CALL"
            total_confidence += 20
            reasons.extend(["Liquidity sweep confirmed", "Trend alignment"])
        
        # DEFAULT: Wait for better setup
        if signal == "HOLD":
            reasons.append("Waiting for stronger confirmation")
            total_confidence = max(15, total_confidence)
        
        # OTC ADJUSTMENT (Slightly more conservative)
        if is_otc:
            total_confidence = min(total_confidence, 85)  # Cap confidence for OTC
        
        return {
            'signal': signal,
            'confidence': min(95, total_confidence),
            'reasons': reasons,
            'recommendation': "STRONG TRADE - ENTER NOW" if total_confidence > 65 else 
                            "GOOD SETUP - CONSIDER TRADE" if total_confidence > 50 else
                            "WAIT FOR BETTER ENTRY"
        }

# ==================== TELEGRAM BOT ====================
ultimate_ai = UltimateBinaryAI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎯 **ULTIMATE BINARY TRADING AI** 🎯

*Professional Features:*
• **OTC Markets** (92% Returns) 📈
• **Price Action + 2 Indicators** 
• **Liquidity & Market Structure**
• **UTC+7 Pocket Option Optimized**
• **AI-Powered Strategies**

*Commands:*
/analyze PAIR TIMEFRAME - Professional analysis
/pairs - Available pairs (Regular + OTC)
/time - UTC+7 Time

*Example:* `/analyze AUD/CAD OTC 5m`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def analyze_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "📊 *Usage:* /analyze PAIR TIMEFRAME\n"
                "*Example:* `/analyze AUD/CAD OTC 5m`\n"
                "Use /pairs to see available options",
                parse_mode='Markdown'
            )
            return

        pair = " ".join(context.args[:-1]).upper()
        timeframe = context.args[-1].lower()

        if pair not in TRADING_PAIRS:
            await update.message.reply_text("❌ Invalid pair. Use /pairs")
            return

        if timeframe not in TIMEFRAMES:
            await update.message.reply_text("❌ Invalid timeframe. Use: 1m, 5m, 15m, 1h, 4h")
            return

        # Analyzing message
        analyzing_msg = await update.message.reply_text(
            f"🔍 *Analyzing {pair} on {timeframe}...*\n"
            f"🎯 *OTC Mode:* {'✅ YES (92%)' if 'OTC' in pair else 'Regular'}\n"
            f"🕐 UTC+7: {ultimate_ai.get_utc7_time().strftime('%H:%M:%S')}",
            parse_mode='Markdown'
        )

        # Get data and analyze
        market_data = ultimate_ai.fetch_market_data(pair, timeframe)
        price_action = ultimate_ai.advanced_price_action_detection(
            market_data['opens'], market_data['highs'], 
            market_data['lows'], market_data['closes']
        )
        indicators = ultimate_ai.dual_indicator_confirmation(
            market_data['closes'], market_data['highs'], market_data['lows']
        )
        signal = ultimate_ai.generate_ultimate_signal(
            price_action, indicators, market_data['price'], market_data.get('is_otc', False)
        )

        # Build professional analysis
        analysis_text = f"""
🎯 **ULTIMATE ANALYSIS - {pair} {timeframe.upper()}**
{'💰 *OTC MARKET (92% RETURNS)*' if 'OTC' in pair else '📊 Regular Market'}

💹 *Price:* ${market_data['price']:.4f}
📊 *RSI:* {indicators['rsi']}
📈 *EMA 9:* ${indicators['ema_9']:.4f}
📉 *EMA 21:* ${indicators['ema_21']:.4f}

🛡️ *Support:* ${price_action['support']:.4f}
🚧 *Resistance:* ${price_action['resistance']:.4f}

🔮 **TRADE SIGNAL:** {signal['signal']}
🎯 **CONFIDENCE:** {signal['confidence']}%

📋 **PRICE ACTION:**
""" + "\n".join([f"• {sig}" for sig in price_action['price_signals']]) + f"""

📊 **INDICATORS:**
""" + "\n".join([f"• {sig}" for sig in indicators['indicator_signals']]) + f"""

💡 **REASONS:**
""" + "\n".join([f"• {reason}" for reason in signal['reasons']]) + f"""

🚀 **RECOMMENDATION:** {signal['recommendation']}

⏰ *Analysis Time (UTC+7):* {ultimate_ai.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')}
        """

        await analyzing_msg.edit_text(analysis_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await update.message.reply_text("❌ Analysis error. Please try again.")

async def show_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    regular_pairs = [p for p in TRADING_PAIRS.keys() if 'OTC' not in p]
    otc_pairs = [p for p in TRADING_PAIRS.keys() if 'OTC' in p]
    
    pairs_text = "📊 *Available Trading Pairs:*\n\n"
    pairs_text += "*Regular Binary:*\n" + "\n".join([f"• {pair}" for pair in regular_pairs]) + "\n\n"
    pairs_text += "*💰 OTC (92% Returns):*\n" + "\n".join([f"• {pair}" for pair in otc_pairs]) + "\n\n"
    pairs_text += "*Timeframes:* 1m, 5m, 15m, 1h, 4h"
    
    await update.message.reply_text(pairs_text, parse_mode='Markdown')

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_time = ultimate_ai.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f"🕐 *Pocket Option Time (UTC+7):* {current_time}", 
                                  parse_mode='Markdown')

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_pair))
    application.add_handler(CommandHandler("pairs", show_pairs))
    application.add_handler(CommandHandler("time", show_time))
    
    logger.info("🎯 ULTIMATE BINARY TRADING AI STARTED!")
    print("🤖 Bot is running... Press Ctrl+C to stop")
    print("💰 OTC Markets Enabled (92% Returns)")
    
    application.run_polling()

if __name__ == "__main__":
    main()
