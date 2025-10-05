#!/usr/bin/env python3
"""
Production startup wrapper for KuCoin Futures Trading Bot
Performs pre-flight checks before starting the bot
"""
import os
import sys
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print_info("Checking dependencies...")
    try:
        import ccxt
        import pandas
        import numpy
        import sklearn
        import ta
        from dotenv import load_dotenv
        print_success("All dependencies installed")
        return True
    except ImportError as e:
        print_error(f"Missing dependency: {e}")
        print_info("Install with: pip install -r requirements.txt")
        return False

def check_config():
    """Check if configuration is valid"""
    print_info("Checking configuration...")
    
    if not os.path.exists('.env'):
        print_error(".env file not found")
        print_info("Create with: cp .env.example .env")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('KUCOIN_API_KEY', '')
    api_secret = os.getenv('KUCOIN_API_SECRET', '')
    api_passphrase = os.getenv('KUCOIN_API_PASSPHRASE', '')
    
    if not api_key or api_key == 'your_api_key_here':
        print_error("KUCOIN_API_KEY not configured in .env")
        return False
    
    if not api_secret or api_secret == 'your_api_secret_here':
        print_error("KUCOIN_API_SECRET not configured in .env")
        return False
    
    if not api_passphrase or api_passphrase == 'your_api_passphrase_here':
        print_error("KUCOIN_API_PASSPHRASE not configured in .env")
        return False
    
    print_success("Configuration valid")
    return True

def check_api_connection():
    """Test API connection to KuCoin"""
    print_info("Testing KuCoin API connection...")
    try:
        from config import Config
        from kucoin_client import KuCoinClient
        
        Config.validate()
        client = KuCoinClient(
            Config.API_KEY,
            Config.API_SECRET,
            Config.API_PASSPHRASE
        )
        
        # Try to fetch balance
        balance = client.get_balance()
        available = float(balance.get('free', {}).get('USDT', 0))
        
        print_success(f"API connection successful (Balance: ${available:.2f} USDT)")
        
        if available < 10:
            print_warning("Balance is very low - bot may not be able to trade")
            print_info("Minimum recommended balance: $100 USDT")
        
        return True
    except Exception as e:
        print_error(f"API connection failed: {e}")
        print_info("Check your API credentials and network connection")
        return False

def create_directories():
    """Create necessary directories"""
    print_info("Creating directories...")
    directories = ['logs', 'models']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print_success("Directories ready")
    return True

def display_config_summary():
    """Display configuration summary"""
    from config import Config
    
    print_info("Configuration summary:")
    if Config.LEVERAGE:
        print(f"  Leverage: {Config.LEVERAGE}x")
    if Config.MAX_POSITION_SIZE:
        print(f"  Max Position: ${Config.MAX_POSITION_SIZE:.0f} USDT")
    if Config.RISK_PER_TRADE:
        print(f"  Risk per Trade: {Config.RISK_PER_TRADE * 100:.1f}%")
    print(f"  Max Open Positions: {Config.MAX_OPEN_POSITIONS}")
    print(f"  Check Interval: {Config.CHECK_INTERVAL}s")
    
    if Config.LEVERAGE is None:
        print_info("  Note: Settings will be auto-configured based on balance")

def main():
    """Main startup function"""
    print_header("KuCoin Bot Production Startup")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Pre-flight checks
    checks = [
        ("Dependencies", check_dependencies),
        ("Directories", create_directories),
        ("Configuration", check_config),
        ("API Connection", check_api_connection),
    ]
    
    failed_checks = []
    for check_name, check_func in checks:
        if not check_func():
            failed_checks.append(check_name)
            print("")  # Empty line for readability
    
    # Display results
    if failed_checks:
        print_header("Pre-flight Check Failed")
        print_error("The following checks failed:")
        for check in failed_checks:
            print(f"  ✗ {check}")
        print("")
        print_info("Please fix the issues above before starting the bot")
        return 1
    
    print_header("Pre-flight Check Passed")
    print_success("All checks passed - ready to start!")
    print("")
    
    # Display config summary
    display_config_summary()
    
    # Start bot
    print("")
    print_header("Starting Trading Bot")
    print_info("Press Ctrl+C to stop the bot")
    print("")
    
    try:
        # Import and run bot
        from bot import main as run_bot
        run_bot()
    except KeyboardInterrupt:
        print("")
        print_info("Bot stopped by user")
        return 0
    except Exception as e:
        print("")
        print_error(f"Bot crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print_error(f"Startup failed: {e}")
        sys.exit(1)
