"""
Test fee accounting in position management
"""
import sys
from position_manager import Position
from config import Config

def test_fee_calculation():
    """Test that trading fees are calculated correctly"""
    print("=" * 60)
    print("TEST: Fee Calculation")
    print("=" * 60)
    
    # Create a test position
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=50000.0,
        amount=0.1,
        leverage=10,
        stop_loss=49000.0,
        take_profit=52000.0
    )
    
    # Test fee calculation
    fees = position.calculate_trading_fees()
    expected_fees = Config.TRADING_FEE_RATE * 2  # Entry + Exit
    
    print(f"Trading fee rate: {Config.TRADING_FEE_RATE:.4%}")
    print(f"Round-trip fees: {fees:.4%}")
    print(f"Expected: {expected_fees:.4%}")
    assert abs(fees - expected_fees) < 0.0001, "Fee calculation mismatch"
    print("✓ Fee calculation correct\n")
    
    return True

def test_pnl_with_fees():
    """Test P/L calculation with and without fees"""
    print("=" * 60)
    print("TEST: P/L with Fees")
    print("=" * 60)
    
    # Create a test position: Long at $50k with 10x leverage
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=50000.0,
        amount=0.1,  # 0.1 BTC = $5000 position
        leverage=10,
        stop_loss=49000.0,
        take_profit=52000.0
    )
    
    # Test scenario: Price moves to $50,500 (1% gain)
    current_price = 50500.0
    
    # Calculate P/L without fees
    pnl_no_fees = position.get_pnl(current_price, include_fees=False)
    leveraged_pnl_no_fees = position.get_leveraged_pnl(current_price, include_fees=False)
    
    # Calculate P/L with fees
    pnl_with_fees = position.get_pnl(current_price, include_fees=True)
    leveraged_pnl_with_fees = position.get_leveraged_pnl(current_price, include_fees=True)
    
    print(f"Entry: ${position.entry_price:,.0f}")
    print(f"Current: ${current_price:,.0f}")
    print(f"Price change: {pnl_no_fees:.2%}")
    print(f"Position size: {position.amount} BTC = ${position.amount * position.entry_price:,.0f}")
    print(f"Leverage: {position.leverage}x")
    print()
    print("Without fees:")
    print(f"  Base P/L: {pnl_no_fees:.2%}")
    print(f"  Leveraged P/L (ROI): {leveraged_pnl_no_fees:.2%}")
    print()
    print("With fees:")
    print(f"  Trading fees: {position.calculate_trading_fees():.4%}")
    print(f"  Base P/L: {pnl_with_fees:.2%}")
    print(f"  Leveraged P/L (ROI): {leveraged_pnl_with_fees:.2%}")
    print()
    print(f"Fee impact on ROI: {leveraged_pnl_no_fees - leveraged_pnl_with_fees:.2%}")
    
    # Verify calculations
    expected_base_pnl = 0.01  # 1% price move
    expected_fees = Config.TRADING_FEE_RATE * 2
    expected_net_base_pnl = expected_base_pnl - expected_fees
    expected_leveraged_pnl = expected_base_pnl * position.leverage
    expected_net_leveraged_pnl = expected_net_base_pnl * position.leverage
    
    assert abs(pnl_no_fees - expected_base_pnl) < 0.0001, "Base P/L mismatch"
    assert abs(leveraged_pnl_no_fees - expected_leveraged_pnl) < 0.0001, "Leveraged P/L mismatch"
    assert abs(pnl_with_fees - expected_net_base_pnl) < 0.0001, "Net base P/L mismatch"
    assert abs(leveraged_pnl_with_fees - expected_net_leveraged_pnl) < 0.0001, "Net leveraged P/L mismatch"
    
    print("✓ P/L calculations correct\n")
    return True

def test_breakeven_with_fees():
    """Test breakeven detection with fees"""
    print("=" * 60)
    print("TEST: Breakeven Move with Fees")
    print("=" * 60)
    
    # Create a test position
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=50000.0,
        amount=0.1,
        leverage=10,
        stop_loss=49000.0,
        take_profit=52000.0
    )
    
    # Calculate minimum profit needed to cover fees
    fees = position.calculate_trading_fees()
    min_profit_for_breakeven = fees + 0.005  # Fees + 0.5% buffer
    
    print(f"Trading fees: {fees:.4%}")
    print(f"Minimum profit for breakeven: {min_profit_for_breakeven:.4%}")
    
    # Test at various profit levels
    test_prices = [
        (50000.0, "Entry price", False),
        (50030.0, "0.06% profit (barely covers entry fee)", False),
        (50060.0, "0.12% profit (covers round-trip fees)", False),
        (50100.0, "0.2% profit (fees + buffer)", False),  # 0.08% net, below 0.62% threshold
        (50350.0, "0.7% profit", False),  # 0.58% net, still below 0.62% threshold
        (50400.0, "0.8% profit (above threshold)", True),  # 0.68% net, above 0.62% threshold
        (50600.0, "1.2% profit (well above)", True),  # 1.08% net, well above threshold
    ]
    
    print()
    for price, description, should_move in test_prices:
        # Create fresh position for each test to avoid state issues
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        pnl = position.get_pnl(price)
        net_pnl = pnl - fees
        moved = position.move_to_breakeven(price)
        
        print(f"Price ${price:,.0f} ({description}):")
        print(f"  Gross P/L: {pnl:.4%}, Net P/L: {net_pnl:+.4%}")
        print(f"  Should move to breakeven: {should_move}, Moved: {moved}")
        
        if moved != should_move:
            print(f"  ✗ FAILED: Expected {should_move}, got {moved}")
            return False
        else:
            print(f"  ✓ PASSED")
        print()
    
    print("✓ Breakeven logic correct\n")
    return True

def test_profit_thresholds():
    """Test profit taking thresholds with fees"""
    print("=" * 60)
    print("TEST: Profit Taking Thresholds")
    print("=" * 60)
    
    # Create a test position with 10x leverage
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=50000.0,
        amount=0.1,
        leverage=10,
        stop_loss=49000.0,
        take_profit=55000.0  # 10% above entry
    )
    
    fees = position.calculate_trading_fees()
    leveraged_fees = fees * position.leverage
    
    print(f"Entry: ${position.entry_price:,.0f}")
    print(f"Leverage: {position.leverage}x")
    print(f"Trading fees: {fees:.4%}")
    print(f"Leveraged fee impact on ROI: {leveraged_fees:.2%}")
    print()
    
    # Test various price levels
    test_cases = [
        (50100, "1% price move = 10% gross ROI"),
        (50250, "2.5% price move = 25% gross ROI"),
        (50500, "5% price move = 50% gross ROI"),
    ]
    
    for price, description in test_cases:
        gross_pnl = position.get_leveraged_pnl(price, include_fees=False)
        net_pnl = position.get_leveraged_pnl(price, include_fees=True)
        
        print(f"{description}:")
        print(f"  Current price: ${price:,.0f}")
        print(f"  Gross ROI: {gross_pnl:+.2%}")
        print(f"  Net ROI (after fees): {net_pnl:+.2%}")
        print(f"  Fee impact: {gross_pnl - net_pnl:.2%}")
        
        # Verify net is always less than gross
        assert net_pnl < gross_pnl, "Net P/L should be less than gross P/L"
        print(f"  ✓ Net < Gross")
        print()
    
    print("✓ Profit threshold calculations correct\n")
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TRADING FEE ACCOUNTING TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Fee Calculation", test_fee_calculation),
        ("P/L with Fees", test_pnl_with_fees),
        ("Breakeven with Fees", test_breakeven_with_fees),
        ("Profit Thresholds", test_profit_thresholds),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"✗ {name} FAILED with exception: {e}\n")
    
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
