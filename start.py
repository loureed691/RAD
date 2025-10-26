#!/usr/bin/env python3
"""
Quick start script for the KuCoin Futures Trading Bot
"""
import os
import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    try:
        import ccxt
        import pandas
        import numpy
        import sklearn
        import ta
        from dotenv import load_dotenv
        print("✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\n💡 Please install dependencies:")
        print("  pip install -r requirements.txt")
        return False

def check_config():
    """Check if configuration is set up"""
    print("\n⚙️  Checking configuration...")
    
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("\n💡 Please create .env file:")
        print("  cp .env.example .env")
        print("  # Then edit .env and add your API credentials")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('KUCOIN_API_KEY', '')
    api_secret = os.getenv('KUCOIN_API_SECRET', '')
    api_passphrase = os.getenv('KUCOIN_API_PASSPHRASE', '')
    
    if not api_key or api_key == 'your_api_key_here':
        print("✗ KUCOIN_API_KEY not set in .env")
        return False
    
    if not api_secret or api_secret == 'your_api_secret_here':
        print("✗ KUCOIN_API_SECRET not set in .env")
        return False
    
    if not api_passphrase or api_passphrase == 'your_api_passphrase_here':
        print("✗ KUCOIN_API_PASSPHRASE not set in .env")
        return False
    
    print("✓ Configuration file exists and credentials are set")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    print("✓ Directories created")

def main():
    """Main setup and start function"""
    print("=" * 70)
    print("🤖 RAD - KuCoin Futures Trading Bot")
    print("   FULLY AUTOMATED - Smart Configuration Based on Your Balance")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n" + "=" * 70)
    print("✅ Setup complete! Starting fully automated bot...")
    print("=" * 70)
    print("\n🎯 Bot Features:")
    print("   • Automatic leverage and position sizing based on your balance")
    print("   • Real-time market data via WebSocket")
    print("   • Advanced AI and machine learning signals")
    print("   • Smart risk management and trailing stops")
    print("   • Multi-timeframe analysis")
    print("   • 24/7 automated trading")
    print("\n💡 Press Ctrl+C to stop the bot")
    print()
    
    # Import and run bot
    try:
        from bot import main as run_bot
        run_bot()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
