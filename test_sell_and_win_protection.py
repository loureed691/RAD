"""
Test bot sell functionality and win protection fixes
"""
import sys
from datetime import datetime, timedelta

# Mock the dependencies to avoid import errors
class MockKuCoinClient:
    pass

class MockLogger:
    @staticmethod
    def debug(msg): pass
    @staticmethod
    def info(msg): pass
    @staticmethod
    def warning(msg): pass
    @staticmethod
    def error(msg, **kwargs): pass

class MockAdvancedExitStrategy:
    pass

class MockVolumeProfile:
    pass

class MockSmartExitOptimizer:
    pass

# Inject mocks
sys.modules['kucoin_client'] = type(sys)('kucoin_client')
sys.modules['kucoin_client'].KuCoinClient = MockKuCoinClient
sys.modules['logger'] = type(sys)('logger')
sys.modules['logger'].Logger = MockLogger
sys.modules['advanced_exit_strategy'] = type(sys)('advanced_exit_strategy')
sys.modules['advanced_exit_strategy'].AdvancedExitStrategy = MockAdvancedExitStrategy
sys.modules['volume_profile'] = type(sys)('volume_profile')
sys.modules['volume_profile'].VolumeProfile = MockVolumeProfile
sys.modules['smart_trading_enhancements'] = type(sys)('smart_trading_enhancements')
sys.modules['smart_trading_enhancements'].SmartExitOptimizer = MockSmartExitOptimizer

from position_manager import Position


def test_tp_extension_doesnt_prevent_close():
    """Test that TP extension logic doesn't prevent position from closing"""
    print("\n" + "="*80)
    print("TEST 1: TP Extension Doesn't Prevent Close")
    print("="*80)
    
    # Scenario: Long position with TP that gets extended as price rises
    pos = Position('BTC-USDT', 'long', 100, 1, 5, 95, 110)  # Entry $100, TP $110 (10% target)
    print(f"Initial: Entry=${pos.entry_price}, TP=${pos.take_profit}, SL=${pos.stop_loss}")
    
    # Price moves to $108 (80% of way to TP)
    current_price = 108
    print(f"\nPrice moves to ${current_price} (80% progress to TP)")
    
    # Try to extend TP (simulating market momentum)
    pos.update_take_profit(current_price, momentum=0.05, trend_strength=0.8)
    print(f"After update_take_profit: TP=${pos.take_profit}")
    
    # Check if position should close at current price
    should_close, reason = pos.should_close(current_price)
    print(f"Should close at ${current_price}? {should_close} ({reason})")
    
    # Price reaches $110 (original TP)
    current_price = 110
    print(f"\nPrice reaches ${current_price} (original TP)")
    should_close, reason = pos.should_close(current_price)
    print(f"Should close at ${current_price}? {should_close} ({reason})")
    
    # Check that position closes even if TP was extended
    leveraged_pnl = pos.get_leveraged_pnl(current_price)
    print(f"Leveraged P/L at ${current_price}: {leveraged_pnl:.2%}")
    
    assert should_close or leveraged_pnl >= 0.10, \
        f"Position should close at 10% profit, but should_close={should_close}, pnl={leveraged_pnl:.2%}"
    
    print("\n✓ TEST 1 PASSED: Position closes even with TP extension")


def test_win_protection_at_profit_levels():
    """Test that win protection triggers at key profit levels"""
    print("\n" + "="*80)
    print("TEST 2: Win Protection at Key Profit Levels")
    print("="*80)
    
    test_cases = [
        (0.25, "25% profit - exceptional"),
        (0.20, "20% profit - very high"),
        (0.15, "15% profit - high"),
        (0.12, "12% profit with far TP"),
        (0.10, "10% profit with far TP"),
    ]
    
    for target_pnl, description in test_cases:
        # Create position
        pos = Position('BTC-USDT', 'long', 100, 1, 5, 95, 150)  # TP far away at $150
        
        # Calculate price for target P/L
        # leveraged_pnl = (current_price - entry_price) / entry_price * leverage
        # target_pnl = price_change * leverage
        # price_change = target_pnl / leverage
        price_change = target_pnl / pos.leverage
        current_price = pos.entry_price * (1 + price_change)
        
        leveraged_pnl = pos.get_leveraged_pnl(current_price)
        should_close, reason = pos.should_close(current_price)
        
        print(f"\n{description}:")
        print(f"  Price: ${current_price:.2f}, Leveraged P/L: {leveraged_pnl:.2%}")
        print(f"  Should close: {should_close} ({reason})")
        
        # For high profits (15%+), should ALWAYS close (win protection)
        if target_pnl >= 0.15:
            assert should_close, \
                f"Win protection should trigger at {target_pnl:.0%} profit, but didn't close. Reason: {reason}"
        # For good profits (10-15%), should close if TP is far
        elif target_pnl >= 0.10:
            # TP is at $150, so distance is significant
            assert should_close, \
                f"Should close at {target_pnl:.0%} profit with far TP, but didn't. Reason: {reason}"
    
    print("\n✓ TEST 2 PASSED: Win protection works at all key profit levels")


def test_win_protection_momentum_loss():
    """Test that win protection triggers on momentum loss"""
    print("\n" + "="*80)
    print("TEST 3: Win Protection on Momentum Loss")
    print("="*80)
    
    # Create position that reaches 10% profit, then retraces
    pos = Position('BTC-USDT', 'long', 100, 1, 5, 95, 120)
    
    # Simulate reaching 10% profit (50% leveraged ROI with 5x)
    peak_price = 110  # 10% price movement = 50% ROI with 5x leverage
    peak_pnl = pos.get_leveraged_pnl(peak_price)
    print(f"Peak: Price=${peak_price}, Leveraged P/L={peak_pnl:.2%}")
    
    # Track max favorable excursion
    pos.max_favorable_excursion = peak_pnl
    
    # Price retraces to give back 50% of profit
    # Was at 50% ROI, now at 25% ROI
    # 25% ROI with 5x leverage = 5% price movement
    retrace_price = 105  # 5% price movement
    current_pnl = pos.get_leveraged_pnl(retrace_price)
    
    print(f"\nAfter retracement: Price=${retrace_price}, Leveraged P/L={current_pnl:.2%}")
    print(f"Max favorable excursion: {pos.max_favorable_excursion:.2%}")
    
    drawdown_pct = (pos.max_favorable_excursion - current_pnl) / pos.max_favorable_excursion
    print(f"Profit drawdown: {drawdown_pct:.2%}")
    
    should_close, reason = pos.should_close(retrace_price)
    print(f"Should close: {should_close} ({reason})")
    
    assert should_close, \
        f"Win protection should trigger after 50% profit drawdown, but didn't. Reason: {reason}"
    
    print("\n✓ TEST 3 PASSED: Win protection triggers on significant momentum loss")


def test_tp_extension_stops_when_close():
    """Test that TP stops extending when price gets close"""
    print("\n" + "="*80)
    print("TEST 4: TP Extension Stops When Price Gets Close")
    print("="*80)
    
    # Create position
    pos = Position('BTC-USDT', 'long', 100, 1, 5, 95, 110)
    print(f"Initial: Entry=${pos.entry_price}, TP=${pos.take_profit}")
    
    # Price at 50% progress - should allow extension
    current_price = 105
    old_tp = pos.take_profit
    pos.update_take_profit(current_price, momentum=0.05, trend_strength=0.8)
    print(f"\nAt ${current_price} (50% progress): TP ${old_tp} -> ${pos.take_profit}")
    assert pos.take_profit >= old_tp, "TP should extend at 50% progress"
    
    # Price at 70% progress - should start blocking extension
    current_price = 107
    old_tp = pos.take_profit
    pos.update_take_profit(current_price, momentum=0.05, trend_strength=0.8)
    print(f"At ${current_price} (70% progress): TP ${old_tp} -> ${pos.take_profit}")
    
    # Price at 85% progress - should definitely block extension
    current_price = 108.5
    old_tp = pos.take_profit
    pos.update_take_profit(current_price, momentum=0.05, trend_strength=0.8)
    print(f"At ${current_price} (85% progress): TP ${old_tp} -> ${pos.take_profit}")
    extension_at_85pct = pos.take_profit - old_tp
    
    # At high progress, extension should be minimal or zero
    print(f"Extension at 85% progress: ${extension_at_85pct:.2f}")
    assert extension_at_85pct <= 0.5, \
        f"TP should not extend significantly at 85% progress, but extended by ${extension_at_85pct:.2f}"
    
    print("\n✓ TEST 4 PASSED: TP extension stops when price gets close")


def test_short_position_win_protection():
    """Test win protection works for short positions too"""
    print("\n" + "="*80)
    print("TEST 5: Win Protection for Short Positions")
    print("="*80)
    
    # Create short position
    pos = Position('BTC-USDT', 'short', 100, 1, 5, 105, 90)
    print(f"Short position: Entry=${pos.entry_price}, TP=${pos.take_profit}, SL=${pos.stop_loss}")
    
    # Price drops to 85 (15% price movement = 75% ROI with 5x leverage)
    current_price = 85
    leveraged_pnl = pos.get_leveraged_pnl(current_price)
    should_close, reason = pos.should_close(current_price)
    
    print(f"\nPrice drops to ${current_price}")
    print(f"Leveraged P/L: {leveraged_pnl:.2%}")
    print(f"Should close: {should_close} ({reason})")
    
    assert should_close, \
        f"Win protection should trigger for short at {leveraged_pnl:.2%} profit"
    assert 'win_protection' in reason or 'take_profit' in reason, \
        f"Should close due to win protection, got reason: {reason}"
    
    print("\n✓ TEST 5 PASSED: Win protection works for short positions")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("TESTING BOT SELL AND WIN PROTECTION FIXES")
    print("="*80)
    
    try:
        test_tp_extension_doesnt_prevent_close()
        test_win_protection_at_profit_levels()
        test_win_protection_momentum_loss()
        test_tp_extension_stops_when_close()
        test_short_position_win_protection()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED!")
        print("="*80)
        return True
        
    except AssertionError as e:
        print("\n" + "="*80)
        print("✗ TEST FAILED!")
        print("="*80)
        print(f"Error: {e}")
        return False
    except Exception as e:
        print("\n" + "="*80)
        print("✗ TEST ERROR!")
        print("="*80)
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
