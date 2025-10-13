"""
Test stop loss execution to find the bug
"""
from position_manager import Position

def test_stop_loss_logic():
    """Test that stop losses trigger correctly"""
    print("="*60)
    print("TEST: Stop Loss Execution Logic")
    print("="*60)
    
    # Create a LONG position
    position = Position(
        symbol='TEST/USDT:USDT',
        side='long',
        entry_price=1.00,
        amount=100.0,
        leverage=5,
        stop_loss=0.98,  # 2% stop
        take_profit=1.06  # 6% target (3x risk)
    )
    
    print(f"\nPosition created:")
    print(f"  Entry: ${position.entry_price:.2f}")
    print(f"  Stop Loss: ${position.stop_loss:.2f} (2% below entry)")
    print(f"  Take Profit: ${position.take_profit:.2f}")
    print(f"  Leverage: {position.leverage}x")
    
    # Test various price levels
    test_prices = [
        (1.05, False, "Above entry, should stay open"),
        (1.00, False, "At entry, should stay open"),
        (0.99, False, "1% below entry, above stop, should stay open"),
        (0.98, True, "At stop loss, should close"),
        (0.97, True, "Below stop loss, should close"),
        (0.95, True, "Well below stop, should close"),
    ]
    
    print(f"\n{'Price':<10} {'Should Close':<15} {'Reason':<30} {'Result':<10}")
    print("-" * 70)
    
    all_passed = True
    for price, should_close_expected, description in test_prices:
        should_close, reason = position.should_close(price)
        
        # Calculate leveraged PnL for context
        base_pnl = (price - position.entry_price) / position.entry_price
        leveraged_pnl = base_pnl * position.leverage
        
        passed = (should_close == should_close_expected)
        result = "✓ PASS" if passed else "✗ FAIL"
        
        if not passed:
            all_passed = False
            
        print(f"${price:<9.2f} {str(should_close_expected):<15} {description:<30} {result}")
        print(f"           Leveraged P/L: {leveraged_pnl:+.2%}, Reason: {reason if should_close else 'N/A'}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    test_stop_loss_logic()
