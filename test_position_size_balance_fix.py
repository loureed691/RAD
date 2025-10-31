#!/usr/bin/env python3
"""
Test the position size balance fix
Demonstrates that position sizes now respect available balance
"""
import sys
import os

# Mock logger to avoid dependencies
class MockLogger:
    def debug(self, msg): 
        pass
    def warning(self, msg): 
        print(f"  WARNING: {msg}")
    def error(self, msg): 
        print(f"  ERROR: {msg}")
    def info(self, msg): 
        pass

# Create mock modules to avoid import errors
sys.modules['joblib'] = type(sys)('joblib')
sys.modules['logger'] = type(sys)('logger')
sys.modules['logger'].Logger = type('Logger', (), {'get_logger': lambda: MockLogger()})()

from risk_manager import RiskManager

def test_position_size_with_balance_constraint():
    """Test that position size respects available balance"""
    print("\n" + "="*70)
    print("TEST: Position Size Respects Available Balance")
    print("="*70)
    
    # Create risk manager with realistic settings
    risk_manager = RiskManager(
        max_position_size=1000,  # Could be set high by user
        risk_per_trade=0.02,     # 2% risk
        max_open_positions=5
    )
    
    # Test Case 1: Normal scenario
    print("\nTest Case 1: $100 balance, 5% stop loss, 10x leverage")
    print("-"*70)
    balance = 100
    entry_price = 50000
    stop_loss_price = entry_price * 0.95  # 5% stop
    leverage = 10
    
    position_size = risk_manager.calculate_position_size(
        balance, entry_price, stop_loss_price, leverage
    )
    
    position_value = position_size * entry_price
    required_margin = position_value / leverage
    
    print(f"Input:")
    print(f"  Balance: ${balance}")
    print(f"  Entry price: ${entry_price}")
    print(f"  Stop loss: ${stop_loss_price} ({((entry_price - stop_loss_price)/entry_price)*100:.1f}%)")
    print(f"  Leverage: {leverage}x")
    print(f"Output:")
    print(f"  Position size: {position_size:.6f} contracts")
    print(f"  Position value: ${position_value:.2f}")
    print(f"  Required margin: ${required_margin:.2f}")
    print(f"  Usable balance (90%): ${balance * 0.90:.2f}")
    print(f"  Margin fits: {required_margin <= balance * 0.90}")
    
    assert required_margin <= balance * 0.90, "Required margin exceeds usable balance!"
    assert position_value <= balance * 0.90 * leverage, "Position value exceeds affordable!"
    print("✓ PASSED")
    
    # Test Case 2: Tight stop loss (would create large position without fix)
    print("\nTest Case 2: $100 balance, 1% stop loss (tight), 10x leverage")
    print("-"*70)
    stop_loss_tight = entry_price * 0.99  # Very tight 1% stop
    
    position_size = risk_manager.calculate_position_size(
        balance, entry_price, stop_loss_tight, leverage
    )
    
    position_value = position_size * entry_price
    required_margin = position_value / leverage
    
    print(f"Input:")
    print(f"  Balance: ${balance}")
    print(f"  Entry price: ${entry_price}")
    print(f"  Stop loss: ${stop_loss_tight} ({((entry_price - stop_loss_tight)/entry_price)*100:.1f}%)")
    print(f"  Leverage: {leverage}x")
    print(f"  Risk per trade: 2%")
    print(f"  Calculated risk amount: ${balance * 0.02:.2f}")
    print(f"  Without fix, position value would be: ${(balance * 0.02) / 0.01:.2f}")
    print(f"Output:")
    print(f"  Position size: {position_size:.6f} contracts")
    print(f"  Position value: ${position_value:.2f}")
    print(f"  Required margin: ${required_margin:.2f}")
    print(f"  Usable balance (90%): ${balance * 0.90:.2f}")
    print(f"  Margin fits: {required_margin <= balance * 0.90}")
    
    assert required_margin <= balance * 0.90, "Required margin exceeds usable balance!"
    assert position_value <= balance * 0.90 * leverage, "Position value exceeds affordable!"
    print("✓ PASSED - Position was capped at affordable size")
    
    # Test Case 3: Small balance
    print("\nTest Case 3: $10 balance, 5% stop loss, 10x leverage")
    print("-"*70)
    small_balance = 10
    
    position_size = risk_manager.calculate_position_size(
        small_balance, entry_price, stop_loss_price, leverage
    )
    
    position_value = position_size * entry_price
    required_margin = position_value / leverage
    
    print(f"Input:")
    print(f"  Balance: ${small_balance}")
    print(f"  Entry price: ${entry_price}")
    print(f"  Stop loss: ${stop_loss_price} ({((entry_price - stop_loss_price)/entry_price)*100:.1f}%)")
    print(f"  Leverage: {leverage}x")
    print(f"Output:")
    print(f"  Position size: {position_size:.6f} contracts")
    print(f"  Position value: ${position_value:.2f}")
    print(f"  Required margin: ${required_margin:.2f}")
    print(f"  Usable balance (90%): ${small_balance * 0.90:.2f}")
    print(f"  Margin fits: {required_margin <= small_balance * 0.90}")
    
    assert required_margin <= small_balance * 0.90, "Required margin exceeds usable balance!"
    assert position_value <= small_balance * 0.90 * leverage, "Position value exceeds affordable!"
    print("✓ PASSED")
    
    # Test Case 4: MAX_POSITION_SIZE set very high (before fix, this would cause issues)
    print("\nTest Case 4: $50 balance, MAX_POSITION_SIZE=$10000, 5% stop, 10x leverage")
    print("-"*70)
    risk_manager_high = RiskManager(
        max_position_size=10000,  # Unrealistically high
        risk_per_trade=0.02,
        max_open_positions=5
    )
    
    med_balance = 50
    position_size = risk_manager_high.calculate_position_size(
        med_balance, entry_price, stop_loss_price, leverage
    )
    
    position_value = position_size * entry_price
    required_margin = position_value / leverage
    
    print(f"Input:")
    print(f"  Balance: ${med_balance}")
    print(f"  MAX_POSITION_SIZE: ${risk_manager_high.max_position_size}")
    print(f"  Entry price: ${entry_price}")
    print(f"  Stop loss: ${stop_loss_price} ({((entry_price - stop_loss_price)/entry_price)*100:.1f}%)")
    print(f"  Leverage: {leverage}x")
    print(f"Output:")
    print(f"  Position size: {position_size:.6f} contracts")
    print(f"  Position value: ${position_value:.2f}")
    print(f"  Required margin: ${required_margin:.2f}")
    print(f"  Usable balance (90%): ${med_balance * 0.90:.2f}")
    print(f"  Max affordable position: ${med_balance * 0.90 * leverage:.2f}")
    print(f"  Margin fits: {required_margin <= med_balance * 0.90}")
    
    assert required_margin <= med_balance * 0.90, "Required margin exceeds usable balance!"
    assert position_value <= med_balance * 0.90 * leverage, "Position value exceeds affordable!"
    print("✓ PASSED - High MAX_POSITION_SIZE doesn't cause problems")
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✓")
    print("="*70)
    print("\nSummary:")
    print("The fix ensures that position sizes NEVER exceed what's affordable")
    print("with the available balance, regardless of:")
    print("  • MAX_POSITION_SIZE configuration")
    print("  • Stop loss distance")
    print("  • Leverage used")
    print("\nThe bot will now calculate position sizes based on:")
    print("  1. Risk management (2% risk per trade)")
    print("  2. Stop loss distance")
    print("  3. MAX_POSITION_SIZE cap")
    print("  4. ✓ NEW: Available balance constraint")
    print("\nThis prevents the bot from attempting to open positions")
    print("that require more margin than available.")

if __name__ == '__main__':
    test_position_size_with_balance_constraint()
