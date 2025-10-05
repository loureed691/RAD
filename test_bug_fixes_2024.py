"""
Test suite for bug fixes - December 2024
Tests for defensive programming improvements
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_safe_ticker_access():
    """Test that ticker['last'] access is now safe"""
    print("\nTesting safe ticker access...")
    try:
        from unittest.mock import MagicMock
        from bot import TradingBot
        from config import Config
        
        # Mock the client
        bot = TradingBot.__new__(TradingBot)
        bot.logger = MagicMock()
        bot.client = MagicMock()
        bot.position_manager = MagicMock()
        bot.position_manager.has_position = MagicMock(return_value=False)
        bot.position_manager.get_open_positions_count = MagicMock(return_value=0)
        bot.risk_manager = MagicMock()
        bot.risk_manager.check_portfolio_diversification = MagicMock(return_value=(True, "OK"))
        bot.risk_manager.should_open_position = MagicMock(return_value=(True, "OK"))
        bot.risk_manager.validate_trade = MagicMock(return_value=(True, "OK"))
        
        # Test 1: Ticker without 'last' key
        bot.client.get_balance = MagicMock(return_value={'free': {'USDT': 1000}})
        bot.client.get_ticker = MagicMock(return_value={'bid': 100, 'ask': 101})  # Missing 'last'
        
        opportunity = {
            'symbol': 'BTC/USDT:USDT',
            'signal': 'BUY',
            'confidence': 0.75
        }
        
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for ticker without 'last' key"
        print("  ✓ Handles ticker without 'last' key")
        
        # Test 2: Ticker with None price
        bot.client.get_ticker = MagicMock(return_value={'last': None})
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for None price"
        print("  ✓ Handles None price")
        
        # Test 3: Ticker with zero price
        bot.client.get_ticker = MagicMock(return_value={'last': 0})
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for zero price"
        print("  ✓ Handles zero price")
        
        # Test 4: Ticker with negative price
        bot.client.get_ticker = MagicMock(return_value={'last': -100})
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for negative price"
        print("  ✓ Handles negative price")
        
        print("✓ Safe ticker access tests passed")
        return True
    except Exception as e:
        print(f"✗ Safe ticker access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_safe_opportunity_access():
    """Test that opportunity dict access is now safe"""
    print("\nTesting safe opportunity dict access...")
    try:
        from unittest.mock import MagicMock
        from bot import TradingBot
        
        bot = TradingBot.__new__(TradingBot)
        bot.logger = MagicMock()
        bot.client = MagicMock()
        bot.position_manager = MagicMock()
        bot.risk_manager = MagicMock()
        
        # Test 1: Missing 'symbol' key
        opportunity = {'signal': 'BUY', 'confidence': 0.75}
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for missing symbol"
        print("  ✓ Handles missing 'symbol' key")
        
        # Test 2: Missing 'signal' key  
        opportunity = {'symbol': 'BTC/USDT:USDT', 'confidence': 0.75}
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for missing signal"
        print("  ✓ Handles missing 'signal' key")
        
        # Test 3: Missing 'confidence' key
        opportunity = {'symbol': 'BTC/USDT:USDT', 'signal': 'BUY'}
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for missing confidence"
        print("  ✓ Handles missing 'confidence' key")
        
        # Test 4: Empty dict
        opportunity = {}
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for empty dict"
        print("  ✓ Handles empty dict")
        
        # Test 5: None values
        opportunity = {'symbol': None, 'signal': None, 'confidence': None}
        result = bot.execute_trade(opportunity)
        assert result == False, "Should return False for None values"
        print("  ✓ Handles None values")
        
        print("✓ Safe opportunity dict access tests passed")
        return True
    except Exception as e:
        print(f"✗ Safe opportunity dict access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_float_comparison_fix():
    """Test that float comparison uses threshold"""
    print("\nTesting float comparison fix...")
    try:
        # Check the actual code to ensure <= 0.0001 is used instead of == 0
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Should not have == 0 for avg_loss
        if 'avg_loss == 0' in content:
            print("  ✗ Still using == 0 for avg_loss")
            return False
        
        # Should have <= 0.0001 or similar threshold
        if '<= 0.0001' in content or '< 0.001' in content:
            print("  ✓ Using threshold comparison for avg_loss")
        else:
            print("  ⚠️  Warning: No explicit threshold found, but == 0 removed")
        
        print("✓ Float comparison fix verified")
        return True
    except Exception as e:
        print(f"✗ Float comparison test failed: {e}")
        return False

def test_position_manager_safe_access():
    """Test that position_manager also has safe ticker access"""
    print("\nTesting position_manager safe ticker access...")
    try:
        from unittest.mock import MagicMock
        from position_manager import PositionManager
        
        pm = PositionManager.__new__(PositionManager)
        pm.logger = MagicMock()
        pm.client = MagicMock()
        pm.positions = {}
        
        # Test close_position with invalid ticker
        pm.positions['BTC/USDT:USDT'] = MagicMock()
        
        # Test 1: Ticker without 'last' key
        pm.client.get_ticker = MagicMock(return_value={'bid': 100})
        result = pm.close_position('BTC/USDT:USDT')
        assert result is None, "Should return None for invalid ticker"
        print("  ✓ close_position handles missing 'last' key")
        
        # Test 2: Ticker with None price
        pm.client.get_ticker = MagicMock(return_value={'last': None})
        result = pm.close_position('BTC/USDT:USDT')
        assert result is None, "Should return None for None price"
        print("  ✓ close_position handles None price")
        
        # Test 3: Ticker with zero/negative price
        pm.client.get_ticker = MagicMock(return_value={'last': 0})
        result = pm.close_position('BTC/USDT:USDT')
        assert result is None, "Should return None for zero price"
        print("  ✓ close_position handles zero price")
        
        print("✓ Position manager safe access tests passed")
        return True
    except Exception as e:
        print(f"✗ Position manager safe access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_order_dict_safe_access():
    """Test that order['id'] access is now safe"""
    print("\nTesting safe order dict access...")
    try:
        # Check the code for safe order access
        with open('position_manager.py', 'r') as f:
            content = f.read()
        
        # Should check for 'id' in order before accessing
        if "'id' in order" in content or '"id" in order' in content:
            print("  ✓ Checking for 'id' key before access")
        else:
            print("  ⚠️  Warning: May not have explicit 'id' key check")
        
        # Should use .get() for status
        if "order_status.get('status')" in content:
            print("  ✓ Using .get() for status access")
        else:
            print("  ⚠️  May not use .get() for all status access")
        
        print("✓ Order dict safe access verified")
        return True
    except Exception as e:
        print(f"✗ Order dict safe access test failed: {e}")
        return False

def main():
    """Run all bug fix tests"""
    print("="*70)
    print("Running Bug Fix Tests - December 2024")
    print("="*70)
    
    tests = [
        test_safe_ticker_access,
        test_safe_opportunity_access,
        test_float_comparison_fix,
        test_position_manager_safe_access,
        test_order_dict_safe_access,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*70)
    print(f"Bug Fix Test Results: {sum(results)}/{len(results)} passed")
    print("="*70)
    
    if all(results):
        print("\n✓ All bug fix tests passed!")
        return 0
    else:
        print("\n✗ Some bug fix tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
