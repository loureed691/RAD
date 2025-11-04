"""
Tests for volume profile analysis enhancements
"""
import sys
import pandas as pd
import numpy as np
from volume_profile import VolumeProfile


def test_volume_profile_calculation():
    """Test volume profile calculation with synthetic data"""
    print("Testing volume profile calculation...")

    # Create synthetic OHLCV data with clear volume clustering
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')

    # Create price range with high volume at specific levels
    prices = np.linspace(100, 120, 100) + np.random.randn(100) * 2
    volumes = np.random.uniform(1000, 5000, 100)

    # Add high volume at specific price levels (POC candidates)
    for i in range(len(prices)):
        if 108 < prices[i] < 112:  # High volume in this range
            volumes[i] *= 3

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + np.abs(np.random.randn(100) * 0.5),
        'low': prices - np.abs(np.random.randn(100) * 0.5),
        'close': prices,
        'volume': volumes
    })

    vp = VolumeProfile()
    profile = vp.calculate_volume_profile(df, num_bins=50)

    # Verify POC exists and is in expected range
    assert profile['poc'] is not None, "POC should not be None"
    assert 100 <= profile['poc'] <= 120, f"POC {profile['poc']} should be in price range"
    assert 108 <= profile['poc'] <= 112, f"POC {profile['poc']} should be in high-volume range"

    # Verify VAH and VAL exist
    assert profile['vah'] is not None, "VAH should not be None"
    assert profile['val'] is not None, "VAL should not be None"
    assert profile['val'] <= profile['poc'] <= profile['vah'], "POC should be between VAL and VAH"

    # Verify volume nodes
    assert 'volume_nodes' in profile, "Should have volume_nodes"
    assert 'total_volume' in profile, "Should have total_volume"
    assert profile['total_volume'] > 0, "Total volume should be positive"

    print(f"  ✓ POC: {profile['poc']:.2f}")
    print(f"  ✓ VAH: {profile['vah']:.2f}")
    print(f"  ✓ VAL: {profile['val']:.2f}")
    print(f"  ✓ Volume nodes: {len(profile['volume_nodes'])}")
    print(f"  ✓ Total volume: {profile['total_volume']:.0f}")
    print("✓ Volume profile calculation working correctly")
    return True


def test_high_volume_node_detection():
    """Test detection of proximity to high-volume nodes"""
    print("\nTesting high-volume node detection...")

    # Create synthetic data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    prices = np.linspace(100, 120, 100)
    volumes = np.random.uniform(1000, 5000, 100)

    # High volume at 110
    for i in range(len(prices)):
        if 109 < prices[i] < 111:
            volumes[i] *= 3

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + 0.5,
        'low': prices - 0.5,
        'close': prices,
        'volume': volumes
    })

    vp = VolumeProfile()
    profile = vp.calculate_volume_profile(df)

    # Test near POC
    current_price = profile['poc'] * 1.005  # 0.5% away
    is_near, node_type = vp.is_near_high_volume_node(current_price, profile, threshold=0.02)
    assert is_near, "Should detect proximity to POC"
    assert node_type == 'POC', f"Should identify as POC, got {node_type}"
    print(f"  ✓ Detected proximity to POC at price {current_price:.2f}")

    # Test far from nodes
    current_price = profile['vah'] * 1.10  # 10% away
    is_near, node_type = vp.is_near_high_volume_node(current_price, profile, threshold=0.02)
    assert not is_near, "Should not detect proximity when far away"
    print(f"  ✓ Correctly identified no proximity at price {current_price:.2f}")

    print("✓ High-volume node detection working correctly")
    return True


def test_support_resistance_from_volume():
    """Test support/resistance identification from volume profile"""
    print("\nTesting support/resistance from volume...")

    # Create synthetic data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    prices = np.linspace(100, 120, 100)
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
        'high': prices + 0.5,
        'low': prices - 0.5,
        'close': prices,
        'volume': volumes
    })

    vp = VolumeProfile()
    profile = vp.calculate_volume_profile(df)

    # Test current price in middle
    current_price = 110.0
    vol_sr = vp.get_support_resistance_from_volume(current_price, profile)

    assert vol_sr['support'] is not None, "Should find support"
    assert vol_sr['resistance'] is not None, "Should find resistance"
    assert vol_sr['support'] < current_price < vol_sr['resistance'], "Support should be below, resistance above"
    assert vol_sr['support_strength'] > 0, "Support strength should be positive"
    assert vol_sr['resistance_strength'] > 0, "Resistance strength should be positive"

    print(f"  ✓ Support: {vol_sr['support']:.2f} (strength: {vol_sr['support_strength']:.2f})")
    print(f"  ✓ Resistance: {vol_sr['resistance']:.2f} (strength: {vol_sr['resistance_strength']:.2f})")
    print(f"  ✓ In value area: {vol_sr['in_value_area']}")

    # Test current price below all levels
    current_price = 95.0
    vol_sr = vp.get_support_resistance_from_volume(current_price, profile)
    assert vol_sr['support'] is None, "Should not find support when below all levels"
    assert vol_sr['resistance'] is not None, "Should find resistance when below all levels"
    print(f"  ✓ Correctly handled price below all levels")

    # Test current price above all levels
    current_price = 125.0
    vol_sr = vp.get_support_resistance_from_volume(current_price, profile)
    assert vol_sr['support'] is not None, "Should find support when above all levels"
    assert vol_sr['resistance'] is None, "Should not find resistance when above all levels"
    print(f"  ✓ Correctly handled price above all levels")

    print("✓ Support/resistance from volume working correctly")
    return True


def test_empty_data_handling():
    """Test handling of empty or insufficient data"""
    print("\nTesting empty data handling...")

    vp = VolumeProfile()

    # Test empty DataFrame
    df_empty = pd.DataFrame()
    profile = vp.calculate_volume_profile(df_empty)
    assert profile['poc'] is None, "Should handle empty DataFrame"
    print("  ✓ Empty DataFrame handled correctly")

    # Test insufficient data
    dates = pd.date_range('2024-01-01', periods=10, freq='1h')
    df_small = pd.DataFrame({
        'timestamp': dates,
        'open': [100] * 10,
        'high': [101] * 10,
        'low': [99] * 10,
        'close': [100] * 10,
        'volume': [1000] * 10
    })
    profile = vp.calculate_volume_profile(df_small)
    assert profile['poc'] is None, "Should handle insufficient data"
    print("  ✓ Insufficient data handled correctly")

    # Test invalid price range
    dates = pd.date_range('2024-01-01', periods=50, freq='1h')
    df_invalid = pd.DataFrame({
        'timestamp': dates,
        'open': [100] * 50,
        'high': [100] * 50,  # All same price
        'low': [100] * 50,
        'close': [100] * 50,
        'volume': [1000] * 50
    })
    profile = vp.calculate_volume_profile(df_invalid)
    assert profile['poc'] is None, "Should handle invalid price range"
    print("  ✓ Invalid price range handled correctly")

    print("✓ Empty data handling working correctly")
    return True


def main():
    """Run all volume profile tests"""
    print("=" * 80)
    print("Running Volume Profile Analysis Tests")
    print("=" * 80)

    tests = [
        test_volume_profile_calculation,
        test_high_volume_node_detection,
        test_support_resistance_from_volume,
        test_empty_data_handling,
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
        print("\n✓ All volume profile tests passed!")
    else:
        print(f"\n✗ Some tests failed ({len(results) - sum(results)} failures)")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
