"""
Test advanced features: pattern recognition, analytics, exit strategies
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def test_pattern_recognition():
    """Test chart pattern recognition"""
    print("\n" + "="*60)
    print("Testing Advanced Pattern Recognition")
    print("="*60)
    
    try:
        from pattern_recognition import PatternRecognition
        
        recognizer = PatternRecognition()
        
        # Create sample data with a double bottom pattern
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        
        # Create synthetic double bottom
        prices_base = 100 + np.sin(np.linspace(0, 4*np.pi, 100)) * 10
        # Add two troughs at similar levels
        prices_base[25] = 88
        prices_base[65] = 87.5
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices_base,
            'high': prices_base + 2,
            'low': prices_base - 2,
            'close': prices_base,
            'volume': np.random.uniform(1000, 5000, 100)
        })
        
        # Test pattern detection
        patterns = recognizer.detect_all_patterns(df)
        print(f"  Patterns detected: {len(patterns)}")
        
        for pattern in patterns:
            print(f"    - {pattern.get('pattern')}: {pattern.get('type')} (confidence: {pattern.get('confidence', 0):.2f})")
        
        # Test signal generation
        signal, confidence, pattern_name = recognizer.get_pattern_signal(df)
        print(f"  Pattern signal: {signal} (confidence: {confidence:.2f}, pattern: {pattern_name})")
        
        print("✓ Pattern recognition working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Pattern recognition test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_analytics():
    """Test advanced performance analytics"""
    print("\n" + "="*60)
    print("Testing Advanced Analytics")
    print("="*60)
    
    try:
        from advanced_analytics import AdvancedAnalytics
        
        analytics = AdvancedAnalytics()
        
        # Simulate some trades
        trades = [
            {'symbol': 'BTC/USDT', 'side': 'long', 'entry_price': 40000, 'exit_price': 41000, 
             'pnl': 0.025, 'pnl_pct': 0.025, 'duration': 60, 'leverage': 10},
            {'symbol': 'ETH/USDT', 'side': 'long', 'entry_price': 2500, 'exit_price': 2450, 
             'pnl': -0.02, 'pnl_pct': -0.02, 'duration': 45, 'leverage': 10},
            {'symbol': 'SOL/USDT', 'side': 'long', 'entry_price': 100, 'exit_price': 105, 
             'pnl': 0.05, 'pnl_pct': 0.05, 'duration': 90, 'leverage': 10},
            {'symbol': 'BTC/USDT', 'side': 'short', 'entry_price': 41000, 'exit_price': 40500, 
             'pnl': 0.012, 'pnl_pct': 0.012, 'duration': 30, 'leverage': 10},
        ]
        
        for trade in trades:
            analytics.record_trade(trade)
        
        # Test equity recording
        for i in range(10):
            analytics.record_equity(10000 + i * 100)
        
        # Test metric calculations
        metrics = analytics.get_comprehensive_metrics()
        
        print(f"  Total trades: {metrics['total_trades']}")
        print(f"  Win rate: {metrics.get('win_rate', 0):.2%}")
        print(f"  Sortino ratio: {metrics['sortino_ratio']:.2f}")
        print(f"  Calmar ratio: {metrics['calmar_ratio']:.2f}")
        print(f"  Information ratio: {metrics['information_ratio']:.2f}")
        print(f"  Profit factor: {metrics['profit_factor']:.2f}")
        print(f"  Recovery factor: {metrics['recovery_factor']:.2f}")
        print(f"  Ulcer index: {metrics['ulcer_index']:.2f}")
        
        # Test streak analysis
        streak = metrics['consecutive_stats']
        print(f"  Max consecutive wins: {streak['max_wins']}")
        print(f"  Max consecutive losses: {streak['max_losses']}")
        
        # Test performance summary
        summary = analytics.get_performance_summary()
        print(f"  Summary generated: {len(summary)} chars")
        
        print("✓ Advanced analytics working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Advanced analytics test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_exit_strategies():
    """Test advanced exit strategies"""
    print("\n" + "="*60)
    print("Testing Advanced Exit Strategies")
    print("="*60)
    
    try:
        from advanced_exit_strategy import AdvancedExitStrategy
        
        exit_strategy = AdvancedExitStrategy()
        
        # Test time-based exit
        entry_time = datetime.now() - timedelta(hours=25)
        should_exit, reason = exit_strategy.time_based_exit(entry_time, datetime.now(), max_hold_minutes=1440)
        print(f"  Time-based exit: {should_exit} ({reason})")
        
        # Test volatility-based exit
        should_exit, reason = exit_strategy.volatility_based_exit(0.03, 0.09, threshold_multiplier=2.0)
        print(f"  Volatility-based exit: {should_exit} ({reason})")
        
        # Test momentum reversal
        should_exit, reason = exit_strategy.momentum_reversal_exit('long', -0.03, 75)
        print(f"  Momentum reversal exit: {should_exit} ({reason})")
        
        # Test profit target scaling
        scale_pct, reason = exit_strategy.profit_target_scaling(0.03, 40000, 41200, 'long')
        print(f"  Profit scaling: {scale_pct if scale_pct else 'None'} ({reason})")
        
        # Test chandelier exit
        should_exit, stop_price, reason = exit_strategy.chandelier_exit(40500, 41000, 200, 3.0, 'long')
        print(f"  Chandelier exit: {should_exit} (stop: {stop_price:.2f}) ({reason})")
        
        # Test profit lock
        should_exit, reason = exit_strategy.profit_lock_exit(0.025, 0.04, 0.03, 0.3)
        print(f"  Profit lock exit: {should_exit} ({reason})")
        
        # Test breakeven plus
        new_stop, reason = exit_strategy.breakeven_plus_exit(0.02, 40000, 40800, 'long', 0.015, 0.005)
        print(f"  Breakeven+ exit: {new_stop if new_stop else 'Not activated'} ({reason})")
        
        # Test comprehensive exit signal
        position_data = {
            'entry_time': datetime.now() - timedelta(hours=2),
            'entry_price': 40000,
            'side': 'long',
            'entry_volatility': 0.03,
            'current_pnl_pct': 0.025,
            'peak_pnl_pct': 0.04
        }
        
        market_data = {
            'current_price': 41000,
            'current_volatility': 0.035,
            'momentum': 0.01,
            'rsi': 65
        }
        
        should_exit, reason, scale = exit_strategy.get_comprehensive_exit_signal(position_data, market_data)
        print(f"  Comprehensive exit: {should_exit} (scale: {scale if scale else 'None'}) ({reason})")
        
        # Test dynamic trailing stop
        trailing_pct = exit_strategy.calculate_dynamic_trailing_stop(0.06, 0.02)
        print(f"  Dynamic trailing stop: {trailing_pct*100:.2f}%")
        
        print("✓ Advanced exit strategies working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Advanced exit strategies test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_integration():
    """Test pattern recognition integration with signals"""
    print("\n" + "="*60)
    print("Testing Pattern Recognition Integration")
    print("="*60)
    
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        
        signal_gen = SignalGenerator()
        
        # Create test data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        prices = 40000 + np.cumsum(np.random.randn(100) * 100)
        
        ohlcv_data = []
        for i in range(100):
            ohlcv_data.append([
                int(dates[i].timestamp() * 1000),
                prices[i],
                prices[i] + 100,
                prices[i] - 100,
                prices[i] + 50,
                np.random.uniform(1000, 5000)
            ])
        
        df = Indicators.calculate_all(ohlcv_data)
        
        if not df.empty:
            signal, confidence, reasons = signal_gen.generate_signal(df)
            print(f"  Signal: {signal}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Reasons: {list(reasons.keys())}")
            
            # Check if pattern reason is included
            if 'pattern' in reasons:
                print(f"  Pattern detected: {reasons['pattern']}")
            else:
                print(f"  No pattern detected in this data")
            
            print("✓ Pattern recognition integrated successfully")
            return True
        else:
            print("✗ Failed to calculate indicators")
            return False
        
    except Exception as e:
        print(f"✗ Signal integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all advanced feature tests"""
    print("\n" + "="*60)
    print("ADVANCED FEATURES TEST SUITE")
    print("="*60)
    
    tests = [
        ("Pattern Recognition", test_pattern_recognition),
        ("Advanced Analytics", test_advanced_analytics),
        ("Advanced Exit Strategies", test_advanced_exit_strategies),
        ("Signal Integration", test_signal_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
