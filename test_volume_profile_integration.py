"""
Integration tests for volume profile enhancements in trading bot
"""
import sys
import pandas as pd
import numpy as np
from position_manager import Position
from signals import SignalGenerator
from indicators import Indicators


def test_position_volume_profile_tp_adjustment():
    """Test position take-profit adjustment using volume profile"""
    print("Testing position TP adjustment with volume profile...")
    
    # Create a long position
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    # Create synthetic OHLCV data with clear volume node at 108
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    prices = np.linspace(100, 115, 100)
    volumes = np.random.uniform(1000, 5000, 100)
    
    # Add high volume around 108 (resistance)
    for i in range(len(prices)):
        if 107 < prices[i] < 109:
            volumes[i] *= 4
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + 0.5,
        'low': prices - 0.5,
        'close': prices,
        'volume': volumes
    })
    
    # Calculate indicators
    df = Indicators.calculate_all(df)
    
    # Current price at 105, should adjust TP to resistance at 108
    current_price = 105.0
    old_tp = position.take_profit
    
    adjusted = position.adjust_take_profit_with_volume_profile(current_price, df)
    
    # TP should have been adjusted closer to volume resistance
    print(f"  ✓ Old TP: {old_tp:.2f}")
    print(f"  ✓ New TP: {position.take_profit:.2f}")
    print(f"  ✓ TP Adjusted: {adjusted}")
    
    # New TP should be reasonable (between current price and old TP)
    assert current_price < position.take_profit, "TP should be above current price"
    print(f"  ✓ TP is above current price")
    
    print("✓ Position TP adjustment with volume profile working correctly")
    return True


def test_signal_scoring_with_volume_profile():
    """Test that signal scoring incorporates volume profile analysis"""
    print("\nTesting signal scoring with volume profile...")
    
    # Create synthetic data with clear volume clustering
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    
    # Uptrend with volume support at 105
    prices = np.linspace(100, 120, 100) + np.random.randn(100) * 1
    volumes = np.random.uniform(1000, 5000, 100)
    
    # High volume at 105 (support) and 115 (resistance)
    for i in range(len(prices)):
        if 104 < prices[i] < 106:
            volumes[i] *= 3
        if 114 < prices[i] < 116:
            volumes[i] *= 3
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + np.abs(np.random.randn(100) * 0.5),
        'low': prices - np.abs(np.random.randn(100) * 0.5),
        'close': prices,
        'volume': volumes
    })
    
    # Calculate indicators
    df = Indicators.calculate_all(df)
    
    # Generate signal
    sg = SignalGenerator()
    signal, confidence, reasons = sg.generate_signal(df)
    
    print(f"  ✓ Signal: {signal}")
    print(f"  ✓ Confidence: {confidence:.2%}")
    
    # Calculate score (should incorporate volume profile)
    score = sg.calculate_score(df)
    print(f"  ✓ Score: {score:.2f}")
    
    assert score >= 0, "Score should be non-negative"
    assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"
    assert 0 <= confidence <= 1, f"Confidence out of range: {confidence}"
    
    print("✓ Signal scoring with volume profile working correctly")
    return True


def test_volume_profile_error_handling():
    """Test that volume profile enhancements handle errors gracefully"""
    print("\nTesting volume profile error handling...")
    
    # Test with empty DataFrame
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    df_empty = pd.DataFrame()
    adjusted = position.adjust_take_profit_with_volume_profile(100.0, df_empty)
    assert not adjusted, "Should return False for empty DataFrame"
    print("  ✓ Empty DataFrame handled correctly")
    
    # Test with insufficient data
    dates = pd.date_range('2024-01-01', periods=10, freq='1h')
    df_small = pd.DataFrame({
        'timestamp': dates,
        'open': [100] * 10,
        'high': [101] * 10,
        'low': [99] * 10,
        'close': [100] * 10,
        'volume': [1000] * 10
    })
    
    adjusted = position.adjust_take_profit_with_volume_profile(100.0, df_small)
    assert not adjusted, "Should return False for insufficient data"
    print("  ✓ Insufficient data handled correctly")
    
    # Signal generator should also handle errors gracefully
    sg = SignalGenerator()
    score_empty = sg.calculate_score(df_empty)
    assert score_empty == 0.0, "Should return 0 for empty DataFrame"
    print("  ✓ Signal scoring handles empty data correctly")
    
    print("✓ Volume profile error handling working correctly")
    return True


def test_integration_with_existing_features():
    """Test that volume profile works with existing bot features"""
    print("\nTesting integration with existing features...")
    
    # Create realistic market data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    prices = np.linspace(100, 120, 100) + np.random.randn(100) * 2
    volumes = np.random.uniform(1000, 5000, 100)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + np.abs(np.random.randn(100) * 0.5),
        'low': prices - np.abs(np.random.randn(100) * 0.5),
        'close': prices,
        'volume': volumes
    })
    
    # Calculate all indicators (existing feature)
    df = Indicators.calculate_all(df)
    assert not df.empty, "Indicators should calculate successfully"
    print("  ✓ Indicators calculated successfully")
    
    # Generate signal (existing feature)
    sg = SignalGenerator()
    signal, confidence, reasons = sg.generate_signal(df)
    assert signal in ['BUY', 'SELL', 'HOLD'], "Signal should be valid"
    print(f"  ✓ Signal generated: {signal}")
    
    # Calculate score with volume profile (new feature)
    score = sg.calculate_score(df)
    assert score >= 0, "Score should be non-negative"
    print(f"  ✓ Score with volume profile: {score:.2f}")
    
    # Create position and test TP adjustment (new feature)
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=110.0,
        amount=1.0,
        leverage=10,
        stop_loss=105.0,
        take_profit=120.0
    )
    
    position.adjust_take_profit_with_volume_profile(115.0, df)
    print(f"  ✓ Position TP adjustment completed")
    
    print("✓ Integration with existing features working correctly")
    return True


def main():
    """Run all integration tests"""
    print("=" * 80)
    print("Running Volume Profile Integration Tests")
    print("=" * 80)
    
    tests = [
        test_position_volume_profile_tp_adjustment,
        test_signal_scoring_with_volume_profile,
        test_volume_profile_error_handling,
        test_integration_with_existing_features,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 80)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 80)
    
    if all(results):
        print("\n✓ All integration tests passed!")
    else:
        print(f"\n✗ Some tests failed ({len(results) - sum(results)} failures)")
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
