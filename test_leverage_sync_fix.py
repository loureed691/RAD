"""
Test for leverage sync bug fix

Tests that positions are synced with correct leverage, not hardcoded 10x
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_leverage_sync_with_ccxt_unified():
    """Test that leverage is correctly read from CCXT unified structure"""
    print("\n" + "="*60)
    print("TEST 1: Leverage sync with CCXT unified structure")
    print("="*60)
    
    try:
        from position_manager import PositionManager
        
        # Create mock client
        mock_client = Mock()
        
        # Mock position data with leverage in unified structure (CCXT standard)
        mock_client.get_open_positions = Mock(return_value=[
            {
                'symbol': 'BTC/USDT:USDT',
                'contracts': 1.0,
                'side': 'long',
                'entryPrice': 50000.0,
                'leverage': 5,  # 5x leverage, NOT 10x
                'info': {}
            }
        ])
        mock_client.get_ticker = Mock(return_value={'last': 51000.0})
        
        # Create position manager
        pm = PositionManager(mock_client)
        
        # Sync positions
        synced = pm.sync_existing_positions()
        
        # Verify position was synced
        assert synced == 1, f"Expected 1 position synced, got {synced}"
        assert 'BTC/USDT:USDT' in pm.positions, "Position not found"
        
        position = pm.positions['BTC/USDT:USDT']
        
        # Check that leverage is 5x, NOT 10x
        print(f"Synced position leverage: {position.leverage}x")
        assert position.leverage == 5, f"Expected 5x leverage, got {position.leverage}x"
        
        # Verify P/L calculation uses correct leverage
        pnl = position.get_pnl(51000.0)  # 2% price increase
        expected_pnl = 0.02 * 5  # 2% * 5x = 10% ROI
        print(f"P/L with 2% price increase: {pnl:.2%} (expected {expected_pnl:.2%})")
        assert abs(pnl - expected_pnl) < 0.001, f"P/L incorrect: expected {expected_pnl:.2%}, got {pnl:.2%}"
        
        print("✓ TEST 1 PASSED: Leverage correctly synced from unified structure")
        return True
        
    except Exception as e:
        print(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_leverage_sync_with_realLeverage():
    """Test that leverage is correctly read from KuCoin's 'realLeverage' field"""
    print("\n" + "="*60)
    print("TEST 2: Leverage sync with KuCoin 'realLeverage' field")
    print("="*60)
    
    try:
        from position_manager import PositionManager
        
        # Create mock client
        mock_client = Mock()
        
        # Mock position data with leverage in 'info' dict (KuCoin raw format)
        mock_client.get_open_positions = Mock(return_value=[
            {
                'symbol': 'ETH/USDT:USDT',
                'contracts': 10.0,
                'side': 'short',
                'entryPrice': 3000.0,
                # No 'leverage' in unified structure
                'info': {
                    'realLeverage': 20  # 20x leverage from KuCoin API
                }
            }
        ])
        mock_client.get_ticker = Mock(return_value={'last': 2900.0})
        
        # Create position manager
        pm = PositionManager(mock_client)
        
        # Sync positions
        synced = pm.sync_existing_positions()
        
        # Verify position was synced
        assert synced == 1, f"Expected 1 position synced, got {synced}"
        assert 'ETH/USDT:USDT' in pm.positions, "Position not found"
        
        position = pm.positions['ETH/USDT:USDT']
        
        # Check that leverage is 20x, NOT 10x
        print(f"Synced position leverage: {position.leverage}x")
        assert position.leverage == 20, f"Expected 20x leverage, got {position.leverage}x"
        
        # Verify P/L calculation uses correct leverage
        pnl = position.get_pnl(2900.0)  # 3.33% price decrease = profit for short
        expected_pnl = ((3000.0 - 2900.0) / 3000.0) * 20  # ~0.667 = 66.7% ROI
        print(f"P/L with 3.33% price decrease: {pnl:.2%} (expected {expected_pnl:.2%})")
        assert abs(pnl - expected_pnl) < 0.001, f"P/L incorrect: expected {expected_pnl:.2%}, got {pnl:.2%}"
        
        print("✓ TEST 2 PASSED: Leverage correctly synced from KuCoin 'realLeverage'")
        return True
        
    except Exception as e:
        print(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_leverage_sync_missing_defaults_to_10():
    """Test that leverage defaults to 10x when not available, with warning"""
    print("\n" + "="*60)
    print("TEST 3: Leverage defaults to 10x with warning when missing")
    print("="*60)
    
    try:
        from position_manager import PositionManager
        
        # Create mock client
        mock_client = Mock()
        
        # Mock position data WITHOUT any leverage information
        mock_client.get_open_positions = Mock(return_value=[
            {
                'symbol': 'SOL/USDT:USDT',
                'contracts': 100.0,
                'side': 'long',
                'entryPrice': 100.0,
                # No 'leverage' field
                'info': {}  # No 'realLeverage' either
            }
        ])
        mock_client.get_ticker = Mock(return_value={'last': 105.0})
        
        # Create position manager
        pm = PositionManager(mock_client)
        
        # Sync positions (should log warning)
        synced = pm.sync_existing_positions()
        
        # Verify position was synced
        assert synced == 1, f"Expected 1 position synced, got {synced}"
        assert 'SOL/USDT:USDT' in pm.positions, "Position not found"
        
        position = pm.positions['SOL/USDT:USDT']
        
        # Check that leverage defaults to 10x
        print(f"Synced position leverage (default): {position.leverage}x")
        assert position.leverage == 10, f"Expected default 10x leverage, got {position.leverage}x"
        
        print("✓ TEST 3 PASSED: Leverage defaults to 10x when missing (expected behavior)")
        print("  Note: Should log a warning in production")
        return True
        
    except Exception as e:
        print(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_positions_different_leverages():
    """Test syncing multiple positions with different leverages"""
    print("\n" + "="*60)
    print("TEST 4: Multiple positions with different leverages")
    print("="*60)
    
    try:
        from position_manager import PositionManager
        
        # Create mock client
        mock_client = Mock()
        
        # Mock multiple positions with different leverages
        mock_client.get_open_positions = Mock(return_value=[
            {
                'symbol': 'BTC/USDT:USDT',
                'contracts': 1.0,
                'side': 'long',
                'entryPrice': 50000.0,
                'leverage': 3,  # Conservative 3x
                'info': {}
            },
            {
                'symbol': 'ETH/USDT:USDT',
                'contracts': 10.0,
                'side': 'short',
                'entryPrice': 3000.0,
                'leverage': 15,  # Aggressive 15x
                'info': {}
            },
            {
                'symbol': 'SOL/USDT:USDT',
                'contracts': 100.0,
                'side': 'long',
                'entryPrice': 100.0,
                'info': {
                    'realLeverage': 7  # From raw API
                }
            }
        ])
        
        # Mock tickers
        def get_ticker_mock(symbol):
            tickers = {
                'BTC/USDT:USDT': {'last': 51000.0},
                'ETH/USDT:USDT': {'last': 2850.0},
                'SOL/USDT:USDT': {'last': 105.0}
            }
            return tickers.get(symbol, {'last': 100.0})
        
        mock_client.get_ticker = get_ticker_mock
        
        # Create position manager
        pm = PositionManager(mock_client)
        
        # Sync positions
        synced = pm.sync_existing_positions()
        
        # Verify all positions were synced
        assert synced == 3, f"Expected 3 positions synced, got {synced}"
        
        # Check BTC position (3x leverage)
        btc_pos = pm.positions['BTC/USDT:USDT']
        assert btc_pos.leverage == 3, f"BTC leverage should be 3x, got {btc_pos.leverage}x"
        btc_pnl = btc_pos.get_pnl(51000.0)  # 2% gain * 3x = 6%
        expected_btc_pnl = 0.02 * 3
        assert abs(btc_pnl - expected_btc_pnl) < 0.001, f"BTC P/L incorrect"
        print(f"✓ BTC: 3x leverage, P/L = {btc_pnl:.2%}")
        
        # Check ETH position (15x leverage)
        eth_pos = pm.positions['ETH/USDT:USDT']
        assert eth_pos.leverage == 15, f"ETH leverage should be 15x, got {eth_pos.leverage}x"
        eth_pnl = eth_pos.get_pnl(2850.0)  # 5% gain for short * 15x = 75%
        expected_eth_pnl = 0.05 * 15
        assert abs(eth_pnl - expected_eth_pnl) < 0.001, f"ETH P/L incorrect"
        print(f"✓ ETH: 15x leverage, P/L = {eth_pnl:.2%}")
        
        # Check SOL position (7x leverage from realLeverage)
        sol_pos = pm.positions['SOL/USDT:USDT']
        assert sol_pos.leverage == 7, f"SOL leverage should be 7x, got {sol_pos.leverage}x"
        sol_pnl = sol_pos.get_pnl(105.0)  # 5% gain * 7x = 35%
        expected_sol_pnl = 0.05 * 7
        assert abs(sol_pnl - expected_sol_pnl) < 0.001, f"SOL P/L incorrect"
        print(f"✓ SOL: 7x leverage, P/L = {sol_pnl:.2%}")
        
        print("\n✓ TEST 4 PASSED: Multiple positions synced with correct leverages")
        return True
        
    except Exception as e:
        print(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("LEVERAGE SYNC BUG FIX TESTS")
    print("="*60)
    
    tests = [
        test_leverage_sync_with_ccxt_unified,
        test_leverage_sync_with_realLeverage,
        test_leverage_sync_missing_defaults_to_10,
        test_multiple_positions_different_leverages
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
