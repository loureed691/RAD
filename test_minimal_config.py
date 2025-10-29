"""
Test minimal configuration setup - verify that only API credentials are required
"""
import os
import sys
import tempfile
from pathlib import Path

def test_minimal_env_config():
    """Test that bot can run with only API credentials in .env"""
    print("=" * 60)
    print("Testing Minimal Configuration")
    print("=" * 60)
    
    # Create a temporary .env file with only API credentials
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("KUCOIN_API_KEY=test_key_12345\n")
        f.write("KUCOIN_API_SECRET=test_secret_67890\n")
        f.write("KUCOIN_API_PASSPHRASE=test_passphrase\n")
        temp_env_path = f.name
    
    try:
        # Set environment variable to use our temp .env
        os.environ['DOTENV_PATH'] = temp_env_path
        
        # Load dotenv from temp file
        from dotenv import load_dotenv
        load_dotenv(temp_env_path, override=True)
        
        # Import config after setting env vars
        from config import Config
        
        # Verify API credentials are loaded
        print("\n1. Testing API Credentials:")
        assert Config.API_KEY == "test_key_12345", "API_KEY not loaded"
        assert Config.API_SECRET == "test_secret_67890", "API_SECRET not loaded"
        assert Config.API_PASSPHRASE == "test_passphrase", "API_PASSPHRASE not loaded"
        print("   ✓ API credentials loaded successfully")
        
        # Verify defaults are set
        print("\n2. Testing Default Values:")
        assert Config.ENABLE_WEBSOCKET == True, "WebSocket should be enabled by default"
        print(f"   ✓ ENABLE_WEBSOCKET: {Config.ENABLE_WEBSOCKET}")
        
        assert Config.ENABLE_DASHBOARD == True, "Dashboard should be enabled by default"
        print(f"   ✓ ENABLE_DASHBOARD: {Config.ENABLE_DASHBOARD}")
        
        assert Config.DASHBOARD_PORT == 5000, "Dashboard port should default to 5000"
        print(f"   ✓ DASHBOARD_PORT: {Config.DASHBOARD_PORT}")
        
        assert Config.CHECK_INTERVAL == 60, "CHECK_INTERVAL should default to 60"
        print(f"   ✓ CHECK_INTERVAL: {Config.CHECK_INTERVAL}s")
        
        assert Config.MAX_WORKERS == 20, "MAX_WORKERS should default to 20"
        print(f"   ✓ MAX_WORKERS: {Config.MAX_WORKERS}")
        
        assert Config.POSITION_UPDATE_INTERVAL == 3, "POSITION_UPDATE_INTERVAL should default to 3"
        print(f"   ✓ POSITION_UPDATE_INTERVAL: {Config.POSITION_UPDATE_INTERVAL}s")
        
        assert Config.LIVE_LOOP_INTERVAL == 0.1, "LIVE_LOOP_INTERVAL should default to 0.1"
        print(f"   ✓ LIVE_LOOP_INTERVAL: {Config.LIVE_LOOP_INTERVAL}s")
        
        assert Config.MAX_OPEN_POSITIONS == 3, "MAX_OPEN_POSITIONS should default to 3"
        print(f"   ✓ MAX_OPEN_POSITIONS: {Config.MAX_OPEN_POSITIONS}")
        
        assert Config.TRAILING_STOP_PERCENTAGE == 0.02, "TRAILING_STOP_PERCENTAGE should default to 0.02"
        print(f"   ✓ TRAILING_STOP_PERCENTAGE: {Config.TRAILING_STOP_PERCENTAGE}")
        
        # Verify DCA defaults
        print("\n3. Testing DCA Strategy Defaults:")
        assert Config.ENABLE_DCA == True, "DCA should be enabled by default"
        print(f"   ✓ ENABLE_DCA: {Config.ENABLE_DCA}")
        
        assert Config.DCA_ENTRY_ENABLED == True, "DCA entry should be enabled by default"
        print(f"   ✓ DCA_ENTRY_ENABLED: {Config.DCA_ENTRY_ENABLED}")
        
        assert Config.DCA_NUM_ENTRIES == 3, "DCA_NUM_ENTRIES should default to 3"
        print(f"   ✓ DCA_NUM_ENTRIES: {Config.DCA_NUM_ENTRIES}")
        
        # Verify Hedging defaults
        print("\n4. Testing Hedging Strategy Defaults:")
        assert Config.ENABLE_HEDGING == True, "Hedging should be enabled by default"
        print(f"   ✓ ENABLE_HEDGING: {Config.ENABLE_HEDGING}")
        
        assert Config.HEDGE_DRAWDOWN_THRESHOLD == 0.10, "HEDGE_DRAWDOWN_THRESHOLD should default to 0.10"
        print(f"   ✓ HEDGE_DRAWDOWN_THRESHOLD: {Config.HEDGE_DRAWDOWN_THRESHOLD}")
        
        # Verify auto-configurable params are None initially
        print("\n5. Testing Auto-Configurable Parameters:")
        assert Config.LEVERAGE is None, "LEVERAGE should be None before auto-config"
        print("   ✓ LEVERAGE: None (will be auto-configured)")
        
        assert Config.MAX_POSITION_SIZE is None, "MAX_POSITION_SIZE should be None before auto-config"
        print("   ✓ MAX_POSITION_SIZE: None (will be auto-configured)")
        
        assert Config.RISK_PER_TRADE is None, "RISK_PER_TRADE should be None before auto-config"
        print("   ✓ RISK_PER_TRADE: None (will be auto-configured)")
        
        assert Config.MIN_PROFIT_THRESHOLD is None, "MIN_PROFIT_THRESHOLD should be None before auto-config"
        print("   ✓ MIN_PROFIT_THRESHOLD: None (will be auto-configured)")
        
        # Test auto-configuration with different balance tiers
        print("\n6. Testing Auto-Configuration by Balance Tier:")
        
        # Micro account ($50)
        Config.auto_configure_from_balance(50)
        assert Config.LEVERAGE == 4, "Micro account should get 4x leverage"
        assert Config.RISK_PER_TRADE == 0.01, "Micro account should get 1% risk"
        print(f"   ✓ Micro ($50): {Config.LEVERAGE}x leverage, {Config.RISK_PER_TRADE:.1%} risk")
        
        # Small account ($500)
        Config.auto_configure_from_balance(500)
        assert Config.LEVERAGE == 6, "Small account should get 6x leverage"
        assert Config.RISK_PER_TRADE == 0.015, "Small account should get 1.5% risk"
        print(f"   ✓ Small ($500): {Config.LEVERAGE}x leverage, {Config.RISK_PER_TRADE:.1%} risk")
        
        # Medium account ($5000)
        Config.auto_configure_from_balance(5000)
        assert Config.LEVERAGE == 8, "Medium account should get 8x leverage"
        assert Config.RISK_PER_TRADE == 0.02, "Medium account should get 2% risk"
        print(f"   ✓ Medium ($5000): {Config.LEVERAGE}x leverage, {Config.RISK_PER_TRADE:.1%} risk")
        
        # Large account ($50000)
        Config.auto_configure_from_balance(50000)
        assert Config.LEVERAGE == 10, "Large account should get 10x leverage"
        assert Config.RISK_PER_TRADE == 0.025, "Large account should get 2.5% risk"
        print(f"   ✓ Large ($50000): {Config.LEVERAGE}x leverage, {Config.RISK_PER_TRADE:.1%} risk")
        
        # Very large account ($150000)
        Config.auto_configure_from_balance(150000)
        assert Config.LEVERAGE == 12, "Very large account should get 12x leverage"
        assert Config.RISK_PER_TRADE == 0.03, "Very large account should get 3% risk"
        print(f"   ✓ Very Large ($150000): {Config.LEVERAGE}x leverage, {Config.RISK_PER_TRADE:.1%} risk")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nMinimal configuration is working correctly!")
        print("Users only need to provide KuCoin API credentials.")
        print("All other parameters auto-configure with optimal defaults.")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_env_path)
        except (OSError, FileNotFoundError):
            pass


def test_env_example_simplicity():
    """Test that .env.example is minimal and only requires API credentials"""
    print("\n" + "=" * 60)
    print("Testing .env.example Simplicity")
    print("=" * 60)
    
    env_example_path = Path('.env.example')
    if not env_example_path.exists():
        print("❌ .env.example not found")
        return False
    
    content = env_example_path.read_text()
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
    
    print(f"\nRequired configuration lines: {len(lines)}")
    
    # Check that only API credentials are uncommented
    required_vars = []
    for line in lines:
        if '=' in line:
            var_name = line.split('=')[0].strip()
            required_vars.append(var_name)
    
    print(f"Required variables: {required_vars}")
    
    # Should only have 3 required variables (API credentials)
    assert len(required_vars) == 3, f"Expected 3 required vars, got {len(required_vars)}"
    assert 'KUCOIN_API_KEY' in required_vars, "KUCOIN_API_KEY should be required"
    assert 'KUCOIN_API_SECRET' in required_vars, "KUCOIN_API_SECRET should be required"
    assert 'KUCOIN_API_PASSPHRASE' in required_vars, "KUCOIN_API_PASSPHRASE should be required"
    
    print("✓ Only API credentials are required (3 variables)")
    print("✓ All other parameters are optional and auto-configured")
    
    return True


if __name__ == "__main__":
    print("\n🧪 Running Minimal Configuration Tests\n")
    
    success = True
    
    # Test 1: Minimal config functionality
    if not test_minimal_env_config():
        success = False
    
    # Test 2: .env.example simplicity
    if not test_env_example_simplicity():
        success = False
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Configuration is minimal and adaptive!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
