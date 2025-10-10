"""
Test to verify the reduce_only parameter fix in scale_out_position
"""

def test_scale_out_uses_reduce_only():
    """Verify that scale_out_position passes reduce_only=True to create_market_order"""
    
    print("\n" + "="*80)
    print("TEST: Verify scale_out_position passes reduce_only=True")
    print("="*80)
    
    # Read source code directly from file
    with open('position_manager.py', 'r') as f:
        content = f.read()
    
    # Find the scale_out_position method
    scale_out_start = content.find('def scale_out_position(')
    if scale_out_start == -1:
        print("✗ Could not find scale_out_position method")
        return False
    
    # Find the next method definition (end of scale_out_position)
    next_def = content.find('\n    def ', scale_out_start + 1)
    scale_out_source = content[scale_out_start:next_def] if next_def != -1 else content[scale_out_start:]
    
    # Check if the method contains create_market_order call with reduce_only=True
    has_create_market = 'create_market_order' in scale_out_source
    has_reduce_only = 'reduce_only=True' in scale_out_source
    
    print(f"  Contains create_market_order: {has_create_market}")
    print(f"  Contains reduce_only=True: {has_reduce_only}")
    
    if has_create_market and has_reduce_only:
        print("\n✓ scale_out_position correctly passes reduce_only=True")
        print("✓ Closing orders will bypass margin checks")
        print("✓ Orders will only reduce positions, not create new ones")
        return True
    else:
        print("\n✗ scale_out_position does NOT pass reduce_only=True")
        print("✗ This can cause orders to fail or create new positions")
        return False


def test_pattern_consistency():
    """Verify that scale_out_position follows the same pattern as close_position"""
    
    print("\n" + "="*80)
    print("TEST: Verify pattern consistency across methods")
    print("="*80)
    
    # Read source code from files
    with open('position_manager.py', 'r') as f:
        pm_content = f.read()
    
    with open('kucoin_client.py', 'r') as f:
        kc_content = f.read()
    
    # Find scale_out_position method
    scale_out_start = pm_content.find('def scale_out_position(')
    next_def = pm_content.find('\n    def ', scale_out_start + 1)
    scale_out_source = pm_content[scale_out_start:next_def] if next_def != -1 else pm_content[scale_out_start:]
    
    # Find close_position method in kucoin_client
    close_pos_start = kc_content.find('def close_position(')
    next_def = kc_content.find('\n    def ', close_pos_start + 1)
    close_pos_source = kc_content[close_pos_start:next_def] if next_def != -1 else kc_content[close_pos_start:]
    
    # Both should use reduce_only=True
    scale_out_has_reduce = 'reduce_only=True' in scale_out_source
    close_pos_has_reduce = 'reduce_only=True' in close_pos_source
    
    print(f"  scale_out_position uses reduce_only=True: {scale_out_has_reduce}")
    print(f"  kucoin_client.close_position uses reduce_only=True: {close_pos_has_reduce}")
    
    if scale_out_has_reduce and close_pos_has_reduce:
        print("\n✓ Pattern is consistent across both methods")
        return True
    else:
        print("\n✗ Pattern inconsistency detected")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("REDUCE_ONLY FIX VALIDATION")
    print("="*80)
    
    test1 = test_scale_out_uses_reduce_only()
    test2 = test_pattern_consistency()
    
    print("\n" + "="*80)
    if test1 and test2:
        print("ALL TESTS PASSED ✓")
        print("="*80)
        return 0
    else:
        print("SOME TESTS FAILED ✗")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit(main())
