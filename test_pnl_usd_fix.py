"""
Test to verify P/L USD calculation is correct
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from position_manager import Position

def test_pnl_usd_calculation():
    """Test that P/L USD is calculated correctly"""
    print("\n" + "="*70)
    print("TESTING P/L USD CALCULATION FIX")
    print("="*70)
    
    # Test Case 1: LONG position with profit
    print("\n--- Test 1: LONG Position with 5% Price Gain ---")
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=100.0,
        amount=1.0,  # 1 contract
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    current_price = 105.0  # 5% price gain
    pnl_percent = position.get_pnl(current_price)
    position_value = position.amount * position.entry_price
    
    # Correct calculation: P/L% already includes leverage
    # Price gain: 5% -> with 10x leverage = 50% P/L
    # USD P/L: 50% * $100 position value = $50
    pnl_usd = pnl_percent * position_value
    
    print(f"  Entry Price: ${position.entry_price}")
    print(f"  Exit Price: ${current_price}")
    print(f"  Position Size: {position.amount} contracts")
    print(f"  Position Value: ${position_value}")
    print(f"  Leverage: {position.leverage}x")
    print(f"  Price Change: {((current_price - position.entry_price) / position.entry_price) * 100:.1f}%")
    print(f"  P/L Percentage: {pnl_percent * 100:.1f}%")
    print(f"  P/L USD: ${pnl_usd:.2f}")
    print(f"  Expected USD P/L: $50.00")
    
    assert abs(pnl_percent - 0.50) < 0.01, f"Expected 50% P/L, got {pnl_percent*100:.1f}%"
    assert abs(pnl_usd - 50.0) < 0.01, f"Expected $50 USD P/L, got ${pnl_usd:.2f}"
    print("  ✓ PASSED")
    
    # Test Case 2: SHORT position with profit
    print("\n--- Test 2: SHORT Position with 5% Price Drop ---")
    position = Position(
        symbol='ETH/USDT:USDT',
        side='short',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=105.0,
        take_profit=90.0
    )
    
    current_price = 95.0  # 5% price drop
    pnl_percent = position.get_pnl(current_price)
    position_value = position.amount * position.entry_price
    pnl_usd = pnl_percent * position_value
    
    print(f"  Entry Price: ${position.entry_price}")
    print(f"  Exit Price: ${current_price}")
    print(f"  Position Size: {position.amount} contracts")
    print(f"  Position Value: ${position_value}")
    print(f"  Leverage: {position.leverage}x")
    print(f"  Price Change: {((current_price - position.entry_price) / position.entry_price) * 100:.1f}%")
    print(f"  P/L Percentage: {pnl_percent * 100:.1f}%")
    print(f"  P/L USD: ${pnl_usd:.2f}")
    print(f"  Expected USD P/L: $50.00")
    
    assert abs(pnl_percent - 0.50) < 0.01, f"Expected 50% P/L, got {pnl_percent*100:.1f}%"
    assert abs(pnl_usd - 50.0) < 0.01, f"Expected $50 USD P/L, got ${pnl_usd:.2f}"
    print("  ✓ PASSED")
    
    # Test Case 3: LONG position with loss
    print("\n--- Test 3: LONG Position with 3% Price Drop ---")
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=100.0,
        amount=2.0,  # 2 contracts
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    current_price = 97.0  # 3% price drop
    pnl_percent = position.get_pnl(current_price)
    position_value = position.amount * position.entry_price
    pnl_usd = pnl_percent * position_value
    
    print(f"  Entry Price: ${position.entry_price}")
    print(f"  Exit Price: ${current_price}")
    print(f"  Position Size: {position.amount} contracts")
    print(f"  Position Value: ${position_value}")
    print(f"  Leverage: {position.leverage}x")
    print(f"  Price Change: {((current_price - position.entry_price) / position.entry_price) * 100:.1f}%")
    print(f"  P/L Percentage: {pnl_percent * 100:.1f}%")
    print(f"  P/L USD: ${pnl_usd:.2f}")
    print(f"  Expected USD P/L: -$60.00")
    
    # -3% price * 10x leverage = -30% P/L
    # -30% * $200 position value = -$60
    assert abs(pnl_percent - (-0.30)) < 0.01, f"Expected -30% P/L, got {pnl_percent*100:.1f}%"
    assert abs(pnl_usd - (-60.0)) < 0.01, f"Expected -$60 USD P/L, got ${pnl_usd:.2f}"
    print("  ✓ PASSED")
    
    # Test Case 4: Different leverage
    print("\n--- Test 4: LONG Position with 20x Leverage ---")
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=50000.0,
        amount=0.01,  # 0.01 contracts
        leverage=20,
        stop_loss=49000.0,
        take_profit=52000.0
    )
    
    current_price = 51000.0  # 2% price gain
    pnl_percent = position.get_pnl(current_price)
    position_value = position.amount * position.entry_price
    pnl_usd = pnl_percent * position_value
    
    print(f"  Entry Price: ${position.entry_price}")
    print(f"  Exit Price: ${current_price}")
    print(f"  Position Size: {position.amount} contracts")
    print(f"  Position Value: ${position_value}")
    print(f"  Leverage: {position.leverage}x")
    print(f"  Price Change: {((current_price - position.entry_price) / position.entry_price) * 100:.1f}%")
    print(f"  P/L Percentage: {pnl_percent * 100:.1f}%")
    print(f"  P/L USD: ${pnl_usd:.2f}")
    print(f"  Expected USD P/L: $200.00")
    
    # 2% price * 20x leverage = 40% P/L
    # 40% * $500 position value = $200
    assert abs(pnl_percent - 0.40) < 0.01, f"Expected 40% P/L, got {pnl_percent*100:.1f}%"
    assert abs(pnl_usd - 200.0) < 0.01, f"Expected $200 USD P/L, got ${pnl_usd:.2f}"
    print("  ✓ PASSED")
    
    print("\n" + "="*70)
    print("✓ ALL P/L USD CALCULATION TESTS PASSED")
    print("="*70)
    
    return True

if __name__ == "__main__":
    try:
        test_pnl_usd_calculation()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
