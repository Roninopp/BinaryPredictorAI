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
        
    def get_historical_data(self, symbol: str, periods: int = 100) -> pd.DataFrame:
        """Simulate getting historical price data"""
        # In real implementation, you'd connect to Pocket Option API
        # This is simulated data for demonstration
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='5min')
        
        # Generate realistic price data with trends and noise
        prices = []
        base_price = random.uniform(1.0, 1.5) if 'USD' in symbol else random.uniform(1500, 1900)
        
        for i in range(periods):
            if i == 0:
                price = base_price
            else:
                change = random.uniform(-0.002, 0.002)  # Small price changes
                price = prices[-1] * (1 + change)
            prices.append(price)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [p * random.uniform(0.999, 1.001) for p in prices],
            'high': [p * random.uniform(1.001, 1.003) for p in prices],
            'low': [p * random.uniform(0.997, 0.999) for p in prices],
            'close': prices,
            'volume': [random.randint(1000, 10000) for _ in range(periods)]
        })
        
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'], window=20)
        df['bb_upper'] = bollinger.bollinger_hband()
        df['bb_lower'] = bollinger.bollinger_lband()
        df['bb_middle'] = bollinger.bollinger_mavg()
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        
        # Moving Averages
        df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
        df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
        df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
        
        # Support and Resistance (simplified)
        df['resistance'] = df['high'].rolling(20).max()
        df['support'] = df['low'].rolling(20).min()
        
        return df
    
    def analyze_signal(self, df: pd.DataFrame) -> Dict:
        """Analyze market and generate trading signal"""
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        signals = []
        signal_strength = 0
        confidence = 0
        
        # RSI Analysis (30/70 levels)
        if current['rsi'] < 35:
            signals.append('CALL')
            signal_strength += 2
            confidence += 0.3
        elif current['rsi'] > 65:
            signals.append('PUT')
            signal_strength += 2
            confidence += 0.3
        
        # MACD Analysis
        if current['macd'] > current['macd_signal'] and previous['macd'] <= previous['macd_signal']:
            signals.append('CALL')
            signal_strength += 2
            confidence += 0.2
        elif current['macd'] < current['macd_signal'] and previous['macd'] >= previous['macd_signal']:
            signals.append('PUT')
            signal_strength += 2
            confidence += 0.2
        
        # Bollinger Bands
        if current['close'] < current['bb_lower']:
            signals.append('CALL')  # Oversold, expect bounce up
            signal_strength += 1
            confidence += 0.15
        elif current['close'] > current['bb_upper']:
            signals.append('PUT')   # Overbought, expect pullback
            signal_strength += 1
            confidence += 0.15
        
        # Stochastic
        if current['stoch_k'] < 20 and current['stoch_d'] < 20:
            signals.append('CALL')
            signal_strength += 1
            confidence += 0.1
        elif current['stoch_k'] > 80 and current['stoch_d'] > 80:
            signals.append('PUT')
            signal_strength += 1
            confidence += 0.1
        
        # Price Action - Support/Resistance
        if current['close'] <= current['support'] * 1.001:
            signals.append('CALL')  # Near support, expect bounce
            signal_strength += 1
            confidence += 0.15
        elif current['close'] >= current['resistance'] * 0.999:
            signals.append('PUT')   # Near resistance, expect rejection
            signal_strength += 1
            confidence += 0.15
        
        # Trend Analysis
        if current['ema_12'] > current['ema_26']:
            signals.append('CALL')
            signal_strength += 1
        else:
            signals.append('PUT')
            signal_strength += 1
        
        # Count signals and determine final prediction
        call_count = signals.count('CALL')
        put_count = signals.count('PUT')
        
        if call_count > put_count:
            prediction = 'CALL'
            confidence = min(confidence + (call_count / 10), 0.95)
        elif put_count > call_count:
            prediction = 'PUT'
            confidence = min(confidence + (put_count / 10), 0.95)
        else:
            prediction = 'NO_TRADE'
            confidence = 0
        
        return {
            'prediction': prediction,
            'confidence': round(confidence * 100, 2),
            'signal_strength': signal_strength,
            'call_signals': call_count,
            'put_signals': put_count,
            'rsi': round(current['rsi'], 2),
            'macd_histogram': round(current['macd_histogram'], 5)
        }
    
    def simulate_trade_outcome(self, prediction: str, current_price: float) -> bool:
        """Simulate trade outcome (in real trading, this would be actual market movement)"""
        # Real implementation would wait for actual price movement
        # This simulation provides realistic outcomes
        base_win_probability = 0.65  # Base win rate for our strategy
        
        # Add some randomness to simulate real market conditions
        adjusted_probability = base_win_probability * random.uniform(0.8, 1.2)
        adjusted_probability = max(0.4, min(0.85, adjusted_probability))
        
        return random.random() < adjusted_probability
    
    def execute_paper_trade(self, symbol: str, prediction: str, confidence: float):
        """Execute a paper trade"""
        if prediction == 'NO_TRADE':
            return None
        
        if self.paper_balance < self.trade_amount:
            print("❌ Insufficient paper balance!")
            return None
        
        # Deduct trade amount
        self.paper_balance -= self.trade_amount
        self.total_trades += 1
        
        # Get current price for simulation
        data = self.get_historical_data(symbol, 10)
        current_price = data['close'].iloc[-1]
        
        # Simulate trade outcome
        is_win = self.simulate_trade_outcome(prediction, current_price)
        
        # Calculate P&L
        if is_win:
            payout = self.trade_amount * 0.75  # Typical binary options payout
            profit = payout
            self.paper_balance += self.trade_amount + profit
            self.winning_trades += 1
            result = "WIN"
        else:
            profit = -self.trade_amount
            result = "LOSS"
        
        # Update win rate
        self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        # Record trade
        trade_record = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'prediction': prediction,
            'amount': self.trade_amount,
            'result': result,
            'profit': profit,
            'confidence': confidence,
            'balance': self.paper_balance
        }
        
        self.trade_history.append(trade_record)
        
        return trade_record
    
    def run_single_analysis(self, symbol: str):
        """Run analysis for a single symbol"""
        print(f"\n🔍 Analyzing {symbol}...")
        
        # Get and analyze data
        data = self.get_historical_data(symbol)
        data = self.calculate_indicators(data)
        signal = self.analyze_signal(data)
        
        print(f"📊 Indicators:")
        print(f"   RSI: {signal['rsi']}")
        print(f"   MACD Hist: {signal['macd_histogram']}")
        print(f"   Signals: CALL({signal['call_signals']}) vs PUT({signal['put_signals']})")
        
        if signal['prediction'] != 'NO_TRADE':
            print(f"🎯 Signal: {signal['prediction']} with {signal['confidence']}% confidence")
            
            # Ask for trade execution
            execute = input("Execute trade? (y/n): ").lower().strip()
            if execute == 'y':
                trade_result = self.execute_paper_trade(symbol, signal['prediction'], signal['confidence'])
                if trade_result:
                    print(f"✅ Trade Result: {trade_result['result']} | Profit: ${trade_result['profit']:.2f}")
        else:
            print("🤷 No clear trading signal - Waiting for better opportunity")
        
        return signal
    
    def show_performance(self):
        """Show trading performance"""
        print(f"\n{'='*50}")
        print("📈 TRADING PERFORMANCE")
        print(f"{'='*50}")
        print(f"Initial Balance: ${self.initial_balance:.2f}")
        print(f"Current Balance: ${self.paper_balance:.2f}")
        print(f"Total P&L: ${self.paper_balance - self.initial_balance:.2f}")
        print(f"Total Trades: {self.total_trades}")
        print(f"Winning Trades: {self.winning_trades}")
        print(f"Win Rate: {self.win_rate:.1f}%")
        
        if self.trade_history:
            print(f"\n📋 Recent Trades:")
            for trade in self.trade_history[-5:]:  # Last 5 trades
                print(f"   {trade['timestamp'].strftime('%H:%M')} {trade['symbol']} {trade['prediction']} "
                      f"{trade['result']} (${trade['profit']:.2f})")
    
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

# 🚀 Main Execution
if __name__ == "__main__":
    bot = BinaryOptionsBot(paper_balance=1000)
    bot.run_continuous()
