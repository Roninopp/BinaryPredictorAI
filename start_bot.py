#!/usr/bin/env python3
"""
Pocket Option AI Bot Launcher
Automatically detects and starts the best available bot version
"""
import os
import sys
import subprocess
import time

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import pandas
        import numpy
        import requests
        import ta
        from telegram import Update
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Installing dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            return True
        except:
            return False

def test_bot_functionality():
    """Quick test of bot functionality"""
    try:
        sys.path.insert(0, 'strategies')
        from low_strategy import generate_low_confidence_signals
        from ai_enhancements import ai_enhancements
        return True
    except Exception as e:
        print(f"❌ Bot functionality test failed: {e}")
        return False

def start_telegram_bot():
    """Start the Telegram bot"""
    print("🚀 Starting Telegram Bot (Enhanced Version)...")
    try:
        subprocess.run([sys.executable, "ultimate_otc_bot_ENHANCED.py"])
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Telegram bot failed: {e}")
        return False
    return True

def start_simple_bot():
    """Start the simple bot"""
    print("🚀 Starting Simple AI Bot...")
    try:
        subprocess.run([sys.executable, "simple_ai_bot.py"])
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Simple bot failed: {e}")
        return False
    return True

def start_paper_trading():
    """Start paper trading bot"""
    print("🚀 Starting Paper Trading Bot...")
    try:
        subprocess.run([sys.executable, "bot.py"])
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Paper trading bot failed: {e}")
        return False
    return True

def main():
    """Main launcher function"""
    print("🤖 POCKET OPTION AI BOT LAUNCHER")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Test functionality
    if not test_bot_functionality():
        print("❌ Bot functionality test failed")
        return False
    
    print("✅ All systems ready!")
    print("\nAvailable bot versions:")
    print("1. 🚀 Enhanced Telegram Bot (Recommended)")
    print("2. 🤖 Simple AI Bot")
    print("3. 📊 Paper Trading Bot (Interactive)")
    print("4. 🧪 Run Tests Only")
    print("5. ❌ Exit")
    
    while True:
        try:
            choice = input("\nSelect bot version (1-5): ").strip()
            
            if choice == "1":
                return start_telegram_bot()
            elif choice == "2":
                return start_simple_bot()
            elif choice == "3":
                return start_paper_trading()
            elif choice == "4":
                print("🧪 Running comprehensive tests...")
                result = subprocess.run([sys.executable, "test_bot.py"])
                return result.returncode == 0
            elif choice == "5":
                print("👋 Goodbye!")
                return True
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)