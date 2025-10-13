"""
Test trailing stop logic for potential bugs
"""
from position_manager import Position

def test_trailing_stop_movements():
    """Test that trailing stops never loosen"""
    print("="*60)
    print("TEST: Trailing Stop Loss Logic")
    print("="*60)
    
    # Create a LONG position
    position = Position(
        symbol='TEST/USDT:USDT',
        side='long',
        entry_price=1.00,
        amount=100.0,
        leverage=5,
        stop_loss=0.98,  # 2% initial stop
        take_profit=1.06
    )
    
    print(f"\nInitial Position:")
    print(f"  Entry: ${position.entry_price:.2f}")
    print(f"  Initial Stop Loss: ${position.stop_loss:.4f}")
    print(f"  Highest Price: ${position.highest_price:.2f}")
    
    # Simulate price movements
    price_sequence = [
        (1.02, "Price rises 2%"),
        (1.05, "Price rises to 5%"),
        (1.03, "Price retraces to 3%"),
        (1.01, "Price retraces more to 1%"),
        (0.99, "Price drops below entry"),
        (0.98, "Price hits original stop loss"),
        (0.95, "Price falls further"),
    ]
    
    print(f"\n{'Price':<10} {'Stop Loss':<12} {'Should Close':<15} {'Description':<30}")
    print("-" * 70)
    
    issues_found = []
    
    for price, description in price_sequence:
        # Update trailing stop
        position.update_trailing_stop(price, trailing_percentage=0.02)
        
        # Check if should close
        should_close, reason = position.should_close(price)
        
        # Calculate PnL
        base_pnl = (price - position.entry_price) / position.entry_price
        leveraged_pnl = base_pnl * position.leverage
        
        # Check for issues:
        # 1. Stop should never go below initial stop for LONG
        if position.stop_loss < 0.98:
            issues_found.append(f"Stop loosened to ${position.stop_loss:.4f} at price ${price:.2f}")
        
        # 2. If price < stop, should always close
        if price < position.stop_loss and not should_close:
            issues_found.append(f"Price ${price:.2f} < Stop ${position.stop_loss:.4f} but not closing!")
        
        status = "CLOSE" if should_close else "OPEN"
        
        print(f"${price:<9.2f} ${position.stop_loss:<11.4f} {status:<15} {description}")
        print(f"           P/L: {leveraged_pnl:+.2%}, Reason: {reason if should_close else 'N/A'}")
    
    print("\n" + "="*60)
    if issues_found:
        print("❌ ISSUES FOUND:")
        for issue in issues_found:
            print(f"   - {issue}")
    else:
        print("✅ NO ISSUES - Trailing stop logic working correctly")
    print("="*60)
    
    return len(issues_found) == 0

if __name__ == "__main__":
    test_trailing_stop_movements()
