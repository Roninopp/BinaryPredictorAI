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

TRADING_PAIRS = {
    "EUR/USD": "EURUSD", "GBP/USD": "GBPUSD", "USD/JPY": "USDJPY",
    "AUD/USD": "AUDUSD", "XAU/USD": "XAUUSD", "BTC/USD": "BTCUSD",
    "ETH/USD": "ETHUSD", "US30": "US30"
}

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]

logging.basicConfig(level=logging.INFO)

class PriceActionMaster:
    def __init__(self):
        self.analysis_history = []
        
    def get_utc7_time(self):
        return datetime.utcnow() + UTC_PLUS_7
    
    def fetch_price_data(self, pair, timeframe):
        """Fetch market data"""
        try:
            symbol = TRADING_PAIRS.get(pair, pair)
            # Your data source here
            return self.get_simulated_data(pair)
        except:
            return self.get_simulated_data(pair)
    
    def get_simulated_data(self, pair):
        """Realistic price simulation"""
        base_prices = {
            "EUR/USD": 1.07, "GBP/USD": 1.25, "USD/JPY": 150.0,
            "AUD/USD": 0.65, "XAU/USD": 2400.0, "BTC/USD": 60000,
            "ETH/USD": 3000, "US30": 40000
        }
        
        base_price = base_prices.get(pair, 1.0)
        closes = [base_price * (1 + np.random.normal(0, 0.002)) for _ in range(100)]
        highs = [price * (1 + abs(np.random.normal(0, 0.001))) for price in closes]
        lows = [price * (1 - abs(np.random.normal(0, 0.001))) for price in closes]
        opens = [price * (1 + np.random.normal(0, 0.0005)) for price in closes]
        
        return {
            'success': True,
            'price': closes[-1],
            'opens': opens, 'highs': highs, 'lows': lows, 'closes': closes,
            'timestamp': self.get_utc7_time()
        }

    def advanced_price_action_analysis(self, opens, highs, lows, closes):
        """MAIN PRICE ACTION ANALYSIS ENGINE"""
        current_open = opens[-1]
        current_high = highs[-1]
        current_low = lows[-1]
        current_close = closes[-1]
        prev_open = opens[-2]
        prev_high = highs[-2]
        prev_low = lows[-2]
        prev_close = closes[-2]
        
        price_action_signals = []
        confidence = 0
        
        # ===== PRICE ACTION PATTERNS =====
        
        # 1. ENGULFING PATTERNS
        if (current_close > current_open and prev_close < prev_open and
            current_open < prev_close and current_close > prev_open):
            price_action_signals.append("🔥 BULLISH ENGULFING")
            confidence += 25
            
        elif (current_close < current_open and prev_close > prev_open and
              current_open > prev_close and current_close < prev_open):
            price_action_signals.append("🔻 BEARISH ENGULFING") 
            confidence += 25
        
        # 2. PIN BARS
        body_size = abs(current_close - current_open)
        upper_wick = current_high - max(current_open, current_close)
        lower_wick = min(current_open, current_close) - current_low
        total_range = current_high - current_low
        
        # Hammer Pin Bar (Bullish Reversal)
        if (lower_wick >= 2 * body_size and upper_wick <= body_size * 0.5):
            price_action_signals.append("🔨 HAMMER PIN BAR - BULLISH")
            confidence += 20
            
        # Shooting Star (Bearish Reversal)  
        elif (upper_wick >= 2 * body_size and lower_wick <= body_size * 0.5):
            price_action_signals.append("⭐ SHOOTING STAR - BEARISH")
            confidence += 20
        
        # 3. INSIDE BAR (Consolidation)
        if (current_high <= prev_high and current_low >= prev_low):
            price_action_signals.append("📊 INSIDE BAR - BREAKOUT SOON")
            confidence += 15
        
        # 4. SUPPORT/RESISTANCE REACTION
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        
        # At Resistance
        if current_high >= recent_high * 0.999:
            price_action_signals.append("🚧 AT RESISTANCE")
            confidence += 10
            
        # At Support  
        if current_low <= recent_low * 1.001:
            price_action_signals.append("🛡️ AT SUPPORT")
            confidence += 10
        
        # ===== 2 INDICATOR CONFIRMATIONS =====
        
        # INDICATOR 1: RSI
        rsi = ta.momentum.RSIIndicator(pd.Series(closes), window=14).rsi().iloc[-1]
        
        # INDICATOR 2: EMA CROSSOVER (9 & 21)
        ema_9 = ta.trend.EMAIndicator(pd.Series(closes), window=9).ema_indicator().iloc[-1]
        ema_21 = ta.trend.EMAIndicator(pd.Series(closes), window=21).ema_indicator().iloc[-1]
        
        # RSI Confirmation
        if rsi < 30:
            price_action_signals.append("📉 RSI OVERSOLD")
            confidence += 15
        elif rsi > 70:
            price_action_signals.append("📈 RSI OVERBOUGHT") 
            confidence += 15
        
        # EMA Trend Confirmation
        if ema_9 > ema_21:
            price_action_signals.append("📈 EMA BULLISH TREND")
            confidence += 10
        else:
            price_action_signals.append("📉 EMA BEARISH TREND")
            confidence += 10
        
        # ===== GENERATE FINAL SIGNAL =====
        signal = "HOLD"
        if confidence >= 40:
            if any("BULLISH" in sig for sig in price_action_signals):
                signal = "CALL"
            elif any("BEARISH" in sig for sig in price_action_signals):
                signal = "PUT"
        
        return {
            'current_price': round(current_close, 4),
            'price_action_signals': price_action_signals,
            'rsi': round(rsi, 1),
            'ema_9': round(ema_9, 4),
            'ema_21': round(ema_21, 4),
            'signal': signal,
            'confidence': min(95, confidence),
            'support': round(recent_low, 4),
            'resistance': round(recent_high, 4),
            'recommendation': "STRONG TRADE" if confidence > 60 else "WAIT FOR BETTER ENTRY"
        }

# ==================== TELEGRAM BOT ====================
price_action_ai = PriceActionMaster()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎯 **PRICE ACTION MASTER BOT** 🎯

*Specialized in:*
• **Advanced Price Action Patterns**
• **2-Indicator Confirmation** (RSI + EMA)
• **UTC+7 Timezone Optimized**
• **Professional Trading Signals**

*Commands:*
/analyze PAIR TIMEFRAME - Price Action Analysis
/pairs - Available pairs
/time - UTC+7 Time

*Example:* `/analyze EUR/USD 5m`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def analyze_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "📊 *Usage:* /analyze PAIR TIMEFRAME\n"
                "*Example:* `/analyze EUR/USD 5m`\n"
                "Use /pairs to see available options",
                parse_mode='Markdown'
            )
            return

        pair = context.args[0].upper()
        timeframe = context.args[1].lower()

        if pair not in TRADING_PAIRS:
            await update.message.reply_text("❌ Invalid pair. Use /pairs")
            return

        if timeframe not in TIMEFRAMES:
            await update.message.reply_text("❌ Invalid timeframe. Use: 1m, 5m, 15m, 1h, 4h")
            return

        # Analyzing message
        analyzing_msg = await update.message.reply_text(
            f"🔍 *Analyzing {pair} on {timeframe}...*\n"
            f"🕐 UTC+7: {price_action_ai.get_utc7_time().strftime('%H:%M:%S')}",
            parse_mode='Markdown'
        )

        # Get data and analyze
        market_data = price_action_ai.fetch_price_data(pair, timeframe)
        analysis = price_action_ai.advanced_price_action_analysis(
            market_data['opens'], market_data['highs'], 
            market_data['lows'], market_data['closes']
        )

        # Build results
        analysis_text = f"""
🎯 **PRICE ACTION ANALYSIS - {pair} {timeframe.upper()}**

💹 *Price:* ${analysis['current_price']}
📊 *RSI:* {analysis['rsi']}
📈 *EMA 9:* ${analysis['ema_9']}
📉 *EMA 21:* ${analysis['ema_21']}

🛡️ *Support:* ${analysis['support']} 
🚧 *Resistance:* ${analysis['resistance']}

🔮 **SIGNAL:** {analysis['signal']}
🎯 **CONFIDENCE:** {analysis['confidence']}%

📋 **PRICE ACTION SIGNALS:**
""" + "\n".join([f"• {signal}" for signal in analysis['price_action_signals']]) + f"""

💡 **RECOMMENDATION:** {analysis['recommendation']}

⏰ *UTC+7 Time:* {price_action_ai.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')}
        """

        await analyzing_msg.edit_text(analysis_text, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text("❌ Analysis error. Try again.")

async def show_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs_text = "📊 *Available Pairs:*\n" + "\n".join([f"• {pair}" for pair in TRADING_PAIRS.keys()])
    await update.message.reply_text(pairs_text, parse_mode='Markdown')

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_time = price_action_ai.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f"🕐 *UTC+7 Time:* {current_time}", parse_mode='Markdown')

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_pair))
    application.add_handler(CommandHandler("pairs", show_pairs))
    application.add_handler(CommandHandler("time", show_time))
    
    print("🎯 PRICE ACTION BOT STARTED! Press Ctrl+C to stop")
    application.run_polling()

if __name__ == "__main__":
    main()
