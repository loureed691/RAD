"""
Test to verify cache is used only as fallback, not proactively
"""
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cache_fallback_behavior():
    """Test that cache is only used when live data fetch fails"""
    print("\n" + "="*80)
    print("Testing cache fallback behavior...")
    print("="*80)
    
    from market_scanner import MarketScanner
    from kucoin_client import KuCoinClient
    
    # Create mock client
    mock_client = Mock(spec=KuCoinClient)
    
    # Create scanner instance
    scanner = MarketScanner(mock_client)
    
    # Test 1: Live data should be fetched even when cache exists and is fresh
    print("\n1. Testing live data fetch with fresh cache available...")
    
    # Pre-populate cache with "old" data
    old_result = ('BTC/USDT:USDT', 50.0, 'BUY', 0.7, {'reason': 'cached_data'})
    scanner.cache['BTC/USDT:USDT'] = (old_result, time.time() - 60)  # 1 minute old
    
    # Mock successful live data fetch
    mock_ohlcv = [[1000, 100, 105, 95, 102, 1000] for _ in range(100)]
    mock_client.get_ohlcv.return_value = mock_ohlcv
    
    # Mock indicators to return valid dataframe
    with patch('market_scanner.Indicators.calculate_all') as mock_indicators:
        import pandas as pd
        mock_df = pd.DataFrame({
            'close': [102.0] * 100,
            'rsi': [55.0] * 100,
            'macd': [0.5] * 100,
            'signal': [0.3] * 100,
            'bb_upper': [105.0] * 100,
            'bb_lower': [99.0] * 100,
            'bb_width': [0.03] * 100
        })
        mock_indicators.return_value = mock_df
        
        # Mock signal generator
        with patch.object(scanner.signal_generator, 'generate_signal') as mock_signal:
            mock_signal.return_value = ('SELL', 0.8, {'reason': 'live_data'})
            
            with patch.object(scanner.signal_generator, 'calculate_score') as mock_score:
                mock_score.return_value = 75.0
                
                # Call scan_pair - should fetch live data, NOT use cache
                result = scanner.scan_pair('BTC/USDT:USDT')
                
                # Verify live data was fetched
                assert mock_client.get_ohlcv.called, "❌ Live data was NOT fetched (cache was used instead)"
                print("   ✓ Live data was fetched even though cache was available")
                
                # Verify result is from live data, not cache
                _, _, signal, confidence, reasons = result
                assert signal == 'SELL', f"❌ Expected 'SELL' from live data, got '{signal}' from cache"
                assert confidence == 0.8, f"❌ Expected 0.8 from live data, got {confidence} from cache"
                assert reasons.get('reason') == 'live_data', f"❌ Got cached data instead of live data"
                print("   ✓ Result is from live data, not cache")
    
    # Test 2: Cache should be used when live data fetch fails
    print("\n2. Testing cache fallback when live data fetch fails...")
    
    # Pre-populate cache
    cached_result = ('ETH/USDT:USDT', 60.0, 'BUY', 0.75, {'reason': 'from_cache'})
    scanner.cache['ETH/USDT:USDT'] = (cached_result, time.time() - 120)  # 2 minutes old
    
    # Mock failed live data fetch (returns empty list)
    mock_client.get_ohlcv.return_value = []
    
    # Call scan_pair - should fall back to cache
    result = scanner.scan_pair('ETH/USDT:USDT')
    
    # Verify cache was used as fallback
    symbol, score, signal, confidence, reasons = result
    assert signal == 'BUY', f"❌ Expected 'BUY' from cache, got '{signal}'"
    assert confidence == 0.75, f"❌ Expected 0.75 from cache, got {confidence}"
    assert reasons.get('reason') == 'from_cache', f"❌ Did not get cached data"
    print("   ✓ Cache was used as fallback when live data fetch failed")
    
    # Test 3: No cache and failed fetch should return error result
    print("\n3. Testing error result when no cache and fetch fails...")
    
    # Clear cache for this symbol
    if 'SOL/USDT:USDT' in scanner.cache:
        del scanner.cache['SOL/USDT:USDT']
    
    # Mock failed live data fetch
    mock_client.get_ohlcv.return_value = []
    
    # Call scan_pair - should return error result
    result = scanner.scan_pair('SOL/USDT:USDT')
    
    # Verify error result
    symbol, score, signal, confidence, reasons = result
    assert signal == 'HOLD', f"❌ Expected 'HOLD' for error, got '{signal}'"
    assert score == 0.0, f"❌ Expected score 0.0 for error, got {score}"
    assert 'error' in reasons, f"❌ Expected error in reasons, got {reasons}"
    print("   ✓ Error result returned when no cache and fetch fails")
    
    # Test 4: scan_all_pairs should also prioritize live data
    print("\n4. Testing scan_all_pairs prioritizes live data...")
    
    # Pre-populate full scan cache
    scanner.scan_results_cache = [
        {'symbol': 'BTC/USDT:USDT', 'score': 50.0, 'signal': 'BUY', 'confidence': 0.7, 'reasons': {'cached': True}}
    ]
    scanner.last_full_scan = time.time() - 60  # 1 minute ago (fresh)
    
    # Mock successful futures fetch
    mock_client.get_active_futures.return_value = [
        {'symbol': 'BTC/USDT:USDT', 'swap': True, 'quoteVolume': 5000000}
    ]
    
    # Mock OHLCV fetch for scan
    mock_client.get_ohlcv.return_value = mock_ohlcv
    
    with patch('market_scanner.Indicators.calculate_all') as mock_indicators:
        mock_indicators.return_value = mock_df
        
        with patch.object(scanner.signal_generator, 'generate_signal') as mock_signal:
            mock_signal.return_value = ('SELL', 0.9, {'live': True})
            
            with patch.object(scanner.signal_generator, 'calculate_score') as mock_score:
                mock_score.return_value = 80.0
                
                # Call scan_all_pairs
                results = scanner.scan_all_pairs(max_workers=1, use_cache=True)
                
                # Verify live data was fetched (not using cached full scan)
                assert mock_client.get_active_futures.called, "❌ Active futures were NOT fetched"
                print("   ✓ Live market scan was performed even with fresh cache")
                
                # Verify results are from live data
                if results:
                    assert results[0]['signal'] == 'SELL', "❌ Results came from cache, not live data"
                    print("   ✓ Results are from live market scan, not cached scan")
    
    print("\n" + "="*80)
    print("✅ All cache fallback tests passed!")
    print("="*80)
    return True

if __name__ == "__main__":
    try:
        success = test_cache_fallback_behavior()
        if success:
            print("\n✓ Cache fallback behavior is working correctly")
            sys.exit(0)
        else:
            print("\n✗ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
