#!/usr/bin/env python3
"""
Start the RAD Trading Bot with Live Web Dashboard

This script starts the trading bot and its web dashboard for live monitoring.
The dashboard will be available at http://localhost:5000
"""
import os
import sys
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open the dashboard in the default browser after a short delay"""
    time.sleep(3)  # Wait for server to start
    try:
        webbrowser.open('http://localhost:5000')
        print("✅ Dashboard opened in browser")
    except Exception as e:
        print(f"⚠️  Could not automatically open browser: {e}")
        print("📱 Please manually open: http://localhost:5000")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    try:
        import ccxt
        import pandas
        import numpy
        import sklearn
        import ta
        import flask
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
    print("🤖 RAD Trading Bot with Live Web Dashboard")
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
    print("✅ Setup complete! Starting bot with web dashboard...")
    print("=" * 70)
    print("\n📊 Web Dashboard Features:")
    print("  • Real-time bot status and balance")
    print("  • Live position monitoring")
    print("  • Trade history and performance metrics")
    print("  • Current trading opportunities")
    print("  • Auto-refresh every 3 seconds")
    print("\n🌐 Dashboard URL: http://localhost:5000")
    print("💡 The dashboard will open automatically in your browser")
    print("💡 Press Ctrl+C to stop the bot")
    print("=" * 70)
    print()
    
    # Schedule browser to open
    Timer(3.0, open_browser).start()
    
    # Import and run bot
    try:
        from bot import main as run_bot
        run_bot()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
