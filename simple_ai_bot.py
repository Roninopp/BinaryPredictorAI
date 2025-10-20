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
    ENHANCED_STRATEGIES_LOADED = True
    print("✅ ALL ENHANCED AI STRATEGIES LOADED!")
except ImportError as e:
    print(f"❌ Enhanced strategies failed: {e}")
    try:
        from low_strategy import generate_low_confidence_signals
        from medium_strategy import generate_medium_confidence_signals
        STRATEGIES_LOADED = True
        ENHANCED_STRATEGIES_LOADED = False
        print("⚠️  Using original strategies as fallback")
    except ImportError as e2:
        print(f"❌ CRITICAL: No strategies found! {e2}")
        STRATEGIES_LOADED = False
        ENHANCED_STRATEGIES_LOADED = False

# Bot configuration
BOT_TOKEN = "7914882777:AAGv_940utBNry2JXfwbzhtZWxtyK1qMO24"
YOUR_CHAT_ID = "-1002903475551"

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
        """Enhanced analysis function with strategy integration"""
        try:
            market_data = self.get_market_data(pair)
            if not market_data['success']:
                return {'success': False, 'error': market_data['error']}
            
            price = market_data['price']
            closes = market_data['closes']
            
            # Calculate basic indicators
            rsi = self.calculate_rsi(closes)
            ema_9 = self.calculate_ema(closes, 9)
            ema_21 = self.calculate_ema(closes, 21)
            
            # Create price action data
            price_action = {
                'price_signals': [],
                'confidence_boost': 0,
                'support': min(closes[-10:]) * 0.9998,
                'resistance': max(closes[-10:]) * 1.0002
            }
            
            # Detect basic price patterns
            if len(closes) >= 2:
                if closes[-1] > closes[-2] and closes[-2] < closes[-3]:
                    price_action['price_signals'].append("BULLISH_ENGULFING")
                elif closes[-1] < closes[-2] and closes[-2] > closes[-3]:
                    price_action['price_signals'].append("BEARISH_ENGULFING")
            
            # Create indicators data
            indicators = {
                'rsi': rsi,
                'ema_9': ema_9,
                'ema_21': ema_21,
                'indicator_signals': [],
                'indicator_confidence': 0
            }
            
            # Use strategies if available
            if STRATEGIES_LOADED:
                try:
                    if ENHANCED_STRATEGIES_LOADED:
                        signal_data = generate_low_confidence_signals(price_action, indicators, closes)
                    else:
                        signal_data = generate_low_confidence_signals(price_action, indicators)
                    
                    signal = signal_data['action']
                    confidence = signal_data['confidence']
                except Exception as e:
                    print(f"Strategy error: {e}")
                    # Fallback to simple logic
                    signal = "CALL" if price > 1.0 else "PUT"
                    confidence = 65
            else:
                # Simple signal logic
                signal = "CALL" if price > 1.0 else "PUT"
                confidence = 65
                
            return {
                'signal': signal,
                'confidence': confidence,
                'price': price,
                'rsi': rsi,
                'ema_9': ema_9,
                'ema_21': ema_21,
                'success': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_rsi(self, closes, period=14):
        """Calculate RSI indicator"""
        try:
            prices = pd.Series(closes)
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50
    
    def calculate_ema(self, closes, period):
        """Calculate EMA indicator"""
        try:
            prices = pd.Series(closes)
            ema = prices.ewm(span=period).mean()
            return ema.iloc[-1] if not pd.isna(ema.iloc[-1]) else closes[-1]
        except:
            return closes[-1] if closes else 1.0

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
📊 **ANALYSIS: {pair}**
💹 **Price:** ${analysis['price']:.4f}
📈 **Signal:** {analysis['signal']}
🎯 **Confidence:** {analysis['confidence']}%
📉 **RSI:** {analysis.get('rsi', 'N/A')}
📈 **EMA 9/21:** ${analysis.get('ema_9', 0):.4f}/${analysis.get('ema_21', 0):.4f}

✅ **SUCCESS!**
            """
        else:
            message = f"❌ **Error:** {analysis['error']}"
            
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
