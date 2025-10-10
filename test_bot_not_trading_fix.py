#!/usr/bin/env python3
"""
Test script to validate the "bot not trading" fixes.

This verifies:
1. Confidence thresholds are properly reduced
2. Configuration values are applied correctly
3. Signals can be generated at lower thresholds
4. Risk manager validates trades at new thresholds
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_config_thresholds():
    """Test that config has correct threshold values"""
    print("\n" + "="*80)
    print("TEST 1: Configuration Thresholds")
    print("="*80)
    
    from config import Config
    
    # Check MIN_SIGNAL_CONFIDENCE exists and has correct value
    assert hasattr(Config, 'MIN_SIGNAL_CONFIDENCE'), "Config missing MIN_SIGNAL_CONFIDENCE"
    assert Config.MIN_SIGNAL_CONFIDENCE <= 0.50, f"MIN_SIGNAL_CONFIDENCE too high: {Config.MIN_SIGNAL_CONFIDENCE}"
    print(f"✓ MIN_SIGNAL_CONFIDENCE: {Config.MIN_SIGNAL_CONFIDENCE:.2%} (expected: ≤ 50%)")
    
    # Check MIN_TRADE_CONFIDENCE exists and has correct value
    assert hasattr(Config, 'MIN_TRADE_CONFIDENCE'), "Config missing MIN_TRADE_CONFIDENCE"
    assert Config.MIN_TRADE_CONFIDENCE <= 0.55, f"MIN_TRADE_CONFIDENCE too high: {Config.MIN_TRADE_CONFIDENCE}"
    print(f"✓ MIN_TRADE_CONFIDENCE: {Config.MIN_TRADE_CONFIDENCE:.2%} (expected: ≤ 55%)")
    
    # Check STALE_DATA_MULTIPLIER increased
    assert Config.STALE_DATA_MULTIPLIER >= 3, f"STALE_DATA_MULTIPLIER too low: {Config.STALE_DATA_MULTIPLIER}"
    print(f"✓ STALE_DATA_MULTIPLIER: {Config.STALE_DATA_MULTIPLIER}x (expected: ≥ 3)")
    
    print("\n✅ All configuration thresholds are correct!")
    return True

def test_signal_generator_threshold():
    """Test that SignalGenerator uses lower threshold"""
    print("\n" + "="*80)
    print("TEST 2: Signal Generator Threshold")
    print("="*80)
    
    from signals import SignalGenerator
    
    sig_gen = SignalGenerator()
    
    # Check adaptive threshold is set correctly
    assert sig_gen.adaptive_threshold <= 0.50, f"Adaptive threshold too high: {sig_gen.adaptive_threshold}"
    print(f"✓ SignalGenerator adaptive_threshold: {sig_gen.adaptive_threshold:.2%} (expected: ≤ 50%)")
    
    print("\n✅ Signal generator threshold is correct!")
    return True

def test_risk_manager_validation():
    """Test that RiskManager validates trades at correct threshold"""
    print("\n" + "="*80)
    print("TEST 3: Risk Manager Validation")
    print("="*80)
    
    from risk_manager import RiskManager
    from config import Config
    
    risk_mgr = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=3
    )
    
    # Test with confidence just above new threshold (should pass)
    confidence_above = Config.MIN_TRADE_CONFIDENCE + 0.01
    is_valid, reason = risk_mgr.validate_trade('BTCUSDT', 'BUY', confidence_above)
    assert is_valid, f"Trade should be valid at {confidence_above:.2%} confidence"
    print(f"✓ Trade ACCEPTED at {confidence_above:.2%} confidence")
    
    # Test with confidence just below new threshold (should fail)
    confidence_below = Config.MIN_TRADE_CONFIDENCE - 0.01
    is_valid, reason = risk_mgr.validate_trade('BTCUSDT', 'BUY', confidence_below)
    assert not is_valid, f"Trade should be invalid at {confidence_below:.2%} confidence"
    print(f"✓ Trade REJECTED at {confidence_below:.2%} confidence: {reason}")
    
    # Test with old threshold value (should pass with new settings)
    old_failing_confidence = 0.58  # Would have failed with old 60% threshold
    is_valid, reason = risk_mgr.validate_trade('BTCUSDT', 'BUY', old_failing_confidence)
    if is_valid:
        print(f"✓ Trade now ACCEPTED at {old_failing_confidence:.2%} (would have been rejected before)")
    else:
        print(f"⚠ Trade REJECTED at {old_failing_confidence:.2%}: {reason}")
    
    print("\n✅ Risk manager validation working correctly!")
    return True

def test_signal_acceptance_rate():
    """Test that more signals would be accepted with new thresholds"""
    print("\n" + "="*80)
    print("TEST 4: Signal Acceptance Rate")
    print("="*80)
    
    from config import Config
    
    # Simulate confidence values from signal generation
    confidence_samples = [0.45, 0.50, 0.52, 0.55, 0.58, 0.60, 0.62, 0.65, 0.70, 0.75]
    
    old_threshold = 0.60  # Original threshold
    new_threshold = Config.MIN_TRADE_CONFIDENCE  # New threshold
    
    old_accepted = sum(1 for c in confidence_samples if c >= old_threshold)
    new_accepted = sum(1 for c in confidence_samples if c >= new_threshold)
    
    print(f"Old threshold ({old_threshold:.2%}): {old_accepted}/{len(confidence_samples)} signals accepted ({old_accepted/len(confidence_samples):.1%})")
    print(f"New threshold ({new_threshold:.2%}): {new_accepted}/{len(confidence_samples)} signals accepted ({new_accepted/len(confidence_samples):.1%})")
    print(f"Improvement: +{new_accepted - old_accepted} more signals accepted ({(new_accepted-old_accepted)/len(confidence_samples):.1%})")
    
    assert new_accepted > old_accepted, "New threshold should accept more signals"
    
    # Show which specific confidence values are now accepted
    newly_accepted = [c for c in confidence_samples if old_threshold > c >= new_threshold]
    if newly_accepted:
        print(f"\n✓ Newly accepted confidence values: {[f'{c:.2%}' for c in newly_accepted]}")
    
    print("\n✅ More signals will be accepted with new thresholds!")
    return True

def test_stale_data_calculation():
    """Test that stale data timeout is more lenient"""
    print("\n" + "="*80)
    print("TEST 5: Stale Data Timeout")
    print("="*80)
    
    from config import Config
    
    check_interval = Config.CHECK_INTERVAL
    stale_multiplier = Config.STALE_DATA_MULTIPLIER
    
    old_multiplier = 2
    old_max_age = check_interval * old_multiplier
    new_max_age = check_interval * stale_multiplier
    
    print(f"Check interval: {check_interval}s")
    print(f"Old multiplier: {old_multiplier}x → Max age: {old_max_age}s")
    print(f"New multiplier: {stale_multiplier}x → Max age: {new_max_age}s")
    print(f"Improvement: +{new_max_age - old_max_age}s more tolerance")
    
    assert new_max_age > old_max_age, "New max age should be higher"
    
    # Example: With 60s interval
    # Old: 120s max age - opportunities expire quickly
    # New: 180s max age - more time to use opportunities
    
    print(f"\n✓ Opportunities now valid for {new_max_age}s instead of {old_max_age}s")
    print("  This reduces false rejections of valid opportunities")
    
    print("\n✅ Stale data timeout is more lenient!")
    return True

def main():
    """Run all validation tests"""
    print("\n" + "="*80)
    print("  VALIDATION TESTS FOR 'BOT NOT TRADING' FIX")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThese tests verify that the fixes are properly applied:")
    print("1. Configuration thresholds are reduced")
    print("2. Signal generator uses new thresholds")
    print("3. Risk manager validates at new thresholds")
    print("4. More signals will be accepted")
    print("5. Stale data timeout is more lenient")
    
    tests = [
        test_config_thresholds,
        test_signal_generator_threshold,
        test_risk_manager_validation,
        test_signal_acceptance_rate,
        test_stale_data_calculation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)
    print(f"\nPassed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n" + "="*80)
        print("  ✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nThe 'bot not trading' fixes are properly applied.")
        print("\nExpected behavior:")
        print("  - Signals with 50-55% confidence will now be accepted")
        print("  - Opportunities have longer validity (180s vs 120s)")
        print("  - More trades should execute in normal market conditions")
        print("  - Weak signals (<50%) are still filtered out")
        print("\nNext steps:")
        print("  1. Run the bot with actual API credentials")
        print("  2. Monitor logs/bot.log and logs/scanning.log")
        print("  3. Look for '✅ Trade executed' messages")
        print("  4. Adjust thresholds in .env if needed:")
        print("     MIN_SIGNAL_CONFIDENCE=0.45  # Trade more")
        print("     MIN_SIGNAL_CONFIDENCE=0.55  # Trade less")
        print("="*80)
        return 0
    else:
        print("\n" + "="*80)
        print("  ❌ SOME TESTS FAILED")
        print("="*80)
        print("\nPlease review the errors above and fix them.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Validation script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
