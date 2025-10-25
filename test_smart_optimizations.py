"""
Test suite for 2025 smart trading optimizations
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime


def test_smart_entry_exit():
    """Test smart entry/exit optimizer"""
    print("\nTesting Smart Entry/Exit Optimizer...")
    try:
        from smart_entry_exit import SmartEntryExit
        
        optimizer = SmartEntryExit()
        
        # Test 1: Entry timing analysis with good conditions
        orderbook = {
            'bids': [[100.0, 10], [99.9, 8], [99.8, 5]],
            'asks': [[100.1, 3], [100.2, 4], [100.3, 2]]
        }
        
        analysis = optimizer.analyze_entry_timing(
            orderbook, 100.0, 'BUY', 0.03
        )
        
        assert 'timing_score' in analysis, "Missing timing_score"
        assert 'recommendation' in analysis, "Missing recommendation"
        assert 0 <= analysis['timing_score'] <= 1, "Invalid timing_score range"
        
        print(f"  ✓ Entry timing analysis working (score: {analysis['timing_score']:.2f})")
        
        # Test 2: Partial exit calculations
        exits = optimizer.calculate_partial_exits(
            entry_price=100.0,
            stop_loss=95.0,
            side='long',
            volatility=0.03
        )
        
        assert len(exits) > 0, "No exit levels calculated"
        total_pct = sum(e['percentage'] for e in exits)
        assert abs(total_pct - 1.0) < 0.01, f"Exit percentages don't sum to 1.0: {total_pct}"
        
        print(f"  ✓ Partial exits calculated: {len(exits)} levels")
        
        # Test 3: Dynamic stop calculation
        dynamic_stop = optimizer.calculate_dynamic_stop(
            entry_price=100.0,
            current_price=105.0,
            side='long',
            atr=2.0,
            volatility=0.03,
            pnl_pct=0.05
        )
        
        assert dynamic_stop < 105.0, "Stop should be below current price for long"
        assert dynamic_stop > 100.0, "Stop should be above entry for profitable position"
        
        print(f"  ✓ Dynamic stop calculated: {dynamic_stop:.2f}")
        
        # Test 4: Scale entry decision
        scale_decision = optimizer.should_scale_entry(
            timing_score=0.5,
            confidence=0.6,
            volatility=0.06  # High volatility
        )
        
        assert 'should_scale' in scale_decision, "Missing should_scale decision"
        
        if scale_decision['should_scale']:
            assert len(scale_decision['levels']) > 0, "No scaling levels provided"
            print(f"  ✓ Entry scaling: {len(scale_decision['levels'])} levels recommended")
        else:
            print(f"  ✓ Single entry recommended")
        
        print("✓ Smart Entry/Exit tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Smart Entry/Exit test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_mtf_analysis():
    """Test enhanced multi-timeframe analysis"""
    print("\nTesting Enhanced Multi-Timeframe Analysis...")
    try:
        from enhanced_mtf_analysis import EnhancedMultiTimeframeAnalysis
        from indicators import Indicators
        
        mtf_analyzer = EnhancedMultiTimeframeAnalysis()
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        df_1h = pd.DataFrame({
            'open': np.random.uniform(95, 105, 100),
            'high': np.random.uniform(100, 110, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(95, 105, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        }, index=dates)
        
        df_1h = Indicators.calculate_all(df_1h)
        
        # Test 1: Timeframe weight calculation
        weight_1h = mtf_analyzer.calculate_timeframe_weight('1h', 0.03, 'trending')
        weight_4h = mtf_analyzer.calculate_timeframe_weight('4h', 0.03, 'trending')
        weight_1d = mtf_analyzer.calculate_timeframe_weight('1d', 0.03, 'trending')
        
        assert 0 < weight_1h < 1, "Invalid 1h weight"
        assert 0 < weight_4h < 1, "Invalid 4h weight"
        assert 0 < weight_1d < 1, "Invalid 1d weight"
        
        print(f"  ✓ Timeframe weights calculated: 1h={weight_1h:.2f}, 4h={weight_4h:.2f}, 1d={weight_1d:.2f}")
        
        # Test 2: Confluence analysis
        confluence = mtf_analyzer.analyze_timeframe_confluence(
            df_1h=df_1h,
            df_4h=None,  # Test with missing data
            df_1d=None,
            signal_1h='BUY',
            volatility=0.03
        )
        
        assert 'confluence_score' in confluence, "Missing confluence_score"
        assert 'alignment' in confluence, "Missing alignment"
        assert 'confidence_multiplier' in confluence, "Missing confidence_multiplier"
        
        print(f"  ✓ Confluence analysis: {confluence['alignment']} (score: {confluence['confluence_score']:.2f})")
        
        # Test 3: Optimal timeframe selection
        optimal_tf = mtf_analyzer.get_optimal_timeframe_for_entry(
            df_1h=df_1h,
            df_4h=None,
            df_1d=None,
            asset_volatility=0.05
        )
        
        assert optimal_tf in ['1h', '4h', '1d'], "Invalid optimal timeframe"
        
        print(f"  ✓ Optimal timeframe for high volatility: {optimal_tf}")
        
        print("✓ Enhanced MTF Analysis tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Enhanced MTF test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_correlation():
    """Test position correlation manager"""
    print("\nTesting Position Correlation Manager...")
    try:
        from position_correlation import PositionCorrelationManager
        
        corr_manager = PositionCorrelationManager()
        
        # Test 1: Asset category identification
        btc_category = corr_manager.get_asset_category('BTCUSDT')
        eth_category = corr_manager.get_asset_category('ETHUSDT')
        uni_category = corr_manager.get_asset_category('UNIUSDT')
        
        print(f"  ✓ Category detection: BTC={btc_category}, ETH={eth_category}, UNI={uni_category}")
        
        # Test 2: Price history updates
        corr_manager.update_price_history('BTCUSDT', 50000.0)
        corr_manager.update_price_history('BTCUSDT', 50100.0)
        corr_manager.update_price_history('ETHUSDT', 3000.0)
        corr_manager.update_price_history('ETHUSDT', 3015.0)
        
        assert 'BTCUSDT' in corr_manager.price_history, "Price history not stored"
        assert len(corr_manager.price_history['BTCUSDT']) == 2, "Incorrect history length"
        
        print(f"  ✓ Price history tracking working")
        
        # Test 3: Correlation calculation
        # Add more price data
        for i in range(20):
            btc_price = 50000 + i * 100
            eth_price = 3000 + i * 6  # Similar trend
            corr_manager.update_price_history('BTCUSDT', btc_price)
            corr_manager.update_price_history('ETHUSDT', eth_price)
        
        correlation = corr_manager.calculate_correlation('BTCUSDT', 'ETHUSDT')
        
        assert -1 <= correlation <= 1, "Invalid correlation value"
        
        print(f"  ✓ Correlation calculated: BTC-ETH = {correlation:.2f}")
        
        # Test 4: Portfolio heat calculation
        positions = [
            {'symbol': 'BTCUSDT', 'value': 1000},
            {'symbol': 'ETHUSDT', 'value': 800},
            {'symbol': 'SOLUSDT', 'value': 500}
        ]
        
        heat = corr_manager.calculate_portfolio_heat(positions)
        
        assert 0 <= heat <= 1, "Invalid heat score"
        
        print(f"  ✓ Portfolio heat: {heat:.2f}")
        
        # Test 5: Correlation-adjusted sizing
        existing_positions = [
            {'symbol': 'BTCUSDT', 'value': 1000}
        ]
        
        adjusted_size = corr_manager.get_correlation_adjusted_size(
            symbol='ETHUSDT',
            base_size=100.0,
            existing_positions=existing_positions
        )
        
        # Should be reduced due to BTC-ETH correlation
        print(f"  ✓ Correlation-adjusted size: {adjusted_size:.2f} (base: 100.0)")
        
        # Test 6: Category concentration check
        is_allowed, reason = corr_manager.check_category_concentration(
            symbol='ADAUSDT',  # Another L1
            existing_positions=[
                {'symbol': 'SOLUSDT', 'value': 2000},
                {'symbol': 'AVAXUSDT', 'value': 1500}
            ],
            portfolio_value=5000
        )
        
        print(f"  ✓ Concentration check: {is_allowed} - {reason}")
        
        print("✓ Position Correlation tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Position Correlation test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration of all components"""
    print("\nTesting Integration...")
    try:
        from smart_entry_exit import SmartEntryExit
        from enhanced_mtf_analysis import EnhancedMultiTimeframeAnalysis
        from position_correlation import PositionCorrelationManager
        
        # Initialize all components
        entry_exit = SmartEntryExit()
        mtf_analyzer = EnhancedMultiTimeframeAnalysis()
        corr_manager = PositionCorrelationManager()
        
        print("  ✓ All components initialized successfully")
        
        # Simulate a trading decision workflow
        orderbook = {
            'bids': [[100.0, 10], [99.9, 8]],
            'asks': [[100.1, 3], [100.2, 4]]
        }
        
        # Step 1: Check entry timing
        entry_analysis = entry_exit.analyze_entry_timing(
            orderbook, 100.0, 'BUY', 0.03
        )
        
        # Step 2: Check correlation
        existing_pos = [{'symbol': 'BTCUSDT', 'value': 1000}]
        adj_size = corr_manager.get_correlation_adjusted_size(
            'ETHUSDT', 100.0, existing_pos
        )
        
        print(f"  ✓ Trading workflow simulation successful")
        print(f"    - Entry timing score: {entry_analysis['timing_score']:.2f}")
        print(f"    - Adjusted position size: {adj_size:.2f}")
        
        print("✓ Integration tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running 2025 Smart Trading Optimization Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Smart Entry/Exit", test_smart_entry_exit()))
    results.append(("Enhanced MTF Analysis", test_enhanced_mtf_analysis()))
    results.append(("Position Correlation", test_position_correlation()))
    results.append(("Integration", test_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 60)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print()
    
    if passed == total:
        print("✓ All optimization tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
