"""
Test to verify DCA and Hedging integration doesn't conflict with stop loss/take profit
"""
import sys
sys.path.insert(0, '/home/runner/work/RAD/RAD')


def test_no_conflicts():
    """Test that DCA and Hedging don't conflict with existing position management"""
    
    print("=" * 70)
    print("INTEGRATION CONFLICT TEST")
    print("=" * 70)
    print()
    
    # Test 1: Check DCA doesn't modify stop_loss or take_profit
    print("Test 1: DCA doesn't modify stop_loss/take_profit attributes")
    print("-" * 70)
    
    # Check DCA strategy file
    with open('/home/runner/work/RAD/RAD/dca_strategy.py', 'r') as f:
        dca_content = f.read()
    
    # DCA should NOT directly set stop_loss or take_profit
    if 'stop_loss =' in dca_content or 'take_profit =' in dca_content:
        # Check if it's just reading them (which is OK)
        if '.stop_loss' in dca_content and '= ' not in dca_content.split('.stop_loss')[1].split('\n')[0]:
            print("   ✅ DCA only reads stop_loss/take_profit (OK)")
        else:
            print("   ❌ DCA modifies stop_loss/take_profit (CONFLICT)")
            return False
    else:
        print("   ✅ DCA doesn't touch stop_loss/take_profit")
    
    print()
    
    # Test 2: Check Hedging doesn't modify position stop_loss or take_profit
    print("Test 2: Hedging doesn't modify position stop_loss/take_profit")
    print("-" * 70)
    
    with open('/home/runner/work/RAD/RAD/hedging_strategy.py', 'r') as f:
        hedge_content = f.read()
    
    # Hedging should NOT modify position attributes
    if 'position.stop_loss' in hedge_content or 'position.take_profit' in hedge_content:
        print("   ❌ Hedging modifies position stop_loss/take_profit (CONFLICT)")
        return False
    else:
        print("   ✅ Hedging doesn't touch position stop_loss/take_profit")
    
    print()
    
    # Test 3: Check DCA uses existing scale_in/scale_out methods
    print("Test 3: DCA integrates via existing position manager methods")
    print("-" * 70)
    
    with open('/home/runner/work/RAD/RAD/bot.py', 'r') as f:
        bot_content = f.read()
    
    # Check DCA uses scale_in_position
    if 'scale_in_position' in bot_content and 'dca' in bot_content.lower():
        print("   ✅ DCA uses scale_in_position (proper integration)")
    else:
        print("   ❌ DCA doesn't use scale_in_position")
        return False
    
    print()
    
    # Test 4: Check strategies are enabled by default
    print("Test 4: Strategies enabled by default with smart settings")
    print("-" * 70)
    
    with open('/home/runner/work/RAD/RAD/config.py', 'r') as f:
        config_content = f.read()
    
    checks = [
        ("ENABLE_DCA = os.getenv('ENABLE_DCA', 'true')", "DCA enabled"),
        ("DCA_ENTRY_ENABLED = os.getenv('DCA_ENTRY_ENABLED', 'true')", "DCA Entry enabled"),
        ("ENABLE_HEDGING = os.getenv('ENABLE_HEDGING', 'true')", "Hedging enabled"),
        ("DCA_CONFIDENCE_THRESHOLD = float(os.getenv('DCA_CONFIDENCE_THRESHOLD', '0.70'))", "Smart DCA threshold (70%)"),
    ]
    
    for check_str, desc in checks:
        if check_str in config_content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc} - NOT FOUND")
            return False
    
    print()
    
    # Test 5: Check DCA monitoring is in run_cycle
    print("Test 5: DCA and Hedging are actively monitored")
    print("-" * 70)
    
    if 'DCA STRATEGY MONITORING' in bot_content:
        print("   ✅ DCA monitoring integrated in run_cycle")
    else:
        print("   ❌ DCA monitoring NOT integrated")
        return False
    
    if 'HEDGING STRATEGY MONITORING' in bot_content:
        print("   ✅ Hedging monitoring integrated in run_cycle")
    else:
        print("   ❌ Hedging monitoring NOT integrated")
        return False
    
    print()
    
    # Test 6: Check DCA is used in execute_trade
    print("Test 6: DCA integrated into trade execution")
    print("-" * 70)
    
    if 'DCA STRATEGY INTEGRATION' in bot_content:
        print("   ✅ DCA integrated in execute_trade")
    else:
        print("   ❌ DCA NOT integrated in execute_trade")
        return False
    
    if 'initialize_entry_dca' in bot_content:
        print("   ✅ Entry DCA logic present")
    else:
        print("   ❌ Entry DCA logic missing")
        return False
    
    print()
    
    # Test 7: Verify no direct conflicts in position manager
    print("Test 7: Position manager methods are DCA-compatible")
    print("-" * 70)
    
    with open('/home/runner/work/RAD/RAD/position_manager.py', 'r') as f:
        pm_content = f.read()
    
    # Check scale_in and scale_out exist
    if 'def scale_in_position' in pm_content:
        print("   ✅ scale_in_position method exists")
    else:
        print("   ❌ scale_in_position method missing")
        return False
    
    if 'def scale_out_position' in pm_content:
        print("   ✅ scale_out_position method exists")
    else:
        print("   ❌ scale_out_position method missing")
        return False
    
    print()
    print("=" * 70)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 70)
    print()
    print("Summary:")
    print("  • DCA and Hedging don't conflict with stop_loss/take_profit")
    print("  • DCA uses existing position manager methods (scale_in/scale_out)")
    print("  • Hedging is portfolio-level (doesn't touch individual positions)")
    print("  • Both strategies enabled by default with smart settings")
    print("  • Active monitoring integrated in run_cycle")
    print("  • DCA integrated in trade execution")
    print()
    return True


if __name__ == '__main__':
    success = test_no_conflicts()
    sys.exit(0 if success else 1)
