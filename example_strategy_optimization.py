#!/usr/bin/env python3
"""
Example: Strategy Analysis and Optimization Usage

This script demonstrates how to use the new StrategyAnalyzer and StrategyOptimizer
for analyzing and optimizing trading strategies.
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import required modules
from strategy_analyzer import StrategyAnalyzer
from strategy_optimizer import StrategyOptimizer
from indicators import Indicators
from signals import SignalGenerator


def create_example_data(symbol='BTC-USDT', periods=100):
    """Create example OHLCV data for demonstration"""
    print(f"\n📊 Creating example data for {symbol}...")
    
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
    
    # Create realistic price data with trend
    base_price = 50000
    trend = np.linspace(0, 2000, periods)  # Uptrend
    noise = np.random.randn(periods) * 200  # Add noise
    close = base_price + trend + noise
    
    # Generate OHLCV
    high = close * (1 + np.random.rand(periods) * 0.015)
    low = close * (1 - np.random.rand(periods) * 0.015)
    open_price = close * (1 + (np.random.rand(periods) - 0.5) * 0.01)
    volume = np.random.randint(1000000, 10000000, periods)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    print(f"   ✓ Created {len(df)} periods of data")
    print(f"   ✓ Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    return df


def example_basic_analysis():
    """Example 1: Basic signal analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Signal Analysis")
    print("="*70)
    
    # Initialize
    analyzer = StrategyAnalyzer()
    signal_gen = SignalGenerator()
    
    # Create and prepare data
    df = create_example_data('BTC-USDT', 100)
    df = Indicators.calculate_all(df)
    
    # Generate signal
    print("\n1. Generating trading signal...")
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    print(f"   Signal: {signal}")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Market Regime: {reasons.get('market_regime', 'unknown')}")
    
    if signal != 'HOLD':
        # Analyze signal quality
        print("\n2. Analyzing signal quality...")
        quality = analyzer.analyze_signal_quality(df, signal, confidence, reasons)
        
        print(f"   Quality Score: {quality['score']:.1f}/{quality['max_score']}")
        print(f"   Quality Percentage: {quality['percentage']:.1f}%")
        print(f"   Quality Rating: {quality['quality'].upper()}")
        
        print("\n   Quality Factors:")
        for factor, score in quality['factors'].items():
            print(f"     • {factor}: {score:.1f} points")
        
        # Analyze entry timing
        print("\n3. Analyzing entry timing...")
        timing = analyzer.analyze_entry_timing(df, signal)
        
        print(f"   Timing Score: {timing['timing_score']}/100")
        print(f"   Recommendation: {timing['recommendation']}")
        print(f"   RSI: {timing.get('rsi', 'N/A'):.1f}")
        
        # Overall recommendation
        print("\n4. Overall Trading Recommendation:")
        if quality['percentage'] >= 70 and timing['timing_score'] >= 70:
            print("   ✅ STRONG TRADE - Execute immediately")
        elif quality['percentage'] >= 60 and timing['timing_score'] >= 60:
            print("   ⚠️  MODERATE TRADE - Consider with normal size")
        elif quality['percentage'] >= 50:
            print("   ⚠️  WEAK TRADE - Reduce size or wait")
        else:
            print("   ❌ AVOID - Quality too low")
    else:
        print("   No actionable signal (HOLD)")


def example_signal_optimization():
    """Example 2: Signal optimization"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Signal Optimization")
    print("="*70)
    
    # Initialize
    optimizer = StrategyOptimizer()
    signal_gen = SignalGenerator()
    
    # Create and prepare data
    df = create_example_data('ETH-USDT', 100)
    df = Indicators.calculate_all(df)
    
    # Generate base signal
    print("\n1. Generating base signal...")
    signal, confidence, reasons = signal_gen.generate_signal(df)
    indicators = Indicators.get_latest_indicators(df)
    
    print(f"   Original Signal: {signal}")
    print(f"   Original Confidence: {confidence:.2%}")
    
    if signal != 'HOLD':
        # Optimize signal
        print("\n2. Optimizing signal with additional filters...")
        opt_signal, opt_confidence, opt_reasons = optimizer.optimize_entry_signal(
            signal, confidence, indicators, reasons
        )
        
        print(f"   Optimized Signal: {opt_signal}")
        print(f"   Optimized Confidence: {opt_confidence:.2%}")
        print(f"   Confidence Change: {((opt_confidence - confidence) * 100):.1f}%")
        
        print("\n   Optimization Factors Applied:")
        for key, value in opt_reasons.items():
            if key not in reasons:  # Show only new factors
                print(f"     • {key}: {value}")
        
        # Optimize position size
        if opt_signal != 'HOLD':
            print("\n3. Optimizing position size...")
            base_size = 100.0
            account_balance = 10000.0
            
            opt_size = optimizer.optimize_position_size(
                base_size, opt_signal, opt_confidence, indicators, account_balance
            )
            
            print(f"   Base Position Size: {base_size:.2f} contracts")
            print(f"   Optimized Size: {opt_size:.2f} contracts")
            print(f"   Size Adjustment: {((opt_size / base_size - 1) * 100):.1f}%")


def example_comprehensive_report():
    """Example 3: Comprehensive strategy report"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Comprehensive Strategy Report")
    print("="*70)
    
    # Initialize
    analyzer = StrategyAnalyzer()
    
    # Create and prepare data
    symbol = 'SOL-USDT'
    df = create_example_data(symbol, 100)
    df = Indicators.calculate_all(df)
    
    print(f"\n1. Generating comprehensive report for {symbol}...")
    
    # Generate full report
    report = analyzer.generate_strategy_report(symbol, df)
    
    print(f"\n{'='*70}")
    print(f"STRATEGY REPORT: {report['symbol']}")
    print(f"{'='*70}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"\nSignal: {report['signal']}")
    print(f"Confidence: {report.get('confidence', 0):.2%}")
    print(f"Recommendation: {report['recommendation'].upper().replace('_', ' ')}")
    
    if report['signal'] != 'HOLD':
        if 'quality_analysis' in report:
            quality = report['quality_analysis']
            print(f"\nQuality Analysis:")
            print(f"  Score: {quality['percentage']:.1f}% ({quality['quality']})")
            print(f"  Factors: {quality['score']:.1f}/{quality['max_score']}")
        
        if 'timing_analysis' in report:
            timing = report['timing_analysis']
            print(f"\nTiming Analysis:")
            print(f"  Score: {timing['timing_score']}/100")
            print(f"  Recommendation: {timing['recommendation']}")
    
    print(f"{'='*70}")


def example_performance_tracking():
    """Example 4: Performance tracking and adaptive thresholds"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Performance Tracking & Adaptive Thresholds")
    print("="*70)
    
    # Initialize
    optimizer = StrategyOptimizer()
    
    print("\n1. Simulating 30 trades...")
    
    # Simulate trades
    for i in range(30):
        # Create random trade outcome
        trade_data = {
            'signal': 'BUY' if i % 2 == 0 else 'SELL',
            'confidence': 0.60 + np.random.rand() * 0.20,
            'pnl': 0.015 if i % 3 != 0 else -0.008,  # ~67% win rate
            'hold_time': np.random.randint(60, 300)
        }
        
        optimizer.record_trade_outcome(trade_data)
    
    # Get stats
    print("\n2. Performance Statistics:")
    stats = optimizer.get_optimization_stats()
    
    print(f"   Total Trades: {stats['total_trades']}")
    print(f"   Wins: {stats['wins']}")
    print(f"   Losses: {stats['losses']}")
    print(f"   Win Rate: {stats['win_rate']:.1%}")
    print(f"   Avg P&L: {stats['avg_pnl']:.2%}")
    
    print("\n3. Adaptive Threshold Adjustment:")
    print(f"   Base Threshold: {stats['base_threshold']:.2f}")
    print(f"   Current Threshold: {stats['current_threshold']:.2f}")
    print(f"   Adjustment: {stats['threshold_adjustment']:.3f}")
    
    if stats['threshold_adjustment'] > 0:
        print("   📈 Threshold increased to improve quality")
    elif stats['threshold_adjustment'] < 0:
        print("   📉 Threshold decreased to increase opportunities")
    else:
        print("   ➡️  Threshold unchanged (performance on target)")


def example_batch_analysis():
    """Example 5: Batch analysis of multiple symbols"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Batch Analysis of Multiple Symbols")
    print("="*70)
    
    # Initialize
    analyzer = StrategyAnalyzer()
    
    # Symbols to analyze
    symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'AVAX-USDT', 'MATIC-USDT']
    
    print(f"\n1. Analyzing {len(symbols)} symbols...")
    
    results = []
    
    for symbol in symbols:
        df = create_example_data(symbol, 100)
        df = Indicators.calculate_all(df)
        
        report = analyzer.generate_strategy_report(symbol, df)
        
        if report['signal'] != 'HOLD':
            quality_pct = report.get('quality_analysis', {}).get('percentage', 0)
            timing_score = report.get('timing_analysis', {}).get('timing_score', 0)
            
            results.append({
                'symbol': symbol,
                'signal': report['signal'],
                'confidence': report.get('confidence', 0),
                'quality': quality_pct,
                'timing': timing_score,
                'recommendation': report['recommendation']
            })
    
    # Sort by quality
    results.sort(key=lambda x: x['quality'], reverse=True)
    
    print(f"\n2. Top Trading Opportunities:")
    print(f"\n{'Symbol':<15} {'Signal':<6} {'Conf':<7} {'Quality':<8} {'Timing':<7} {'Recommendation'}")
    print("-" * 70)
    
    for r in results[:5]:  # Top 5
        print(f"{r['symbol']:<15} {r['signal']:<6} {r['confidence']:>6.1%} {r['quality']:>7.1f}% {r['timing']:>6.0f} {r['recommendation']}")


def main():
    """Run all examples"""
    print("="*70)
    print("STRATEGY ANALYSIS & OPTIMIZATION EXAMPLES")
    print("="*70)
    print("\nThis script demonstrates the new strategy analysis and optimization")
    print("features for the RAD trading bot.\n")
    
    try:
        # Run examples
        example_basic_analysis()
        example_signal_optimization()
        example_comprehensive_report()
        example_performance_tracking()
        example_batch_analysis()
        
        print("\n" + "="*70)
        print("✅ All examples completed successfully!")
        print("="*70)
        
        print("\n📚 For more information, see:")
        print("   • STRATEGY_OPTIMIZATION_GUIDE.md - Complete documentation")
        print("   • strategy_analyzer.py - Source code for analyzer")
        print("   • strategy_optimizer.py - Source code for optimizer")
        print("   • test_strategy_analysis.py - Test suite\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
