# Testing Guide for KuCoin Futures Trading Bot

## Overview

This directory contains comprehensive validation tests for the trading bot, covering core functionality, advanced features, and edge cases.

## Core Test Files

### 1. `test_bot.py`
**Core functionality tests** covering:
- Module imports
- Configuration auto-configuration
- Logger functionality
- Technical indicators
- Signal generation
- Risk management
- ML model validation
- Futures filtering
- Data handling
- Market regime detection
- Adaptive leverage
- Cache mechanism

### 2. `test_small_balance_support.py`
**Small balance tests** specifically for:
- Very small balance configuration ($10-$100)
- Position sizing with micro accounts
- Position opening logic
- Division by zero protection
- Kelly Criterion edge cases
- Market regime detection
- Adaptive leverage
- Portfolio diversification

### 3. `test_thread_safety.py`
**Thread safety validation:**
- Market scanner cache (1000 concurrent ops)
- Position manager locks
- Race condition detection

### 4. `test_integration.py`
**Integration tests** for:
- End-to-end trading workflows
- Component integration
- System-level validation

## Additional Test Categories

The repository includes additional specialized tests:

- **2025 AI Features**: `test_2025_ai_enhancements.py`, `test_enhanced_ml_intelligence.py`, `test_modern_gradient_boosting.py`, `test_ml_coordinator_2025.py`
- **Advanced Features**: `test_comprehensive_advanced.py`, `test_advanced_strategy_integration.py`, `test_dca_hedging_strategies.py`, `test_smart_adaptive_exits.py`
- **Risk Management**: `test_risk_management.py`, `test_emergency_stops.py`, `test_adaptive_stops.py`
- **Trading Methods**: `test_enhanced_trading_methods.py`, `test_smart_enhancements.py`, `test_smart_optimizations.py`, `test_smart_profit_taking.py`
- **Live Trading**: `test_live_trading.py`, `test_live_mode_comprehensive.py`, `test_real_bot_functionality.py`
- **Performance**: `test_performance_improvements.py`, `test_profitability_improvements.py`
- **WebSocket**: `test_websocket_integration.py`
- **Feature Verification**: `test_feature_verification.py`, `test_state_persistence.py`, `test_volume_profile.py`
- **Strategy Testing**: `test_trading_strategies.py`, `test_strategy_optimizations.py`
- **Simulation**: `test_real_world_simulation.py`, `test_realistic_scenario.py`, `test_trade_simulation.py`

## Running Tests

### Run Core Tests
```bash
# Core functionality
python test_bot.py

# Small balance support
python test_small_balance_support.py

# Thread safety
python test_thread_safety.py

# Integration tests
python test_integration.py
```

### Run All Tests
```bash
python run_all_tests.py
```

## Test Coverage

The test suite validates:

### Balance Tiers
- $10 (minimum practical)
- $25-$99 (micro accounts)
- $100-$1,000 (small accounts)
- $10,000+ (medium/large accounts)

### Edge Cases
- ✅ Division by zero protection
- ✅ Invalid/None data handling
- ✅ Zero/negative balances
- ✅ Zero price distance
- ✅ Empty order books
- ✅ Insufficient OHLCV data
- ✅ Balance fetch failures
- ✅ API errors

### Core Features
- ✅ Auto-configuration from balance
- ✅ Kelly Criterion position sizing
- ✅ Market regime detection
- ✅ Adaptive leverage (3x-20x)
- ✅ Portfolio diversification
- ✅ Enhanced ML model
- ✅ Thread-safe operations
- ✅ Caching mechanism
- ✅ WebSocket integration
- ✅ 2025 AI enhancements
- ✅ Advanced risk management

## Requirements

```bash
pip install -r requirements.txt
```

## Troubleshooting

### Tests Fail
1. Install dependencies: `pip install -r requirements.txt`
2. Check Python version (3.11+ recommended)
3. Review error messages in output

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### API Errors (in production)
1. Verify `.env` file exists
2. Check API credentials
3. Ensure sufficient balance

## Production Checklist

Before using with real money:

- [ ] Run `python test_bot.py` - verify core functionality
- [ ] Run `python test_small_balance_support.py` - verify balance handling
- [ ] Configure `.env` with valid API credentials
- [ ] Start with a small balance ($10-50 recommended)
- [ ] Monitor `logs/bot.log` actively
- [ ] Set `CLOSE_POSITIONS_ON_SHUTDOWN=true`

## Summary

The test suite provides comprehensive validation of:
- ✅ Core trading functionality
- ✅ Small balance support (down to $10)
- ✅ Advanced AI features
- ✅ Risk management systems
- ✅ Thread safety
- ✅ Error handling
- ✅ WebSocket integration

The bot has been thoroughly tested and is ready for production use!
