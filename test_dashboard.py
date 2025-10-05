#!/usr/bin/env python3
"""
Test script to verify the web dashboard functionality
"""
import time
import requests
from dashboard import BotDashboard

def test_dashboard():
    """Test the dashboard functionality"""
    print("=" * 60)
    print("🧪 Testing Web Dashboard")
    print("=" * 60)
    
    # Initialize dashboard
    print("\n1. Initializing dashboard...")
    dashboard = BotDashboard(port=5001)  # Use different port for testing
    
    # Start dashboard
    print("2. Starting dashboard server...")
    dashboard.start()
    
    # Give server time to start
    time.sleep(2)
    
    # Test health endpoint
    print("3. Testing health endpoint...")
    try:
        response = requests.get('http://localhost:5001/api/health')
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Failed to connect to dashboard: {e}")
        return False
    
    # Update some test data
    print("4. Updating test data...")
    dashboard.update_status('running')
    dashboard.update_balance(10000.50)
    dashboard.update_config({
        'leverage': 10,
        'max_positions': 3,
        'risk_per_trade': 0.02,
        'check_interval': 300
    })
    
    dashboard.update_positions([
        {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'entry_price': 45000.0,
            'current_price': 45500.0,
            'amount': 0.1,
            'leverage': 10,
            'pnl': 0.011
        }
    ])
    
    dashboard.add_trade({
        'symbol': 'ETHUSDT',
        'side': 'short',
        'entry_price': 2500.0,
        'exit_price': 2450.0,
        'pnl': 0.02,
        'duration': 120
    })
    
    dashboard.update_performance({
        'total_trades': 10,
        'winning_trades': 6,
        'losing_trades': 4,
        'win_rate': 0.6,
        'total_pnl': 0.15,
        'avg_win': 0.03,
        'avg_loss': -0.015,
        'profit_factor': 2.0
    })
    
    dashboard.update_opportunities([
        {
            'symbol': 'ADAUSDT',
            'signal': 'BUY',
            'score': 8.5,
            'confidence': 0.75,
            'price': 0.45
        }
    ])
    
    dashboard.update_uptime(3600)
    
    # Test API endpoints
    print("5. Testing API endpoints...")
    endpoints = [
        '/api/status',
        '/api/positions',
        '/api/trades?limit=10',
        '/api/performance',
        '/api/opportunities',
        '/api/config'
    ]
    
    all_passed = True
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:5001{endpoint}')
            if response.status_code == 200:
                print(f"   ✅ {endpoint}")
            else:
                print(f"   ❌ {endpoint} - Status: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")
            all_passed = False
    
    # Test main page
    print("6. Testing main dashboard page...")
    try:
        response = requests.get('http://localhost:5001/')
        if response.status_code == 200 and 'RAD Trading Bot' in response.text:
            print("   ✅ Main page loads successfully")
        else:
            print(f"   ❌ Main page failed: {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Main page error: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All dashboard tests passed!")
        print(f"\n🌐 Test dashboard running at: http://localhost:5001")
        print("💡 Open this URL in your browser to see the test data")
        print("💡 Press Ctrl+C to stop the test server")
        print("=" * 60)
        
        # Keep server running to allow manual inspection
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Test stopped")
    else:
        print("❌ Some tests failed")
        print("=" * 60)
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_dashboard()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
