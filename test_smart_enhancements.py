"""
Tests for smart trading enhancements
"""
import pytest
import numpy as np
from smart_trading_enhancements import (
    SmartTradeFilter,
    SmartPositionSizer,
    SmartExitOptimizer,
    MarketContextAnalyzer,
    VolatilityAdaptiveParameters
)


def test_smart_trade_filter_excellent_trade():
    """Test trade filter with excellent conditions"""
    filter = SmartTradeFilter()

    result = filter.calculate_trade_quality_score(
        signal_confidence=0.85,
        volatility=0.03,  # Optimal
        volume_ratio=1.8,  # Strong volume
        trend_strength=0.75,  # Strong trend
        rsi=55,  # Moderate
        recent_win_rate=0.72,
        market_regime='trending'
    )

    assert result['quality_score'] > 0.70, "Excellent conditions should give high score"
    assert result['passed'], "Excellent conditions should pass filter"
    assert result['recommendation'] in ['EXCELLENT', 'GOOD'], "Should recommend trade"
    assert result['position_multiplier'] >= 1.0, "Should allow normal or increased position"
    print(f"✅ Excellent trade quality: {result['quality_score']:.2f}")


def test_smart_trade_filter_poor_trade():
    """Test trade filter with poor conditions"""
    filter = SmartTradeFilter()

    result = filter.calculate_trade_quality_score(
        signal_confidence=0.55,  # Low confidence
        volatility=0.12,  # Too high
        volume_ratio=0.5,  # Low volume
        trend_strength=0.2,  # Weak trend
        rsi=78,  # Overbought
        recent_win_rate=0.45,  # Below 50%
        market_regime='high_vol'
    )

    assert result['quality_score'] < 0.65, "Poor conditions should give low score"
    assert not result['passed'], "Poor conditions should not pass filter"
    assert result['recommendation'] == 'SKIP', "Should skip poor trades"
    print(f"✅ Poor trade quality correctly filtered: {result['quality_score']:.2f}")


def test_smart_position_sizer_increases_for_quality():
    """Test position sizer increases size for high-quality trades"""
    sizer = SmartPositionSizer()

    result = sizer.calculate_optimal_position_size(
        base_position_size=1.0,
        signal_confidence=0.85,  # High
        trade_quality_score=0.80,  # High
        volatility=0.03,  # Normal
        correlation_risk=0.2,  # Low
        portfolio_heat=0.3,  # Low
        recent_win_rate=0.75  # High
    )

    assert result['adjusted_size'] > result['original_size'], "Should increase size for quality"
    assert result['multiplier'] > 1.0, "Multiplier should be > 1.0"
    print(f"✅ Position size increased: {result['original_size']:.2f} → {result['adjusted_size']:.2f} ({result['multiplier']:.2f}x)")


def test_smart_position_sizer_decreases_for_risk():
    """Test position sizer decreases size for risky conditions"""
    sizer = SmartPositionSizer()

    result = sizer.calculate_optimal_position_size(
        base_position_size=1.0,
        signal_confidence=0.60,  # Low
        trade_quality_score=0.55,  # Low
        volatility=0.08,  # High
        correlation_risk=0.8,  # High
        portfolio_heat=0.75,  # High
        recent_win_rate=0.45  # Low
    )

    assert result['adjusted_size'] < result['original_size'], "Should decrease size for risk"
    assert result['multiplier'] < 1.0, "Multiplier should be < 1.0"
    print(f"✅ Position size decreased: {result['original_size']:.2f} → {result['adjusted_size']:.2f} ({result['multiplier']:.2f}x)")


def test_smart_position_sizer_safety_bounds():
    """Test position sizer respects safety bounds"""
    sizer = SmartPositionSizer()

    # Test extreme positive adjustments don't exceed 200%
    result_high = sizer.calculate_optimal_position_size(
        base_position_size=1.0,
        signal_confidence=0.95,
        trade_quality_score=0.95,
        volatility=0.02,
        correlation_risk=0.1,
        portfolio_heat=0.2,
        recent_win_rate=0.85
    )

    assert result_high['adjusted_size'] <= result_high['original_size'] * 2.0, "Should not exceed 200%"

    # Test extreme negative adjustments don't go below 25%
    result_low = sizer.calculate_optimal_position_size(
        base_position_size=1.0,
        signal_confidence=0.50,
        trade_quality_score=0.45,
        volatility=0.15,
        correlation_risk=0.9,
        portfolio_heat=0.9,
        recent_win_rate=0.35
    )

    assert result_low['adjusted_size'] >= result_low['original_size'] * 0.25, "Should not go below 25%"
    print(f"✅ Safety bounds respected: {result_low['adjusted_size']:.2f} >= {result_low['original_size']*0.25:.2f}")


def test_smart_exit_optimizer_momentum_reversal():
    """Test exit optimizer detects momentum reversal"""
    optimizer = SmartExitOptimizer()

    result = optimizer.should_exit_early(
        position_pnl=0.04,  # 4% profit
        position_duration_minutes=120,
        current_momentum=-0.025,  # Strong negative
        current_rsi=72,  # Overbought
        volatility=0.04,
        volume_ratio=1.0,
        trend_weakening=False
    )

    assert result['should_exit'], "Should exit on momentum reversal"
    assert 'momentum_reversal' in result['reasons'], "Should identify momentum reversal"
    print(f"✅ Momentum reversal detected: {result['reason_text']}")


def test_smart_exit_optimizer_profit_protection():
    """Test exit optimizer protects large profits"""
    optimizer = SmartExitOptimizer()

    result = optimizer.should_exit_early(
        position_pnl=0.08,  # 8% profit (large)
        position_duration_minutes=240,
        current_momentum=-0.005,  # Slight negative
        current_rsi=60,
        volatility=0.03,
        volume_ratio=1.0,
        trend_weakening=False
    )

    assert result['should_exit'], "Should exit to protect large profit"
    assert 'exceptional_profit' in result['reasons'], "Should identify exceptional profit"
    print(f"✅ Large profit protection: {result['reason_text']}")


def test_market_context_analyzer_bullish_market():
    """Test market context analyzer identifies bullish market"""
    analyzer = MarketContextAnalyzer()

    result = analyzer.analyze_market_context(
        current_pairs_analyzed=50,
        bullish_signals=35,
        bearish_signals=10,
        avg_volatility=0.03,
        avg_volume_ratio=1.5
    )

    assert result['sentiment'] in ['bullish', 'strong_bullish'], "Should identify bullish sentiment"
    assert result['market_health_score'] > 0.6, "Healthy market should have good score"
    assert result['recommendation'] in ['favorable_conditions', 'normal_trading'], "Should recommend trading"
    print(f"✅ Bullish market identified: {result['sentiment']} (health: {result['market_health_score']:.2f})")


def test_market_context_analyzer_low_activity():
    """Test market context analyzer handles low activity"""
    analyzer = MarketContextAnalyzer()

    result = analyzer.analyze_market_context(
        current_pairs_analyzed=50,
        bullish_signals=3,
        bearish_signals=2,
        avg_volatility=0.02,
        avg_volume_ratio=0.7
    )

    assert result['activity'] == 'low', "Should identify low activity"
    assert result['volume_health'] in ['weak', 'healthy'], "Should note volume state"
    print(f"✅ Low activity detected: {result['activity']} (volume: {result['volume_health']})")


def test_volatility_adaptive_parameters_high_vol():
    """Test parameter adjustment for high volatility"""
    adapter = VolatilityAdaptiveParameters()

    base_params = {
        'confidence_threshold': 0.62,
        'stop_loss_multiplier': 1.0,
        'position_size_multiplier': 1.0,
        'trailing_stop_distance': 0.02
    }

    adjusted = adapter.adjust_parameters(0.09, base_params)  # High volatility

    assert adjusted['confidence_threshold'] > base_params['confidence_threshold'], "Should increase threshold"
    assert adjusted['stop_loss_multiplier'] > 1.0, "Should widen stops"
    assert adjusted['position_size_multiplier'] < 1.0, "Should reduce position size"
    assert adjusted['volatility_regime'] == 'high_volatility', "Should identify high vol regime"
    print(f"✅ High volatility adjustments: threshold={adjusted['confidence_threshold']:.2f}, stops={adjusted['stop_loss_multiplier']:.2f}x")


def test_volatility_adaptive_parameters_low_vol():
    """Test parameter adjustment for low volatility"""
    adapter = VolatilityAdaptiveParameters()

    base_params = {
        'confidence_threshold': 0.62,
        'stop_loss_multiplier': 1.0,
        'position_size_multiplier': 1.0,
        'trailing_stop_distance': 0.02
    }

    adjusted = adapter.adjust_parameters(0.015, base_params)  # Low volatility

    assert adjusted['stop_loss_multiplier'] < 1.0, "Should tighten stops"
    assert adjusted['volatility_regime'] == 'low_volatility', "Should identify low vol regime"
    print(f"✅ Low volatility adjustments: stops={adjusted['stop_loss_multiplier']:.2f}x, trail={adjusted['trailing_stop_distance']:.3f}")


def test_trade_quality_components():
    """Test individual components of trade quality score"""
    filter = SmartTradeFilter()

    result = filter.calculate_trade_quality_score(
        signal_confidence=0.75,
        volatility=0.03,
        volume_ratio=1.5,
        trend_strength=0.7,
        rsi=55,
        recent_win_rate=0.68,
        market_regime='trending'
    )

    components = result['components']

    # Verify all components are present and reasonable
    assert 'signal_confidence' in components, "Should have signal confidence component"
    assert 'market_conditions' in components, "Should have market conditions component"
    assert 'trend_alignment' in components, "Should have trend alignment component"
    assert 'recent_performance' in components, "Should have performance component"
    assert 'market_regime' in components, "Should have regime component"

    # Verify weights sum reasonably (should be close to quality_score)
    total_components = sum(components.values())
    assert abs(total_components - result['quality_score']) < 0.01, "Components should sum to quality score"

    print(f"✅ Trade quality components:")
    for name, value in components.items():
        print(f"   {name}: {value:.3f}")


def test_position_sizing_adjustments():
    """Test individual adjustment factors in position sizing"""
    sizer = SmartPositionSizer()

    result = sizer.calculate_optimal_position_size(
        base_position_size=1.0,
        signal_confidence=0.75,
        trade_quality_score=0.72,
        volatility=0.04,
        correlation_risk=0.5,
        portfolio_heat=0.5,
        recent_win_rate=0.65
    )

    adjustments = result['adjustments']

    # Verify all adjustment factors are present
    assert 'confidence' in adjustments, "Should have confidence adjustment"
    assert 'quality' in adjustments, "Should have quality adjustment"
    assert 'volatility' in adjustments, "Should have volatility adjustment"
    assert 'correlation' in adjustments, "Should have correlation adjustment"
    assert 'portfolio_heat' in adjustments, "Should have portfolio heat adjustment"
    assert 'performance' in adjustments, "Should have performance adjustment"

    # Verify multiplier is product of adjustments
    expected_mult = 1.0
    for adj in adjustments.values():
        expected_mult *= adj

    assert abs(expected_mult - result['multiplier']) < 0.01, "Multiplier should be product of adjustments"

    print(f"✅ Position sizing adjustments:")
    for name, value in adjustments.items():
        print(f"   {name}: {value:.3f}x")


if __name__ == '__main__':
    # Run all tests with verbose output
    pytest.main([__file__, '-v', '-s'])
