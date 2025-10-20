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
        """Simulate market data for testing"""
        base_prices = {
            'EURUSD': 1.068, 'GBPUSD': 1.344, 'USDJPY': 159.2, 'XAUUSD': 2415.0
        }
        base_price = base_prices.get(symbol, 1.0)
        
        # Generate realistic price data
        import numpy as np
        closes = [base_price * (1 + np.random.normal(0, 0.002)) for _ in range(50)]
        highs = [price * (1 + abs(np.random.normal(0, 0.001))) for price in closes]
        lows = [price * (1 - abs(np.random.normal(0, 0.001))) for price in closes]
        opens = [price * (1 + np.random.normal(0, 0.0005)) for price in closes]
        
        return {
            'success': True,
            'price': closes[-1],
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes
        }
    
    def calculate_indicators(self, closes):
        """Calculate technical indicators"""
        try:
            import ta
            prices = pd.Series(closes)
            
            # RSI
            rsi = ta.momentum.RSIIndicator(prices, window=14).rsi().iloc[-1]
            if pd.isna(rsi):
                rsi = 50
            
            # EMA
            ema_9 = ta.trend.EMAIndicator(prices, window=9).ema_indicator().iloc[-1]
            ema_21 = ta.trend.EMAIndicator(prices, window=21).ema_indicator().iloc[-1]
            
            if pd.isna(ema_9):
                ema_9 = prices.iloc[-1]
            if pd.isna(ema_21):
                ema_21 = prices.iloc[-1]
                
            return {
                'rsi': round(rsi, 1),
                'ema_9': round(ema_9, 4),
                'ema_21': round(ema_21, 4)
            }
        except:
            # Fallback calculation
            return {
                'rsi': 50.0,
                'ema_9': closes[-1],
                'ema_21': closes[-1]
            }
    
    def detect_price_patterns(self, opens, highs, lows, closes):
        """Detect price action patterns"""
        if len(closes) < 2:
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
        
        # Engulfing patterns
        if (current_close > current_open and prev_close < prev_open and
            current_open < prev_close and current_close > prev_open):
            price_signals.append("BULLISH_ENGULFING")
            
        elif (current_close < current_open and prev_close > prev_open and
              current_open > prev_close and current_close < prev_open):
            price_signals.append("BEARISH_ENGULFING")
        
        # Pin bars
        body_size = abs(current_close - current_open)
        upper_wick = current_high - max(current_open, current_close)
        lower_wick = min(current_open, current_close) - current_low
        
        if body_size > 0:
            if (lower_wick >= 2 * body_size and upper_wick <= body_size * 0.3):
                price_signals.append("HAMMER_PINBAR")
            elif (upper_wick >= 2 * body_size and lower_wick <= body_size * 0.3):
                price_signals.append("SHOOTING_STAR")
        
        # Support/Resistance
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        resistance = recent_high * 1.0002
        support = recent_low * 0.9998
        
        if abs(current_high - resistance) / resistance < 0.0003:
            price_signals.append("AT_RESISTANCE")
        if abs(current_low - support) / support < 0.0003:
            price_signals.append("AT_SUPPORT")
        
        return {
            'price_signals': price_signals,
            'confidence_boost': len(price_signals) * 10,
            'support': support,
            'resistance': resistance
        }
    
    def generate_signal(self, symbol):
        """Generate trading signal"""
        try:
            # Get market data
            market_data = self.get_market_data(symbol)
            if not market_data['success']:
                return {'signal': 'HOLD', 'confidence': 0, 'reason': 'No data'}
            
            # Calculate indicators
            indicators = self.calculate_indicators(market_data['closes'])
            
            # Detect price patterns
            price_action = self.detect_price_patterns(
                market_data['opens'], market_data['highs'],
                market_data['lows'], market_data['closes']
            )
            
            # Simple signal logic
            signal = "HOLD"
            confidence = 0
            reasons = []
            
            # RSI signals
            if indicators['rsi'] < 30:
                signal = "CALL"
                confidence += 25
                reasons.append("RSI Oversold")
            elif indicators['rsi'] > 70:
                signal = "PUT"
                confidence += 25
                reasons.append("RSI Overbought")
            
            # EMA trend
            if indicators['ema_9'] > indicators['ema_21']:
                if signal == "HOLD":
                    signal = "CALL"
                confidence += 15
                reasons.append("Bullish EMA")
            elif indicators['ema_9'] < indicators['ema_21']:
                if signal == "HOLD":
                    signal = "PUT"
                confidence += 15
                reasons.append("Bearish EMA")
            
            # Price action confirmation
            if "BULLISH_ENGULFING" in price_action['price_signals']:
                signal = "CALL"
                confidence += 20
                reasons.append("Bullish Engulfing")
            elif "BEARISH_ENGULFING" in price_action['price_signals']:
                signal = "PUT"
                confidence += 20
                reasons.append("Bearish Engulfing")
            
            return {
                'signal': signal,
                'confidence': min(confidence, 95),
                'price': market_data['price'],
                'rsi': indicators['rsi'],
                'ema_9': indicators['ema_9'],
                'ema_21': indicators['ema_21'],
                'reasons': reasons,
                'success': True
            }
            
        except Exception as e:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': f'Error: {e}', 'success': False}
    
    def execute_trade(self, signal_data):
        """Execute paper trade"""
        if signal_data['signal'] == 'HOLD' or signal_data['confidence'] < 50:
            return False
            
        # Simulate trade execution
        trade_result = random.choice([True, False])  # 50/50 for demo
        
        if trade_result:
            self.paper_balance += self.trade_amount * 0.8  # 80% payout
            self.winning_trades += 1
            print(f"✅ WIN: +${self.trade_amount * 0.8:.2f}")
        else:
            self.paper_balance -= self.trade_amount
            print(f"❌ LOSS: -${self.trade_amount:.2f}")
        
        self.total_trades += 1
        self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        # Add to history
        self.trade_history.append({
            'symbol': signal_data.get('symbol', 'UNKNOWN'),
            'signal': signal_data['signal'],
            'confidence': signal_data['confidence'],
            'result': 'WIN' if trade_result else 'LOSS',
            'amount': self.trade_amount,
            'balance': self.paper_balance,
            'time': datetime.now()
        })
        
        return True
    
    def run_single_analysis(self, symbol):
        """Run analysis for a single symbol"""
        print(f"\n🔍 Analyzing {symbol}...")
        
        signal_data = self.generate_signal(symbol)
        signal_data['symbol'] = symbol
        
        if signal_data['success']:
            print(f"💹 Price: ${signal_data['price']:.4f}")
            print(f"📊 RSI: {signal_data['rsi']}")
            print(f"📈 EMA 9/21: {signal_data['ema_9']:.4f}/{signal_data['ema_21']:.4f}")
            print(f"🎯 Signal: {signal_data['signal']}")
            print(f"📊 Confidence: {signal_data['confidence']}%")
            print(f"💡 Reasons: {', '.join(signal_data['reasons'])}")
            
            if signal_data['confidence'] >= 60:
                print("🚨 HIGH CONFIDENCE - Executing trade!")
                self.execute_trade(signal_data)
            else:
                print("⏳ Low confidence - Skipping trade")
        else:
            print(f"❌ Analysis failed: {signal_data.get('reason', 'Unknown error')}")
    
    def show_performance(self):
        """Show trading performance"""
        print(f"\n{'='*50}")
        print("📊 TRADING PERFORMANCE")
        print(f"{'='*50}")
        print(f"💰 Current Balance: ${self.paper_balance:.2f}")
        print(f"📈 P&L: ${self.paper_balance - self.initial_balance:.2f}")
        print(f"🎯 Total Trades: {self.total_trades}")
        print(f"✅ Winning Trades: {self.winning_trades}")
        print(f"📊 Win Rate: {self.win_rate:.1f}%")
        
        if self.trade_history:
            print(f"\n📋 Recent Trades:")
            for trade in self.trade_history[-5:]:
                print(f"  {trade['time'].strftime('%H:%M:%S')} | {trade['symbol']} | "
                      f"{trade['signal']} | {trade['confidence']}% | {trade['result']}")
        print(f"{'='*50}")
    
    
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
