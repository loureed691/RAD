"""
Tests for Strategy Analyzer and Optimizer

Validates the new strategy analysis and optimization features
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_test_data(length=100, trend='bullish'):
    """Create test OHLCV data"""
    dates = pd.date_range(end=datetime.now(), periods=length, freq='1h')
    
    if trend == 'bullish':
        # Uptrend with some noise
        close = 100 + np.cumsum(np.random.randn(length) * 0.5 + 0.2)
    elif trend == 'bearish':
        # Downtrend with some noise
        close = 150 - np.cumsum(np.random.randn(length) * 0.5 + 0.2)
    else:  # ranging
        # Sideways with noise
        close = 100 + np.random.randn(length) * 2
    
    high = close * (1 + np.random.rand(length) * 0.02)
    low = close * (1 - np.random.rand(length) * 0.02)
    open_price = close * (1 + (np.random.rand(length) - 0.5) * 0.01)
    volume = np.random.randint(1000000, 5000000, length)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    return df


def test_strategy_analyzer():
    """Test Strategy Analyzer functionality"""
    print("\n" + "="*60)
    print("Testing Strategy Analyzer")
    print("="*60)
    
    try:
        from strategy_analyzer import StrategyAnalyzer
        from indicators import Indicators
        
        analyzer = StrategyAnalyzer()
        
        # Test 1: Signal Quality Analysis
        print("\n1. Testing signal quality analysis...")
        df = create_test_data(100, 'bullish')
        df = Indicators.calculate_all(df)
        
        indicators = Indicators.get_latest_indicators(df)
        quality = analyzer.analyze_signal_quality(
            df, 'BUY', 0.75, {'trend': 'bullish'}
        )
        
        assert 'score' in quality, "Quality analysis should return score"
        assert 'percentage' in quality, "Should return percentage"
        assert 'quality' in quality, "Should return quality rating"
        assert 'factors' in quality, "Should return quality factors"
        
        print(f"   ✓ Quality score: {quality['score']:.1f}/{quality['max_score']}")
        print(f"   ✓ Quality percentage: {quality['percentage']:.1f}%")
        print(f"   ✓ Quality rating: {quality['quality']}")
        print(f"   ✓ Factors analyzed: {len(quality['factors'])}")
        
        # Test 2: Entry Timing Analysis
        print("\n2. Testing entry timing analysis...")
        timing = analyzer.analyze_entry_timing(df, 'BUY')
        
        assert 'timing_score' in timing, "Should return timing score"
        assert 'recommendation' in timing, "Should return recommendation"
        
        print(f"   ✓ Timing score: {timing['timing_score']:.1f}/100")
        print(f"   ✓ Recommendation: {timing['recommendation']}")
        
        # Test 3: Threshold Optimization
        print("\n3. Testing threshold optimization...")
        
        # Create mock historical signals
        historical_signals = []
        for i in range(50):
            historical_signals.append({
                'confidence': 0.55 + np.random.rand() * 0.3,
                'outcome': 0.02 if np.random.rand() > 0.3 else -0.01
            })
        
        optimal_threshold = analyzer.optimize_signal_threshold(
            historical_signals, target_win_rate=0.70
        )
        
        assert 0.50 <= optimal_threshold <= 0.85, "Threshold should be reasonable"
        print(f"   ✓ Optimal threshold: {optimal_threshold:.2f}")
        
        # Test 4: Strategy Report Generation
        print("\n4. Testing strategy report generation...")
        report = analyzer.generate_strategy_report('BTC-USDT', df)
        
        assert 'symbol' in report, "Report should include symbol"
        assert 'signal' in report, "Report should include signal"
        assert 'recommendation' in report, "Report should include recommendation"
        
        print(f"   ✓ Symbol: {report['symbol']}")
        print(f"   ✓ Signal: {report['signal']}")
        print(f"   ✓ Recommendation: {report['recommendation']}")
        
        print("\n✅ Strategy Analyzer: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Strategy Analyzer test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_optimizer():
    """Test Strategy Optimizer functionality"""
    print("\n" + "="*60)
    print("Testing Strategy Optimizer")
    print("="*60)
    
    try:
        from strategy_optimizer import StrategyOptimizer
        from indicators import Indicators
        
        optimizer = StrategyOptimizer()
        
        # Test 1: Entry Signal Optimization
        print("\n1. Testing entry signal optimization...")
        df = create_test_data(100, 'bullish')
        df = Indicators.calculate_all(df)
        indicators = Indicators.get_latest_indicators(df)
        
        original_signal = 'BUY'
        original_confidence = 0.65
        reasons = {'trend': 'bullish'}
        
        opt_signal, opt_confidence, opt_reasons = optimizer.optimize_entry_signal(
            original_signal, original_confidence, indicators, reasons
        )
        
        assert opt_signal in ['BUY', 'SELL', 'HOLD'], "Should return valid signal"
        assert 0 <= opt_confidence <= 1.0, "Confidence should be valid"
        assert len(opt_reasons) >= len(reasons), "Should add optimization reasons"
        
        print(f"   ✓ Original: {original_signal} ({original_confidence:.2f})")
        print(f"   ✓ Optimized: {opt_signal} ({opt_confidence:.2f})")
        print(f"   ✓ Additional factors: {len(opt_reasons) - len(reasons)}")
        
        # Test 2: Position Size Optimization
        print("\n2. Testing position size optimization...")
        base_size = 100.0
        optimized_size = optimizer.optimize_position_size(
            base_size, 'BUY', 0.75, indicators, 10000.0
        )
        
        assert optimized_size > 0, "Optimized size should be positive"
        assert 0.5 * base_size <= optimized_size <= 1.5 * base_size, \
               "Size should be within reasonable bounds"
        
        print(f"   ✓ Base size: {base_size:.2f}")
        print(f"   ✓ Optimized size: {optimized_size:.2f}")
        print(f"   ✓ Adjustment: {((optimized_size/base_size - 1) * 100):.1f}%")
        
        # Test 3: Dynamic Threshold Adjustment
        print("\n3. Testing dynamic threshold adjustment...")
        
        # Record some trades
        for i in range(25):
            optimizer.record_trade_outcome({
                'signal': 'BUY',
                'confidence': 0.70,
                'pnl': 0.02 if i % 3 != 0 else -0.01,  # ~67% win rate
                'hold_time': 120
            })
        
        stats = optimizer.get_optimization_stats()
        
        assert stats['total_trades'] == 25, "Should track all trades"
        assert stats['win_rate'] > 0, "Should calculate win rate"
        assert 'current_threshold' in stats, "Should track threshold"
        
        print(f"   ✓ Total trades: {stats['total_trades']}")
        print(f"   ✓ Win rate: {stats['win_rate']:.1%}")
        print(f"   ✓ Current threshold: {stats['current_threshold']:.2f}")
        print(f"   ✓ Threshold adjustment: {stats['threshold_adjustment']:.3f}")
        
        # Test 4: Volume-Price Divergence Detection
        print("\n4. Testing volume-price divergence detection...")
        
        # Create scenario with divergence
        indicators_divergence = indicators.copy()
        indicators_divergence['momentum'] = 0.02  # Price up
        indicators_divergence['volume_ratio'] = 0.7  # Volume down
        
        div_signal, div_conf, div_reasons = optimizer.optimize_entry_signal(
            'BUY', 0.70, indicators_divergence, {}
        )
        
        assert div_conf < 0.70, "Confidence should be reduced due to divergence"
        assert 'volume_divergence' in div_reasons, "Should detect divergence"
        
        print(f"   ✓ Divergence detected: {div_reasons.get('volume_divergence')}")
        print(f"   ✓ Confidence reduction: {((0.70 - div_conf) * 100):.1f}%")
        
        # Test 5: Volatility Regime Adaptation
        print("\n5. Testing volatility regime adaptation...")
        
        # Test extreme volatility
        indicators_extreme = indicators.copy()
        indicators_extreme['bb_width'] = 0.08  # Extreme volatility
        
        ext_signal, ext_conf, ext_reasons = optimizer.optimize_entry_signal(
            'BUY', 0.70, indicators_extreme, {}
        )
        
        assert 'volatility_regime' in ext_reasons, "Should identify regime"
        assert ext_reasons['volatility_regime'] == 'extreme', "Should detect extreme volatility"
        
        print(f"   ✓ Volatility regime: {ext_reasons['volatility_regime']}")
        print(f"   ✓ Confidence adjustment: {ext_reasons.get('volatility_adjustment', 'none')}")
        
        print("\n✅ Strategy Optimizer: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Strategy Optimizer test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration of analyzer and optimizer"""
    print("\n" + "="*60)
    print("Testing Analyzer-Optimizer Integration")
    print("="*60)
    
    try:
        from strategy_analyzer import StrategyAnalyzer
        from strategy_optimizer import StrategyOptimizer
        from indicators import Indicators
        
        analyzer = StrategyAnalyzer()
        optimizer = StrategyOptimizer()
        
        print("\n1. Testing full analysis and optimization flow...")
        
        # Create test data
        df = create_test_data(100, 'bullish')
        df = Indicators.calculate_all(df)
        
        # Generate strategy report
        report = analyzer.generate_strategy_report('BTC-USDT', df)
        
        if report['signal'] != 'HOLD':
            # Optimize the signal
            indicators = Indicators.get_latest_indicators(df)
            opt_signal, opt_conf, opt_reasons = optimizer.optimize_entry_signal(
                report['signal'],
                report['confidence'],
                indicators,
                report['reasons']
            )
            
            # Analyze optimized signal quality
            opt_quality = analyzer.analyze_signal_quality(
                df, opt_signal, opt_conf, opt_reasons
            )
            
            print(f"   ✓ Original signal: {report['signal']} ({report['confidence']:.2f})")
            print(f"   ✓ Optimized signal: {opt_signal} ({opt_conf:.2f})")
            print(f"   ✓ Quality score: {opt_quality['percentage']:.1f}%")
            print(f"   ✓ Quality rating: {opt_quality['quality']}")
            
            # Optimize position size
            if opt_signal != 'HOLD':
                opt_size = optimizer.optimize_position_size(
                    100.0, opt_signal, opt_conf, indicators, 10000.0
                )
                print(f"   ✓ Optimized position size: {opt_size:.2f}")
        
        print("\n2. Testing performance tracking...")
        
        # Simulate trades and track performance
        for i in range(30):
            df = create_test_data(100, 'bullish' if i % 2 == 0 else 'bearish')
            df = Indicators.calculate_all(df)
            
            report = analyzer.generate_strategy_report(f'TEST-{i}', df)
            
            if report['signal'] != 'HOLD':
                # Simulate trade outcome
                optimizer.record_trade_outcome({
                    'signal': report['signal'],
                    'confidence': report['confidence'],
                    'pnl': 0.015 if i % 4 != 0 else -0.008,
                    'hold_time': 180
                })
        
        stats = optimizer.get_optimization_stats()
        print(f"   ✓ Trades simulated: {stats['total_trades']}")
        print(f"   ✓ Win rate: {stats['win_rate']:.1%}")
        print(f"   ✓ Avg P&L: {stats['avg_pnl']:.2%}")
        print(f"   ✓ Adaptive threshold: {stats['current_threshold']:.2f}")
        
        print("\n✅ Integration Tests: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("="*60)
    print("STRATEGY ANALYSIS & OPTIMIZATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Strategy Analyzer", test_strategy_analyzer()))
    results.append(("Strategy Optimizer", test_strategy_optimizer()))
    results.append(("Integration", test_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    print("="*60)
    print(f"Results: {passed}/{total} test suites passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        sys.exit(1)
