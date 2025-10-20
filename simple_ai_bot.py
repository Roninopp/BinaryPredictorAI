import pandas as pd
import numpy as np
import requests
import time
import json
import logging
import asyncio
import sys
import os
from datetime import datetime, timedelta
import ta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

print("🚀 STARTING ULTIMATE AI TRADING BOT...")

# Add strategies folder to path
current_dir = os.path.dirname(os.path.abspath(__file__))
strategies_path = os.path.join(current_dir, 'strategies')
sys.path.insert(0, strategies_path)

print(f"📁 Strategies path: {strategies_path}")

# Try to import strategies
try:
    from ai_enhancements import ai_enhancements
    from low_strategy_ENHANCED import generate_low_confidence_signals
    from medium_strategy_ENHANCED import generate_medium_confidence_signals
    from high_strategy_ENHANCED import generate_high_confidence_signals
    STRATEGIES_LOADED = True
    print("✅ ALL ENHANCED AI STRATEGIES LOADED!")
except ImportError as e:
    print(f"❌ Enhanced strategies failed: {e}")
    try:
        from low_strategy import generate_low_confidence_signals
        from medium_strategy import generate_medium_confidence_signals
        STRATEGIES_LOADED = True
        print("⚠️  Using original strategies as fallback")
    except ImportError as e2:
        print(f"❌ CRITICAL: No strategies found! {e2}")
        STRATEGIES_LOADED = False

# Bot configuration (env vars preferred)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
YOUR_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class SimpleAITradingBot:
    def __init__(self):
        self.auto_trade_enabled = False
        
    def get_market_data(self, pair):
        """Simple market data simulation"""
        base_prices = {
            "AUD/CAD OTC": 0.885, "EUR/USD": 1.068, 
            "GBP/USD": 1.344, "XAU/USD": 2415.0
        }
        base_price = base_prices.get(pair, 1.0)
        closes = [base_price * (1 + np.random.normal(0, 0.002)) for _ in range(50)]
        return {
            'price': closes[-1],
            'closes': closes,
            'success': True
        }
    
    def analyze_pair(self, pair):
        """Simple analysis function"""
        try:
            market_data = self.get_market_data(pair)
            price = market_data['price']
            
            # Simple signal logic
            if price > 1.0:
                signal = "CALL"
                confidence = 65
            else:
                signal = "PUT" 
                confidence = 65
                
            return {
                'signal': signal,
                'confidence': confidence,
                'price': price,
                'success': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Create bot instance
bot = SimpleAITradingBot()

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 SIMPLE AI BOT STARTED!\nUse /analyze PAIR")

async def analyze_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Usage: /analyze PAIR")
            return
            
        pair = " ".join(context.args).upper()
        analysis = bot.analyze_pair(pair)
        
        if analysis['success']:
            message = f"""
📊 ANALYSIS: {pair}
💹 Price: ${analysis['price']:.4f}
📈 Signal: {analysis['signal']}
🎯 Confidence: {analysis['confidence']}%
✅ SUCCESS!
            """
        else:
            message = f"❌ Error: {analysis['error']}"
            
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Analysis failed: {str(e)}")

def main():
    """Start the simple bot"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("analyze", analyze_pair))
        
        print("🤖 SIMPLE AI BOT STARTED SUCCESSFULLY!")
        print("📱 Commands: /start, /analyze PAIR")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ BOT FAILED: {e}")

if __name__ == "__main__":
    main()
