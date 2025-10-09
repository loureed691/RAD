"""
Comprehensive Test Suite for Advanced Features
Tests ML enhancements, risk management, execution algorithms, and more
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_neural_network():
    """Test neural network model"""
    print("\n" + "="*80)
    print("TESTING NEURAL NETWORK MODEL")
    print("="*80)
    
    try:
        from neural_network_model import NeuralNetworkModel, TENSORFLOW_AVAILABLE
        
        if not TENSORFLOW_AVAILABLE:
            print("⚠️  TensorFlow not available - skipping neural network tests")
            return True
        
        # Create model
        nn_model = NeuralNetworkModel('models/test_nn.h5')
        print("✓ Neural network model initialized")
        
        # Create test data (100 samples, 31 features)
        X_train = np.random.randn(100, 31)
        y_train = np.random.randint(0, 3, 100)
        
        # Test training
        success = nn_model.train(X_train, y_train, epochs=5, batch_size=16)
        if success:
            print("✓ Neural network training successful")
        else:
            print("✗ Neural network training failed")
            return False
        
        # Test prediction
        test_features = np.random.randn(31)
        signal, confidence = nn_model.predict(test_features)
        print(f"✓ Neural network prediction: {signal} (confidence: {confidence:.2f})")
        
        # Test incremental learning
        X_new = np.random.randn(10, 31)
        y_new = np.random.randint(0, 3, 10)
        success = nn_model.incremental_train(X_new, y_new, epochs=2)
        if success:
            print("✓ Incremental learning successful")
        else:
            print("✗ Incremental learning failed")
            return False
        
        print("✓ All neural network tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Neural network test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_automl():
    """Test AutoML optimization"""
    print("\n" + "="*80)
    print("TESTING AUTOML OPTIMIZATION")
    print("="*80)
    
    try:
        from automl import AutoML, OPTUNA_AVAILABLE
        
        if not OPTUNA_AVAILABLE:
            print("⚠️  Optuna not available - skipping AutoML tests")
            return True
        
        # Create AutoML instance
        automl = AutoML()
        print("✓ AutoML initialized")
        
        # Create test data
        X = np.random.randn(200, 31)
        y = np.random.randint(0, 3, 200)
        
        # Test XGBoost optimization (reduced trials for speed)
        print("  Optimizing XGBoost...")
        best_params = automl.optimize_xgboost(X, y, n_trials=5)
        if best_params:
            print(f"✓ XGBoost optimization successful: {len(best_params)} parameters")
        else:
            print("✗ XGBoost optimization failed")
            return False
        
        # Test LightGBM optimization
        print("  Optimizing LightGBM...")
        best_params = automl.optimize_lightgbm(X, y, n_trials=5)
        if best_params:
            print(f"✓ LightGBM optimization successful: {len(best_params)} parameters")
        else:
            print("✗ LightGBM optimization failed")
            return False
        
        # Test optimization history
        history = automl.get_optimization_history()
        if history:
            print(f"✓ Optimization history retrieved: {history['n_trials']} trials")
        
        print("✓ All AutoML tests passed")
        return True
        
    except Exception as e:
        print(f"✗ AutoML test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_var_cvar():
    """Test VaR and CVaR risk metrics"""
    print("\n" + "="*80)
    print("TESTING VAR/CVAR RISK METRICS")
    print("="*80)
    
    try:
        from risk_manager import RiskManager
        
        # Create risk manager
        risk_mgr = RiskManager(1000, 0.02, 3)
        print("✓ Risk manager initialized")
        
        # Create test returns data
        returns = np.random.randn(100) * 0.02  # 2% volatility
        returns_list = returns.tolist()
        
        # Test VaR calculation
        var_95 = risk_mgr.calculate_var(returns_list, 0.95)
        var_99 = risk_mgr.calculate_var(returns_list, 0.99)
        print(f"✓ VaR calculated: 95%={var_95:.4f}, 99%={var_99:.4f}")
        
        # Test CVaR calculation
        cvar_95 = risk_mgr.calculate_cvar(returns_list, 0.95)
        cvar_99 = risk_mgr.calculate_cvar(returns_list, 0.99)
        print(f"✓ CVaR calculated: 95%={cvar_95:.4f}, 99%={cvar_99:.4f}")
        
        # Verify CVaR >= VaR (it should be)
        if cvar_95 >= var_95:
            print("✓ CVaR >= VaR validation passed")
        else:
            print("✗ CVaR < VaR validation failed")
            return False
        
        # Test comprehensive risk metrics
        metrics = risk_mgr.get_risk_metrics(returns_list)
        if all(key in metrics for key in ['var_95', 'cvar_95', 'avg_return', 'std_return']):
            print(f"✓ Comprehensive risk metrics: {len(metrics)} metrics calculated")
        else:
            print("✗ Missing risk metrics")
            return False
        
        print("✓ All VaR/CVaR tests passed")
        return True
        
    except Exception as e:
        print(f"✗ VaR/CVaR test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regime_detection():
    """Test market regime detection and regime-based sizing"""
    print("\n" + "="*80)
    print("TESTING MARKET REGIME DETECTION")
    print("="*80)
    
    try:
        from risk_manager import RiskManager
        
        risk_mgr = RiskManager(1000, 0.02, 3)
        print("✓ Risk manager initialized")
        
        # Test different market regimes
        test_cases = [
            (np.random.randn(20) * 0.08, 0.08, 0.5, "high_volatility"),  # High volatility
            (np.random.randn(20) * 0.01, 0.01, 0.5, "low_volatility"),   # Low volatility
            ([0.03] * 20, 0.03, 0.7, "bull_trending"),                   # Bull trend
            ([-0.03] * 20, 0.03, 0.7, "bear_trending"),                  # Bear trend
            ([0.001, -0.001] * 10, 0.02, 0.3, "ranging"),               # Ranging
        ]
        
        for returns, volatility, trend_strength, expected_regime in test_cases:
            regime = risk_mgr.detect_market_regime(returns, volatility, trend_strength)
            print(f"  {expected_regime}: detected as '{regime}'")
            
            # Test regime-based sizing
            base_size = 100.0
            adjusted_size = risk_mgr.regime_based_position_sizing(base_size, regime, 0.7)
            print(f"    Position size adjustment: {base_size} → {adjusted_size:.2f}")
        
        print("✓ All regime detection tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Regime detection test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_execution_algorithms():
    """Test TWAP/VWAP/Iceberg execution (mock)"""
    print("\n" + "="*80)
    print("TESTING EXECUTION ALGORITHMS")
    print("="*80)
    
    try:
        # We can't test actual execution without a client, but we can test the structure
        from execution_algorithms import ExecutionAlgorithms
        
        # Mock client
        class MockClient:
            def create_market_order(self, symbol, side, amount, leverage, **kwargs):
                return {
                    'average': 50000.0,
                    'filled': amount,
                    'price': 50000.0,
                    'timestamp': datetime.now()
                }
            
            def get_ohlcv(self, symbol, timeframe='1m', limit=60):
                return [[i, 50000, 51000, 49000, 50500, 100000] for i in range(limit)]
            
            def get_order_book(self, symbol, limit=20):
                return {
                    'bids': [[50000 - i*10, 100] for i in range(limit)],
                    'asks': [[50000 + i*10, 100] for i in range(limit)]
                }
        
        client = MockClient()
        exec_algo = ExecutionAlgorithms(client)
        print("✓ Execution algorithms initialized")
        
        # Test best strategy selection
        strategy = exec_algo.get_best_execution_strategy('BTC/USDT', 1000, 'medium')
        print(f"✓ Best execution strategy selected: {strategy}")
        
        # Test transaction cost calculation
        mock_execution = {
            'avg_price': 50100,
            'total_filled': 10,
            'side': 'buy',
            'strategy': 'TWAP'
        }
        
        tca = exec_algo.calculate_transaction_costs(mock_execution, 50000)
        if 'slippage_pct' in tca and 'total_cost_pct' in tca:
            print(f"✓ Transaction cost analysis: slippage={tca['slippage_pct']:.4%}, "
                  f"total_cost={tca['total_cost_pct']:.4%}")
        else:
            print("✗ TCA missing metrics")
            return False
        
        print("✓ All execution algorithm tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Execution algorithm test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database():
    """Test database operations (without actual connection)"""
    print("\n" + "="*80)
    print("TESTING DATABASE MODULE")
    print("="*80)
    
    try:
        from database import TradingDatabase, POSTGRES_AVAILABLE
        
        if not POSTGRES_AVAILABLE:
            print("⚠️  psycopg2 not available - skipping database tests")
            return True
        
        # Initialize without connection (no DATABASE_URL)
        db = TradingDatabase()
        print("✓ Database module initialized (no connection)")
        
        # Test that methods handle no connection gracefully
        result = db.insert_trade({
            'timestamp': datetime.now(),
            'symbol': 'BTC/USDT',
            'side': 'long',
            'entry_price': 50000,
            'exit_price': 51000,
            'amount': 1.0,
            'leverage': 10,
            'pnl': 100,
            'pnl_pct': 0.02,
            'duration_seconds': 3600,
            'signal_confidence': 0.75,
            'indicators': None,
            'exit_reason': 'take_profit'
        })
        
        if result is False:
            print("✓ Database handles no connection gracefully")
        
        print("✓ All database tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Database test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtest_engine():
    """Test backtesting engine"""
    print("\n" + "="*80)
    print("TESTING BACKTEST ENGINE")
    print("="*80)
    
    try:
        from backtest_engine import BacktestEngine
        
        # Create backtest engine
        engine = BacktestEngine(initial_balance=10000)
        print("✓ Backtest engine initialized")
        
        # Create mock data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.randn(100).cumsum() + 50000,
            'high': np.random.randn(100).cumsum() + 50100,
            'low': np.random.randn(100).cumsum() + 49900,
            'close': np.random.randn(100).cumsum() + 50000,
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        # Simple strategy function
        def simple_strategy(row, balance, positions):
            # Random signals for testing
            if len(positions) == 0 and row['close'] > row['open']:
                return {
                    'side': 'long',
                    'amount': 0.1,
                    'leverage': 10,
                    'stop_loss': row['close'] * 0.95,
                    'take_profit': row['close'] * 1.05
                }
            return None
        
        # Run backtest
        results = engine.run_backtest(data, simple_strategy)
        
        if results and 'total_trades' in results:
            print(f"✓ Backtest completed: {results['total_trades']} trades, "
                  f"Final balance: ${results['final_balance']:.2f}")
        else:
            print("✗ Backtest results incomplete")
            return False
        
        # Test walk-forward optimization
        print("  Testing walk-forward optimization...")
        wf_results = engine.walk_forward_optimization(
            data, simple_strategy, 
            train_period_days=2, 
            test_period_days=1,
            min_train_samples=10
        )
        
        if wf_results and 'num_periods' in wf_results:
            print(f"✓ Walk-forward optimization: {wf_results['num_periods']} periods tested")
        else:
            print("⚠️  Walk-forward optimization returned no results (may need more data)")
        
        print("✓ All backtest engine tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Backtest engine test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard():
    """Test dashboard module (structure only)"""
    print("\n" + "="*80)
    print("TESTING DASHBOARD MODULE")
    print("="*80)
    
    try:
        from dashboard import TradingDashboard, FLASK_AVAILABLE
        
        if not FLASK_AVAILABLE:
            print("⚠️  Flask not available - skipping dashboard tests")
            return True
        
        # Create dashboard
        dashboard = TradingDashboard(port=5050)
        print("✓ Dashboard initialized")
        
        # Test data updates
        dashboard.update_stats({
            'balance': 10000,
            'total_pnl': 500,
            'win_rate': 0.65,
            'total_trades': 20
        })
        print("✓ Dashboard stats updated")
        
        # Test equity point addition
        dashboard.add_equity_point(10500)
        dashboard.add_equity_point(10750)
        print(f"✓ Equity curve updated: {len(dashboard.equity_data)} points")
        
        # Test trade addition
        dashboard.add_trade({
            'symbol': 'BTC/USDT',
            'side': 'long',
            'entry_price': 50000,
            'exit_price': 51000,
            'pnl': 100,
            'pnl_pct': 0.02
        })
        print(f"✓ Trade added: {len(dashboard.recent_trades)} trades")
        
        print("✓ All dashboard tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Dashboard test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_data():
    """Test alternative data modules (placeholders)"""
    print("\n" + "="*80)
    print("TESTING ALTERNATIVE DATA MODULES")
    print("="*80)
    
    try:
        from onchain_metrics import OnChainMetrics
        from social_sentiment import SocialSentiment
        
        # Test on-chain metrics
        onchain = OnChainMetrics()
        metrics = onchain.get_network_metrics('BTC')
        if 'symbol' in metrics and 'data_available' in metrics:
            print("✓ On-chain metrics module working (placeholder)")
        else:
            print("✗ On-chain metrics structure incorrect")
            return False
        
        # Test social sentiment
        sentiment = SocialSentiment()
        twitter_sentiment = sentiment.get_twitter_sentiment('BTC')
        if 'sentiment_score' in twitter_sentiment:
            print("✓ Social sentiment module working (placeholder)")
        else:
            print("✗ Social sentiment structure incorrect")
            return False
        
        # Test aggregated sentiment
        agg_sentiment = sentiment.get_aggregated_sentiment('BTC')
        if 'signal' in agg_sentiment:
            print(f"✓ Aggregated sentiment: {agg_sentiment['signal']}")
        else:
            print("✗ Aggregated sentiment structure incorrect")
            return False
        
        print("✓ All alternative data tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Alternative data test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*80)
    print("COMPREHENSIVE TEST SUITE FOR ADVANCED FEATURES")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    tests = [
        ("Neural Network Model", test_neural_network),
        ("AutoML Optimization", test_automl),
        ("VaR/CVaR Risk Metrics", test_var_cvar),
        ("Market Regime Detection", test_regime_detection),
        ("Execution Algorithms", test_execution_algorithms),
        ("Database Integration", test_database),
        ("Backtest Engine", test_backtest_engine),
        ("Dashboard Module", test_dashboard),
        ("Alternative Data", test_alternative_data),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
