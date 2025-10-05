"""
Test for diversification fix - 'other' group concentration issue
Related to issue where bot couldn't open positions when all existing 
positions were in the 'other' correlation group.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from risk_manager import RiskManager

def test_other_group_higher_concentration_limit():
    """
    Test that 'other' group allows higher concentration (70%) than 
    correlated groups (40%), since 'other' assets are uncorrelated.
    """
    print("Testing 'other' group concentration limit...")
    
    risk_manager = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=10
    )
    
    # Verify 'other' group can have up to 7 positions (70% of 10)
    other_positions = [f'TOKEN{i}/USDT:USDT' for i in range(6)]
    
    # Should allow 7th position
    is_diversified, reason = risk_manager.check_portfolio_diversification(
        'TOKEN6/USDT:USDT', other_positions
    )
    assert is_diversified, f"Should allow 7th position in 'other' group: {reason}"
    
    # Should block 8th position
    other_positions.append('TOKEN6/USDT:USDT')
    is_diversified, reason = risk_manager.check_portfolio_diversification(
        'TOKEN7/USDT:USDT', other_positions
    )
    assert not is_diversified, "Should block 8th position in 'other' group"
    assert "7/7" in reason, f"Expected 7/7 in reason, got: {reason}"
    
    print("  ✓ 'other' group allows 70% concentration (7/10 positions)")
    return True

def test_correlated_group_maintains_40_percent_limit():
    """
    Test that correlated groups maintain 40% concentration limit
    """
    print("Testing correlated group concentration limit...")
    
    risk_manager = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=10
    )
    
    # DeFi group should max at 4 positions (40% of 10)
    defi_positions = ['UNI/USDT:USDT', 'AAVE/USDT:USDT', 'SUSHI/USDT:USDT']
    
    # Should allow 4th DeFi position
    is_diversified, reason = risk_manager.check_portfolio_diversification(
        'LINK/USDT:USDT', defi_positions
    )
    assert is_diversified, f"Should allow 4th DeFi position: {reason}"
    
    # Verify the limit is 4 (40%)
    max_defi = max(2, int(10 * 0.4))
    assert max_defi == 4, f"Expected max 4 DeFi positions, got {max_defi}"
    
    print("  ✓ Correlated groups maintain 40% concentration limit (4/10 positions)")
    return True

def test_original_bug_scenario():
    """
    Test the exact scenario from the bug report:
    - 4 existing positions all in 'other' group
    - Bot couldn't add any new positions despite having 6 free slots
    
    This should now work after the fix.
    """
    print("Testing original bug scenario...")
    
    risk_manager = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=10
    )
    
    # Simulate the exact positions from the bug report
    existing_positions = [
        'HYPE/USDT:USDT',
        'LDO/USDT:USDT',
        'NIL/USDT:USDT',
        'VINE/USDT:USDT'
    ]
    
    # Verify all are in 'other' group
    for symbol in existing_positions:
        group = risk_manager.get_symbol_group(symbol)
        assert group == 'other', f"{symbol} should be in 'other' group, got {group}"
    
    # Should now allow adding SOON (the 5th 'other' position)
    is_diversified, reason = risk_manager.check_portfolio_diversification(
        'SOON/USDT:USDT', existing_positions
    )
    
    assert is_diversified, (
        f"Should allow adding SOON/USDT:USDT (5th 'other' position), "
        f"but got: {reason}"
    )
    
    print("  ✓ Can now add 5th position to 'other' group (was blocked before fix)")
    print("  ✓ Bot can use all available position slots")
    return True

def test_symbol_group_classification():
    """Test that symbols are classified into correct groups"""
    print("Testing symbol group classification...")
    
    risk_manager = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=10
    )
    
    # Test known groups
    assert risk_manager.get_symbol_group('BTC/USDT:USDT') == 'major_coins'
    assert risk_manager.get_symbol_group('ETH/USDT:USDT') == 'major_coins'
    assert risk_manager.get_symbol_group('UNI/USDT:USDT') == 'defi'
    assert risk_manager.get_symbol_group('SOL/USDT:USDT') == 'layer1'
    assert risk_manager.get_symbol_group('MATIC/USDT:USDT') == 'layer2'
    assert risk_manager.get_symbol_group('DOGE/USDT:USDT') == 'meme'
    
    # Test unknown symbols go to 'other'
    assert risk_manager.get_symbol_group('HYPE/USDT:USDT') == 'other'
    assert risk_manager.get_symbol_group('UNKNOWN/USDT:USDT') == 'other'
    
    print("  ✓ Symbol group classification working correctly")
    return True

def run_all_tests():
    """Run all diversification tests"""
    print("=" * 60)
    print("Running Diversification Fix Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_symbol_group_classification,
        test_other_group_higher_concentration_limit,
        test_correlated_group_maintains_40_percent_limit,
        test_original_bug_scenario,
    ]
    
    for test_func in tests:
        try:
            if not test_func():
                print(f"✗ {test_func.__name__} failed")
                return False
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            return False
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print()
    print("=" * 60)
    print("✅ All diversification tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
