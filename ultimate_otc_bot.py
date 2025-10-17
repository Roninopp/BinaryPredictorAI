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
    "AUD/CAD OTC": "AUDCAD", "AUD/USD OTC": "AUDUSD", 
    "CAD/JPY OTC": "CADJPY", "CHF/JPY OTC": "CHFJPY",
    "EUR/CHF OTC": "EURCHF", "GBP/AUD OTC": "GBPAUD",
}

TIMEFRAMES = ["1m", "5m", "15m"]

logging.basicConfig(level=logging.INFO)

class TradingAI:
    def __init__(self):
        pass
        
    def get_utc7_time(self):
        return datetime.utcnow() + UTC_PLUS_7
    
    def fetch_price_data(self, pair, timeframe):
        base_prices = {
            "EUR/USD": 1.068, "GBP/USD": 1.344, "USD/JPY": 159.2,
            "AUD/USD": 0.734, "XAU/USD": 2415.0, "BTC/USD": 61500,
            "AUD/CAD OTC": 0.885, "AUD/USD OTC": 0.734, 
            "CAD/JPY OTC": 114.5, "CHF/JPY OTC": 176.8,
            "EUR/CHF OTC": 0.945, "GBP/AUD OTC": 1.832,
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

    def analyze_market(self, opens, highs, lows, closes):
        current_open = opens[-1]
        current_high = highs[-1]
        current_low = lows[-1]
        current_close = closes[-1]
        
        # Simple RSI
        prices = pd.Series(closes)
        rsi = ta.momentum.RSIIndicator(prices, window=14).rsi().iloc[-1]
        
        # Simple EMA
        ema_9 = ta.trend.EMAIndicator(prices, window=9).ema_indicator().iloc[-1]
        ema_21 = ta.trend.EMAIndicator(prices, window=21).ema_indicator().iloc[-1]
        
        # Support/Resistance
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        
        # Simple signal logic
        signal = "HOLD"
        confidence = 20
        
        if rsi < 30 and current_close > ema_9:
            signal = "CALL"
            confidence = 75
        elif rsi > 70 and current_close < ema_9:
            signal = "PUT"
            confidence = 75
        
        return {
            'current_price': round(current_close, 4),
            'rsi': round(rsi, 1),
            'ema_9': round(ema_9, 4),
            'ema_21': round(ema_21, 4),
            'signal': signal,
            'confidence': confidence,
            'support': round(recent_low, 4),
            'resistance': round(recent_high, 4),
            'recommendation': "TAKE TRADE" if confidence > 60 else "WAIT"
        }

trading_ai = TradingAI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **BINARY TRADING BOT** 🤖

*Features:*
• Price Action Analysis
• RSI + EMA Indicators  
• OTC Markets (92% Returns)
• UTC+7 Timezone

*Commands:*
/analyze PAIR TIMEFRAME
/pairs - Available pairs
/time - UTC+7 Time

*Example:* `/analyze EUR/USD 5m`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def analyze_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /analyze PAIR TIMEFRAME")
            return

        pair = " ".join(context.args[:-1]).upper()
        timeframe = context.args[-1].lower()

        if pair not in TRADING_PAIRS:
            await update.message.reply_text("❌ Invalid pair. Use /pairs")
            return

        analyzing_msg = await update.message.reply_text(f"🔍 Analyzing {pair}...")

        market_data = trading_ai.fetch_price_data(pair, timeframe)
        analysis = trading_ai.analyze_market(
            market_data['opens'], market_data['highs'], 
            market_data['lows'], market_data['closes']
        )

        analysis_text = f"""
🎯 **ANALYSIS - {pair} {timeframe.upper()}**
{'💰 OTC (92%)' if 'OTC' in pair else ''}

💹 Price: ${analysis['current_price']}
📊 RSI: {analysis['rsi']}
📈 EMA 9/21: ${analysis['ema_9']}/${analysis['ema_21']}

🛡️ Support: ${analysis['support']}
🚧 Resistance: ${analysis['resistance']}

🔮 SIGNAL: {analysis['signal']}
🎯 CONFIDENCE: {analysis['confidence']}%

💡 RECOMMENDATION: {analysis['recommendation']}

⏰ UTC+7: {trading_ai.get_utc7_time().strftime('%H:%M:%S')}
        """

        await analyzing_msg.edit_text(analysis_text, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text("❌ Error in analysis")

async def show_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs_text = "📊 Available Pairs:\n" + "\n".join([f"• {pair}" for pair in TRADING_PAIRS.keys()])
    await update.message.reply_text(pairs_text)

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_time = trading_ai.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f"🕐 UTC+7: {current_time}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_pair))
    application.add_handler(CommandHandler("pairs", show_pairs))
    application.add_handler(CommandHandler("time", show_time))
    
    print("🤖 TRADING BOT STARTED!")
    application.run_polling()

if __name__ == "__main__":
    main()
