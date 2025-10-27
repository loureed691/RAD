"""
Integration test for bot state lifecycle
Simulates bot startup, operation, shutdown, and restart to verify state persistence
"""
import os
import shutil
from datetime import datetime
from unittest.mock import MagicMock, patch

from advanced_analytics import AdvancedAnalytics
from risk_manager import RiskManager
from attention_features_2025 import AttentionFeatureSelector


def test_bot_lifecycle():
    """
    Simulate a complete bot lifecycle:
    1. Bot starts and initializes components
    2. Bot runs and accumulates data
    3. Bot shuts down and saves state
    4. Bot restarts and verifies state is restored
    """
    print("=" * 70)
    print("BOT STATE LIFECYCLE TEST")
    print("=" * 70)
    
    # Clean up any existing state files
    print("\n1. Cleaning up existing state files...")
    if os.path.exists('models'):
        shutil.rmtree('models')
    os.makedirs('models', exist_ok=True)
    print("   ✓ Clean environment ready")
    
    # ===== FIRST LIFECYCLE: Initialize and accumulate data =====
    print("\n2. First lifecycle - Bot startup and data accumulation...")
    
    # Initialize components (first time, no state to load)
    analytics1 = AdvancedAnalytics()
    risk1 = RiskManager(1000, 0.02, 5)
    attention1 = AttentionFeatureSelector(31)
    
    print(f"   Initial state:")
    print(f"   - Analytics: {len(analytics1.trade_history)} trades")
    print(f"   - Risk Manager: {risk1.total_trades} trades tracked")
    print(f"   - Attention: weights sum = {attention1.attention_weights.sum():.4f}")
    
    # Simulate bot operation - record some trades
    print("\n3. Simulating trading activity...")
    for i in range(5):
        analytics1.record_trade({
            'symbol': f'TEST-{i}',
            'side': 'long' if i % 2 == 0 else 'short',
            'entry_price': 100 + i,
            'exit_price': 102 + i,
            'pnl': 0.01 + i * 0.005,
            'pnl_pct': 0.01 + i * 0.005,
            'duration': 30 + i * 10,
            'leverage': 10
        })
        
        # Record in risk manager
        risk1.record_trade_outcome(0.01 + i * 0.005)
    
    # Record some equity points
    for balance in [10000, 10050, 10150, 10120, 10200]:
        analytics1.record_equity(balance)
    
    # Update risk manager state
    risk1.peak_balance = 10200
    risk1.current_drawdown = -0.008
    
    # Modify attention weights (simulate learning)
    import numpy as np
    attention1.attention_weights *= np.random.uniform(0.8, 1.2, 31)
    attention1.attention_weights /= attention1.attention_weights.sum()
    
    print(f"   After trading:")
    print(f"   - Analytics: {len(analytics1.trade_history)} trades, {len(analytics1.equity_curve)} equity points")
    print(f"   - Risk Manager: {risk1.total_trades} trades, Win rate: {risk1.get_win_rate():.1%}")
    print(f"   - Attention: weights modified (sum = {attention1.attention_weights.sum():.4f})")
    
    # Save state (simulating shutdown)
    print("\n4. Saving state (simulating bot shutdown)...")
    analytics1.save_state()
    risk1.save_state()
    attention1.save_weights()
    print("   ✓ All states saved")
    
    # Verify files exist
    assert os.path.exists(analytics1.state_path), "Analytics state file not created"
    assert os.path.exists(risk1.state_path), "Risk manager state file not created"
    assert os.path.exists('models/attention_weights.npy'), "Attention weights file not created"
    print("   ✓ All state files verified")
    
    # ===== SECOND LIFECYCLE: Restart and verify restoration =====
    print("\n5. Second lifecycle - Bot restart and state restoration...")
    
    # Create new instances (simulating bot restart)
    analytics2 = AdvancedAnalytics()
    risk2 = RiskManager(1000, 0.02, 5)
    attention2 = AttentionFeatureSelector(31)
    
    print(f"   After restart:")
    print(f"   - Analytics: {len(analytics2.trade_history)} trades, {len(analytics2.equity_curve)} equity points")
    print(f"   - Risk Manager: {risk2.total_trades} trades, Win rate: {risk2.get_win_rate():.1%}")
    print(f"   - Attention: weights sum = {attention2.attention_weights.sum():.4f}")
    
    # ===== VERIFICATION =====
    print("\n6. Verifying state restoration...")
    
    # Verify analytics
    assert len(analytics2.trade_history) == 5, f"Expected 5 trades, got {len(analytics2.trade_history)}"
    assert len(analytics2.equity_curve) == 5, f"Expected 5 equity points, got {len(analytics2.equity_curve)}"
    assert analytics2.trade_history[0]['symbol'] == 'TEST-0'
    assert analytics2.equity_curve[-1]['balance'] == 10200
    print("   ✓ Analytics state restored correctly")
    
    # Verify risk manager
    assert risk2.total_trades == 5, f"Expected 5 trades, got {risk2.total_trades}"
    assert risk2.wins == 5, f"Expected 5 wins, got {risk2.wins}"
    assert risk2.losses == 0, f"Expected 0 losses, got {risk2.losses}"
    assert risk2.peak_balance == 10200
    assert abs(risk2.current_drawdown - (-0.008)) < 0.0001
    print("   ✓ Risk manager state restored correctly")
    
    # Verify attention weights
    np.testing.assert_array_almost_equal(
        attention1.attention_weights,
        attention2.attention_weights,
        decimal=6,
        err_msg="Attention weights not restored correctly"
    )
    print("   ✓ Attention weights restored correctly")
    
    # ===== CLEANUP =====
    print("\n7. Cleaning up test environment...")
    if os.path.exists('models'):
        shutil.rmtree('models')
    print("   ✓ Cleanup complete")
    
    print("\n" + "=" * 70)
    print("✅ BOT STATE LIFECYCLE TEST PASSED")
    print("=" * 70)
    print("\nSummary:")
    print("- State is correctly saved during shutdown")
    print("- State is correctly restored on restart")
    print("- All components maintain their data across lifecycles")
    print("- Bot can resume operations seamlessly after restart")


if __name__ == '__main__':
    try:
        test_bot_lifecycle()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise
