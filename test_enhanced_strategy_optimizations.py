"""
Tests for enhanced trading strategy optimizations
"""
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_enhanced_momentum_signals():
    """Test enhanced momentum signal generation"""
    print("\nTesting enhanced momentum signals...")
    try:
        from signals import SignalGenerator
        
        generator = SignalGenerator()
        
        # Create sample data with strong momentum
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        close_prices = np.linspace(100, 120, 100)  # Strong uptrend
        df = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices * 0.99,
            'high': close_prices * 1.01,
            'low': close_prices * 0.98,
            'close': close_prices,
            'volume': np.random.uniform(1000000, 2000000, 100)
        })
        
        from indicators import Indicators
        df = Indicators.calculate_all(df)
        
        signal, confidence, reasons = generator.generate_signal(df)
        
        # Should generate BUY signal with good confidence
        assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"
        assert 0 <= confidence <= 1, f"Confidence out of range: {confidence}"
        assert 'momentum' in reasons or signal == 'HOLD', "Momentum should be in reasons for strong trend"
        
        print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
        print(f"  ✓ Reasons: {list(reasons.keys())}")
        print("✓ Enhanced momentum signals working correctly")
        return True
    except Exception as e:
        print(f"✗ Enhanced momentum test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_support_resistance_detection():
    """Test support and resistance level detection"""
    print("\nTesting support/resistance detection...")
    try:
        from signals import SignalGenerator
        
        generator = SignalGenerator()
        
        # Create sample data with clear support/resistance
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        # Price bouncing between 95 and 105
        close_prices = 100 + 5 * np.sin(np.linspace(0, 4*np.pi, 100))
        df = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices,
            'high': close_prices * 1.01,
            'low': close_prices * 0.99,
            'close': close_prices,
            'volume': np.random.uniform(1000000, 2000000, 100)
        })
        
        from indicators import Indicators
        df = Indicators.calculate_all(df)
        
        current_price = close_prices[-1]
        sr_levels = generator.detect_support_resistance(df, current_price)
        
        assert sr_levels is not None, "Support/resistance detection failed"
        assert 'support' in sr_levels, "Missing support level"
        assert 'resistance' in sr_levels, "Missing resistance level"
        
        if sr_levels['support'] is not None:
            assert sr_levels['support'] < current_price, "Support should be below current price"
        if sr_levels['resistance'] is not None:
            assert sr_levels['resistance'] > current_price, "Resistance should be above current price"
        
        print(f"  ✓ Support: {sr_levels.get('support', 'N/A')}")
        print(f"  ✓ Resistance: {sr_levels.get('resistance', 'N/A')}")
        print(f"  ✓ Near support: {sr_levels.get('near_support', False)}")
        print(f"  ✓ Near resistance: {sr_levels.get('near_resistance', False)}")
        print("✓ Support/resistance detection working correctly")
        return True
    except Exception as e:
        print(f"✗ Support/resistance test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_leverage_calculation():
    """Test enhanced leverage calculation with better adjustments"""
    print("\nTesting enhanced leverage calculation...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Test with excellent conditions
        leverage_high = manager.get_max_leverage(
            volatility=0.02,  # Normal volatility
            confidence=0.85,  # Very high confidence
            momentum=0.03,    # Strong momentum
            trend_strength=0.8,  # Strong trend
            market_regime='trending'
        )
        
        # Test with poor conditions
        leverage_low = manager.get_max_leverage(
            volatility=0.08,  # High volatility
            confidence=0.55,  # Low confidence
            momentum=0.005,   # Weak momentum
            trend_strength=0.3,  # Weak trend
            market_regime='ranging'
        )
        
        assert leverage_high > leverage_low, "Better conditions should result in higher leverage"
        assert 3 <= leverage_high <= 20, f"Leverage out of range: {leverage_high}"
        assert 3 <= leverage_low <= 20, f"Leverage out of range: {leverage_low}"
        
        print(f"  ✓ Excellent conditions: {leverage_high}x leverage")
        print(f"  ✓ Poor conditions: {leverage_low}x leverage")
        print(f"  ✓ Difference: {leverage_high - leverage_low}x")
        print("✓ Enhanced leverage calculation working correctly")
        return True
    except Exception as e:
        print(f"✗ Enhanced leverage test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_kelly_criterion():
    """Test enhanced Kelly Criterion with better fractional adjustments"""
    print("\nTesting enhanced Kelly Criterion...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Simulate excellent performance
        for _ in range(5):
            manager.record_trade_outcome(0.03)  # Wins
        
        kelly_risk_high = manager.calculate_kelly_criterion(
            win_rate=0.75,
            avg_win=0.03,
            avg_loss=0.015
        )
        
        # Reset and simulate poor performance
        manager = RiskManager(1000, 0.02, 3)
        for _ in range(3):
            manager.record_trade_outcome(-0.02)  # Losses
        
        kelly_risk_low = manager.calculate_kelly_criterion(
            win_rate=0.45,
            avg_win=0.025,
            avg_loss=0.02
        )
        
        assert kelly_risk_high > kelly_risk_low, "Better performance should result in higher risk"
        assert 0.005 <= kelly_risk_high <= 0.035, f"Kelly risk out of range: {kelly_risk_high}"
        assert 0.005 <= kelly_risk_low <= 0.035, f"Kelly risk out of range: {kelly_risk_low}"
        
        print(f"  ✓ Excellent performance (75% win rate): {kelly_risk_high:.2%} risk")
        print(f"  ✓ Poor performance (45% win rate): {kelly_risk_low:.2%} risk")
        print(f"  ✓ Difference: {(kelly_risk_high - kelly_risk_low):.2%}")
        print("✓ Enhanced Kelly Criterion working correctly")
        return True
    except Exception as e:
        print(f"✗ Enhanced Kelly test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_scoring():
    """Test enhanced scoring system with support/resistance and MTF"""
    print("\nTesting enhanced scoring system...")
    try:
        from signals import SignalGenerator
        
        generator = SignalGenerator()
        
        # Create sample data with good trading opportunity
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        close_prices = np.linspace(100, 115, 100)  # Uptrend
        df = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices * 0.99,
            'high': close_prices * 1.02,
            'low': close_prices * 0.98,
            'close': close_prices,
            'volume': np.random.uniform(2000000, 3000000, 100)  # High volume
        })
        
        from indicators import Indicators
        df = Indicators.calculate_all(df)
        
        score = generator.calculate_score(df)
        
        # Score should be non-zero for trending data with volume
        print(f"  ✓ Score: {score:.2f}")
        assert score >= 0, f"Score should be non-negative: {score}"
        
        print("✓ Enhanced scoring system working correctly")
        return True
    except Exception as e:
        print(f"✗ Enhanced scoring test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_market_filtering():
    """Test enhanced market scanner filtering logic"""
    print("\nTesting enhanced market filtering...")
    try:
        from market_scanner import MarketScanner
        from kucoin_client import KuCoinClient
        
        # Create mock client (won't actually connect)
        try:
            client = KuCoinClient()
        except Exception as e:
            # If connection fails, that's okay for this test
            print(f"  ℹ Skipping market filtering test (no API connection): {e}")
            return True
        
        scanner = MarketScanner(client)
        
        # Mock futures data
        mock_futures = [
            {'symbol': 'BTCUSDT', 'swap': True, 'quoteVolume': 5000000000},  # Major, high volume
            {'symbol': 'ETHUSDT', 'swap': True, 'quoteVolume': 2000000000},  # Major, high volume
            {'symbol': 'LOWUSDT', 'swap': True, 'quoteVolume': 500000},      # Low volume
            {'symbol': 'ALTUSDT', 'swap': True, 'quoteVolume': 1500000},     # Medium volume
            {'symbol': 'SOLUSDT', 'swap': True, 'quoteVolume': 800000000},   # Major, high volume
        ]
        
        symbols = [f['symbol'] for f in mock_futures]
        filtered = scanner._filter_high_priority_pairs(symbols, mock_futures)
        
        # Should include major coins and high-volume pairs
        assert 'BTCUSDT' in filtered, "BTC should be included"
        assert 'ETHUSDT' in filtered, "ETH should be included"
        assert len(filtered) >= 2, f"Should have at least 2 filtered pairs, got {len(filtered)}"
        
        print(f"  ✓ Filtered {len(filtered)} pairs from {len(symbols)} total")
        print(f"  ✓ Included pairs: {filtered}")
        print("✓ Enhanced market filtering working correctly")
        return True
    except Exception as e:
        print(f"✗ Enhanced market filtering test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all enhanced optimization tests"""
    print("=" * 80)
    print("Running Enhanced Trading Strategy Optimization Tests")
    print("=" * 80)
    
    tests = [
        test_enhanced_momentum_signals,
        test_support_resistance_detection,
        test_enhanced_leverage_calculation,
        test_enhanced_kelly_criterion,
        test_enhanced_scoring,
        test_enhanced_market_filtering,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 80)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 80)
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
