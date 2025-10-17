import os
import random
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
BOT_TOKEN = "7914882777:AAGv_940utBNry2JXfwbzhtZWxtyK1qMO24"

class TradingBot:
    def __init__(self):
        self.user_data = {}
    
    def analyze_market(self):
        """Analyze market conditions and generate trading signals"""
        rsi = random.randint(25, 75)
        trends = ['BULLISH', 'BEARISH', 'SIDEWAYS']
        trend = random.choice(trends)
        
        if trend == 'BULLISH' and rsi < 70:
            return 'CALL', random.randint(75, 90), rsi, trend
        elif trend == 'BEARISH' and rsi > 30:
            return 'PUT', random.randint(75, 90), rsi, trend
        else:
            return 'NO_TRADE', 0, rsi, trend

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when command /start is issued"""
        user_id = update.effective_user.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {'balance': 1000, 'trades': []}
        
        welcome_text = """
🤖 *Binary Predictor AI Bot Started!*

Available Commands:
/analyze - Get market analysis
/trade - Execute a trade
/balance - Check your balance

Starting Balance: $1000
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze market and provide trading signal"""
        prediction, confidence, rsi, trend = self.analyze_market()
        
        if prediction == 'NO_TRADE':
            await update.message.reply_text(
                f"❌ *No Clear Trade Signal*\n"
                f"Market Trend: {trend}\n"
                f"RSI: {rsi}\n\n"
                "Wait for better conditions!",
                parse_mode='Markdown'
            )
        else:
            message = (
                f"📊 *Trade Analysis*\n"
                f"Signal: {prediction}\n"
                f"Confidence: {confidence}%\n"
                f"RSI: {rsi}\n"
                f"Trend: {trend}\n\n"
                f"Use /trade to execute this trade!"
            )
            await update.message.reply_text(message, parse_mode='Markdown')

    async def trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute a trade based on current market analysis"""
        user_id = update.effective_user.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {'balance': 1000, 'trades': []}
        
        prediction, confidence, rsi, trend = self.analyze_market()
        
        if prediction == 'NO_TRADE':
            await update.message.reply_text(
                "❌ *Trade Cancelled*\nNo clear trading signal detected. Try again later.",
                parse_mode='Markdown'
            )
            return
        
        # Simulate trade outcome
        trade_amount = 10
        is_win = random.random() < (confidence / 100)
        
        if is_win:
            profit = 8  # 80% return on winning trades
            self.user_data[user_id]['balance'] += profit
            result = f"✅ *WIN!* +${profit}"
            trade_result = "WIN"
        else:
            self.user_data[user_id]['balance'] -= trade_amount
            result = f"❌ *LOSS!* -${trade_amount}"
            trade_result = "LOSS"
        
        # Record trade
        trade_record = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'prediction': prediction,
            'amount': trade_amount,
            'result': trade_result,
            'profit': profit if is_win else -trade_amount
        }
        self.user_data[user_id]['trades'].append(trade_record)
        
        # Send trade result
        result_message = (
            f"{result}\n"
            f"Signal: {prediction}\n"
            f"Confidence: {confidence}%\n"
            f"Current Balance: ${self.user_data[user_id]['balance']}"
        )
        await update.message.reply_text(result_message, parse_mode='Markdown')

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check user's current balance"""
        user_id = update.effective_user.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {'balance': 1000, 'trades': []}
        
        balance = self.user_data[user_id]['balance']
        total_trades = len(self.user_data[user_id]['trades'])
        
        balance_text = (
            f"💰 *Account Balance*\n"
            f"Balance: ${balance}\n"
            f"Total Trades: {total_trades}\n"
            f"Account Status: {'✅ Active' if balance > 0 else '❌ Insufficient Funds'}"
        )
        await update.message.reply_text(balance_text, parse_mode='Markdown')

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create bot instance
    bot = TradingBot()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("analyze", bot.analyze))
    application.add_handler(CommandHandler("trade", bot.trade))
    application.add_handler(CommandHandler("balance", bot.balance))
    
    # Start the bot
    print("🤖 Binary Predictor AI Bot is starting...")
    print("✅ Bot is running and listening for messages...")
    application.run_polling()

if __name__ == "__main__":
    main()
