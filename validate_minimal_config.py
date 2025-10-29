"""
Quick validation that bot can initialize with minimal configuration
"""
import os
import sys
import tempfile

def validate_minimal_config():
    """Validate that bot can initialize with only API credentials"""
    print("=" * 60)
    print("Validating Minimal Configuration Bot Initialization")
    print("=" * 60)
    
    # Create a temporary .env with only API credentials
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("KUCOIN_API_KEY=test_key_validation\n")
        f.write("KUCOIN_API_SECRET=test_secret_validation\n")
        f.write("KUCOIN_API_PASSPHRASE=test_passphrase_validation\n")
        temp_env_path = f.name
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv(temp_env_path, override=True)
        
        # Try to import and validate config
        print("\n1. Testing Config Import:")
        from config import Config
        print("   ✓ Config imported successfully")
        
        # Verify API credentials loaded
        print("\n2. Testing API Credentials:")
        assert Config.API_KEY == "test_key_validation"
        assert Config.API_SECRET == "test_secret_validation"
        assert Config.API_PASSPHRASE == "test_passphrase_validation"
        print("   ✓ API credentials loaded correctly")
        
        # Verify all defaults are set
        print("\n3. Testing Default Configuration:")
        checks = [
            ("ENABLE_WEBSOCKET", Config.ENABLE_WEBSOCKET, True),
            ("ENABLE_DASHBOARD", Config.ENABLE_DASHBOARD, True),
            ("DASHBOARD_PORT", Config.DASHBOARD_PORT, 5000),
            ("CHECK_INTERVAL", Config.CHECK_INTERVAL, 60),
            ("MAX_WORKERS", Config.MAX_WORKERS, 20),
            ("POSITION_UPDATE_INTERVAL", Config.POSITION_UPDATE_INTERVAL, 3),
            ("LIVE_LOOP_INTERVAL", Config.LIVE_LOOP_INTERVAL, 0.1),
            ("MAX_OPEN_POSITIONS", Config.MAX_OPEN_POSITIONS, 3),
            ("ENABLE_DCA", Config.ENABLE_DCA, True),
            ("ENABLE_HEDGING", Config.ENABLE_HEDGING, True),
        ]
        
        for name, actual, expected in checks:
            assert actual == expected, f"{name}: expected {expected}, got {actual}"
            print(f"   ✓ {name}: {actual}")
        
        # Verify auto-config params are None before balance fetch
        print("\n4. Testing Auto-Config Parameters (Before Balance):")
        assert Config.LEVERAGE is None, "LEVERAGE should be None"
        assert Config.MAX_POSITION_SIZE is None, "MAX_POSITION_SIZE should be None"
        assert Config.RISK_PER_TRADE is None, "RISK_PER_TRADE should be None"
        assert Config.MIN_PROFIT_THRESHOLD is None, "MIN_PROFIT_THRESHOLD should be None"
        print("   ✓ All auto-config parameters are None (awaiting balance)")
        
        # Test auto-configuration
        print("\n5. Testing Auto-Configuration with $5000 Balance:")
        Config.auto_configure_from_balance(5000)
        assert Config.LEVERAGE == 8, f"Expected 8x leverage, got {Config.LEVERAGE}"
        assert Config.MAX_POSITION_SIZE == 2500, f"Expected $2500 position size, got {Config.MAX_POSITION_SIZE}"
        assert Config.RISK_PER_TRADE == 0.02, f"Expected 2% risk, got {Config.RISK_PER_TRADE}"
        print(f"   ✓ LEVERAGE: {Config.LEVERAGE}x")
        print(f"   ✓ MAX_POSITION_SIZE: ${Config.MAX_POSITION_SIZE}")
        print(f"   ✓ RISK_PER_TRADE: {Config.RISK_PER_TRADE:.1%}")
        print(f"   ✓ MIN_PROFIT_THRESHOLD: {Config.MIN_PROFIT_THRESHOLD:.2%}")
        
        # Test validation
        print("\n6. Testing Config Validation:")
        try:
            Config.validate()
            print("   ✓ Configuration validation passed")
        except Exception as e:
            print(f"   ✗ Validation failed: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ VALIDATION SUCCESSFUL!")
        print("=" * 60)
        print("\nBot can initialize with minimal configuration:")
        print("  • Only 3 lines needed (API credentials)")
        print("  • All features auto-configure")
        print("  • Settings adapt to account balance")
        print("  • Validation passes")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            os.unlink(temp_env_path)
        except:
            pass


if __name__ == "__main__":
    print("\n🔍 Running Configuration Validation\n")
    
    if validate_minimal_config():
        print("\n✅ All validation checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Validation failed!")
        sys.exit(1)
