#!/usr/bin/env python3
"""
Test suite for health monitoring functionality
"""
import time
from datetime import datetime, timedelta
from health_monitor import HealthMonitor


def test_api_call_tracking():
    """Test API call tracking"""
    print("Testing API call tracking...")
    monitor = HealthMonitor()
    
    # Record some API calls
    monitor.record_api_call(success=True)
    monitor.record_api_call(success=True)
    monitor.record_api_call(success=False)
    monitor.record_api_call(success=True, rate_limited=True)
    
    report = monitor.get_health_report()
    
    assert report['api']['total_calls'] == 4, "Should track 4 API calls"
    assert report['api']['successful'] == 3, "Should track 3 successful calls"
    assert report['api']['failed'] == 1, "Should track 1 failed call"
    assert report['api']['rate_limited'] == 1, "Should track 1 rate limited call"
    assert report['api']['success_rate'] == 75.0, "Success rate should be 75%"
    
    print("✅ API call tracking test passed")


def test_position_tracking():
    """Test position tracking"""
    print("Testing position tracking...")
    monitor = HealthMonitor()
    
    # Open positions
    monitor.record_position_opened('BTC-USDT')
    monitor.record_position_opened('ETH-USDT')
    
    report = monitor.get_health_report()
    assert report['positions']['total_opened'] == 2, "Should track 2 opened positions"
    assert report['positions']['currently_open'] == 2, "Should have 2 open positions"
    
    # Close positions
    monitor.record_position_closed('BTC-USDT', 0.05, True)  # +5% win
    monitor.record_position_closed('ETH-USDT', -0.02, False)  # -2% loss
    
    report = monitor.get_health_report()
    assert report['positions']['total_closed'] == 2, "Should track 2 closed positions"
    assert report['positions']['currently_open'] == 0, "Should have 0 open positions"
    assert report['positions']['wins'] == 1, "Should track 1 win"
    assert report['positions']['losses'] == 1, "Should track 1 loss"
    assert report['positions']['win_rate'] == 50.0, "Win rate should be 50%"
    assert report['positions']['total_pnl'] == 0.03, "Total P/L should be +3%"
    
    print("✅ Position tracking test passed")


def test_scan_tracking():
    """Test scan tracking"""
    print("Testing scan tracking...")
    monitor = HealthMonitor()
    
    # Record scans
    monitor.record_scan_completed(5.2)
    monitor.record_scan_completed(4.8)
    monitor.record_scan_completed(6.0)
    monitor.record_scan_error()
    
    report = monitor.get_health_report()
    assert report['performance']['scans_completed'] == 3, "Should track 3 completed scans"
    assert report['performance']['scan_errors'] == 1, "Should track 1 scan error"
    
    avg_duration = report['performance']['avg_scan_duration']
    expected_avg = (5.2 + 4.8 + 6.0) / 3
    assert abs(avg_duration - expected_avg) < 0.01, f"Avg scan duration should be ~{expected_avg:.2f}s"
    
    print("✅ Scan tracking test passed")


def test_thread_health():
    """Test thread health monitoring"""
    print("Testing thread health monitoring...")
    monitor = HealthMonitor()
    
    # Initially, no heartbeats
    health = monitor.check_thread_health(timeout_seconds=1)
    assert not health['main_loop'], "Main loop should be unhealthy (no heartbeat)"
    assert not health['scanner'], "Scanner should be unhealthy (no heartbeat)"
    assert not health['position_monitor'], "Position monitor should be unhealthy (no heartbeat)"
    
    # Send heartbeats
    monitor.heartbeat_main_loop()
    monitor.heartbeat_scanner()
    monitor.heartbeat_position_monitor()
    
    # Check health immediately
    health = monitor.check_thread_health(timeout_seconds=1)
    assert health['main_loop'], "Main loop should be healthy"
    assert health['scanner'], "Scanner should be healthy"
    assert health['position_monitor'], "Position monitor should be healthy"
    
    # Wait for timeout
    time.sleep(2)
    
    # Check health again - should be unhealthy
    health = monitor.check_thread_health(timeout_seconds=1)
    assert not health['main_loop'], "Main loop should be unhealthy after timeout"
    assert not health['scanner'], "Scanner should be unhealthy after timeout"
    assert not health['position_monitor'], "Position monitor should be unhealthy after timeout"
    
    print("✅ Thread health monitoring test passed")


def test_error_tracking():
    """Test error tracking"""
    print("Testing error tracking...")
    monitor = HealthMonitor()
    
    # Record errors
    monitor.record_error('api', 'Connection timeout')
    monitor.record_error('scanner', 'Invalid data')
    monitor.record_error('main_loop', 'Unexpected exception')
    
    report = monitor.get_health_report()
    assert len(report['recent_errors']) == 3, "Should track 3 errors"
    assert report['recent_errors'][0]['type'] == 'api', "First error type should be 'api'"
    assert 'Connection timeout' in report['recent_errors'][0]['message'], "Should track error message"
    
    print("✅ Error tracking test passed")


def test_api_rate_calculation():
    """Test API calls per minute calculation"""
    print("Testing API calls per minute calculation...")
    monitor = HealthMonitor()
    
    # Record several calls
    for _ in range(10):
        monitor.record_api_call()
        time.sleep(0.1)
    
    # Should have ~10 calls in last minute
    rate = monitor.get_api_calls_per_minute()
    assert rate == 10, f"Should have 10 calls in last minute, got {rate}"
    
    print("✅ API rate calculation test passed")


def test_health_report():
    """Test comprehensive health report"""
    print("Testing comprehensive health report...")
    monitor = HealthMonitor()
    
    # Simulate some activity
    monitor.heartbeat_main_loop()
    monitor.heartbeat_scanner()
    monitor.heartbeat_position_monitor()
    
    monitor.record_api_call(success=True)
    monitor.record_api_call(success=True)
    
    monitor.record_position_opened('BTC-USDT')
    monitor.record_position_closed('BTC-USDT', 0.05, True)
    
    monitor.record_scan_completed(5.0)
    
    report = monitor.get_health_report()
    
    # Check report structure
    assert 'uptime' in report, "Report should have uptime"
    assert 'api' in report, "Report should have API section"
    assert 'positions' in report, "Report should have positions section"
    assert 'performance' in report, "Report should have performance section"
    assert 'threads' in report, "Report should have threads section"
    assert 'recent_errors' in report, "Report should have recent errors"
    assert 'overall_health' in report, "Report should have overall health status"
    
    # With good metrics, overall health should be true
    assert report['overall_health'], "Overall health should be true with good metrics"
    
    print("✅ Health report test passed")


def test_status_summary():
    """Test status summary formatting"""
    print("Testing status summary formatting...")
    monitor = HealthMonitor()
    
    # Add some data
    monitor.heartbeat_main_loop()
    monitor.heartbeat_scanner()
    monitor.heartbeat_position_monitor()
    
    monitor.record_position_opened('BTC-USDT')
    monitor.record_position_closed('BTC-USDT', 0.05, True)
    
    monitor.record_api_call(success=True)
    
    summary = monitor.get_status_summary()
    
    # Check that summary contains key sections
    assert 'BOT HEALTH STATUS' in summary, "Summary should have title"
    assert 'Uptime:' in summary, "Summary should show uptime"
    assert 'POSITIONS:' in summary, "Summary should have positions section"
    assert 'API HEALTH:' in summary, "Summary should have API section"
    assert 'THREADS:' in summary, "Summary should have threads section"
    assert 'PERFORMANCE:' in summary, "Summary should have performance section"
    assert 'Overall Health:' in summary, "Summary should have overall health"
    
    print("✅ Status summary formatting test passed")


def run_all_tests():
    """Run all health monitor tests"""
    print("=" * 60)
    print("🧪 HEALTH MONITOR TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_api_call_tracking,
        test_position_tracking,
        test_scan_tracking,
        test_thread_health,
        test_error_tracking,
        test_api_rate_calculation,
        test_health_report,
        test_status_summary,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{len(tests)} passed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
