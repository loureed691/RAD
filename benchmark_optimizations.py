"""
Benchmark script to measure the performance improvements from optimizations
"""
import time
import pandas as pd
import numpy as np
from indicators import Indicators
from volume_profile import VolumeProfile
from backtest_engine import BacktestEngine


def benchmark_indicators():
    """Benchmark indicator calculations"""
    print("\n" + "="*80)
    print("BENCHMARKING INDICATOR CALCULATIONS")
    print("="*80)
    
    # Generate test data
    sizes = [100, 500, 1000]
    
    for size in sizes:
        test_data = []
        for i in range(size):
            test_data.append([
                i * 60000,  # timestamp
                100.0 + (i % 10),  # open
                102.0 + (i % 10),  # high
                99.0 + (i % 10),   # low
                101.0 + (i % 10),  # close
                1000.0 + (i % 100) # volume
            ])
        
        # Benchmark calculate_all
        start = time.time()
        df = Indicators.calculate_all(test_data)
        calc_time = (time.time() - start) * 1000
        
        # Benchmark support/resistance
        if not df.empty:
            start = time.time()
            sr = Indicators.calculate_support_resistance(df, min(50, len(df)))
            sr_time = (time.time() - start) * 1000
        else:
            sr_time = 0
        
        print(f"\n{size} candles:")
        print(f"  calculate_all: {calc_time:.2f}ms")
        print(f"  support/resistance: {sr_time:.2f}ms")
        print(f"  Total: {calc_time + sr_time:.2f}ms")
        print(f"  Per candle: {(calc_time + sr_time) / size:.3f}ms")


def benchmark_volume_profile():
    """Benchmark volume profile calculations"""
    print("\n" + "="*80)
    print("BENCHMARKING VOLUME PROFILE")
    print("="*80)
    
    vp = VolumeProfile()
    sizes = [100, 500, 1000]
    
    for size in sizes:
        # Create DataFrame with test data
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=size, freq='1h'),
            'open': 100.0 + np.random.randn(size),
            'high': 102.0 + np.random.randn(size),
            'low': 99.0 + np.random.randn(size),
            'close': 101.0 + np.random.randn(size),
            'volume': 1000.0 + np.random.randn(size) * 100
        })
        
        start = time.time()
        profile = vp.calculate_volume_profile(df, num_bins=50)
        vp_time = (time.time() - start) * 1000
        
        print(f"\n{size} candles:")
        print(f"  Volume profile: {vp_time:.2f}ms")
        print(f"  Per candle: {vp_time / size:.3f}ms")
        if profile['poc']:
            print(f"  POC: ${profile['poc']:.2f}")
            print(f"  Value Area: ${profile['val']:.2f} - ${profile['vah']:.2f}")


def benchmark_backtest():
    """Benchmark backtest engine"""
    print("\n" + "="*80)
    print("BENCHMARKING BACKTEST ENGINE")
    print("="*80)
    
    engine = BacktestEngine(initial_balance=10000)
    sizes = [100, 500, 1000]
    
    def simple_strategy(row, balance, positions):
        """Simple test strategy"""
        if isinstance(row, dict):
            rsi = row.get('rsi', 50)
        else:
            rsi = getattr(row, 'rsi', 50)
        
        if rsi < 30 and len(positions) == 0:
            return 'BUY'
        elif rsi > 70 and len(positions) > 0:
            return 'SELL'
        return 'HOLD'
    
    for size in sizes:
        # Create test data with indicators
        test_data = []
        for i in range(size):
            test_data.append([
                i * 60000,
                100.0 + (i % 10),
                102.0 + (i % 10),
                99.0 + (i % 10),
                101.0 + (i % 10),
                1000.0 + (i % 100)
            ])
        
        df = Indicators.calculate_all(test_data)
        if df.empty:
            print(f"\n{size} candles: Skipped (insufficient data)")
            continue
        
        start = time.time()
        results = engine.run_backtest(df, simple_strategy)
        bt_time = (time.time() - start) * 1000
        
        print(f"\n{size} candles:")
        print(f"  Backtest time: {bt_time:.2f}ms")
        print(f"  Per candle: {bt_time / size:.3f}ms")
        if results:
            print(f"  Trades executed: {results.get('total_trades', 0)}")


def main():
    """Run all benchmarks"""
    print("="*80)
    print("OPTIMIZATION PERFORMANCE BENCHMARKS")
    print("="*80)
    print("\nThis benchmark measures the performance improvements from:")
    print("1. Vectorized indicator calculations")
    print("2. Optimized volume profile (removed iterrows)")
    print("3. Fast backtest engine (itertuples instead of iterrows)")
    
    benchmark_indicators()
    benchmark_volume_profile()
    benchmark_backtest()
    
    print("\n" + "="*80)
    print("BENCHMARK COMPLETE")
    print("="*80)
    print("\nExpected improvements:")
    print("- Volume profile: 10-20x faster (removed iterrows)")
    print("- Support/resistance: 5-10x faster (vectorized nested loops)")
    print("- Backtest engine: 10-100x faster (itertuples vs iterrows)")
    print("\nActual improvements visible in 'Per candle' times above.")


if __name__ == "__main__":
    main()
