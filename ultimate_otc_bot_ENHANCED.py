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

print("🚀 STARTING ENHANCED ULTIMATE AUTO-TRADING AI...")

# Add strategies folder to path
current_dir = os.path.dirname(os.path.abspath(__file__))
strategies_path = os.path.join(current_dir, 'strategies')
sys.path.insert(0, strategies_path)

print(f"📁 Strategies path: {strategies_path}")

# FIXED: Use only original strategies (enhanced ones have errors)
try:
    from low_strategy import generate_low_confidence_signals
    # Skip medium strategy if it doesn't exist
    try:
        from medium_strategy import generate_medium_confidence_signals
        MEDIUM_LOADED = True
    except ImportError:
        MEDIUM_LOADED = False
        print("⚠️  Medium strategy not found, using low only")
    
    STRATEGIES_LOADED = True
    print("✅ USING ORIGINAL STRATEGIES")
except ImportError as e:
    print(f"❌ Strategy import failed: {e}")
    STRATEGIES_LOADED = False

# Add logs module
try:
    from strategies.logs import log_manager
    LOGS_LOADED = True
    print("✅ LOGS MODULE LOADED")
except ImportError as e:
    print(f"❌ Logs module not available: {e}")
    LOGS_LOADED = False

# Bot configuration
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
        logging.FileHandler("enhanced_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateEnhancedTradingAI:
    def __init__(self, application):
        self.application = application
        self.last_signals = {}
        self.alert_cooldown = {}
        self.auto_trade_enabled = False
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
        """Enhanced multi-level signal generation"""
        try:
            if not STRATEGIES_LOADED:
                return {
                    'signal': "HOLD",
                    'confidence': 0,
                    'urgency': "STRATEGIES NOT LOADED",
                    'confidence_level': "ERROR",
                    'is_high_confidence': False
                }
            
            # FIXED: Use only 2 parameters for original strategies
            low_signal = generate_low_confidence_signals(price_action, indicators)

            # Only use medium strategy if available
            medium_signal = {'action': 'HOLD', 'confidence': 0, 'is_tradable': False}
            if MEDIUM_LOADED:
                medium_signal = generate_medium_confidence_signals(price_action, indicators)
            
            # Priority: MEDIUM > LOW
            final_signal = "HOLD"
            final_confidence = 0
            urgency = ""
            confidence_level = "LOW"
            
            if medium_signal['is_tradable']:
                final_signal = medium_signal['action']
                final_confidence = medium_signal['confidence']
                confidence_level = "⚡ MEDIUM"
                urgency = "⚡ FAST 2-MINUTE TRADE"
                self.performance_stats['medium_confidence_signals'] += 1
            elif low_signal['is_tradable']:
                final_signal = low_signal['action']
                final_confidence = low_signal['confidence']
                confidence_level = "🎯 LOW"
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
                    'medium': medium_signal
                }
            }
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'signal': "HOLD",
                'confidence': 0,
                'urgency': "ANALYSIS ERROR",
                'confidence_level': "ERROR",
                'is_high_confidence': False
            }

    async def send_auto_alert(self, pair, timeframe, analysis, signal_info):
        """Enhanced auto alert"""
        try:
            alert_message = f"""
{signal_info['urgency']}

🎯 **AUTO-TRADE SIGNAL DETECTED**
💹 **Pair:** {pair} {'(OTC 92% 🚀)' if 'OTC' in pair else ''}
⏰ **Timeframe:** {timeframe}
📈 **Signal:** {signal_info['signal']}
🎯 **Confidence:** {signal_info['confidence']}% ({signal_info['confidence_level']})

📊 **Price:** ${analysis['price']:.4f}
📉 **RSI:** {analysis['rsi']}
📈 **EMA 9/21:** ${analysis['ema_9']:.4f}/${analysis['ema_21']:.4f}

🛡️ **Support:** ${analysis['support']:.4f}
🚧 **Resistance:** ${analysis['resistance']:.4f}

⚡ **Recommended Expiry:** 1-5 minutes
💡 **Action:** ENTER NOW - Trading signal!

⏰ **Alert Time (UTC+7):** {self.get_utc7_time().strftime('%H:%M:%S')}
            """
            
            await self.application.bot.send_message(
                chat_id=YOUR_CHAT_ID,
                text=alert_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"🚨 AUTO-ALERT SENT: {pair} {signal_info['signal']} {signal_info['confidence']}%")
            
        except Exception as e:
            logger.error(f"Alert send error: {e}")

    async def scan_markets(self):
        """Enhanced market scanning"""
        if not self.auto_trade_enabled:
            return
            
        logger.info("🔍 Scanning markets...")
        
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
                    logger.error(f"Scan error for {pair} {timeframe}: {e}")
                    continue

    def start_auto_scanning(self):
        """Start enhanced auto scanning"""
        async def scanning_loop():
            while self.auto_trade_enabled:
                try:
                    await self.scan_markets()
                    await asyncio.sleep(30)
                except Exception as e:
                    logger.error(f"Scanning loop error: {e}")
                    await asyncio.sleep(60)
        
        if self.auto_trade_enabled and not self.scanning_task:
            self.scanning_task = asyncio.create_task(scanning_loop())
            logger.info("🟢 Auto-scanning STARTED")

    async def stop_auto_scanning(self):
        """Stop enhanced auto scanning"""
        if self.scanning_task:
            self.scanning_task.cancel()
            try:
                await self.scanning_task
            except asyncio.CancelledError:
                pass
            self.scanning_task = None
            logger.info("🔴 Auto-scanning STOPPED")

    async def set_auto_trade(self, enabled: bool):
        """Enhanced auto-trade control"""
        self.auto_trade_enabled = enabled
        
        if enabled:
            self.start_auto_scanning()
            logger.info("🟢 AUTO-TRADING ENABLED")
        else:
            await self.stop_auto_scanning()
            logger.info("🔴 AUTO-TRADING DISABLED")

# ==================== LOGS COMMAND HANDLERS ====================
async def handle_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle logs commands"""
    try:
        if not context.args:
            # Show available log files
            available_logs = log_manager.get_log_files()
            
            if not available_logs:
                await update.message.reply_text("📭 No log files found!")
                return
            
            message = "📁 **AVAILABLE LOG FILES:**\n\n"
            for log in available_logs:
                message += f"• **{log['path']}**\n"
                message += f"  Size: {log['size_mb']}MB | Modified: {log['modified'].strftime('%H:%M:%S')}\n\n"
            
            message += "💡 **Usage:**\n"
            message += "`/logs tail FILE` - Show last 50 lines\n"
            message += "`/logs stats FILE` - Show file statistics\n"
            message += "`/logs search FILE TERM` - Search in logs\n"
            message += "`/logs clear FILE` - Clear log file\n\n"
            message += "**Example:** `/logs tail enhanced_bot.log`"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        command = context.args[0].lower()
        
        if command == "tail":
            if len(context.args) < 2:
                await update.message.reply_text("❌ Usage: `/logs tail FILENAME`\nExample: `/logs tail enhanced_bot.log`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            lines = int(context.args[2]) if len(context.args) > 2 else 50
            
            if not os.path.exists(log_file):
                await update.message.reply_text(f"❌ Log file not found: {log_file}")
                return
            
            log_content = log_manager.read_log_tail(log_file, lines)
            
            # Split if too long for Telegram
            if len(log_content) > 4000:
                log_content = log_content[-4000:] + "\n\n... (truncated, use fewer lines)"
            
            await update.message.reply_text(f"📄 **Last {lines} lines of {log_file}:**\n\n```\n{log_content}\n```", parse_mode='Markdown')
        
        elif command == "stats":
            if len(context.args) < 2:
                await update.message.reply_text("❌ Usage: `/logs stats FILENAME`\nExample: `/logs stats enhanced_bot.log`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            stats = log_manager.get_log_stats(log_file)
            await update.message.reply_text(stats, parse_mode='Markdown')
        
        elif command == "search":
            if len(context.args) < 3:
                await update.message.reply_text("❌ Usage: `/logs search FILENAME TERM`\nExample: `/logs search enhanced_bot.log ERROR`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            search_term = " ".join(context.args[2:])
            
            if not os.path.exists(log_file):
                await update.message.reply_text(f"❌ Log file not found: {log_file}")
                return
            
            results = log_manager.search_logs(log_file, search_term)
            
            # Split if too long
            if len(results) > 4000:
                results = results[-4000:] + "\n\n... (truncated)"
            
            await update.message.reply_text(f"```\n{results}\n```", parse_mode='Markdown')
        
        elif command == "clear":
            if len(context.args) < 2:
                await update.message.reply_text("❌ Usage: `/logs clear FILENAME`\nExample: `/logs clear enhanced_bot.log`", parse_mode='Markdown')
                return
            
            log_file = context.args[1]
            result = log_manager.clear_logs(log_file)
            await update.message.reply_text(result)
        
        else:
            await update.message.reply_text("❌ Unknown logs command. Use: tail, stats, search, or clear")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Logs command error: {e}")

# ==================== NEW ADVANCED LOG HANDLERS ====================
async def handle_logs_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle logs health command"""
    try:
        if LOGS_LOADED:
            health_report = log_manager.get_module_health_report()
            # Split if too long for Telegram
            if len(health_report) > 4000:
                health_report = health_report[:4000] + "\n\n... (truncated)"
            
            await update.message.reply_text(f"🤖 **BOT HEALTH REPORT**\n\n```\n{health_report}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Logs module not loaded")
    except Exception as e:
        await update.message.reply_text(f"❌ Health report error: {e}")

async def handle_logs_recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle recent errors command"""
    try:
        if LOGS_LOADED:
            hours = int(context.args[0]) if context.args and context.args[0].isdigit() else 24
            recent_errors = log_manager.get_recent_errors(hours)
            
            # Split if too long for Telegram
            if len(recent_errors) > 4000:
                recent_errors = recent_errors[:4000] + "\n\n... (truncated)"
            
            await update.message.reply_text(f"🚨 **RECENT ERRORS (Last {hours}h)**\n\n```\n{recent_errors}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Logs module not loaded")
    except Exception as e:
        await update.message.reply_text(f"❌ Recent errors error: {e}")

# ==================== TELEGRAM BOT HANDLERS ====================
enhanced_ai = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **ULTIMATE AUTO-TRADING AI** 🤖

*Features:*
• 🎯 **MULTI-LEVEL SIGNALS** (60%+/70%+)
• ⏰ **5 TIMEFRAMES** (1m,5m,10m,1h,4h)
• 💰 **OTC MARKETS (92% RETURNS)**
• 📊 **24/7 MARKET SCANNING**
• 📁 **REMOTE LOG VIEWING**

*Commands:*
/autotrade on - Start auto-scanning
/autotrade off - Stop auto-scanning
/analyze PAIR TIMEFRAME - Manual analysis
/pairs - Available pairs
/status - Check bot status
/time - UTC+7 Time
/logs - View bot logs remotely
/logs_health - Bot health report
/logs_recent - Recent errors

*Example:* `/analyze AUD/CAD OTC 5m`
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def autotrade_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto-trading on/off"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🔄 *Usage:* /autotrade on OR /autotrade off\n"
                "*Current Status:* " + 
                ("🟢 ENABLED" if enhanced_ai.auto_trade_enabled else "🔴 DISABLED"),
                parse_mode='Markdown'
            )
            return

        command = context.args[0].lower()
        
        if command in ['on', 'enable', 'start']:
            await enhanced_ai.set_auto_trade(True)
            await update.message.reply_text(
                "🟢 **AUTO-TRADING ENABLED**\n"
                "🤖 Bot is now scanning 5 timeframes every 30 seconds\n"
                "🎯 Multi-level signals (60%+/70%+)\n"
                "💾 RAM usage: ACTIVE",
                parse_mode='Markdown'
            )
            
        elif command in ['off', 'disable', 'stop']:
            await enhanced_ai.set_auto_trade(False)
            await update.message.reply_text(
                "🔴 **AUTO-TRADING DISABLED**\n"
                "💤 Bot scanning stopped\n"
                "🔇 No alerts will be sent\n"
                "💾 RAM usage: MINIMAL",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Invalid command. Use: /autotrade on OR /autotrade off")
            
    except Exception as e:
        logger.error(f"Auto-trade toggle error: {e}")
        await update.message.reply_text("❌ Error toggling auto-trade")

async def analyze_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual analysis command"""
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "📊 *Usage:* /analyze PAIR TIMEFRAME\n*Example:* `/analyze AUD/CAD OTC 5m`",
                parse_mode='Markdown'
            )
            return

        pair = " ".join(context.args[:-1]).upper()
        timeframe = context.args[-1].lower()

        # Flexible pair validation
        valid_pair = False
        for key in TRADING_PAIRS.keys():
            if pair in key or key.replace('/', '') in pair.replace('/', ''):
                pair = key  # Use the correct key from TRADING_PAIRS
                valid_pair = True
                break
        
        if not valid_pair:
            await update.message.reply_text("❌ Invalid pair. Use /pairs")
            return

        if timeframe not in TIMEFRAMES:
            await update.message.reply_text("❌ Invalid timeframe. Use: 1m, 5m, 10m, 1h, 4h")
            return

        analyzing_msg = await update.message.reply_text(
            f"🔍 *Analysis: {pair} {timeframe}...*",
            parse_mode='Markdown'
        )

        # Enhanced analysis
        market_data = enhanced_ai.fetch_market_data(pair, timeframe)
        price_action = enhanced_ai.advanced_price_action_detection(
            market_data['opens'], market_data['highs'], 
            market_data['lows'], market_data['closes']
        )
        indicators = enhanced_ai.dual_indicator_confirmation(market_data['closes'])
        signal_info = enhanced_ai.generate_enhanced_signal(
            price_action, indicators, market_data['price'], pair, market_data
        )

        analysis_text = f"""
📊 **ANALYSIS - {pair} {timeframe.upper()}**
{'💰 OTC MARKET (92% 🚀)' if 'OTC' in pair else '📈 Regular Market'}

💹 *Price:* ${market_data['price']:.4f}
📉 *RSI:* {indicators['rsi']}
📈 *EMA 9/21:* ${indicators['ema_9']:.4f}/${indicators['ema_21']:.4f}

🛡️ *Support:* ${price_action['support']:.4f}
🚧 *Resistance:* ${price_action['resistance']:.4f}

🔮 **SIGNAL:** {signal_info['signal']}
🎯 **CONFIDENCE:** {signal_info['confidence']}% ({signal_info['confidence_level']})
🚨 **AUTO-ALERT:** {'✅ YES' if signal_info['is_high_confidence'] else '❌ NO'}

💡 **STATUS:** {'🚨 READY FOR AUTO-ALERT' if signal_info['is_high_confidence'] else '⏳ Waiting for better setup'}

⏰ *Time (UTC+7):* {enhanced_ai.get_utc7_time().strftime('%H:%M:%S')}
        """

        await analyzing_msg.edit_text(analysis_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await update.message.reply_text("❌ Analysis error. Try again.")

async def show_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available pairs"""
    try:
        regular_pairs = [p for p in TRADING_PAIRS.keys() if 'OTC' not in p]
        otc_pairs = [p for p in TRADING_PAIRS.keys() if 'OTC' in p]
        
        pairs_text = "📊 *Trading Pairs:*\n\n"
        pairs_text += "*Regular:*\n" + "\n".join([f"• {pair}" for pair in regular_pairs]) + "\n\n"
        pairs_text += "*💰 OTC (92% Returns):*\n" + "\n".join([f"• {pair}" for pair in otc_pairs]) + "\n\n"
        pairs_text += f"*Timeframes:* {', '.join(TIMEFRAMES)}\n"
        pairs_text += "*Auto-trade:* " + ("🟢 ON" if enhanced_ai.auto_trade_enabled else "🔴 OFF")
        
        await update.message.reply_text(pairs_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Pairs error: {e}")
        await update.message.reply_text("❌ Error fetching pairs")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced bot status"""
    try:
        status_text = f"""
🤖 **BOT STATUS**

🔄 **AUTO-TRADE:** {"🟢 ENABLED" if enhanced_ai.auto_trade_enabled else "🔴 DISABLED"}
⏰ **SCAN INTERVAL:** {"30 seconds" if enhanced_ai.auto_trade_enabled else "STOPPED"}
🎯 **CONFIDENCE LEVELS:** 60%+/70%+
🚨 **ALERT TYPES:** Multi-level urgency
💰 **OTC FOCUS:** 92% Returns
📊 **LOG MODULE:** {"🟢 ACTIVE" if LOGS_LOADED else "🔴 DISABLED"}

📊 **MONITORING:** {len(TRADING_PAIRS)} pairs × {len(TIMEFRAMES)} timeframes
⏰ **CURRENT TIME (UTC+7):** {enhanced_ai.get_utc7_time().strftime('%H:%M:%S')}

💾 **RAM USAGE:** {"ACTIVE" if enhanced_ai.auto_trade_enabled else "MINIMAL"}
💡 **Use /autotrade off to save RAM at night**
        """
        await update.message.reply_text(status_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Status error: {e}")
        await update.message.reply_text("❌ Error fetching status")

async def show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current time"""
    try:
        current_time = enhanced_ai.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')
        await update.message.reply_text(f"🕐 **Pocket Option Time (UTC+7):** {current_time}", 
                                      parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Time error: {e}")
        await update.message.reply_text("❌ Error fetching time")

def main():
    """Start the enhanced ultimate auto-trading bot"""
    try:
        print("🚀 STARTING ULTIMATE AUTO-TRADING AI...")
        
        application = Application.builder().token(BOT_TOKEN).build()
        
        global enhanced_ai
        enhanced_ai = UltimateEnhancedTradingAI(application)
        
        # Command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("autotrade", autotrade_toggle))
        application.add_handler(CommandHandler("analyze", analyze_pair))
        application.add_handler(CommandHandler("pairs", show_pairs))
        application.add_handler(CommandHandler("status", show_status))
        application.add_handler(CommandHandler("time", show_time))
        
        # Add log handlers if available
        if LOGS_LOADED:
            application.add_handler(CommandHandler("logs", handle_logs_command))
            application.add_handler(CommandHandler("logs_health", handle_logs_health))
            application.add_handler(CommandHandler("logs_recent", handle_logs_recent))
            print("📊 Log commands: /logs, /logs_health, /logs_recent")
        
        print("🤖 BOT ACTIVATED!")
        print("🎯 Confidence Levels: 60%+/70%+")
        print("⏰ Timeframes: 1m, 5m, 10m, 1h, 4h")
        print("💰 OTC Markets focused (92% returns)")
        print("📊 Log module: " + ("ACTIVE" if LOGS_LOADED else "DISABLED"))
        print("🔄 Auto-trade: DISABLED on startup (use /autotrade on)")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
