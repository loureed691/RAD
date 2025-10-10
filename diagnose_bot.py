#!/usr/bin/env python3
"""
Comprehensive diagnostic script to identify why the trading bot has stopped trading.

This script checks:
1. Configuration issues
2. API connectivity
3. Signal generation thresholds
4. Risk management conditions
5. Market scanner functionality
6. Position limits
7. Balance availability
"""

import os
import sys
from datetime import datetime
from config import Config
from logger import Logger

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def main():
    print_header("TRADING BOT DIAGNOSTICS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    issues_found = []
    warnings_found = []
    
    # 1. Check Configuration
    print_header("1. CONFIGURATION CHECK")
    
    try:
        Config.validate()
        print_success("API credentials are configured")
    except ValueError as e:
        print_error(f"Configuration validation failed: {e}")
        issues_found.append("Missing or invalid API credentials in .env file")
        print_info("Action: Create .env file from .env.example and add your KuCoin API credentials")
        return  # Can't continue without credentials
    
    # Check .env file exists
    if os.path.exists('.env'):
        print_success(".env file exists")
    else:
        print_error(".env file not found")
        issues_found.append("No .env file found")
        print_info("Action: Copy .env.example to .env and configure your settings")
    
    # Check configuration values
    print(f"\n{Colors.BOLD}Current Configuration:{Colors.END}")
    print(f"  CHECK_INTERVAL: {Config.CHECK_INTERVAL}s")
    print(f"  POSITION_UPDATE_INTERVAL: {Config.POSITION_UPDATE_INTERVAL}s")
    print(f"  MAX_OPEN_POSITIONS: {Config.MAX_OPEN_POSITIONS}")
    print(f"  MAX_WORKERS: {Config.MAX_WORKERS}")
    print(f"  ENABLE_WEBSOCKET: {Config.ENABLE_WEBSOCKET}")
    
    # Check if values will be auto-configured
    if Config.LEVERAGE is None:
        print_info("LEVERAGE will be auto-configured based on balance")
    else:
        print(f"  LEVERAGE: {Config.LEVERAGE}x")
    
    if Config.MAX_POSITION_SIZE is None:
        print_info("MAX_POSITION_SIZE will be auto-configured based on balance")
    else:
        print(f"  MAX_POSITION_SIZE: ${Config.MAX_POSITION_SIZE}")
    
    if Config.RISK_PER_TRADE is None:
        print_info("RISK_PER_TRADE will be auto-configured based on balance")
    else:
        print(f"  RISK_PER_TRADE: {Config.RISK_PER_TRADE:.2%}")
    
    # 2. Check API Connectivity
    print_header("2. API CONNECTIVITY CHECK")
    
    try:
        from kucoin_client import KuCoinClient
        client = KuCoinClient(
            Config.API_KEY,
            Config.API_SECRET,
            Config.API_PASSPHRASE,
            enable_websocket=False  # Don't start websocket for diagnostic
        )
        
        # Test balance fetch
        print_info("Testing balance fetch...")
        balance = client.get_balance()
        
        if balance and 'free' in balance:
            available = float(balance.get('free', {}).get('USDT', 0))
            print_success(f"API connection working - Balance: ${available:.2f} USDT")
            
            if available < 10:
                print_warning(f"Balance is very low (${available:.2f}) - may prevent trading")
                warnings_found.append(f"Low balance (${available:.2f}) may prevent opening positions")
            elif available < 1:
                print_error(f"Insufficient balance (${available:.2f}) to trade")
                issues_found.append(f"Insufficient balance (${available:.2f})")
        else:
            print_error("Failed to fetch balance - unexpected response format")
            issues_found.append("Balance fetch returned unexpected format")
        
        # Test market data fetch
        print_info("Testing market data fetch...")
        futures = client.get_active_futures()
        if futures and len(futures) > 0:
            print_success(f"Market data accessible - {len(futures)} futures pairs available")
        else:
            print_error("Failed to fetch active futures")
            issues_found.append("Cannot fetch active futures list")
        
        # Test ticker fetch for a common pair
        if futures and len(futures) > 0:
            test_symbol = futures[0]
            print_info(f"Testing ticker fetch for {test_symbol}...")
            ticker = client.get_ticker(test_symbol)
            if ticker and 'last' in ticker:
                print_success(f"Ticker data working - {test_symbol} @ ${ticker['last']}")
            else:
                print_warning(f"Ticker fetch returned unexpected format for {test_symbol}")
                warnings_found.append("Ticker data may have format issues")
        
        client.close()
        
    except Exception as e:
        print_error(f"API connectivity test failed: {e}")
        issues_found.append(f"API error: {str(e)}")
        print_info("Action: Check API credentials, network connection, and KuCoin API status")
    
    # 3. Check Signal Generation
    print_header("3. SIGNAL GENERATION CHECK")
    
    print_info("Signal confidence thresholds:")
    print("  - Trending market: 0.52 (52%)")
    print("  - Ranging market: 0.58 (58%)")
    print("  - Neutral market: 0.55 (55%) [adaptive threshold]")
    print("  - Risk manager validation: 0.60 (60%) minimum")
    
    print_warning("High confidence thresholds may prevent trades in sideways markets")
    warnings_found.append("Default confidence thresholds (52-60%) may be preventing signals")
    print_info("Suggestion: Monitor logs/scanning.log to see if signals are being generated but rejected")
    
    # 4. Check Risk Management Conditions
    print_header("4. RISK MANAGEMENT CONDITIONS")
    
    print_info("Risk management checks that could block trades:")
    print("  1. Confidence threshold (60% minimum)")
    print("  2. Maximum open positions limit")
    print("  3. Minimum balance requirement")
    print("  4. Portfolio diversification rules")
    print("  5. Correlation risk checks")
    print("  6. Drawdown protection")
    print("  7. Loss streak protection")
    
    print_warning("Multiple risk checks must pass for trade execution")
    warnings_found.append("Strict risk management may be preventing trades - check logs for rejection reasons")
    
    # 5. Check Position Limits
    print_header("5. POSITION LIMITS CHECK")
    
    max_positions = Config.MAX_OPEN_POSITIONS
    print(f"Maximum open positions: {max_positions}")
    
    if max_positions < 3:
        print_warning(f"Low position limit ({max_positions}) may restrict trading")
        warnings_found.append(f"Consider increasing MAX_OPEN_POSITIONS from {max_positions}")
    else:
        print_success(f"Position limit ({max_positions}) is reasonable")
    
    # 6. Check Scan Interval
    print_header("6. SCAN INTERVAL CHECK")
    
    scan_interval = Config.CHECK_INTERVAL
    print(f"Opportunity scan interval: {scan_interval}s")
    
    if scan_interval > 300:
        print_warning(f"Scan interval is quite long ({scan_interval}s / {scan_interval/60:.1f} min)")
        warnings_found.append(f"Long scan interval ({scan_interval}s) may miss opportunities")
        print_info("Suggestion: Consider reducing CHECK_INTERVAL to 60-120 seconds")
    elif scan_interval < 30:
        print_warning(f"Scan interval is very short ({scan_interval}s) - may hit API rate limits")
        warnings_found.append(f"Short scan interval ({scan_interval}s) may cause API rate limit issues")
    else:
        print_success(f"Scan interval ({scan_interval}s) is reasonable")
    
    # 7. Check Logs
    print_header("7. LOG FILE CHECK")
    
    log_files = [
        Config.LOG_FILE,
        Config.POSITION_LOG_FILE,
        Config.SCANNING_LOG_FILE,
        Config.ORDERS_LOG_FILE,
        Config.STRATEGY_LOG_FILE
    ]
    
    for log_file in log_files:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            print_warning(f"Log directory missing: {log_dir}")
            warnings_found.append(f"Create directory: {log_dir}")
        elif os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            if file_size > 0:
                print_success(f"Log file exists: {log_file} ({file_size} bytes)")
            else:
                print_warning(f"Log file is empty: {log_file}")
        else:
            print_info(f"Log file will be created: {log_file}")
    
    # 8. Market Scanner Configuration
    print_header("8. MARKET SCANNER CHECK")
    
    cache_duration = Config.CACHE_DURATION
    stale_multiplier = Config.STALE_DATA_MULTIPLIER
    max_stale_age = scan_interval * stale_multiplier
    
    print(f"Cache duration: {cache_duration}s")
    print(f"Stale data multiplier: {stale_multiplier}x")
    print(f"Max opportunity age: {max_stale_age}s")
    
    if max_stale_age < scan_interval:
        print_error("Max opportunity age is less than scan interval!")
        issues_found.append("Opportunities expire before they can be used")
        print_info(f"Action: Increase STALE_DATA_MULTIPLIER to at least 2")
    elif max_stale_age > scan_interval * 3:
        print_warning("Opportunities may be too old when used")
        warnings_found.append("Consider reducing STALE_DATA_MULTIPLIER for fresher data")
    else:
        print_success("Opportunity freshness settings are reasonable")
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    if issues_found:
        print(f"\n{Colors.RED}{Colors.BOLD}CRITICAL ISSUES FOUND ({len(issues_found)}):{Colors.END}")
        for i, issue in enumerate(issues_found, 1):
            print(f"{Colors.RED}  {i}. {issue}{Colors.END}")
    else:
        print_success("No critical issues found")
    
    if warnings_found:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS ({len(warnings_found)}):{Colors.END}")
        for i, warning in enumerate(warnings_found, 1):
            print(f"{Colors.YELLOW}  {i}. {warning}{Colors.END}")
    else:
        print_success("No warnings")
    
    # Recommendations
    print(f"\n{Colors.BOLD}RECOMMENDATIONS TO FIX 'BOT NOT TRADING' ISSUE:{Colors.END}")
    print()
    print("1. Check recent logs to identify rejection reasons:")
    print("   - logs/bot.log - main bot activity")
    print("   - logs/scanning.log - market scanning and signals")
    print("   - logs/strategy.log - signal generation details")
    print()
    print("2. Most common causes of 'bot not trading':")
    print("   a) No valid signals above confidence threshold")
    print("      → Monitor scanning.log for signals and why they're rejected")
    print("      → Consider lowering confidence thresholds if market is quiet")
    print()
    print("   b) Risk management rejecting trades")
    print("      → Check for: loss streaks, drawdown protection, correlation limits")
    print("      → Review risk_manager conditions in logs")
    print()
    print("   c) Low balance or position limits reached")
    print("      → Ensure sufficient USDT balance")
    print("      → Check no positions are already open at limit")
    print()
    print("   d) API issues or rate limiting")
    print("      → Check KuCoin API status")
    print("      → Verify API keys have correct permissions")
    print()
    print("3. Immediate actions to try:")
    print("   a) Lower confidence thresholds temporarily:")
    print("      → Modify signals.py: reduce min_confidence values")
    print("      → Or modify risk_manager.py: lower validate_trade min_confidence")
    print()
    print("   b) Check current market conditions:")
    print("      → Run market scanner manually to see if any signals exist")
    print("      → Low volatility markets may not generate strong signals")
    print()
    print("   c) Enable more detailed logging:")
    print("      → Set LOG_LEVEL=DEBUG in .env")
    print("      → Monitor logs in real-time: tail -f logs/bot.log")
    print()
    print("4. Test mode:")
    print("   - Consider running bot in test/demo mode first")
    print("   - Use small balance to verify it's working")
    print("   - Monitor for at least 1-2 scan cycles")
    print()
    
    if not issues_found:
        print(f"\n{Colors.GREEN}{Colors.BOLD}DIAGNOSIS: No critical issues detected.{Colors.END}")
        print(f"{Colors.GREEN}The bot should be operational, but trading depends on:{Colors.END}")
        print(f"{Colors.GREEN}  1. Market conditions generating valid signals{Colors.END}")
        print(f"{Colors.GREEN}  2. Signals meeting confidence thresholds{Colors.END}")
        print(f"{Colors.GREEN}  3. Risk management checks passing{Colors.END}")
        print(f"{Colors.GREEN}  4. Available balance and position limits{Colors.END}")
        print()
        print(f"{Colors.BLUE}→ Check logs to see if signals are being generated and why trades may be rejected{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}DIAGNOSIS: Critical issues must be fixed before bot can trade.{Colors.END}")
        print(f"{Colors.RED}Address all issues listed above.{Colors.END}")
    
    print()
    print_header("DIAGNOSTIC COMPLETE")
    
    return len(issues_found)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print_error(f"Diagnostic script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
