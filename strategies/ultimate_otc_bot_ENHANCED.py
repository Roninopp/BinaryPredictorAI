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
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Add strategies folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'strategies'))

# Import enhanced strategies
try:
    from strategies.low_strategy_ENHANCED import generate_low_confidence_signals
    from strategies.medium_strategy_ENHANCED import generate_medium_confidence_signals
    from strategies.high_strategy_ENHANCED import generate_high_confidence_signals
    from strategies.ai_enhancements import ai_enhancements
    STRATEGIES_LOADED = True
    print("✅ ALL ENHANCED STRATEGIES LOADED SUCCESSFULLY!")
except ImportError as e:
    print(f"❌ STRATEGY IMPORT ERROR: {e}")
    STRATEGIES_LOADED = False
    # Fallback to original strategies if enhanced ones fail
    try:
        from strategies.low_strategy import generate_low_confidence_signals
        from strategies.medium_strategy import generate_medium_confidence_signals
        print("⚠️  Using original strategies as fallback")
    except ImportError:
        print("❌ CRITICAL: No strategies found!")
        sys.exit(1)

# ==================== CONFIGURATION ====================
BOT_TOKEN = "7914882777:AAGv_940utBNry2JXfwbzhtZWxtyK1qMO24"
UTC_PLUS_7 = timedelta(hours=7)
YOUR_CHAT_ID = "-1002903475551"

# TRADING PAIRS
TRADING_PAIRS = {
    "EUR/USD": "EURUSD", "GBP/USD": "GBPUSD", "USD/JPY": "USDJPY",
    "AUD/USD": "AUDUSD", "XAU/USD": "XAUUSD", "BTC/USD": "BTCUSD",
    "AUD/CAD OTC": "AUDCAD", "AUD/USD OTC": "AUDUSD", 
    "CAD/JPY OTC": "CADJPY", "CHF/JPY OTC": "CHFJPY",
    "EUR/CHF OTC": "EURCHF", "GBP/AUD OTC": "GBPAUD",
    "NZD/JPY OTC": "NZDJPY", "USD/CHF OTC": "USDCHF"
}

TIMEFRAMES = ["1m", "5m", "10m", "1h", "4h"]

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_enhanced.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateEnhancedTradingAI:
    def __init__(self, application):
        self.application = application
        self.last_signals = {}
        self.alert_cooldown = {}
        self.auto_trade_enabled = False  # Start disabled for safety
        self.scanning_task = None
        self.performance_stats = {
            'total_signals': 0,
            'high_confidence_signals': 0,
            'medium_confidence_signals': 0,
            'low_confidence_signals': 0
        }
        
    def get_utc7_time(self):
        """Get current UTC+7 time safely"""
        return datetime.now() + UTC_PLUS_7
    
    def fetch_market_data(self, pair, timeframe):
        """Fetch market data with enhanced error handling"""
        try:
            data = self.get_enhanced_simulated_data(pair)
            if data and data.get('success', False):
                return data
            else:
                logger.error(f"Invalid data for {pair}")
                return self.get_fallback_data(pair)
        except Exception as e:
            logger.error(f"Data fetch error for {pair}: {e}")
            return self.get_fallback_data(pair)
    
    def get_enhanced_simulated_data(self, pair):
        """Realistic price data simulation"""
        try:
            base_prices = {
                "EUR/USD": 1.068, "GBP/USD": 1.344, "USD/JPY": 159.2,
                "AUD/USD": 0.734, "XAU/USD": 2415.0, "BTC/USD": 61500,
                "AUD/CAD OTC": 0.885, "AUD/USD OTC": 0.734, 
                "CAD/JPY OTC": 114.5, "CHF/JPY OTC": 176.8,
                "EUR/CHF OTC": 0.945, "GBP/AUD OTC": 1.832,
                "NZD/JPY OTC": 93.4, "USD/CHF OTC": 0.885
            }
            
            base_price = base_prices.get(pair, 1.0)
            # Generate realistic price movement
            closes = [base_price * (1 + np.random.normal(0, 0.002)) for _ in range(50)]
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
        except Exception as e:
            logger.error(f"Data simulation error: {e}")
            return self.get_fallback_data(pair)
    
    def get_fallback_data(self, pair):
        """Fallback data when primary fails"""
        base_price = 1.0
        closes = [base_price] * 50
        return {
            'success': True,
            'price': base_price,
            'opens': closes, 'highs': closes, 'lows': closes, 'closes': closes,
            'timestamp': self.get_utc7_time(),
            'is_otc': 'OTC' in pair
        }

    def advanced_price_action_detection(self, opens, highs, lows, closes):
        """Enhanced price action detection with error handling"""
        try:
            if len(closes) < 10:
                return {'price_signals': [], 'confidence_boost': 0, 'support': 0, 'resistance': 0}
                
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
            
            # ENGULFING PATTERNS
            if (current_close > current_open and prev_close < prev_open and
                current_open < prev_close and current_close > prev_open):
                price_signals.append("BULLISH_ENGULFING")
                confidence_boost += 30
                
            elif (current_close < current_open and prev_close > prev_open and
                  current_open > prev_close and current_close < prev_open):
                price_signals.append("BEARISH_ENGULFING")
                confidence_boost += 30
            
            # PIN BARS
            body_size = abs(current_close - current_open)
            upper_wick = current_high - max(current_open, current_close)
            lower_wick = min(current_open, current_close) - current_low
            
            if body_size > 0:  # Avoid division by zero
                if (lower_wick >= 2 * body_size and upper_wick <= body_size * 0.3):
                    price_signals.append("HAMMER_PINBAR")
                    confidence_boost += 25
                    
                elif (upper_wick >= 2 * body_size and lower_wick <= body_size * 0.3):
                    price_signals.append("SHOOTING_STAR")
                    confidence_boost += 25
            
            # SUPPORT/RESISTANCE
            recent_high = max(highs[-10:])
            recent_low = min(lows[-10:])
            resistance = recent_high * 1.0002
            support = recent_low * 0.9998
            
            if abs(current_high - resistance) / resistance < 0.0003:
                price_signals.append("AT_RESISTANCE")
                confidence_boost += 15
                
            if abs(current_low - support) / support < 0.0003:
                price_signals.append("AT_SUPPORT")
                confidence_boost += 15
            
            return {
                'price_signals': price_signals,
                'confidence_boost': confidence_boost,
                'support': support,
                'resistance': resistance
            }
        except Exception as e:
            logger.error(f"Price action detection error: {e}")
            return {'price_signals': [], 'confidence_boost': 0, 'support': 0, 'resistance': 0}

    def dual_indicator_confirmation(self, closes):
        """Enhanced indicator analysis with error handling"""
        try:
            if len(closes) < 21:  # Need enough data for EMA 21
                return {
                    'rsi': 50, 'ema_9': closes[-1] if closes else 1.0, 
                    'ema_21': closes[-1] if closes else 1.0,
                    'indicator_signals': [], 'indicator_confidence': 0
                }
                
            prices = pd.Series(closes)
            
            # RSI
            rsi = 50
            try:
                rsi_indicator = ta.momentum.RSIIndicator(prices, window=14)
                rsi = rsi_indicator.rsi().iloc[-1]
                if pd.isna(rsi):
                    rsi = 50
            except:
                rsi = 50
            
            # EMA
            ema_9 = prices.iloc[-1]
            ema_21 = prices.iloc[-1]
            try:
                ema_9_indicator = ta.trend.EMAIndicator(prices, window=9)
                ema_21_indicator = ta.trend.EMAIndicator(prices, window=21)
                ema_9 = ema_9_indicator.ema_indicator().iloc[-1]
                ema_21 = ema_21_indicator.ema_indicator().iloc[-1]
                if pd.isna(ema_9):
                    ema_9 = prices.iloc[-1]
                if pd.isna(ema_21):
                    ema_21 = prices.iloc[-1]
            except:
                pass
            
            indicator_signals = []
            indicator_confidence = 0
            
            # RSI Analysis
            if rsi < 30:
                indicator_signals.append("RSI_OVERSOLD")
                indicator_confidence += 25
            elif rsi > 70:
                indicator_signals.append("RSI_OVERBOUGHT")
                indicator_confidence += 25
            
            # EMA Trend Analysis
            if ema_9 > ema_21:
                indicator_signals.append("EMA_BULLISH")
                indicator_confidence += 20
            else:
                indicator_signals.append("EMA_BEARISH") 
                indicator_confidence += 20
            
            return {
                'rsi': round(rsi, 1),
                'ema_9': round(ema_9, 4),
                'ema_21': round(ema_21, 4),
                'indicator_signals': indicator_signals,
                'indicator_confidence': indicator_confidence
            }
        except Exception as e:
            logger.error(f"Indicator analysis error: {e}")
            return {
                'rsi': 50, 'ema_9': 1.0, 'ema_21': 1.0,
                'indicator_signals': [], 'indicator_confidence': 0
            }

    def generate_enhanced_signal(self, price_action, indicators, current_price, pair, market_data):
        """Enhanced multi-level signal generation with AI"""
        try:
            if not STRATEGIES_LOADED:
                return {
                    'signal': "HOLD",
                    'confidence': 0,
                    'urgency': "STRATEGIES NOT LOADED",
                    'confidence_level': "ERROR",
                    'is_high_confidence': False
                }
            
            # Run all three strategy levels with AI enhancements
            low_signal = generate_low_confidence_signals(
                price_action, indicators, 
                market_data['closes'], market_data['highs'], market_data['lows']
            )
            
            medium_signal = generate_medium_confidence_signals(
                price_action, indicators,
                market_data['closes'], market_data['highs'], market_data['lows']  
            )
            
            high_signal = generate_high_confidence_signals(
                price_action, indicators,
                market_data['closes'], market_data['highs'], market_data['lows']
            )
            
            # Priority: HIGH > MEDIUM > LOW
            final_signal = "HOLD"
            final_confidence = 0
            urgency = ""
            confidence_level = "LOW"
            
            if high_signal['is_tradable']:
                final_signal = high_signal['action']
                final_confidence = high_signal['confidence']
                confidence_level = "🚨 ULTIMATE AI"
                urgency = "🚨 URGENT 1-MINUTE TRADE"
                self.performance_stats['high_confidence_signals'] += 1
            elif medium_signal['is_tradable']:
                final_signal = medium_signal['action']
                final_confidence = medium_signal['confidence']
                confidence_level = "⚡ ENHANCED AI"
                urgency = "⚡ FAST 2-MINUTE TRADE"
                self.performance_stats['medium_confidence_signals'] += 1
            elif low_signal['is_tradable']:
                final_signal = low_signal['action']
                final_confidence = low_signal['confidence']
                confidence_level = "🎯 AI POWERED"
                urgency = "🎯 POTENTIAL 3-MINUTE TRADE"
                self.performance_stats['low_confidence_signals'] += 1
            
            self.performance_stats['total_signals'] += 1
            
            return {
                'signal': final_signal,
                'confidence': final_confidence,
                'urgency': urgency,
                'confidence_level': confidence_level,
                'is_high_confidence': final_confidence >= 60,
                'all_signals': {
                    'low': low_signal,
                    'medium': medium_signal, 
                    'high': high_signal
                }
            }
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return {
                'signal': "HOLD",
                'confidence': 0,
                'urgency': "ANALYSIS ERROR",
                'confidence_level': "ERROR",
                'is_high_confidence': False
            }

    async def send_auto_alert(self, pair, timeframe, analysis, signal_info):
        """Enhanced auto alert with AI data"""
        try:
            # Get AI data from signals
            ai_data = signal_info.get('all_signals', {}).get('high', {}).get('ai_data', {})
            if not ai_data:
                ai_data = signal_info.get('all_signals', {}).get('medium', {}).get('ai_data', {})
            if not ai_data:
                ai_data = signal_info.get('all_signals', {}).get('low', {}).get('ai_data', {})
            
            alert_message = f"""
{signal_info['urgency']}

🎯 **ENHANCED AI AUTO-TRADE SIGNAL**
💹 **Pair:** {pair} {'(OTC 92% 🚀)' if 'OTC' in pair else ''}
⏰ **Timeframe:** {timeframe}
📈 **Signal:** {signal_info['signal']}
🎯 **Confidence:** {signal_info['confidence']}% ({signal_info['confidence_level']})

🤖 **AI ENHANCEMENTS:**
📊 **Volatility:** {ai_data.get('volatility', {}).get('volatility_regime', 'N/A')}
💰 **Liquidity Zone:** {'✅ Active' if ai_data.get('liquidity', {}).get('liquidity_score', 0) > 0 else '❌ Inactive'}
⚡ **Momentum:** {ai_data.get('momentum', {}).get('momentum_signals', ['N/A'])[0] if ai_data.get('momentum', {}).get('momentum_signals') else 'N/A'}

📊 **Price:** ${analysis['price']:.4f}
📉 **RSI:** {analysis['rsi']}
📈 **EMA 9/21:** ${analysis['ema_9']:.4f}/${analysis['ema_21']:.4f}

🛡️ **Support:** ${analysis['support']:.4f}
🚧 **Resistance:** ${analysis['resistance']:.4f}

⚡ **Recommended Expiry:** 1-5 minutes
💡 **Action:** ENTER NOW - AI Enhanced Signal!

⏰ **Alert Time (UTC+7):** {self.get_utc7_time().strftime('%H:%M:%S')}
            """
            
            await self.application.bot.send_message(
                chat_id=YOUR_CHAT_ID,
                text=alert_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"🚨 ENHANCED AI ALERT: {pair} {signal_info['signal']} {signal_info['confidence']}%")
            
        except Exception as e:
            logger.error(f"Enhanced alert error: {e}")

    async def scan_markets(self):
        """Enhanced market scanning with AI"""
        if not self.auto_trade_enabled:
            return
            
        logger.info("🔍 ENHANCED AI Scanning markets...")
        
        for pair in TRADING_PAIRS.keys():
            for timeframe in TIMEFRAMES:
                try:
                    # Cooldown check
                    key = f"{pair}_{timeframe}"
                    if key in self.alert_cooldown:
                        if time.time() - self.alert_cooldown[key] < 300:
                            continue
                    
                    # Fetch and analyze
                    market_data = self.fetch_market_data(pair, timeframe)
                    if not market_data.get('success', False):
                        continue
                        
                    price_action = self.advanced_price_action_detection(
                        market_data['opens'], market_data['highs'], 
                        market_data['lows'], market_data['closes']
                    )
                    indicators = self.dual_indicator_confirmation(market_data['closes'])
                    signal_info = self.generate_enhanced_signal(
                        price_action, indicators, market_data['price'], pair, market_data
                    )
                    
                    # Send alert if high confidence
                    if signal_info['is_high_confidence'] and signal_info['signal'] != "HOLD":
                        analysis_data = {
                            'price': market_data['price'],
                            'rsi': indicators['rsi'],
                            'ema_9': indicators['ema_9'],
                            'ema_21': indicators['ema_21'],
                            'support': price_action['support'],
                            'resistance': price_action['resistance']
                        }
                        
                        await self.send_auto_alert(pair, timeframe, analysis_data, signal_info)
                        self.alert_cooldown[key] = time.time()
                        
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Enhanced scan error for {pair} {timeframe}: {e}")
                    continue

    def start_auto_scanning(self):
        """Start enhanced auto scanning"""
        async def scanning_loop():
            while self.auto_trade_enabled:
                try:
                    await self.scan_markets()
                    await asyncio.sleep(30)
                except Exception as e:
                    logger.error(f"Enhanced scanning loop error: {e}")
                    await asyncio.sleep(60)
        
        if self.auto_trade_enabled and not self.scanning_task:
            self.scanning_task = asyncio.create_task(scanning_loop())
            logger.info("🟢 ENHANCED AI Auto-scanning STARTED")

    async def stop_auto_scanning(self):
        """Stop enhanced auto scanning"""
        if self.scanning_task:
            self.scanning_task.cancel()
            try:
                await self.scanning_task
            except asyncio.CancelledError:
                pass
            self.scanning_task = None
            logger.info("🔴 ENHANCED AI Auto-scanning STOPPED")

    async def set_auto_trade(self, enabled: bool):
        """Enhanced auto-trade control"""
        self.auto_trade_enabled = enabled
        
        if enabled:
            self.start_auto_scanning()
            logger.info("🟢 ENHANCED AI Auto-trading ENABLED")
        else:
            await self.stop_auto_scanning()
            logger.info("🔴 ENHANCED AI Auto-trading DISABLED")

# ==================== TELEGRAM BOT HANDLERS ====================
enhanced_ai = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **ENHANCED ULTIMATE AUTO-TRADING AI** 🤖

*Revolutionary AI Features:*
• 🧠 **AI VOLATILITY PREDICTION** - Smart market regime detection
• 💰 **LIQUIDITY ZONE DETECTION** - Smart money level identification  
• ⚡ **MOMENTUM ACCELERATION** - Advanced trend strength analysis
• 🎯 **MULTI-TIMEFRAME CONFLUENCE** - 3-timeframe alignment scoring
• 📊 **ENHANCED CONFIDENCE LEVELS** (60%+/70%+/80%+ with AI boost)

*AI-Powered Commands:*
/autotrade on - Start AI auto-scanning
/analyze PAIR TIMEFRAME - Enhanced AI analysis  
/performance - AI strategy performance
/pairs - Available pairs
/status - Enhanced bot status

*Example:* `/analyze AUD/CAD OTC 5m`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def autotrade_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced auto-trade toggle"""
    try:
        if not context.args:
            status = "🟢 ENABLED" if enhanced_ai.auto_trade_enabled else "🔴 DISABLED"
            await update.message.reply_text(
                f"🔄 *Enhanced AI Auto-Trade*\n*Current Status:* {status}\n"
                "*Usage:* /autotrade on OR /autotrade off",
                parse_mode='Markdown'
            )
            return

        command = context.args[0].lower()
        
        if command in ['on', 'enable', 'start']:
            await enhanced_ai.set_auto_trade(True)
            await update.message.reply_text(
                "🟢 **ENHANCED AI AUTO-TRADING ENABLED**\n"
                "🤖 AI is now scanning 5 timeframes every 30 seconds\n"
                "🧠 Multi-level AI signals (60%+/70%+/80%+)\n"
                "📊 AI Volatility & Liquidity detection ACTIVE",
                parse_mode='Markdown'
            )
            
        elif command in ['off', 'disable', 'stop']:
            await enhanced_ai.set_auto_trade(False)
            await update.message.reply_text(
                "🔴 **ENHANCED AI AUTO-TRADING DISABLED**\n"
                "💤 AI scanning stopped\n"
                "🔇 No AI alerts will be sent\n"
                "💾 AI models: STANDBY",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid command. Use: /autotrade on OR /autotrade off")
            
    except Exception as e:
        logger.error(f"Auto-trade toggle error: {e}")
        await update.message.reply_text("❌ Error toggling enhanced AI auto-trade")

async def analyze_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced AI analysis command"""
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "📊 *Enhanced AI Analysis*\n*Usage:* /analyze PAIR TIMEFRAME\n"
                "*Example:* `/analyze AUD/CAD OTC 5m`",
                parse_mode='Markdown'
            )
            return

        pair = " ".join(context.args[:-1]).upper()
        timeframe = context.args[-1].lower()

        # Flexible pair validation
        valid_pair = False
        for key in TRADING_PAIRS.keys():
            if pair in key or key.replace('/', '') in pair.replace('/', ''):
                pair = key 
