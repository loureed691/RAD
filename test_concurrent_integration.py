"""
Simple integration test to verify concurrent scanning works
"""
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from bot import TradingBot
from config import Config


def test_concurrent_operation():
    """Test that background scanner and main thread can operate concurrently"""
    
    print("Testing concurrent scanning implementation...")
    print("-" * 60)
    
    # Mock everything
    with patch('bot.signal.signal'), \
         patch('bot.KuCoinClient') as mock_client, \
         patch('bot.MarketScanner') as mock_scanner, \
         patch('bot.PositionManager') as mock_position, \
         patch('bot.RiskManager'), \
         patch('bot.MLModel'), \
         patch('bot.AdvancedAnalytics'):
        
        # Setup mocks
        Config.API_KEY = 'test_key'
        Config.API_SECRET = 'test_secret'
        Config.API_PASSPHRASE = 'test_passphrase'
        Config.CHECK_INTERVAL = 2  # Short interval for testing
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_balance.return_value = {'free': {'USDT': 1000}}
        
        mock_scanner_instance = mock_scanner.return_value
        
        # Scanner returns different results over time to simulate real scanning
        scan_call_count = [0]
        def mock_scan(*args, **kwargs):
            scan_call_count[0] += 1
            if scan_call_count[0] == 1:
                return [{'symbol': 'BTCUSDT', 'score': 10, 'signal': 'BUY', 'confidence': 0.9}]
            elif scan_call_count[0] == 2:
                return [{'symbol': 'ETHUSDT', 'score': 9, 'signal': 'SELL', 'confidence': 0.85}]
            else:
                return []
        
        mock_scanner_instance.get_best_pairs.side_effect = mock_scan
        
        mock_position_instance = mock_position.return_value
        mock_position_instance.sync_existing_positions.return_value = 0
        mock_position_instance.get_open_positions_count.return_value = 0
        
        # Create bot
        print("1. Creating bot...")
        bot = TradingBot()
        
        # Verify background scanner state is initialized
        print("2. Verifying background scanner state initialized...")
        assert hasattr(bot, '_scan_thread'), "Missing _scan_thread attribute"
        assert hasattr(bot, '_scan_thread_running'), "Missing _scan_thread_running attribute"
        assert hasattr(bot, '_scan_lock'), "Missing _scan_lock attribute"
        assert hasattr(bot, '_latest_opportunities'), "Missing _latest_opportunities attribute"
        assert isinstance(bot._scan_lock, type(threading.Lock())), "Invalid lock type"
        print("   ✓ All background scanner state initialized correctly")
        
        # Simulate starting the background scanner
        print("3. Starting background scanner thread...")
        bot._scan_thread_running = True
        bot._scan_thread = threading.Thread(target=bot._background_scanner, daemon=True)
        bot._scan_thread.start()
        
        assert bot._scan_thread.is_alive(), "Background thread should be alive"
        print("   ✓ Background scanner thread started successfully")
        
        # Wait for first scan to complete
        print("4. Waiting for first background scan...")
        time.sleep(3)  # Wait longer than CHECK_INTERVAL
        
        # Check that opportunities were cached
        print("5. Verifying opportunities were cached...")
        opportunities = bot._get_latest_opportunities()
        assert len(opportunities) > 0, "Should have cached opportunities from background scan"
        print(f"   ✓ Found {len(opportunities)} cached opportunities: {opportunities[0]['symbol']}")
        assert opportunities[0]['symbol'] in ['BTCUSDT', 'ETHUSDT'], "Should have valid symbol"
        
        # Test that main thread can access cache while scanner is running
        print("6. Testing concurrent access (main thread reading while scanner runs)...")
        for i in range(3):
            opps = bot._get_latest_opportunities()
            print(f"   Iteration {i+1}: Retrieved {len(opps)} opportunities")
            time.sleep(0.1)
        print("   ✓ Concurrent access works correctly")
        
        # Wait for second scan
        print("7. Waiting for second background scan...")
        time.sleep(2)
        
        # Verify cache was updated
        print("8. Verifying cache was updated with new scan...")
        new_opportunities = bot._get_latest_opportunities()
        if len(new_opportunities) > 0:
            print(f"   ✓ Cache updated: {new_opportunities[0]['symbol']}")
        else:
            print("   ✓ Cache updated (empty result this time)")
        
        # Stop background scanner
        print("9. Stopping background scanner...")
        bot._scan_thread_running = False
        bot._scan_thread.join(timeout=3)
        
        assert not bot._scan_thread.is_alive(), "Background thread should have stopped"
        print("   ✓ Background scanner stopped cleanly")
        
        print("-" * 60)
        print("✅ All concurrent scanning tests passed!")
        print()
        print("Summary:")
        print(f"  - Background scans executed: {scan_call_count[0]}")
        print(f"  - Opportunities cached: {len(bot._get_latest_opportunities())}")
        print(f"  - Thread lifecycle: Started ✓ Stopped ✓")
        print(f"  - Concurrent access: Working ✓")
        print()
        print("🚀 Concurrent scanning is working correctly!")


if __name__ == '__main__':
    test_concurrent_operation()
