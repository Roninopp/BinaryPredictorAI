import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime, timedelta
import ta
from typing import Dict, List, Tuple
import random

class BinaryOptionsBot:
    def __init__(self, paper_balance=1000):
        self.paper_balance = paper_balance
        self.initial_balance = paper_balance
        self.trade_history = []
        self.win_rate = 0
        self.total_trades = 0
        self.winning_trades = 0
        
        # Trading parameters
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        self.timeframe = '5m'
        self.trade_duration = 5  # minutes
        self.trade_amount = 10   # virtual dollars per trade
    
    def get_market_data(self, symbol):
        """Get market data for a symbol"""
        try:
            # Simulate market data for demo purposes
            base_prices = {
                'EURUSD': 1.068, 'GBPUSD': 1.344, 
                'USDJPY': 159.2, 'XAUUSD': 2415.0
            }
            base_price = base_prices.get(symbol, 1.0)
            
            # Generate realistic price movement
            closes = [base_price * (1 + np.random.normal(0, 0.002)) for _ in range(50)]
            highs = [price * (1 + abs(np.random.normal(0, 0.001))) for price in closes]
            lows = [price * (1 - abs(np.random.normal(0, 0.001))) for price in closes]
            opens = [price * (1 + np.random.normal(0, 0.0005)) for price in closes]
            
            return {
                'success': True,
                'price': closes[-1],
                'opens': opens, 'highs': highs, 'lows': lows, 'closes': closes,
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def analyze_market(self, symbol):
        """Analyze market data and generate signals"""
        try:
            market_data = self.get_market_data(symbol)
            if not market_data['success']:
                return {'success': False, 'error': market_data['error']}
            
            # Simple analysis logic
            closes = market_data['closes']
            price = market_data['price']
            
            # Calculate simple indicators
            rsi = self.calculate_rsi(closes)
            ema_9 = self.calculate_ema(closes, 9)
            ema_21 = self.calculate_ema(closes, 21)
            
            # Generate signal
            signal = "HOLD"
            confidence = 0
            
            if rsi < 30 and ema_9 > ema_21:
                signal = "CALL"
                confidence = 75
            elif rsi > 70 and ema_9 < ema_21:
                signal = "PUT"
                confidence = 75
            elif rsi < 40 and ema_9 > ema_21:
                signal = "CALL"
                confidence = 60
            elif rsi > 60 and ema_9 < ema_21:
                signal = "PUT"
                confidence = 60
            
            return {
                'success': True,
                'signal': signal,
                'confidence': confidence,
                'price': price,
                'rsi': rsi,
                'ema_9': ema_9,
                'ema_21': ema_21
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
    
    def run_single_analysis(self, symbol):
        """Run analysis for a single symbol"""
        print(f"\n🔍 Analyzing {symbol}...")
        
        analysis = self.analyze_market(symbol)
        
        if analysis['success']:
            print(f"📊 Analysis Results for {symbol}:")
            print(f"💹 Current Price: ${analysis['price']:.4f}")
            print(f"📈 Signal: {analysis['signal']}")
            print(f"🎯 Confidence: {analysis['confidence']}%")
            print(f"📉 RSI: {analysis['rsi']:.1f}")
            print(f"📈 EMA 9/21: ${analysis['ema_9']:.4f}/${analysis['ema_21']:.4f}")
            
            if analysis['signal'] != "HOLD":
                print(f"🚨 TRADING SIGNAL: {analysis['signal']} with {analysis['confidence']}% confidence!")
                print("💡 Consider entering this trade!")
            else:
                print("⏳ No clear signal - waiting for better setup")
        else:
            print(f"❌ Analysis failed: {analysis['error']}")
    
    def show_performance(self):
        """Show trading performance"""
        print(f"\n📊 PERFORMANCE SUMMARY")
        print(f"{'='*40}")
        print(f"💰 Initial Balance: ${self.initial_balance:.2f}")
        print(f"💰 Current Balance: ${self.paper_balance:.2f}")
        print(f"📈 Total Trades: {self.total_trades}")
        print(f"✅ Winning Trades: {self.winning_trades}")
        print(f"📊 Win Rate: {self.win_rate:.1f}%")
        
        if self.total_trades > 0:
            profit_loss = self.paper_balance - self.initial_balance
            print(f"💵 P&L: ${profit_loss:.2f}")
            print(f"📈 ROI: {(profit_loss/self.initial_balance)*100:.1f}%")
    
    def run_continuous(self):
        """Run continuous trading simulation"""
        print("🤖 Starting Binary Options Paper Trading Bot...")
        print("💡 This is for EDUCATIONAL PURPOSES only!")
        
        while True:
            print(f"\n{'='*40}")
            print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"💰 Paper Balance: ${self.paper_balance:.2f}")
            print(f"📊 Win Rate: {self.win_rate:.1f}%")
            print(f"{'='*40}")
            
            print("\nAvailable Symbols:")
            for i, symbol in enumerate(self.symbols, 1):
                print(f"  {i}. {symbol}")
            print("  5. Show Performance")
            print("  6. Exit")
            
            try:
                choice = input("\nSelect symbol (1-6): ").strip()
                
                if choice == '6':
                    break
                elif choice == '5':
                    self.show_performance()
                    continue
                elif choice in ['1', '2', '3', '4']:
                    symbol = self.symbols[int(choice) - 1]
                    self.run_single_analysis(symbol)
                else:
                    print("❌ Invalid choice!")
                    
                # Small delay to simulate real trading
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        self.show_performance()

# 🚀 Main Execution - FIXED THIS LINE
if __name__ == "__main__":
    bot = BinaryOptionsBot(paper_balance=1000)
    bot.run_continuous()
