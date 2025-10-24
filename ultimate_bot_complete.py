import pandas as pd
import numpy as np
import time
import json
import logging
import asyncio
import sys
import os
from datetime import datetime, timedelta
import ta
# --- Make sure InputFile is imported ---
from telegram import Update, InputFile
# ----------------------------------------
from telegram.ext import Application, CommandHandler, ContextTypes

print("🚀 STARTING COMPLETE FIXED ULTIMATE TRADING BOT...")

# Add strategies folder to path
current_dir = os.path.dirname(os.path.abspath(__file__))
strategies_path = os.path.join(current_dir, 'strategies')
if os.path.exists(strategies_path):
    sys.path.insert(0, strategies_path)

# Import fixed modules
try:
    from market_data_api import pocket_api
    from candlestick_patterns import pattern_scanner
    from low_strategy import generate_low_confidence_signals
    from medium_strategy import generate_medium_confidence_signals
    from logs import log_manager
    MODULES_LOADED = True
    print("✅ ALL MODULES LOADED SUCCESSFULLY")
except ImportError as e:
    print(f"⚠️ Module import warning: {e}")
    MODULES_LOADED = False

# Bot configuration
BOT_TOKEN = "6506132532:AAGjfMXlSkefR5uldDwCRhxdk7YRES5385k"
YOUR_CHAT_ID = "-1002903475551"
UTC_PLUS_7 = timedelta(hours=7)

# REAL OTC PAIRS
TRADING_PAIRS = {
    "AUD/CAD OTC": True, "AUD/USD OTC": True,
    "CAD/JPY OTC": True, "CHF/JPY OTC": True,
    "EUR/CHF OTC": True, "GBP/AUD OTC": True,
    "NZD/JPY OTC": True, "USD/CHF OTC": True,
    "EUR/USD": False, "GBP/USD": False,
    "USD/JPY": False, "XAU/USD": False
}

TIMEFRAMES = ["1m", "5m", "15m", "1h"]

# Enhanced logging with no markdown issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateCompleteBot:
    def __init__(self, application):
        self.application = application
        self.auto_trade_enabled = False
        self.scanning_task = None
        self.alert_cooldown = {}
        self.stats = {
            'signals_generated': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'patterns_detected': 0
        }

    def get_utc7_time(self):
        """Get UTC+7 time for Pocket Option"""
        return datetime.now() + UTC_PLUS_7

    def fetch_real_market_data(self, pair, timeframe="5m"):
        """
        Fetch REAL market data with comprehensive analysis
        """
        try:
            market_data = pocket_api.fetch_real_candles(pair, timeframe, limit=100)
            if not market_data or not market_data.get('success'):
                logger.error(f"Failed to fetch data for {pair}")
                return None
            logger.info(f"✅ Data source: {market_data.get('data_source', 'UNKNOWN')} for {pair}")
            return market_data
        except Exception as e:
            logger.error(f"Market data error: {e}")
            return None

    def calculate_real_indicators(self, closes, highs, lows):
        """
        Calculate REAL RSI, EMA, and other indicators from live data
        """
        try:
            if len(closes) < 21: return None
            prices = pd.Series(closes)
            rsi = ta.momentum.RSIIndicator(prices, window=14).rsi().iloc[-1]
            if pd.isna(rsi): rsi = 50.0
            ema_9 = ta.trend.EMAIndicator(prices, window=9).ema_indicator().iloc[-1]
            ema_21 = ta.trend.EMAIndicator(prices, window=21).ema_indicator().iloc[-1]
            if pd.isna(ema_9): ema_9 = prices.iloc[-1]
            if pd.isna(ema_21): ema_21 = prices.iloc[-1]
            macd_indicator = ta.trend.MACD(prices)
            macd, macd_signal, macd_histogram = macd_indicator.macd().iloc[-1], macd_indicator.macd_signal().iloc[-1], macd_indicator.macd_diff().iloc[-1]
            bb_indicator = ta.volatility.BollingerBands(prices)
            bb_upper, bb_lower, bb_middle = bb_indicator.bollinger_hband().iloc[-1], bb_indicator.bollinger_lband().iloc[-1], bb_indicator.bollinger_mavg().iloc[-1]
            atr_indicator = ta.volatility.AverageTrueRange(pd.Series(highs), pd.Series(lows), prices)
            atr = atr_indicator.average_true_range().iloc[-1]
            return {
                'rsi': round(float(rsi), 2), 'ema_9': round(float(ema_9), 5), 'ema_21': round(float(ema_21), 5),
                'macd': round(float(macd), 5) if not pd.isna(macd) else 0, 'macd_signal': round(float(macd_signal), 5) if not pd.isna(macd_signal) else 0,
                'macd_histogram': round(float(macd_histogram), 5) if not pd.isna(macd_histogram) else 0, 'bb_upper': round(float(bb_upper), 5) if not pd.isna(bb_upper) else 0,
                'bb_lower': round(float(bb_lower), 5) if not pd.isna(bb_lower) else 0, 'bb_middle': round(float(bb_middle), 5) if not pd.isna(bb_middle) else 0,
                'atr': round(float(atr), 5) if not pd.isna(atr) else 0
            }
        except Exception as e: logger.error(f"Indicator calculation error: {e}"); return None

    def detect_support_resistance(self, highs, lows, closes):
        """ Advanced support/resistance detection """
        try:
            recent_highs, recent_lows = highs[-20:], lows[-20:]
            resistance_levels, support_levels = [], []
            for i in range(2, len(recent_highs)-2):
                if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i-2] and recent_highs[i] > recent_highs[i+1] and recent_highs[i] > recent_highs[i+2]: resistance_levels.append(recent_highs[i])
                if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i-2] and recent_lows[i] < recent_lows[i+1] and recent_lows[i] < recent_lows[i+2]: support_levels.append(recent_lows[i])
            resistance = resistance_levels[-1] if resistance_levels else max(highs[-20:])
            support = support_levels[-1] if support_levels else min(lows[-20:])
            current_price = closes[-1]
            return {'support': round(support, 5), 'resistance': round(resistance, 5), 'near_support': abs(current_price - support) / support < 0.003, 'near_resistance': abs(current_price - resistance) / resistance < 0.003}
        except Exception as e: logger.error(f"S/R detection error: {e}"); return {'support': 0, 'resistance': 0, 'near_support': False, 'near_resistance': False}

    def generate_complete_signal(self, pair, market_data, indicators, sr_levels, patterns):
        """ Generate comprehensive trading signal """
        try:
            price_action = {'price_signals': patterns['bullish_patterns'] + patterns['bearish_patterns'], 'confidence_boost': patterns['confidence_boost'], 'support': sr_levels['support'], 'resistance': sr_levels['resistance']}
            low_signal, medium_signal = generate_low_confidence_signals(price_action, indicators), generate_medium_confidence_signals(price_action, indicators)
            final_signal, final_confidence, strategy_used, all_reasons = "HOLD", 0, "NONE", []
            if medium_signal['is_tradable'] and medium_signal['confidence'] >= 60:
                final_signal, final_confidence, strategy_used, all_reasons = medium_signal['action'], medium_signal['confidence'], "MEDIUM", medium_signal['reasons']
            elif low_signal['is_tradable'] and low_signal['confidence'] >= 50:
                final_signal, final_confidence, strategy_used, all_reasons = low_signal['action'], low_signal['confidence'], "LOW", low_signal['reasons']
            if patterns['at_key_level']: final_confidence += 10; all_reasons.append("At Key Support/Resistance Level")
            if indicators['macd_histogram'] > 0 and final_signal == "CALL": final_confidence += 5; all_reasons.append("MACD Bullish Confirmation")
            elif indicators['macd_histogram'] < 0 and final_signal == "PUT": final_confidence += 5; all_reasons.append("MACD Bearish Confirmation")
            final_confidence = min(final_confidence, 95)
            atr = indicators.get('atr', 0)
            stop_loss = round(market_data['price'] - (2 * atr), 5) if final_signal == "CALL" else round(market_data['price'] + (2 * atr), 5)
            take_profit = round(market_data['price'] + (3 * atr), 5) if final_signal == "CALL" else round(market_data['price'] - (3 * atr), 5)
            self.stats['signals_generated'] += 1
            if final_confidence >= 70: self.stats['high_confidence'] += 1
            return {
                'signal': final_signal, 'confidence': final_confidence, 'strategy': strategy_used, 'reasons': all_reasons, 'patterns': patterns,
                'indicators': indicators, 'sr_levels': sr_levels, 'risk_management': {'stop_loss': stop_loss, 'take_profit': take_profit, 'risk_reward_ratio': '1:1.5'},
                'is_high_confidence': final_confidence >= 70, 'market_sentiment': pocket_api.get_market_sentiment(pair),
                'recommended_expiry': medium_signal.get('recommended_expiry', '2-5 minutes') if strategy_used == "MEDIUM" else low_signal.get('recommended_expiry', '1-3 minutes')
            }
        except Exception as e: logger.error(f"Signal generation error: {e}"); return None

    async def send_high_confidence_alert(self, pair, timeframe, signal_data, market_data):
        """ Send alert for high confidence signals """
        try:
            alert = f"""🚨 HIGH CONFIDENCE SIGNAL DETECTED\n\nPAIR: {pair} {'(OTC 92% PAYOUT)' if 'OTC' in pair else ''}\nTIMEFRAME: {timeframe}\nSIGNAL: {signal_data['signal']}\nCONFIDENCE: {signal_data['confidence']}%\nSTRATEGY: {signal_data['strategy']}\n\nPRICE DATA:\nCurrent Price: ${market_data['price']:.5f}\nSupport: ${signal_data['sr_levels']['support']:.5f}\nResistance: ${signal_data['sr_levels']['resistance']:.5f}\n\nINDICATORS:\nRSI: {signal_data['indicators']['rsi']}\nEMA 9/21: {signal_data['indicators']['ema_9']:.5f} / {signal_data['indicators']['ema_21']:.5f}\nMACD Histogram: {signal_data['indicators']['macd_histogram']:.5f}\n\nPATTERNS DETECTED: {signal_data['patterns']['total_patterns']}\nBullish: {', '.join(signal_data['patterns']['bullish_patterns'][:3]) if signal_data['patterns']['bullish_patterns'] else 'None'}\nBearish: {', '.join(signal_data['patterns']['bearish_patterns'][:3]) if signal_data['patterns']['bearish_patterns'] else 'None'}\n\nREASONS:\n{chr(10).join('- ' + r for r in signal_data['reasons'][:5])}\n\nRISK MANAGEMENT:\nStop Loss: ${signal_data['risk_management']['stop_loss']:.5f}\nTake Profit: ${signal_data['risk_management']['take_profit']:.5f}\nRisk/Reward: {signal_data['risk_management']['risk_reward_ratio']}\n\nMARKET SENTIMENT: {signal_data['market_sentiment']['sentiment']} ({signal_data['market_sentiment']['strength']}%) \n\nRECOMMENDED EXPIRY: {signal_data['recommended_expiry']}\n\nTIME (UTC+7): {self.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')}\n\nACTION: ENTER {signal_data['signal']} NOW!"""
            await self.application.bot.send_message(chat_id=YOUR_CHAT_ID, text=alert)
            logger.info(f"🚨 ALERT SENT: {pair} {signal_data['signal']} {signal_data['confidence']}%")
        except Exception as e: logger.error(f"Alert send error: {e}")

    async def scan_all_markets(self):
        """ Comprehensive market scanning """
        if not self.auto_trade_enabled: return
        logger.info("🔍 Scanning all markets...")
        for pair, is_otc in TRADING_PAIRS.items():
            for timeframe in TIMEFRAMES:
                try:
                    key = f"{pair}_{timeframe}"
                    if key in self.alert_cooldown and time.time() - self.alert_cooldown[key] < 300: continue
                    market_data = self.fetch_real_market_data(pair, timeframe)
                    if not market_data: continue
                    indicators = self.calculate_real_indicators(market_data['closes'], market_data['highs'], market_data['lows'])
                    if not indicators: continue
                    sr_levels = self.detect_support_resistance(market_data['highs'], market_data['lows'], market_data['closes'])
                    patterns = pattern_scanner.scan_all_patterns(market_data['opens'], market_data['highs'], market_data['lows'], market_data['closes'], sr_levels['support'], sr_levels['resistance'])
                    self.stats['patterns_detected'] += patterns['total_patterns']
                    signal_data = self.generate_complete_signal(pair, market_data, indicators, sr_levels, patterns)
                    if not signal_data: continue
                    if signal_data['is_high_confidence'] and signal_data['signal'] != "HOLD":
                        await self.send_high_confidence_alert(pair, timeframe, signal_data, market_data)
                        self.alert_cooldown[key] = time.time()
                        await asyncio.sleep(2)
                except Exception as e: logger.error(f"Scan error {pair} {timeframe}: {e}"); continue
                await asyncio.sleep(0.5)

    async def start_auto_scanning(self):
        """ Start continuous market scanning """
        async def scanning_loop():
            while self.auto_trade_enabled:
                try: await self.scan_all_markets(); await asyncio.sleep(30)
                except Exception as e: logger.error(f"Scanning loop error: {e}"); await asyncio.sleep(60)
        if not self.scanning_task: self.scanning_task = asyncio.create_task(scanning_loop()); logger.info("🟢 Auto-scanning STARTED")

    async def stop_auto_scanning(self):
        """ Stop continuous scanning """
        if self.scanning_task:
            self.scanning_task.cancel()
            try: await self.scanning_task
            except asyncio.CancelledError: pass
            self.scanning_task = None; logger.info("🔴 Auto-scanning STOPPED")

# ==================== TELEGRAM COMMAND HANDLERS ====================

bot_instance = None # Define global bot_instance

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Start command """
    welcome = """🤖 ULTIMATE TRADING BOT - COMPLETE VERSION\n\nFEATURES:\n✅ REAL Pocket Option API Integration\n✅ 30+ Candlestick Pattern Detection\n✅ Multi-Timeframe Analysis (1m, 5m, 15m, 1h)\n✅ Real RSI, EMA, MACD, Bollinger Bands\n✅ Advanced Support/Resistance Detection\n✅ Risk Management (Stop Loss, Take Profit)\n✅ Market Sentiment Analysis\n✅ Auto UP/DOWN Signals (70%+ confidence)\n✅ FIXED Logs Module (No Parsing Errors)\n\nCOMMANDS:\n/autotrade on - Start auto-scanning\n/autotrade off - Stop auto-scanning\n/analyze PAIR TIMEFRAME - Manual analysis\n/pairs - Show available pairs\n/status - Bot status and statistics\n/logs tail FILENAME - View logs\n/logs stats FILENAME - Log statistics\n/logs health - System health report\n/get_screenshot - (TEMP) Get login error screenshot\n\nEXAMPLE: /analyze AUD/CAD OTC 5m\n\nOTC PAIRS (92% PAYOUT):\nAUD/CAD, AUD/USD, CAD/JPY, CHF/JPY\nEUR/CHF, GBP/AUD, NZD/JPY, USD/CHF"""
    await update.message.reply_text(welcome)

async def autotrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Toggle auto-trading """
    try:
        if not context.args: status = "ENABLED" if bot_instance.auto_trade_enabled else "DISABLED"; await update.message.reply_text(f"Auto-trade status: {status}\nUsage: /autotrade on OR /autotrade off"); return
        command = context.args[0].lower()
        if command in ['on', 'start', 'enable']:
            if not bot_instance.auto_trade_enabled: bot_instance.auto_trade_enabled = True; await bot_instance.start_auto_scanning(); await update.message.reply_text("🟢 AUTO-TRADING ENABLED\n✅ Scanning...\n✅ Real-time alerts...\n⏰ Scan interval: 30 seconds")
            else: await update.message.reply_text("Auto-trading is already enabled.")
        elif command in ['off', 'stop', 'disable']:
            if bot_instance.auto_trade_enabled: bot_instance.auto_trade_enabled = False; await bot_instance.stop_auto_scanning(); await update.message.reply_text("🔴 AUTO-TRADING DISABLED\n❌ Market scanning stopped")
            else: await update.message.reply_text("Auto-trading is already disabled.")
        else: await update.message.reply_text("Invalid command. Use: on or off")
    except Exception as e: logger.error(f"Autotrade command error: {e}"); await update.message.reply_text(f"Error: {str(e)}")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Manual pair analysis """
    try:
        if len(context.args) < 2: await update.message.reply_text("Usage: /analyze PAIR TIMEFRAME\nEx: /analyze AUD/CAD OTC 5m"); return
        pair, timeframe = " ".join(context.args[:-1]).upper(), context.args[-1].lower()
        if pair not in TRADING_PAIRS: await update.message.reply_text(f"Invalid pair. Use /pairs"); return
        if timeframe not in TIMEFRAMES: await update.message.reply_text(f"Invalid timeframe. Use: {', '.join(TIMEFRAMES)}"); return
        analyzing_msg = await update.message.reply_text(f"🔍 Analyzing {pair} {timeframe}...")
        market_data = bot_instance.fetch_real_market_data(pair, timeframe)
        if not market_data: await analyzing_msg.edit_text("Error fetching market data."); return
        indicators = bot_instance.calculate_real_indicators(market_data['closes'], market_data['highs'], market_data['lows'])
        if not indicators: await analyzing_msg.edit_text("Error calculating indicators."); return # Added check
        sr_levels = bot_instance.detect_support_resistance(market_data['highs'], market_data['lows'], market_data['closes'])
        patterns = pattern_scanner.scan_all_patterns(market_data['opens'], market_data['highs'], market_data['lows'], market_data['closes'], sr_levels['support'], sr_levels['resistance'])
        signal_data = bot_instance.generate_complete_signal(pair, market_data, indicators, sr_levels, patterns)
        if not signal_data: await analyzing_msg.edit_text("Error generating signal."); return # Added check
        result = f"""ANALYSIS: {pair} {timeframe}\nData Source: {market_data.get('data_source', 'API')}\n\nPRICE: ${market_data['price']:.5f}\nSIGNAL: {signal_data['signal']}\nCONFIDENCE: {signal_data['confidence']}%\nSTRATEGY: {signal_data['strategy']}\n\nINDICATORS:\nRSI: {indicators.get('rsi', 'N/A')}\nEMA 9/21: {indicators.get('ema_9', 0):.5f} / {indicators.get('ema_21', 0):.5f}\nMACD: {indicators.get('macd_histogram', 0):.5f}\n\nSUPPORT/RESISTANCE:\nSupport: ${sr_levels.get('support', 0):.5f}\nResistance: ${sr_levels.get('resistance', 0):.5f}\n\nPATTERNS: {patterns.get('total_patterns', 0)}\nBullish: {len(patterns.get('bullish_patterns',[]))}\nBearish: {len(patterns.get('bearish_patterns',[]))}\n\nTOP REASONS:\n{chr(10).join('- ' + r for r in signal_data.get('reasons',[])[:3]) if signal_data.get('reasons') else 'N/A'}\n\nRISK:\nStop Loss: ${signal_data.get('risk_management',{}).get('stop_loss', 0):.5f}\nTake Profit: ${signal_data.get('risk_management',{}).get('take_profit', 0):.5f}\n\nSENTIMENT: {signal_data.get('market_sentiment',{}).get('sentiment', 'N/A')}\n\nRECOMMENDED: {signal_data.get('recommended_expiry', 'N/A')}\n\nTime: {bot_instance.get_utc7_time().strftime('%H:%M:%S')}"""
        await analyzing_msg.edit_text(result)
    except Exception as e: logger.error(f"Analyze error: {e}"); await update.message.reply_text(f"Analysis error: {str(e)}")

async def pairs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Show available pairs """
    otc_pairs = [p for p in TRADING_PAIRS if 'OTC' in p]; regular_pairs = [p for p in TRADING_PAIRS if 'OTC' not in p]
    message = f"""AVAILABLE PAIRS\n\nOTC (92% PAYOUT):\n{chr(10).join('- ' + p for p in otc_pairs)}\n\nREGULAR:\n{chr(10).join('- ' + p for p in regular_pairs)}\n\nTIMEFRAMES: {', '.join(TIMEFRAMES)}\n\nAuto-trade: {'ON' if bot_instance.auto_trade_enabled else 'OFF'}"""
    await update.message.reply_text(message)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Show bot status """
    status = f"""BOT STATUS\n\nAuto-Trade: {'ON' if bot_instance.auto_trade_enabled else 'OFF'}\nScan Interval: 30s\nModules: {'OK' if MODULES_LOADED else 'ERROR'}\n\nSTATS:\nSignals: {bot_instance.stats['signals_generated']}\nHigh Conf: {bot_instance.stats['high_confidence']}\nMedium Conf: {bot_instance.stats['medium_confidence']}\nPatterns: {bot_instance.stats['patterns_detected']}\n\nMONITORING:\nPairs: {len(TRADING_PAIRS)}\nTimeframes: {len(TIMEFRAMES)}\nTotal: {len(TRADING_PAIRS) * len(TIMEFRAMES)}\n\nTime (UTC+7): {bot_instance.get_utc7_time().strftime('%Y-%m-%d %H:%M:%S')}"""
    await update.message.reply_text(status)

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handle log commands """
    try:
        if not context.args:
            files = log_manager.get_log_files(); message = "LOG FILES:\n\n" + '\n'.join(f"{f['path']}: {f['size_mb']} MB" for f in files) if files else "No log files found."
            message += "\n\nCommands:\n/logs tail FILE\n/logs stats FILE\n/logs health"; await update.message.reply_text(message); return
        command = context.args[0].lower()
        if command == "tail":
            if len(context.args) < 2: await update.message.reply_text("Usage: /logs tail FILENAME"); return
            filename, lines = context.args[1], int(context.args[2]) if len(context.args) > 2 else 30
            content = log_manager.read_log_tail(filename, lines); content = content[-4000:] if len(content) > 4000 else content
            await update.message.reply_text(f"Last {lines} lines of {filename}:\n\n{content}")
        elif command == "stats":
            if len(context.args) < 2: await update.message.reply_text("Usage: /logs stats FILENAME"); return
            filename = context.args[1]; stats = log_manager.get_log_stats(filename); await update.message.reply_text(stats)
        elif command == "health": health = log_manager.get_module_health_report(); await update.message.reply_text(health)
        else: await update.message.reply_text("Unknown command. Use: tail, stats, or health")
    except Exception as e: await update.message.reply_text(f"Logs error: {str(e)}")


# ==================== NEW SCREENSHOT COMMAND ====================
async def get_screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """A temporary command to fetch the login_error.png file from the VPS."""
    # Define the expected path - Adjust if the 'find' command showed a different path
    # Assuming the clean redeploy puts it in the main bot directory now
    screenshot_dir = os.path.dirname(os.path.abspath(__file__)) # Get current script directory
    file_path = os.path.join(screenshot_dir, 'login_error.png')

    # --- Use the hardcoded path from 'find' if the above is wrong ---
    # file_path = '/home/admin01/BinaryPredictorAI/BinaryPredictorAI/BinaryPredictorAI/login_error.png'
    # ---------------------------------------------------------------

    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text=f"Attempting to find screenshot at: {file_path}")

    if os.path.exists(file_path):
        try:
            # Send the file as a document
            await context.bot.send_document(
                chat_id=chat_id,
                document=open(file_path, 'rb'), # Open file in binary read mode
                filename='login_error.png',
                caption='Here is the login error screenshot from the VPS.'
            )
            logger.info(f"Successfully sent {file_path} to user {chat_id}.")
        except Exception as e:
            error_message = f"Found the file, but failed to send it via Telegram. Error: {e}"
            logger.error(error_message)
            await context.bot.send_message(chat_id=chat_id, text=error_message)
    else:
        error_message = f"Screenshot file not found at {file_path}. Please run `python3 get_token.py` on the VPS first to generate it, then try this command again."
        logger.warning(error_message + f" (Chat ID: {chat_id})")
        await context.bot.send_message(chat_id=chat_id, text=error_message)
# =============================================================


def main():
    """ Start the complete fixed bot """
    try:
        print("🚀 STARTING COMPLETE ULTIMATE TRADING BOT...")
        application = Application.builder().token(BOT_TOKEN).build()
        global bot_instance
        bot_instance = UltimateCompleteBot(application)

        # Register all commands
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("autotrade", autotrade_command))
        application.add_handler(CommandHandler("analyze", analyze_command))
        application.add_handler(CommandHandler("pairs", pairs_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("logs", logs_command))
        # --- ADD THE NEW COMMAND HANDLER ---
        application.add_handler(CommandHandler("get_screenshot", get_screenshot_command))
        # -----------------------------------

        print("✅ ALL FEATURES LOADED")
        print("✅ Real API Integration: ACTIVE")
        print("✅ 30+ Pattern Detection: ACTIVE")
        print("✅ Multi-Timeframe Analysis: ACTIVE")
        print("✅ Risk Management: ACTIVE")
        print("✅ Logs Module: FIXED")
        print("\n🎯 Bot is ready!")
        application.run_polling()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()
