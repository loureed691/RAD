"""
Comprehensive bottleneck and bug analysis for the trading bot
"""
import time
import sys
import os
import cProfile
import pstats
from io import StringIO
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def profile_function(func, *args, **kwargs):
    """Profile a function and return execution time and stats"""
    profiler = cProfile.Profile()
    start_time = time.time()
    
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Get stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    return execution_time, s.getvalue(), result

def analyze_indicators_performance():
    """Analyze indicator calculation performance"""
    print("\n" + "="*80)
    print("ANALYZING INDICATOR CALCULATION PERFORMANCE")
    print("="*80)
    
    from indicators import Indicators
    
    # Generate test data
    test_data = []
    for i in range(100):
        test_data.append([
            i * 60000,  # timestamp
            100.0 + (i % 10),  # open
            102.0 + (i % 10),  # high
            99.0 + (i % 10),   # low
            101.0 + (i % 10),  # close
            1000.0 + (i % 100) # volume
        ])
    
    # Profile indicator calculation
    exec_time, stats, df = profile_function(Indicators.calculate_all, test_data)
    
    print(f"\n✓ Indicator calculation time: {exec_time*1000:.2f}ms")
    print(f"  Data points: {len(test_data)}")
    print(f"  Indicators calculated: {len(df.columns) if not df.empty else 0}")
    
    if exec_time > 0.1:  # > 100ms
        print(f"⚠ WARNING: Indicator calculation is slow ({exec_time*1000:.2f}ms)")
        print("\nTop time-consuming functions:")
        print(stats[:1000])
    
    return exec_time

def analyze_signal_generation_performance():
    """Analyze signal generation performance"""
    print("\n" + "="*80)
    print("ANALYZING SIGNAL GENERATION PERFORMANCE")
    print("="*80)
    
    from indicators import Indicators
    from signals import SignalGenerator
    
    # Generate test data
    test_data = []
    for i in range(100):
        test_data.append([
            i * 60000,
            100.0 + (i % 10),
            102.0 + (i % 10),
            99.0 + (i % 10),
            101.0 + (i % 10),
            1000.0 + (i % 100)
        ])
    
    df = Indicators.calculate_all(test_data)
    signal_gen = SignalGenerator()
    
    # Profile signal generation
    exec_time, stats, result = profile_function(
        signal_gen.generate_signal, df, None, None
    )
    
    print(f"\n✓ Signal generation time: {exec_time*1000:.2f}ms")
    print(f"  Signal: {result[0]}")
    print(f"  Confidence: {result[1]:.2f}")
    
    if exec_time > 0.05:  # > 50ms
        print(f"⚠ WARNING: Signal generation is slow ({exec_time*1000:.2f}ms)")
        print("\nTop time-consuming functions:")
        print(stats[:1000])
    
    return exec_time

def analyze_risk_calculations_performance():
    """Analyze risk manager performance"""
    print("\n" + "="*80)
    print("ANALYZING RISK MANAGER PERFORMANCE")
    print("="*80)
    
    from risk_manager import RiskManager
    
    rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    # Profile position size calculation
    exec_time, stats, result = profile_function(
        rm.calculate_position_size,
        balance=10000,
        entry_price=100.0,
        stop_loss=95.0,
        leverage=10,
        risk_per_trade=0.02
    )
    
    print(f"\n✓ Position size calculation time: {exec_time*1000:.2f}ms")
    print(f"  Position size: {result:.4f}")
    
    if exec_time > 0.01:  # > 10ms
        print(f"⚠ WARNING: Risk calculation is slow ({exec_time*1000:.2f}ms)")
    
    return exec_time

def check_for_blocking_operations():
    """Check for potential blocking operations"""
    print("\n" + "="*80)
    print("CHECKING FOR BLOCKING OPERATIONS")
    print("="*80)
    
    issues = []
    
    # Check market scanner for blocking operations
    print("\n1. Checking market_scanner.py...")
    with open('market_scanner.py', 'r') as f:
        content = f.read()
        if 'time.sleep' in content:
            print("  ⚠ WARNING: Found time.sleep() in market_scanner.py")
            issues.append("time.sleep in market_scanner")
        if 'ThreadPoolExecutor' in content:
            print("  ✓ Using ThreadPoolExecutor for parallel scanning")
        else:
            print("  ⚠ WARNING: Not using parallel execution in scanner")
            issues.append("No parallel execution in scanner")
    
    # Check for synchronous API calls
    print("\n2. Checking kucoin_client.py...")
    with open('kucoin_client.py', 'r') as f:
        content = f.read()
        if 'enableRateLimit' in content:
            print("  ✓ Rate limiting enabled for API calls")
        else:
            print("  ⚠ WARNING: Rate limiting may not be properly configured")
            issues.append("Rate limiting configuration unclear")
    
    # Check for inefficient loops
    print("\n3. Checking for inefficient patterns...")
    files_to_check = ['bot.py', 'position_manager.py', 'risk_manager.py', 'signals.py']
    
    for file in files_to_check:
        with open(file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                # Check for nested loops
                if 'for ' in line:
                    indent = len(line) - len(line.lstrip())
                    # Look ahead for another loop
                    if i < len(lines):
                        next_line = lines[i] if i < len(lines) else ""
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if 'for ' in next_line and next_indent > indent:
                            print(f"  ⚠ Potential nested loop in {file}:{i}")
                            issues.append(f"Nested loop in {file}:{i}")
    
    if not issues:
        print("\n✓ No obvious blocking operations found")
    else:
        print(f"\n⚠ Found {len(issues)} potential issues")
    
    return issues

def check_memory_efficiency():
    """Check for potential memory issues"""
    print("\n" + "="*80)
    print("CHECKING MEMORY EFFICIENCY")
    print("="*80)
    
    issues = []
    
    # Check for large data structures
    print("\n1. Checking for large data structures...")
    
    files_to_check = ['ml_model.py', 'position_manager.py', 'market_scanner.py']
    
    for file in files_to_check:
        with open(file, 'r') as f:
            content = f.read()
            
            # Check for unlimited list growth
            has_append = '.append(' in content
            has_limiting = any(keyword in content for keyword in [
                '.pop(', 'del ', '= []', 'clear()', '[-10000:]', '[-1000:]', 
                'if len(', 'max_', 'limit'
            ])
            
            if has_append and not has_limiting:
                print(f"  ⚠ WARNING: {file} may have unlimited list growth")
                issues.append(f"Potential memory leak in {file}")
            elif has_append and has_limiting:
                print(f"  ✓ {file} has list growth but with size limiting")
            
            # Check for caching without limits
            if 'cache' in content.lower() and 'cache_duration' in content:
                print(f"  ✓ {file} has time-based cache eviction")
            elif 'cache' in content.lower() and any(x in content for x in ['max_cache', 'cache_size', 'if len(', 'clear_cache']):
                print(f"  ✓ {file} has cache with size/time management")
            elif 'cache' in content.lower():
                print(f"  ⚠ WARNING: {file} has caching without clear eviction")
                issues.append(f"Cache without eviction in {file}")
    
    if not issues:
        print("\n✓ No obvious memory issues found")
    else:
        print(f"\n⚠ Found {len(issues)} potential memory issues")
    
    return issues

def check_for_race_conditions():
    """Check for potential race conditions"""
    print("\n" + "="*80)
    print("CHECKING FOR RACE CONDITIONS")
    print("="*80)
    
    issues = []
    
    print("\n1. Checking shared state access...")
    
    # Check position_manager for thread-safety
    with open('position_manager.py', 'r') as f:
        content = f.read()
        if 'self.positions' in content and 'threading' not in content and 'Lock' not in content:
            print("  ⚠ WARNING: position_manager.py modifies shared state without locks")
            issues.append("No thread locks in position_manager")
        else:
            print("  ✓ Position manager appears to be single-threaded")
    
    # Check market_scanner for thread-safety
    with open('market_scanner.py', 'r') as f:
        content = f.read()
        if 'ThreadPoolExecutor' in content and 'self.cache' in content:
            if 'Lock' not in content:
                print("  ⚠ WARNING: market_scanner uses threads and shared cache without locks")
                issues.append("Race condition in market scanner cache")
            else:
                print("  ✓ Market scanner has thread synchronization")
    
    if not issues:
        print("\n✓ No obvious race conditions found")
    else:
        print(f"\n⚠ Found {len(issues)} potential race conditions")
    
    return issues

def check_error_handling():
    """Check error handling patterns"""
    print("\n" + "="*80)
    print("CHECKING ERROR HANDLING")
    print("="*80)
    
    issues = []
    
    files_to_check = ['bot.py', 'kucoin_client.py', 'position_manager.py', 'market_scanner.py']
    
    for file in files_to_check:
        print(f"\n{file}:")
        with open(file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            
            try_count = content.count('try:')
            except_count = content.count('except ')
            bare_except = content.count('except:')
            
            print(f"  Try blocks: {try_count}")
            print(f"  Except blocks: {except_count}")
            
            if bare_except > 0:
                print(f"  ⚠ WARNING: {bare_except} bare except clause(s)")
                issues.append(f"Bare except in {file}")
            
            if try_count > except_count:
                print(f"  ⚠ WARNING: More try blocks than except blocks")
                issues.append(f"Missing except in {file}")
            
            # Check for pass in except blocks
            for i, line in enumerate(lines):
                if 'except' in line:
                    # Look at next few lines
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j].strip() == 'pass':
                            print(f"  ⚠ WARNING: Silent exception at line {j+1}")
                            issues.append(f"Silent exception in {file}:{j+1}")
                            break
    
    if not issues:
        print("\n✓ Error handling looks good")
    else:
        print(f"\n⚠ Found {len(issues)} error handling issues")
    
    return issues

def main():
    """Run all bottleneck and bug checks"""
    print("="*80)
    print("TRADING BOT BOTTLENECK AND BUG ANALYSIS")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    all_issues = []
    
    # Performance analysis
    print("\n" + "="*80)
    print("PERFORMANCE ANALYSIS")
    print("="*80)
    
    try:
        indicator_time = analyze_indicators_performance()
    except Exception as e:
        print(f"✗ Error analyzing indicators: {e}")
        all_issues.append(f"Indicator analysis error: {e}")
        indicator_time = 0
    
    try:
        signal_time = analyze_signal_generation_performance()
    except Exception as e:
        print(f"✗ Error analyzing signals: {e}")
        all_issues.append(f"Signal analysis error: {e}")
        signal_time = 0
    
    try:
        risk_time = analyze_risk_calculations_performance()
    except Exception as e:
        print(f"✗ Error analyzing risk manager: {e}")
        all_issues.append(f"Risk manager analysis error: {e}")
        risk_time = 0
    
    # Calculate total cycle time estimate
    print("\n" + "="*80)
    print("ESTIMATED CYCLE TIME")
    print("="*80)
    
    single_pair_time = indicator_time + signal_time + risk_time
    print(f"Single pair analysis time: {single_pair_time*1000:.2f}ms")
    
    # Assume 50 pairs with 10 workers
    estimated_scan_time = (50 * single_pair_time) / 10
    print(f"Estimated scan time (50 pairs, 10 workers): {estimated_scan_time:.2f}s")
    
    if estimated_scan_time > 30:
        print("⚠ WARNING: Market scan may be slow")
        all_issues.append("Slow market scanning")
    else:
        print("✓ Market scan time acceptable")
    
    # Code quality checks
    blocking_issues = check_for_blocking_operations()
    all_issues.extend(blocking_issues)
    
    memory_issues = check_memory_efficiency()
    all_issues.extend(memory_issues)
    
    race_issues = check_for_race_conditions()
    all_issues.extend(race_issues)
    
    error_issues = check_error_handling()
    all_issues.extend(error_issues)
    
    # Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    if all_issues:
        print(f"\n⚠ Found {len(all_issues)} potential issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✓ No significant bottlenecks or bugs detected!")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    recommendations = []
    
    if indicator_time > 0.1:
        recommendations.append("- Optimize indicator calculations (consider caching)")
    
    if signal_time > 0.05:
        recommendations.append("- Optimize signal generation algorithm")
    
    if any('cache' in issue.lower() for issue in all_issues):
        recommendations.append("- Implement cache size limits to prevent memory growth")
    
    if any('race condition' in issue.lower() for issue in all_issues):
        recommendations.append("- Add thread locks for shared state in multi-threaded code")
    
    if any('nested loop' in issue.lower() for issue in all_issues):
        recommendations.append("- Refactor nested loops for better performance")
    
    if recommendations:
        for rec in recommendations:
            print(rec)
    else:
        print("✓ No immediate optimizations needed")
    
    print("\n" + "="*80)
    print(f"Analysis complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()
