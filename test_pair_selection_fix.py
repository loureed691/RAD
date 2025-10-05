"""
Test to verify pair selection fix
"""
import sys
from unittest.mock import Mock

def test_pair_selection_with_correct_data_structure():
    """Test that pair selection works with correct data structure"""
    print("\nTesting pair selection with corrected data structure...")
    
    try:
        from market_scanner import MarketScanner
        
        # Create mock client
        mock_client = Mock()
        scanner = MarketScanner(mock_client)
        
        # Simulate the FIXED data structure from get_active_futures
        # NOTE: Need > 10 pairs to avoid fallback behavior
        futures = [
            # Major coins - should always be included
            {'symbol': 'BTC/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 5000000},
            {'symbol': 'ETH/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 3000000},
            {'symbol': 'SOL/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 2000000},
            {'symbol': 'BNB/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 2500000},
            {'symbol': 'ADA/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 1800000},
            {'symbol': 'XRP/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 2200000},
            {'symbol': 'DOGE/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 1500000},
            {'symbol': 'MATIC/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 1600000},
            
            # Other perpetual swaps with good volume - should be included
            {'symbol': 'AVAX/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 1500000},
            {'symbol': 'ATOM/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 1200000},
            {'symbol': 'LINK/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 1800000},
            
            # Perpetual swaps with low volume - should be filtered out
            {'symbol': 'LOWVOL/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 500000},
            {'symbol': 'TINY/USDT:USDT', 'swap': True, 'future': False, 'quoteVolume': 100000},
            
            # Non-perpetual futures - should be filtered out (not perpetual swaps)
            {'symbol': 'BTC/USD:BTC-251226', 'swap': False, 'future': True, 'quoteVolume': 2000000},
        ]
        
        symbols = [f['symbol'] for f in futures]
        
        # Run the filter
        filtered = scanner._filter_high_priority_pairs(symbols, futures)
        
        print(f"  Input: {len(symbols)} pairs")
        print(f"  Output: {len(filtered)} filtered pairs")
        
        # Expected: 11 pairs (8 major + 3 high-volume swaps)
        assert len(filtered) == 11, f"Expected 11 pairs, got {len(filtered)}"
        print("  ✓ Correct number of pairs filtered")
        
        # Verify major coins are included
        assert 'BTC/USDT:USDT' in filtered, "BTC should be included (major coin)"
        assert 'ETH/USDT:USDT' in filtered, "ETH should be included (major coin)"
        assert 'SOL/USDT:USDT' in filtered, "SOL should be included (major coin)"
        print("  ✓ Major coins included")
        
        # Verify high-volume perpetual swaps are included
        assert 'AVAX/USDT:USDT' in filtered, "AVAX should be included (high volume swap)"
        assert 'ATOM/USDT:USDT' in filtered, "ATOM should be included (high volume swap)"
        assert 'LINK/USDT:USDT' in filtered, "LINK should be included (high volume swap)"
        print("  ✓ High-volume perpetual swaps included")
        
        # Verify low-volume pairs are excluded
        assert 'LOWVOL/USDT:USDT' not in filtered, "LOWVOL should be excluded (low volume)"
        assert 'TINY/USDT:USDT' not in filtered, "TINY should be excluded (low volume)"
        print("  ✓ Low-volume pairs excluded")
        
        # Verify non-perpetual futures are excluded
        assert 'BTC/USD:BTC-251226' not in filtered, "Non-USDT futures should be excluded"
        print("  ✓ Non-perpetual futures excluded")
        
        print("✓ Pair selection works correctly with fixed data structure")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pair_selection_without_volume_data():
    """Test that pair selection works even without volume data"""
    print("\nTesting pair selection fallback without volume data...")
    
    try:
        from market_scanner import MarketScanner
        
        # Create mock client
        mock_client = Mock()
        scanner = MarketScanner(mock_client)
        
        # Simulate data structure WITHOUT volume data
        futures = [
            # Major coins - should always be included
            {'symbol': 'BTC/USDT:USDT', 'swap': True, 'future': False},
            {'symbol': 'ETH/USDT:USDT', 'swap': True, 'future': False},
            
            # Other perpetual swaps - should be included
            {'symbol': 'AVAX/USDT:USDT', 'swap': True, 'future': False},
            {'symbol': 'ATOM/USDT:USDT', 'swap': True, 'future': False},
            {'symbol': 'RANDOM/USDT:USDT', 'swap': True, 'future': False},
        ]
        
        symbols = [f['symbol'] for f in futures]
        
        # Run the filter
        filtered = scanner._filter_high_priority_pairs(symbols, futures)
        
        print(f"  Input: {len(symbols)} pairs")
        print(f"  Output: {len(filtered)} filtered pairs")
        
        # Without volume data, all major coins should be included
        assert 'BTC/USDT:USDT' in filtered, "BTC should be included"
        assert 'ETH/USDT:USDT' in filtered, "ETH should be included"
        print("  ✓ Major coins included")
        
        # Without volume data, all perpetual swaps should be included
        assert 'AVAX/USDT:USDT' in filtered, "AVAX should be included (perpetual swap)"
        assert 'ATOM/USDT:USDT' in filtered, "ATOM should be included (perpetual swap)"
        assert 'RANDOM/USDT:USDT' in filtered, "RANDOM should be included (perpetual swap)"
        print("  ✓ All perpetual swaps included (no volume filtering)")
        
        print("✓ Pair selection works correctly without volume data")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Pair Selection Fix")
    print("=" * 60)
    
    results = []
    results.append(test_pair_selection_with_correct_data_structure())
    results.append(test_pair_selection_without_volume_data())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
