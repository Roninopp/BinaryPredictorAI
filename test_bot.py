#!/usr/bin/env python3
"""
Pocket Option AI Prediction Bot - Test Script
This script demonstrates the bot's functionality and sends test predictions
"""

import sys
import os
import time
from datetime import datetime

# Add strategies folder to path
current_dir = os.path.dirname(os.path.abspath(__file__))
strategies_path = os.path.join(current_dir, 'strategies')
sys.path.insert(0, strategies_path)

def test_simple_bot():
    """Test the simple AI bot"""
    print("🤖 Testing Simple AI Bot...")
    print("=" * 50)
    
    try:
        from simple_ai_bot import SimpleAITradingBot
        bot = SimpleAITradingBot()
        
        # Test pairs
        test_pairs = ['EUR/USD', 'GBP/USD', 'AUD/CAD OTC', 'XAU/USD']
        
        for pair in test_pairs:
            print(f"\n📊 Analyzing {pair}...")
            result = bot.analyze_pair(pair)
            
            if result['success']:
                print(f"✅ Signal: {result['signal']}")
                print(f"🎯 Confidence: {result['confidence']}%")
                print(f"💹 Price: ${result['price']:.4f}")
                print(f"📉 RSI: {result.get('rsi', 'N/A')}")
                print(f"📈 EMA 9/21: ${result.get('ema_9', 0):.4f}/${result.get('ema_21', 0):.4f}")
                
                if result['signal'] != 'HOLD':
                    print(f"🚨 TRADING SIGNAL DETECTED: {result['signal']} with {result['confidence']}% confidence!")
            else:
                print(f"❌ Analysis failed: {result['error']}")
            
            time.sleep(1)  # Small delay between analyses
            
    except Exception as e:
        print(f"❌ Simple bot test failed: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_bot():
    """Test the enhanced AI bot"""
    print("\n🚀 Testing Enhanced AI Bot...")
    print("=" * 50)
    
    try:
        from ultimate_otc_bot_ENHANCED import UltimateEnhancedTradingAI
        
        class MockApp:
            pass
        
        app = MockApp()
        bot = UltimateEnhancedTradingAI(app)
        
        # Test pairs and timeframes
        test_pairs = ['EUR/USD', 'GBP/USD', 'AUD/CAD OTC', 'XAU/USD']
        test_timeframes = ['1m', '5m', '10m']
        
        for pair in test_pairs:
            for timeframe in test_timeframes:
                print(f"\n📊 Analyzing {pair} {timeframe}...")
                
                # Fetch market data
                market_data = bot.fetch_market_data(pair, timeframe)
                if not market_data.get('success', False):
                    print(f"❌ Failed to fetch data for {pair} {timeframe}")
                    continue
                
                # Analyze price action
                price_action = bot.advanced_price_action_detection(
                    market_data['opens'], market_data['highs'], 
                    market_data['lows'], market_data['closes']
                )
                
                # Analyze indicators
                indicators = bot.dual_indicator_confirmation(market_data['closes'])
                
                # Generate signal
                signal_info = bot.generate_enhanced_signal(
                    price_action, indicators, market_data['price'], pair, market_data
                )
                
                print(f"💹 Price: ${market_data['price']:.4f}")
                print(f"📉 RSI: {indicators['rsi']}")
                print(f"📈 EMA 9/21: ${indicators['ema_9']:.4f}/${indicators['ema_21']:.4f}")
                print(f"🔮 Signal: {signal_info['signal']}")
                print(f"🎯 Confidence: {signal_info['confidence']}% ({signal_info['confidence_level']})")
                print(f"⚡ Urgency: {signal_info['urgency']}")
                
                if signal_info['is_high_confidence']:
                    print(f"🚨 HIGH CONFIDENCE SIGNAL: {signal_info['signal']} - READY FOR AUTO-ALERT!")
                
                time.sleep(0.5)  # Small delay between analyses
                
    except Exception as e:
        print(f"❌ Enhanced bot test failed: {e}")
        import traceback
        traceback.print_exc()

def test_strategies():
    """Test individual strategy modules"""
    print("\n🧠 Testing Strategy Modules...")
    print("=" * 50)
    
    try:
        from low_strategy import generate_low_confidence_signals
        from medium_strategy import generate_medium_confidence_signals
        
        # Mock data for testing
        price_action = {
            'price_signals': ['BULLISH_ENGULFING', 'AT_SUPPORT'],
            'confidence_boost': 30,
            'support': 1.0650,
            'resistance': 1.0700
        }
        
        indicators = {
            'rsi': 25,
            'ema_9': 1.0680,
            'ema_21': 1.0670,
            'indicator_signals': ['RSI_OVERSOLD', 'EMA_BULLISH'],
            'indicator_confidence': 40
        }
        
        # Test low confidence strategy
        print("Testing Low Confidence Strategy...")
        low_signal = generate_low_confidence_signals(price_action, indicators)
        print(f"Low Signal: {low_signal['action']} (Confidence: {low_signal['confidence']}%)")
        print(f"Tradable: {low_signal['is_tradable']}")
        
        # Test medium confidence strategy
        print("\nTesting Medium Confidence Strategy...")
        medium_signal = generate_medium_confidence_signals(price_action, indicators)
        print(f"Medium Signal: {medium_signal['action']} (Confidence: {medium_signal['confidence']}%)")
        print(f"Tradable: {medium_signal['is_tradable']}")
        
    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🚀 POCKET OPTION AI PREDICTION BOT - TEST SUITE")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test individual strategies
    test_strategies()
    
    # Test simple bot
    test_simple_bot()
    
    # Test enhanced bot
    test_enhanced_bot()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("🤖 Bot is ready for Pocket Option market analysis!")
    print("📱 Use the Telegram bot commands to start auto-trading")
    print("=" * 60)

if __name__ == "__main__":
    main()