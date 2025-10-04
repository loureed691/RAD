"""
Tests for trading strategy optimizations
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_kelly_criterion_with_tracked_losses():
    """Test Kelly Criterion with actual tracked average loss"""
    print("\nTesting Kelly Criterion with tracked losses...")
    try:
        from ml_model import MLModel
        from risk_manager import RiskManager
        
        model = MLModel('models/test_kelly.pkl')
        
        # Simulate some trades with outcomes
        sample_indicators = {
            'rsi': 50, 'macd': 0.5, 'macd_signal': 0.3, 'macd_diff': 0.2,
            'stoch_k': 50, 'stoch_d': 50, 'bb_width': 0.05, 'volume_ratio': 1.5,
            'momentum': 0.01, 'roc': 1.0, 'atr': 2.5, 'close': 100,
            'bb_high': 105, 'bb_low': 95, 'bb_mid': 100,
            'ema_12': 100, 'ema_26': 99
        }
        
        # Record wins and losses
        model.record_outcome(sample_indicators, 'BUY', 0.03)  # Win
        model.record_outcome(sample_indicators, 'BUY', 0.025) # Win
        model.record_outcome(sample_indicators, 'BUY', -0.02) # Loss
        model.record_outcome(sample_indicators, 'BUY', 0.015) # Win
        model.record_outcome(sample_indicators, 'BUY', -0.015) # Loss
        model.record_outcome(sample_indicators, 'BUY', 0.02)  # Win (4th win)
        
        metrics = model.get_performance_metrics()
        
        # Verify separate tracking
        assert 'avg_loss' in metrics, "avg_loss should be tracked"
        assert metrics['wins'] == 4, f"Expected 4 wins, got {metrics['wins']}"
        assert metrics['losses'] == 2, f"Expected 2 losses, got {metrics['losses']}"
        assert abs(metrics['win_rate'] - 0.667) < 0.01, f"Expected ~66.7% win rate, got {metrics['win_rate']}"
        assert metrics['avg_profit'] > 0, "Average profit should be positive"
        assert metrics['avg_loss'] > 0, "Average loss should be positive"
        
        # Test Kelly calculation with tracked data
        manager = RiskManager(1000, 0.02, 3)
        optimal_risk = manager.calculate_kelly_criterion(
            metrics['win_rate'],
            metrics['avg_profit'],
            metrics['avg_loss']
        )
        
        assert 0.005 <= optimal_risk <= 0.03, f"Kelly risk should be between 0.5% and 3%, got {optimal_risk}"
        
        print(f"  ✓ Tracked {metrics['wins']} wins with avg profit: {metrics['avg_profit']:.2%}")
        print(f"  ✓ Tracked {metrics['losses']} losses with avg loss: {metrics['avg_loss']:.2%}")
        print(f"  ✓ Kelly-optimized risk: {optimal_risk:.2%}")
        print("✓ Kelly Criterion with tracked losses working correctly")
        return True
    except Exception as e:
        print(f"✗ Kelly Criterion test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_drawdown_protection():
    """Test drawdown protection mechanism"""
    print("\nTesting drawdown protection...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Test normal conditions (no drawdown)
        risk_adj = manager.update_drawdown(10000)
        assert risk_adj == 1.0, f"No drawdown should have 1.0 adjustment, got {risk_adj}"
        
        # Peak should be updated
        assert manager.peak_balance == 10000, f"Peak should be 10000, got {manager.peak_balance}"
        
        # Test moderate drawdown (16%)
        risk_adj = manager.update_drawdown(8400)
        assert risk_adj == 0.75, f"16% drawdown should have 0.75 adjustment, got {risk_adj}"
        assert abs(manager.current_drawdown - 0.16) < 0.01, f"Drawdown should be 16%, got {manager.current_drawdown:.2%}"
        
        # Test high drawdown (25%)
        risk_adj = manager.update_drawdown(7500)
        assert risk_adj == 0.5, f"25% drawdown should have 0.5 adjustment, got {risk_adj}"
        assert abs(manager.current_drawdown - 0.25) < 0.01, f"Drawdown should be 25%, got {manager.current_drawdown:.2%}"
        
        # Test recovery (new peak)
        risk_adj = manager.update_drawdown(12000)
        assert risk_adj == 1.0, f"New peak should reset to 1.0 adjustment, got {risk_adj}"
        assert manager.peak_balance == 12000, f"New peak should be 12000, got {manager.peak_balance}"
        assert manager.current_drawdown == 0.0, f"Drawdown should be 0%, got {manager.current_drawdown:.2%}"
        
        print(f"  ✓ Normal conditions: 100% risk")
        print(f"  ✓ 16% drawdown: 75% risk")
        print(f"  ✓ 25% drawdown: 50% risk")
        print(f"  ✓ New peak: reset to 100% risk")
        print("✓ Drawdown protection working correctly")
        return True
    except Exception as e:
        print(f"✗ Drawdown protection test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_sizing_with_risk_override():
    """Test position sizing with Kelly risk override"""
    print("\nTesting position sizing with risk override...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Test with default risk
        balance = 10000
        entry_price = 100
        stop_loss_price = 95
        leverage = 10
        
        size_default = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
        
        # Test with Kelly-optimized risk (lower)
        size_kelly_low = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage, risk_per_trade=0.01
        )
        
        # Test with Kelly-optimized risk (higher)
        size_kelly_high = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage, risk_per_trade=0.03
        )
        
        assert size_default > 0, "Default position size should be positive"
        assert size_kelly_low < size_default, "Lower risk should result in smaller position"
        assert size_kelly_high > size_default, "Higher risk should result in larger position"
        
        print(f"  ✓ Default (2% risk): {size_default:.4f} contracts")
        print(f"  ✓ Kelly low (1% risk): {size_kelly_low:.4f} contracts")
        print(f"  ✓ Kelly high (3% risk): {size_kelly_high:.4f} contracts")
        print("✓ Position sizing with risk override working correctly")
        return True
    except Exception as e:
        print(f"✗ Position sizing test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_scanner_volume_filter():
    """Test market scanner volume filtering"""
    print("\nTesting market scanner volume filter...")
    try:
        from market_scanner import MarketScanner
        from unittest.mock import Mock
        
        mock_client = Mock()
        scanner = MarketScanner(mock_client)
        
        # Create test futures data with volume (need >10 to avoid fallback)
        futures = [
            {'symbol': 'BTC/USDT:USDT', 'swap': True, 'quoteVolume': 5000000},  # High volume
            {'symbol': 'ETH/USDT:USDT', 'swap': True, 'quoteVolume': 3000000},  # High volume
            {'symbol': 'SOL/USDT:USDT', 'swap': True, 'quoteVolume': 2000000},  # Major coin
            {'symbol': 'BNB/USDT:USDT', 'swap': True, 'quoteVolume': 2500000},  # Major coin
            {'symbol': 'ADA/USDT:USDT', 'swap': True, 'quoteVolume': 1800000},  # Major coin
            {'symbol': 'XRP/USDT:USDT', 'swap': True, 'quoteVolume': 2200000},  # Major coin
            {'symbol': 'DOGE/USDT:USDT', 'swap': True, 'quoteVolume': 1500000},  # Major coin
            {'symbol': 'MATIC/USDT:USDT', 'swap': True, 'quoteVolume': 1600000},  # Major coin
            {'symbol': 'AVAX/USDT:USDT', 'swap': True, 'quoteVolume': 1400000},  # Good volume
            {'symbol': 'DOT/USDT:USDT', 'swap': True, 'quoteVolume': 1300000},  # Good volume
            {'symbol': 'ATOM/USDT:USDT', 'swap': True, 'quoteVolume': 1200000},  # Good volume
            {'symbol': 'LOW/USDT:USDT', 'swap': True, 'quoteVolume': 500000},   # Low volume (should filter)
            {'symbol': 'TINY/USDT:USDT', 'swap': True, 'quoteVolume': 100000},  # Very low volume (should filter)
        ]
        
        symbols = [f['symbol'] for f in futures]
        filtered = scanner._filter_high_priority_pairs(symbols, futures)
        
        # Should filter out low volume pairs
        assert 'BTC/USDT:USDT' in filtered, "BTC should be included"
        assert 'ETH/USDT:USDT' in filtered, "ETH should be included"
        assert 'SOL/USDT:USDT' in filtered, "SOL should be included"
        assert 'AVAX/USDT:USDT' in filtered, "AVAX with good volume should be included"
        
        # Low volume should be filtered when we have enough other pairs
        assert 'LOW/USDT:USDT' not in filtered, "Low volume should be filtered"
        assert 'TINY/USDT:USDT' not in filtered, "Tiny volume should be filtered"
        
        # Should have enough pairs (>=10)
        assert len(filtered) >= 10, f"Should have at least 10 pairs, got {len(filtered)}"
        
        print(f"  ✓ Filtered to {len(filtered)} high-quality pairs")
        print(f"  ✓ Low volume pairs excluded")
        print("✓ Market scanner volume filter working correctly")
        return True
    except Exception as e:
        print(f"✗ Market scanner filter test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_adjusted_scoring():
    """Test risk-adjusted signal scoring"""
    print("\nTesting risk-adjusted signal scoring...")
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        
        generator = SignalGenerator()
        
        # Create data with high momentum but low volatility (good risk/reward)
        good_rr_data = [
            [i * 60000, 100 + i * 0.8, 101 + i * 0.8, 99 + i * 0.8, 100.5 + i * 0.8, 2000]
            for i in range(100)
        ]
        
        # Create data with low momentum but high volatility (poor risk/reward)
        poor_rr_data = [
            [i * 60000, 100 + (i % 10) * 2, 105 + (i % 10) * 2, 95 + (i % 10) * 2, 100 + (i % 10) * 2, 1000]
            for i in range(100)
        ]
        
        df_good = Indicators.calculate_all(good_rr_data)
        df_poor = Indicators.calculate_all(poor_rr_data)
        
        score_good = generator.calculate_score(df_good)
        score_poor = generator.calculate_score(df_poor)
        
        # Good risk/reward should score higher
        assert score_good > score_poor, f"Good R/R should score higher: {score_good} vs {score_poor}"
        
        print(f"  ✓ Good risk/reward score: {score_good:.1f}")
        print(f"  ✓ Poor risk/reward score: {score_poor:.1f}")
        print("✓ Risk-adjusted scoring working correctly")
        return True
    except Exception as e:
        print(f"✗ Risk-adjusted scoring test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all optimization tests"""
    print("="*60)
    print("Running Trading Strategy Optimization Tests")
    print("="*60)
    
    tests = [
        test_kelly_criterion_with_tracked_losses,
        test_drawdown_protection,
        test_position_sizing_with_risk_override,
        test_market_scanner_volume_filter,
        test_risk_adjusted_scoring,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)
    
    if all(results):
        print("\n✓ All optimization tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
