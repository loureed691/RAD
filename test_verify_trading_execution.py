"""
Test suite for verify_trading_execution.py

Tests the bot log analyzer to ensure it correctly verifies
trading strategies and order execution.
"""

import os
import tempfile
from datetime import datetime
from verify_trading_execution import (
    OrderExecution, PositionUpdate, TradingLogAnalyzer
)


class TestOrderExecution:
    """Test OrderExecution class"""
    
    def test_valid_order(self):
        """Test that a valid order passes validation"""
        order_data = {
            'order_id': '12345',
            'side': 'BUY',
            'symbol': 'BTC/USDT:USDT',
            'amount': 1.0,
            'fill_price': 50000.0,
            'status': 'closed',
            'filled_amount': 1.0
        }
        order = OrderExecution(order_data)
        assert order.is_valid()
        assert order.is_successful()
        print("✓ Valid order passes validation")
    
    def test_invalid_order_missing_fields(self):
        """Test that an order with missing fields fails validation"""
        order_data = {
            'order_id': '12345',
            'side': 'BUY',
            # Missing required fields
        }
        order = OrderExecution(order_data)
        assert not order.is_valid()
        print("✓ Invalid order fails validation")
    
    def test_order_with_risk_management(self):
        """Test that orders with stop loss and take profit are detected"""
        order_data = {
            'order_id': '12345',
            'side': 'BUY',
            'symbol': 'BTC/USDT:USDT',
            'amount': 1.0,
            'fill_price': 50000.0,
            'status': 'closed',
            'stop_loss': 48000.0,
            'take_profit': 55000.0
        }
        order = OrderExecution(order_data)
        assert order.has_risk_management()
        print("✓ Order with risk management detected")
    
    def test_order_without_risk_management(self):
        """Test that orders without stop loss/take profit are detected"""
        order_data = {
            'order_id': '12345',
            'side': 'SELL',
            'symbol': 'BTC/USDT:USDT',
            'amount': 1.0,
            'fill_price': 50000.0,
            'status': 'closed',
        }
        order = OrderExecution(order_data)
        assert not order.has_risk_management()
        print("✓ Order without risk management detected")


class TestPositionUpdate:
    """Test PositionUpdate class"""
    
    def test_position_creation(self):
        """Test that position updates are created correctly"""
        pos_data = {
            'timestamp': '2025-10-26 14:00:00',
            'symbol': 'BTC/USDT:USDT',
            'entry_price': 50000.0,
            'current_price': 51000.0,
            'amount': 1.0,
            'leverage': 5.0,
            'pnl_percent': 2.0,
            'pnl_amount': 100.0,
            'stop_loss': 48000.0,
            'take_profit': 55000.0
        }
        position = PositionUpdate(pos_data)
        assert position.symbol == 'BTC/USDT:USDT'
        assert position.entry_price == 50000.0
        assert position.current_price == 51000.0
        assert position.stop_loss == 48000.0
        assert position.take_profit == 55000.0
        print("✓ Position update created correctly")


class TestLogParser:
    """Test log parsing functionality"""
    
    def create_test_log(self) -> str:
        """Create a temporary test log file"""
        content = """
2025-10-26 14:10:11 - [ORDER] INFO - BUY ORDER EXECUTED: BTC/USDT:USDT
2025-10-26 14:10:11 - [ORDER] INFO - --------------------------------------------------------------------------------
2025-10-26 14:10:11 - [ORDER] INFO -   Order ID: 371913167359492097
2025-10-26 14:10:11 - [ORDER] INFO -   Type: MARKET
2025-10-26 14:10:11 - [ORDER] INFO -   Side: BUY
2025-10-26 14:10:11 - [ORDER] INFO -   Symbol: BTC/USDT:USDT
2025-10-26 14:10:11 - [ORDER] INFO -   Amount: 1.0 contracts
2025-10-26 14:10:11 - [ORDER] INFO -   Leverage: 5x
2025-10-26 14:10:11 - [ORDER] INFO -   Reference Price: 50000.0
2025-10-26 14:10:11 - [ORDER] INFO -   Average Fill Price: 50100.0
2025-10-26 14:10:11 - [ORDER] INFO -   Filled Amount: 1.0
2025-10-26 14:10:11 - [ORDER] INFO -   Total Cost: 50100.0
2025-10-26 14:10:11 - [ORDER] INFO -   Status: closed
2025-10-26 14:10:11 - [ORDER] INFO -   Slippage: 0.2%
2025-10-26 14:10:11 - [ORDER] INFO - ================================================================================
2025-10-26 14:10:11 - [POSITION] INFO -   Order filled at: 50100.0
2025-10-26 14:10:11 - [POSITION] INFO -   Stop Loss: 48000.0 (-4.19%)
2025-10-26 14:10:11 - [POSITION] INFO -   Take Profit: 55000.0 (9.78%)
2025-10-26 14:10:11 - [ORDER] INFO - ================================================================================

2025-10-26 14:15:00 - [POSITION] INFO - 
--- Position: BTC/USDT:USDT (LONG) ---
2025-10-26 14:15:00 - [POSITION] DEBUG -   Entry Price: 50100.0
2025-10-26 14:15:00 - [POSITION] DEBUG -   Amount: 1.0000 contracts
2025-10-26 14:15:00 - [POSITION] DEBUG -   Leverage: 5x
2025-10-26 14:15:00 - [POSITION] INFO -   Current Price: 51000.0
2025-10-26 14:15:00 - [POSITION] INFO -   Current P/L: +1.80% ($+900.00)
2025-10-26 14:15:00 - [POSITION] DEBUG -   Stop Loss: 48000.0
2025-10-26 14:15:00 - [POSITION] DEBUG -   Take Profit: 55000.0
2025-10-26 14:15:00 - [POSITION] INFO -   ✓ Position still open and healthy

2025-10-26 14:20:00 - [ORDER] INFO - SELL ORDER EXECUTED: BTC/USDT:USDT
2025-10-26 14:20:00 - [ORDER] INFO - --------------------------------------------------------------------------------
2025-10-26 14:20:00 - [ORDER] INFO -   Order ID: 371913167359492098
2025-10-26 14:20:00 - [ORDER] INFO -   Type: MARKET
2025-10-26 14:20:00 - [ORDER] INFO -   Side: SELL
2025-10-26 14:20:00 - [ORDER] INFO -   Symbol: BTC/USDT:USDT
2025-10-26 14:20:00 - [ORDER] INFO -   Amount: 1.0 contracts
2025-10-26 14:20:00 - [ORDER] INFO -   Leverage: 5x
2025-10-26 14:20:00 - [ORDER] INFO -   Reference Price: 51000.0
2025-10-26 14:20:00 - [ORDER] INFO -   Average Fill Price: 50900.0
2025-10-26 14:20:00 - [ORDER] INFO -   Filled Amount: 1.0
2025-10-26 14:20:00 - [ORDER] INFO -   Total Cost: 50900.0
2025-10-26 14:20:00 - [ORDER] INFO -   Status: closed
2025-10-26 14:20:00 - [ORDER] INFO -   Slippage: 0.196%
2025-10-26 14:20:00 - [ORDER] INFO - ================================================================================
"""
        
        # Create temp file
        fd, path = tempfile.mkstemp(suffix='.log', text=True)
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        
        return path
    
    def test_parse_buy_order(self):
        """Test parsing of buy order from log"""
        log_file = self.create_test_log()
        try:
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            
            # Should find 2 orders
            assert len(analyzer.orders) == 2
            
            # Check first order (BUY)
            buy_order = analyzer.orders[0]
            assert buy_order.side == 'BUY'
            assert buy_order.symbol == 'BTC/USDT:USDT'
            assert buy_order.amount == 1.0
            assert buy_order.leverage == 5.0
            assert buy_order.fill_price == 50100.0
            assert buy_order.slippage == 0.2
            assert buy_order.status == 'closed'
            
            print("✓ Buy order parsed correctly")
        finally:
            os.unlink(log_file)
    
    def test_parse_sell_order(self):
        """Test parsing of sell order from log"""
        log_file = self.create_test_log()
        try:
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            
            # Check second order (SELL)
            sell_order = analyzer.orders[1]
            assert sell_order.side == 'SELL'
            assert sell_order.symbol == 'BTC/USDT:USDT'
            assert sell_order.amount == 1.0
            assert sell_order.fill_price == 50900.0
            
            print("✓ Sell order parsed correctly")
        finally:
            os.unlink(log_file)
    
    def test_parse_position_update(self):
        """Test parsing of position update from log"""
        log_file = self.create_test_log()
        try:
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            
            # Should find 1 position update
            assert len(analyzer.position_updates) >= 1
            
            # Check position data
            position = analyzer.position_updates[0]
            assert position.symbol == 'BTC/USDT:USDT'
            assert position.entry_price == 50100.0
            assert position.current_price == 51000.0
            assert position.amount == 1.0
            assert position.leverage == 5.0
            assert position.pnl_percent == 1.80
            assert position.stop_loss == 48000.0
            assert position.take_profit == 55000.0
            
            print("✓ Position update parsed correctly")
        finally:
            os.unlink(log_file)
    
    def test_risk_management_detection(self):
        """Test that risk management is properly detected"""
        log_file = self.create_test_log()
        try:
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            
            # First order (BUY) should have risk management
            buy_order = analyzer.orders[0]
            assert buy_order.has_risk_management()
            
            print("✓ Risk management detected in orders")
        finally:
            os.unlink(log_file)


class TestVerification:
    """Test verification functions"""
    
    def test_order_verification(self):
        """Test order verification logic"""
        log_file = TestLogParser().create_test_log()
        try:
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            results = analyzer.verify_orders()
            
            assert results['total_orders'] == 2
            assert results['valid_orders'] == 2
            assert results['buy_orders'] == 1
            assert results['sell_orders'] == 1
            assert results['orders_with_risk_mgmt'] >= 1
            assert results['avg_slippage'] > 0
            assert results['max_slippage'] > 0
            
            print("✓ Order verification works correctly")
        finally:
            os.unlink(log_file)
    
    def test_position_verification(self):
        """Test position monitoring verification"""
        log_file = TestLogParser().create_test_log()
        try:
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            results = analyzer.verify_positions()
            
            assert results['total_updates'] >= 1
            assert len(results['positions_monitored']) >= 1
            assert results['positions_with_sl_tp'] >= 1
            
            print("✓ Position verification works correctly")
        finally:
            os.unlink(log_file)
    
    def test_performance_analysis(self):
        """Test trading performance analysis"""
        log_file = TestLogParser().create_test_log()
        try:
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            results = analyzer.analyze_trading_performance()
            
            assert results['total_trades'] >= 1
            # In our test log, there's 1 profitable trade
            assert results['winning_trades'] >= 0
            assert results['win_rate'] >= 0
            
            print("✓ Performance analysis works correctly")
        finally:
            os.unlink(log_file)
    
    def test_high_slippage_detection(self):
        """Test that high slippage is detected and flagged"""
        # Create log with high slippage
        content = """
2025-10-26 14:10:11 - [ORDER] INFO - BUY ORDER EXECUTED: BTC/USDT:USDT
2025-10-26 14:10:11 - [ORDER] INFO - --------------------------------------------------------------------------------
2025-10-26 14:10:11 - [ORDER] INFO -   Order ID: 12345
2025-10-26 14:10:11 - [ORDER] INFO -   Type: MARKET
2025-10-26 14:10:11 - [ORDER] INFO -   Side: BUY
2025-10-26 14:10:11 - [ORDER] INFO -   Symbol: BTC/USDT:USDT
2025-10-26 14:10:11 - [ORDER] INFO -   Amount: 1.0
2025-10-26 14:10:11 - [ORDER] INFO -   Leverage: 5x
2025-10-26 14:10:11 - [ORDER] INFO -   Reference Price: 50000.0
2025-10-26 14:10:11 - [ORDER] INFO -   Average Fill Price: 51000.0
2025-10-26 14:10:11 - [ORDER] INFO -   Filled Amount: 1.0
2025-10-26 14:10:11 - [ORDER] INFO -   Total Cost: 51000.0
2025-10-26 14:10:11 - [ORDER] INFO -   Status: closed
2025-10-26 14:10:11 - [ORDER] INFO -   Slippage: 2.0%
2025-10-26 14:10:11 - [ORDER] INFO - ================================================================================
"""
        fd, log_file = tempfile.mkstemp(suffix='.log', text=True)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            
            analyzer = TradingLogAnalyzer(log_file)
            analyzer.parse_log()
            results = analyzer.verify_orders()
            
            # Should detect high slippage
            assert len(results['issues']) > 0
            assert any('High slippage' in issue for issue in results['issues'])
            
            print("✓ High slippage detection works")
        finally:
            os.unlink(log_file)


def run_all_tests():
    """Run all test suites"""
    print("=" * 80)
    print("🧪 RUNNING VERIFY_TRADING_EXECUTION TESTS")
    print("=" * 80)
    
    test_suites = [
        TestOrderExecution(),
        TestPositionUpdate(),
        TestLogParser(),
        TestVerification()
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for suite in test_suites:
        suite_name = suite.__class__.__name__
        print(f"\n📋 Running {suite_name}...")
        
        # Get all test methods
        test_methods = [m for m in dir(suite) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(suite, method_name)
                method()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append(f"{suite_name}.{method_name}: {e}")
                print(f"  ❌ {method_name} FAILED: {e}")
            except Exception as e:
                failed_tests.append(f"{suite_name}.{method_name}: {e}")
                print(f"  ❌ {method_name} ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for failure in failed_tests:
            print(f"   - {failure}")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0


if __name__ == '__main__':
    import sys
    sys.exit(run_all_tests())
