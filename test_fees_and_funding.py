#!/usr/bin/env python3
"""
Test Priority 1 - Funding & Fees Implementation
Tests that trading fees and funding rates are incorporated into PnL calculations
"""
import sys
import pandas as pd
import numpy as np
from backtest_engine import BacktestEngine

def test_trading_fees_calculation():
    """Test that trading fees are correctly deducted from PnL"""
    print("\n" + "="*70)
    print("TEST 1: TRADING FEES CALCULATION")
    print("="*70)
    
    # Create backtest engine with known fee rate
    engine = BacktestEngine(
        initial_balance=10000,
        trading_fee_rate=0.001,  # 0.1% for easy calculation
        funding_rate=0.0  # Disable funding for this test
    )
    
    print("\n1. Testing fee calculation on a winning trade...")
    
    # Simulate a simple winning trade
    position = {
        'side': 'long',
        'entry_price': 100.0,
        'amount': 10.0,
        'leverage': 1
    }
    
    exit_price = 110.0  # 10% gain
    
    # Calculate expected values
    position_value = 10.0 * 100.0  # $1000
    gross_pnl = 100.0  # 10% of $1000 = $100
    entry_fee = position_value * 0.001  # $1
    exit_value = 10.0 * 110.0  # $1100
    exit_fee = exit_value * 0.001  # $1.10
    expected_trading_fees = entry_fee + exit_fee  # $2.10
    expected_net_pnl = gross_pnl - expected_trading_fees  # $97.90
    
    print(f"   Position value: ${position_value:.2f}")
    print(f"   Gross PnL: ${gross_pnl:.2f}")
    print(f"   Expected trading fees: ${expected_trading_fees:.2f}")
    print(f"   Expected net PnL: ${expected_net_pnl:.2f}")
    
    # Close position
    engine.positions = [position]
    engine.close_position(position, exit_price, 'test')
    
    # Verify
    trade = engine.closed_trades[0]
    assert abs(trade['trading_fees'] - expected_trading_fees) < 0.01, \
        f"Trading fees mismatch: {trade['trading_fees']} != {expected_trading_fees}"
    assert abs(trade['net_pnl'] - expected_net_pnl) < 0.01, \
        f"Net PnL mismatch: {trade['net_pnl']} != {expected_net_pnl}"
    
    print(f"   ✓ Actual trading fees: ${trade['trading_fees']:.2f}")
    print(f"   ✓ Actual net PnL: ${trade['net_pnl']:.2f}")
    
    print("\n✅ Trading fees calculation test PASSED")

def test_funding_fees_calculation():
    """Test that funding fees are correctly calculated"""
    print("\n" + "="*70)
    print("TEST 2: FUNDING FEES CALCULATION")
    print("="*70)
    
    # Create backtest engine with known funding rate
    engine = BacktestEngine(
        initial_balance=10000,
        trading_fee_rate=0.0,  # Disable trading fees for this test
        funding_rate=0.0001  # 0.01% per 8 hours
    )
    
    print("\n1. Testing funding calculation on a position...")
    
    # Simulate a position
    position = {
        'side': 'long',
        'entry_price': 100.0,
        'amount': 10.0,
        'leverage': 1
    }
    
    exit_price = 100.0  # No price change, just funding
    
    # Calculate expected values
    position_value = 10.0 * 100.0  # $1000
    # Default: 1 funding period (since we don't have entry/exit times)
    expected_funding_fees = position_value * 0.0001  # $0.10
    
    print(f"   Position value: ${position_value:.2f}")
    print(f"   Funding rate: 0.01% per 8h")
    print(f"   Expected funding fees (1 period): ${expected_funding_fees:.2f}")
    
    # Close position
    engine.positions = [position]
    engine.close_position(position, exit_price, 'test')
    
    # Verify
    trade = engine.closed_trades[0]
    assert abs(trade['funding_fees'] - expected_funding_fees) < 0.01, \
        f"Funding fees mismatch: {trade['funding_fees']} != {expected_funding_fees}"
    
    print(f"   ✓ Actual funding fees: ${trade['funding_fees']:.2f}")
    
    print("\n✅ Funding fees calculation test PASSED")

def test_fee_impact_on_profitability():
    """Test that fees significantly impact reported profitability"""
    print("\n" + "="*70)
    print("TEST 3: FEE IMPACT ON PROFITABILITY")
    print("="*70)
    
    print("\n1. Running backtest WITHOUT fees...")
    engine_no_fees = BacktestEngine(
        initial_balance=10000,
        trading_fee_rate=0.0,
        funding_rate=0.0
    )
    
    # Simulate multiple small trades
    for i in range(10):
        position = {
            'side': 'long',
            'entry_price': 100.0,
            'amount': 1.0,
            'leverage': 1
        }
        engine_no_fees.positions = [position]
        # Small 1% profit per trade
        engine_no_fees.close_position(position, 101.0, 'test')
    
    results_no_fees = engine_no_fees.calculate_results()
    print(f"   Net PnL (no fees): ${results_no_fees['total_pnl']:.2f}")
    
    print("\n2. Running backtest WITH realistic fees...")
    engine_with_fees = BacktestEngine(
        initial_balance=10000,
        trading_fee_rate=0.0006,  # 0.06% taker fee
        funding_rate=0.0001  # 0.01% per 8h
    )
    
    # Same trades
    for i in range(10):
        position = {
            'side': 'long',
            'entry_price': 100.0,
            'amount': 1.0,
            'leverage': 1
        }
        engine_with_fees.positions = [position]
        engine_with_fees.close_position(position, 101.0, 'test')
    
    results_with_fees = engine_with_fees.calculate_results()
    print(f"   Gross PnL: ${results_with_fees['gross_pnl']:.2f}")
    print(f"   Trading fees: ${results_with_fees['total_trading_fees']:.2f}")
    print(f"   Funding fees: ${results_with_fees['total_funding_fees']:.2f}")
    print(f"   Net PnL (with fees): ${results_with_fees['total_pnl']:.2f}")
    print(f"   Fee impact: {results_with_fees['fee_impact_pct']:.1f}%")
    
    # Verify fees reduce profit
    assert results_with_fees['total_pnl'] < results_no_fees['total_pnl'], \
        "Fees should reduce profitability"
    assert results_with_fees['fee_impact_pct'] > 0, \
        "Fee impact should be positive"
    
    print(f"\n   ✓ PnL reduced by fees: ${results_no_fees['total_pnl']:.2f} → ${results_with_fees['total_pnl']:.2f}")
    print(f"   ✓ Fee impact: {results_with_fees['fee_impact_pct']:.1f}%")
    
    print("\n✅ Fee impact test PASSED")

def test_leverage_amplifies_fees():
    """Test that leverage amplifies fee impact correctly"""
    print("\n" + "="*70)
    print("TEST 4: LEVERAGE AMPLIFIES FEES")
    print("="*70)
    
    engine = BacktestEngine(
        initial_balance=10000,
        trading_fee_rate=0.0006,
        funding_rate=0.0001
    )
    
    print("\n1. Testing 1x leverage...")
    position_1x = {
        'side': 'long',
        'entry_price': 100.0,
        'amount': 10.0,
        'leverage': 1
    }
    engine.positions = [position_1x]
    engine.close_position(position_1x, 102.0, 'test')
    trade_1x = engine.closed_trades[0]
    
    print(f"   1x leverage: Trading fees = ${trade_1x['trading_fees']:.2f}")
    
    print("\n2. Testing 10x leverage...")
    position_10x = {
        'side': 'long',
        'entry_price': 100.0,
        'amount': 10.0,  # Same amount
        'leverage': 10  # But 10x leverage
    }
    engine.positions = [position_10x]
    engine.close_position(position_10x, 102.0, 'test')
    trade_10x = engine.closed_trades[1]
    
    print(f"   10x leverage: Trading fees = ${trade_10x['trading_fees']:.2f}")
    
    # Fees should be the same (based on position value, not leverage)
    # But PnL impact is different due to leverage
    assert abs(trade_1x['trading_fees'] - trade_10x['trading_fees']) < 0.01, \
        "Trading fees should be same regardless of leverage"
    
    # Net PnL should be different due to leverage amplifying returns
    assert trade_10x['gross_pnl'] > trade_1x['gross_pnl'], \
        "10x leverage should amplify gross PnL"
    
    print(f"\n   ✓ Fees are position-value based (not leverage amplified)")
    print(f"   ✓ 1x gross PnL: ${trade_1x['gross_pnl']:.2f}, net: ${trade_1x['net_pnl']:.2f}")
    print(f"   ✓ 10x gross PnL: ${trade_10x['gross_pnl']:.2f}, net: ${trade_10x['net_pnl']:.2f}")
    
    print("\n✅ Leverage and fees test PASSED")

def test_realistic_fee_scenario():
    """Test with realistic KuCoin fee structure"""
    print("\n" + "="*70)
    print("TEST 5: REALISTIC KUCOIN FEE SCENARIO")
    print("="*70)
    
    # KuCoin futures fees:
    # Maker: 0.02%, Taker: 0.06%
    # Funding: typically 0.01% per 8h (0.03% per day)
    
    engine = BacktestEngine(
        initial_balance=1000,
        trading_fee_rate=0.0006,  # Conservative taker fee
        funding_rate=0.0001  # 0.01% per 8h
    )
    
    print("\n1. Simulating a realistic trading scenario...")
    print("   Starting balance: $1000")
    print("   Fee structure: 0.06% taker, 0.01% funding per 8h")
    
    # Simulate 5 trades with varying outcomes
    trades_config = [
        (100.0, 105.0, 5, 'win'),    # 5% win
        (105.0, 103.0, 5, 'loss'),   # ~2% loss
        (103.0, 108.0, 5, 'win'),    # ~5% win
        (108.0, 107.0, 5, 'small loss'),  # ~1% loss
        (107.0, 112.0, 5, 'win'),    # ~5% win
    ]
    
    for entry, exit, amount, outcome in trades_config:
        position = {
            'side': 'long',
            'entry_price': entry,
            'amount': amount,
            'leverage': 5  # 5x leverage
        }
        engine.positions = [position]
        engine.close_position(position, exit, outcome)
        print(f"   Trade: ${entry:.0f} → ${exit:.0f} ({outcome})")
    
    results = engine.calculate_results()
    
    print(f"\n2. Results:")
    print(f"   Total trades: {results['total_trades']}")
    print(f"   Win rate: {results['win_rate']:.1%}")
    print(f"   Gross PnL: ${results['gross_pnl']:.2f}")
    print(f"   Trading fees: ${results['total_trading_fees']:.2f}")
    print(f"   Funding fees: ${results['total_funding_fees']:.2f}")
    print(f"   Total fees: ${results['total_fees']:.2f}")
    print(f"   Net PnL: ${results['total_pnl']:.2f}")
    print(f"   Fee impact: {results['fee_impact_pct']:.1f}% of gross PnL")
    print(f"   Final balance: ${results['final_balance']:.2f}")
    
    # Verify fees were applied
    assert results['total_fees'] > 0, "Total fees should be positive"
    assert results['gross_pnl'] != results['total_pnl'], "Gross and net PnL should differ"
    assert results['total_pnl'] < results['gross_pnl'], "Net PnL should be less than gross"
    
    print(f"\n   ✓ Fees properly deducted from gross PnL")
    print(f"   ✓ Realistic fee scenario calculated correctly")
    
    print("\n✅ Realistic fee scenario test PASSED")

def run_all_tests():
    """Run all funding & fees tests"""
    print("\n" + "="*80)
    print("PRIORITY 1 - FUNDING & FEES TEST SUITE")
    print("="*80)
    print("Testing realistic trading fees and funding rates in PnL calculations")
    print("="*80)
    
    tests = [
        ("Trading Fees Calculation", test_trading_fees_calculation),
        ("Funding Fees Calculation", test_funding_fees_calculation),
        ("Fee Impact on Profitability", test_fee_impact_on_profitability),
        ("Leverage and Fees", test_leverage_amplifies_fees),
        ("Realistic Fee Scenario", test_realistic_fee_scenario),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "PASSED" if success else "FAILED"))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, f"FAILED: {str(e)}"))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results:
        status = "✅" if result == "PASSED" else "❌"
        print(f"{status} {test_name}: {result}")
    
    passed = sum(1 for _, r in results if r == "PASSED")
    total = len(results)
    
    print("\n" + "="*80)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
    print("="*80)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
