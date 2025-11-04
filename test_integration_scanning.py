"""
Integration test to verify scanning optimization behavior
"""
import time
from unittest.mock import Mock, MagicMock, patch
from market_scanner import MarketScanner


def test_scanning_optimization():
    """Test that priority pairs caching reduces API calls"""
    print("\n" + "="*70)
    print("Integration Test: Scanning Optimization")
    print("="*70)
    
    # Create mock client
    mock_client = Mock()
    
    # Track API call counts
    futures_call_count = 0
    
    def mock_get_active_futures():
        nonlocal futures_call_count
        futures_call_count += 1
        return [
            {'symbol': 'BTCUSDT', 'quoteVolume': 10000000, 'swap': True},
            {'symbol': 'ETHUSDT', 'quoteVolume': 5000000, 'swap': True},
            {'symbol': 'SOLUSDT', 'quoteVolume': 2000000, 'swap': True},
            {'symbol': 'ADAUSDT', 'quoteVolume': 1500000, 'swap': True},
            {'symbol': 'XRPUSDT', 'quoteVolume': 1200000, 'swap': True},
        ]
    
    mock_client.get_active_futures = mock_get_active_futures
    
    # Create scanner
    scanner = MarketScanner(mock_client)
    
    # Mock scan_pair to return dummy results
    scan_pair_call_count = 0
    
    def mock_scan_pair(symbol):
        nonlocal scan_pair_call_count
        scan_pair_call_count += 1
        # Simulate some pairs having opportunities
        if symbol in ['BTCUSDT', 'ETHUSDT']:
            return (symbol, 60.0, 'BUY', 0.80, {'test': True}, None)
        return (symbol, 30.0, 'HOLD', 0.50, {}, None)
    
    with patch.object(scanner, 'scan_pair', side_effect=mock_scan_pair):
        print("\n1. First scan - should fetch and cache priority pairs")
        print("-" * 70)
        
        results1 = scanner.scan_all_pairs(max_workers=1)
        
        print(f"✓ Futures API calls: {futures_call_count}")
        print(f"✓ Pairs scanned: {scan_pair_call_count}")
        print(f"✓ Opportunities found: {len(results1)}")
        print(f"✓ Priority pairs cached: {len(scanner._cached_priority_pairs)}")
        
        assert futures_call_count == 1, "Should fetch futures on first scan"
        assert scanner._cached_priority_pairs is not None, "Should cache priority pairs"
        assert scanner._last_priority_pairs_update is not None, "Should record update time"
        
        # Reset counters
        futures_call_count = 0
        scan_pair_call_count = 0
        
        print("\n2. Second scan (immediate) - should use cached priority pairs")
        print("-" * 70)
        
        results2 = scanner.scan_all_pairs(max_workers=1)
        
        print(f"✓ Futures API calls: {futures_call_count}")
        print(f"✓ Pairs scanned: {scan_pair_call_count}")
        print(f"✓ Opportunities found: {len(results2)}")
        
        assert futures_call_count == 0, "Should NOT fetch futures on second scan"
        assert scan_pair_call_count > 0, "Should still scan pairs"
        
        # Reset counters
        futures_call_count = 0
        scan_pair_call_count = 0
        
        print("\n3. Third scan (immediate) - should still use cached priority pairs")
        print("-" * 70)
        
        results3 = scanner.scan_all_pairs(max_workers=1)
        
        print(f"✓ Futures API calls: {futures_call_count}")
        print(f"✓ Pairs scanned: {scan_pair_call_count}")
        print(f"✓ Opportunities found: {len(results3)}")
        
        assert futures_call_count == 0, "Should NOT fetch futures on third scan"
        
        print("\n4. Test cache expiry - simulate time passing")
        print("-" * 70)
        
        # Simulate cache expiry by setting old update time
        scanner._last_priority_pairs_update = time.time() - (scanner._priority_pairs_refresh_interval + 10)
        
        # Reset counters
        futures_call_count = 0
        scan_pair_call_count = 0
        
        results4 = scanner.scan_all_pairs(max_workers=1)
        
        print(f"✓ Futures API calls: {futures_call_count}")
        print(f"✓ Pairs scanned: {scan_pair_call_count}")
        print(f"✓ Opportunities found: {len(results4)}")
        
        assert futures_call_count == 1, "Should refresh futures after cache expires"
        
        print("\n5. Test clear_cache")
        print("-" * 70)
        
        scanner.clear_cache()
        
        print(f"✓ Priority pairs cache cleared: {scanner._cached_priority_pairs is None}")
        print(f"✓ Update time cleared: {scanner._last_priority_pairs_update is None}")
        
        assert scanner._cached_priority_pairs is None, "Cache should be cleared"
        assert scanner._last_priority_pairs_update is None, "Update time should be cleared"
    
    print("\n" + "="*70)
    print("✓ All integration tests passed!")
    print("="*70)
    print("\nSummary:")
    print("  - Priority pairs are cached and reused across scans")
    print("  - API calls to get_active_futures() reduced significantly")
    print("  - Cache refreshes automatically after configured interval")
    print("  - clear_cache() properly clears all caches")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_scanning_optimization()
    print("\n✅ Integration test completed successfully!\n")
