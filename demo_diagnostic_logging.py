#!/usr/bin/env python3
"""
Demo script to show enhanced logging in action
Simulates various trading scenarios to demonstrate diagnostic capabilities
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_logging():
    """Demonstrate enhanced logging with various scenarios"""
    print("\n" + "="*80)
    print("TRADING BOT DIAGNOSTIC LOGGING DEMO")
    print("="*80)
    print("\nThis demo shows how the enhanced logging helps diagnose trading issues.")
    print("Watch for ✓ (success) and ❌ (rejection) messages.\n")
    
    from config import Config
    from logger import Logger
    from bot import TradingBot
    
    # Setup logging
    logger = Logger.setup('INFO', 'logs/demo.log')
    
    print("\n" + "-"*80)
    print("SCENARIO 1: Successful Trade Flow")
    print("-"*80)
    
    with patch('bot.Config.validate'), \
         patch('bot.KuCoinClient') as mock_client_class, \
         patch('bot.MarketScanner') as mock_scanner_class, \
         patch('bot.PositionManager') as mock_pos_mgr_class, \
         patch('bot.RiskManager') as mock_risk_mgr_class, \
         patch('bot.MLModel') as mock_ml_class, \
         patch('bot.AdvancedAnalytics') as mock_analytics_class, \
         patch('bot.signal') as mock_signal:
        
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_balance.return_value = {'free': {'USDT': 1000}}
        mock_client.get_ticker.return_value = {'last': 43250.50}
        mock_client.get_ohlcv.return_value = [[1, 43000, 43500, 42900, 43250, 1000]]
        
        mock_pos_mgr = Mock()
        mock_pos_mgr_class.return_value = mock_pos_mgr
        mock_pos_mgr.sync_existing_positions.return_value = 0
        
        # Create bot
        bot = TradingBot()
        
        # Setup for successful trade
        bot.position_manager.has_position = Mock(return_value=False)
        bot.position_manager.positions = {}
        bot.position_manager.get_open_positions_count = Mock(return_value=0)
        bot.position_manager.open_position = Mock(return_value=True)
        bot.risk_manager.check_portfolio_diversification = Mock(return_value=(True, "OK"))
        bot.risk_manager.should_open_position = Mock(return_value=(True, "OK"))
        bot.risk_manager.validate_trade = Mock(return_value=(True, "OK"))
        bot.risk_manager.calculate_stop_loss_percentage = Mock(return_value=0.05)
        bot.risk_manager.get_max_leverage = Mock(return_value=10)
        bot.risk_manager.get_win_rate = Mock(return_value=0.6)
        bot.risk_manager.get_avg_win = Mock(return_value=0.05)
        bot.risk_manager.get_avg_loss = Mock(return_value=0.03)
        bot.risk_manager.total_trades = 5
        bot.risk_manager.update_drawdown = Mock(return_value=1.0)
        bot.risk_manager.calculate_position_size = Mock(return_value=450.0)
        
        opportunity = {
            'symbol': 'BTC-USDT',
            'signal': 'BUY',
            'confidence': 0.82,
            'score': 85.5
        }
        
        print("\nExecuting trade with high confidence...")
        result = bot.execute_trade(opportunity)
        print(f"\nResult: {'✅ TRADE EXECUTED' if result else '❌ TRADE REJECTED'}")
    
    print("\n" + "-"*80)
    print("SCENARIO 2: Low Confidence Rejection")
    print("-"*80)
    
    with patch('bot.Config.validate'), \
         patch('bot.KuCoinClient') as mock_client_class, \
         patch('bot.MarketScanner') as mock_scanner_class, \
         patch('bot.PositionManager') as mock_pos_mgr_class, \
         patch('bot.RiskManager') as mock_risk_mgr_class, \
         patch('bot.MLModel') as mock_ml_class, \
         patch('bot.AdvancedAnalytics') as mock_analytics_class, \
         patch('bot.signal') as mock_signal:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_balance.return_value = {'free': {'USDT': 1000}}
        
        mock_pos_mgr = Mock()
        mock_pos_mgr_class.return_value = mock_pos_mgr
        mock_pos_mgr.sync_existing_positions.return_value = 0
        
        bot = TradingBot()
        bot.position_manager.has_position = Mock(return_value=False)
        bot.position_manager.positions = {}
        bot.risk_manager.check_portfolio_diversification = Mock(return_value=(True, "OK"))
        bot.risk_manager.should_open_position = Mock(return_value=(True, "OK"))
        bot.risk_manager.validate_trade = Mock(return_value=(False, "Confidence too low (0.45 < 0.6)"))
        
        low_conf_opportunity = {
            'symbol': 'ETH-USDT',
            'signal': 'SELL',
            'confidence': 0.45,
            'score': 52.1
        }
        
        print("\nAttempting trade with low confidence...")
        result = bot.execute_trade(low_conf_opportunity)
        print(f"\nResult: {'✅ TRADE EXECUTED' if result else '❌ TRADE REJECTED (Expected)'}")
    
    print("\n" + "-"*80)
    print("SCENARIO 3: Maximum Positions Reached")
    print("-"*80)
    
    with patch('bot.Config.validate'), \
         patch('bot.KuCoinClient') as mock_client_class, \
         patch('bot.MarketScanner') as mock_scanner_class, \
         patch('bot.PositionManager') as mock_pos_mgr_class, \
         patch('bot.RiskManager') as mock_risk_mgr_class, \
         patch('bot.MLModel') as mock_ml_class, \
         patch('bot.AdvancedAnalytics') as mock_analytics_class, \
         patch('bot.signal') as mock_signal:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_balance.return_value = {'free': {'USDT': 1000}}
        
        mock_pos_mgr = Mock()
        mock_pos_mgr_class.return_value = mock_pos_mgr
        mock_pos_mgr.sync_existing_positions.return_value = 0
        
        bot = TradingBot()
        bot.position_manager.has_position = Mock(return_value=False)
        bot.position_manager.positions = {'BTC-USDT': Mock(), 'ETH-USDT': Mock(), 'SOL-USDT': Mock()}
        bot.risk_manager.check_portfolio_diversification = Mock(return_value=(True, "OK"))
        bot.risk_manager.should_open_position = Mock(return_value=(False, "Maximum positions reached (3)"))
        
        opportunity = {
            'symbol': 'AVAX-USDT',
            'signal': 'BUY',
            'confidence': 0.78,
            'score': 72.3
        }
        
        print("\nAttempting trade with max positions...")
        result = bot.execute_trade(opportunity)
        print(f"\nResult: {'✅ TRADE EXECUTED' if result else '❌ TRADE REJECTED (Expected)'}")
    
    print("\n" + "-"*80)
    print("SCENARIO 4: Scanner Finding No Opportunities")
    print("-"*80)
    
    from market_scanner import MarketScanner
    
    with patch('market_scanner.KuCoinClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        scanner = MarketScanner(mock_client)
        scanner.scan_all_pairs = Mock(return_value=[])
        
        print("\nScanning market with no good opportunities...")
        opportunities = scanner.get_best_pairs(n=3)
        print(f"\nResult: Found {len(opportunities)} opportunities (Expected: 0)")
    
    print("\n" + "-"*80)
    print("SCENARIO 5: Scanner Finding Multiple Opportunities")
    print("-"*80)
    
    with patch('market_scanner.KuCoinClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        scanner = MarketScanner(mock_client)
        mock_opportunities = [
            {'symbol': 'BTC-USDT', 'score': 85.5, 'signal': 'BUY', 'confidence': 0.82, 'reasons': {'market_regime': 'trending'}},
            {'symbol': 'ETH-USDT', 'score': 78.3, 'signal': 'SELL', 'confidence': 0.75, 'reasons': {'market_regime': 'ranging'}},
            {'symbol': 'SOL-USDT', 'score': 72.1, 'signal': 'BUY', 'confidence': 0.68, 'reasons': {'market_regime': 'trending'}},
        ]
        scanner.scan_all_pairs = Mock(return_value=mock_opportunities)
        
        print("\nScanning market with good opportunities...")
        opportunities = scanner.get_best_pairs(n=3)
        print(f"\nResult: Found {len(opportunities)} opportunities")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\n✅ Enhanced logging is working correctly!")
    print("\nKey Features Demonstrated:")
    print("  ✓ Clear success/failure indicators (✅/❌)")
    print("  ✓ Detailed rejection reasons with exact values")
    print("  ✓ Step-by-step validation logging")
    print("  ✓ Scanner status and opportunity details")
    print("  ✓ Trade attempt and execution tracking")
    print("\nCheck 'logs/demo.log' for complete details.")
    print("\nRefer to DIAGNOSTIC_LOGGING_GUIDE.md for full documentation.")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        demo_logging()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
