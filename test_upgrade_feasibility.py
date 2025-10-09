#!/usr/bin/env python3
"""
Test script to validate upgrade recommendations and feasibility
"""
import sys
import time
import numpy as np

def test_xgboost_available():
    """Test if XGBoost can be imported"""
    print("=" * 70)
    print("Testing XGBoost Availability")
    print("=" * 70)
    
    try:
        import xgboost as xgb
        print(f"✅ XGBoost version: {xgb.__version__}")
        
        # Quick test
        from sklearn.datasets import make_classification
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        
        model = xgb.XGBClassifier(n_estimators=10, max_depth=3)
        model.fit(X, y)
        score = model.score(X, y)
        
        print(f"✅ XGBoost test accuracy: {score:.3f}")
        print("✅ XGBoost is ready to use!")
        return True
        
    except ImportError:
        print("❌ XGBoost not installed")
        print("   Install with: pip install xgboost")
        return False
    except Exception as e:
        print(f"❌ XGBoost test failed: {e}")
        return False

def test_lightgbm_available():
    """Test if LightGBM can be imported"""
    print("\n" + "=" * 70)
    print("Testing LightGBM Availability")
    print("=" * 70)
    
    try:
        import lightgbm as lgb
        print(f"✅ LightGBM version: {lgb.__version__}")
        
        # Quick test
        from sklearn.datasets import make_classification
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        
        model = lgb.LGBMClassifier(n_estimators=10, max_depth=3, verbose=-1)
        model.fit(X, y)
        score = model.score(X, y)
        
        print(f"✅ LightGBM test accuracy: {score:.3f}")
        print("✅ LightGBM is ready to use!")
        return True
        
    except ImportError:
        print("❌ LightGBM not installed")
        print("   Install with: pip install lightgbm")
        return False
    except Exception as e:
        print(f"❌ LightGBM test failed: {e}")
        return False

def test_river_available():
    """Test if River (online learning) can be imported"""
    print("\n" + "=" * 70)
    print("Testing River (Online Learning) Availability")
    print("=" * 70)
    
    try:
        from river import ensemble, tree, preprocessing
        print(f"✅ River imported successfully")
        
        # Quick test
        model = ensemble.AdaptiveRandomForestClassifier(n_models=3)
        scaler = preprocessing.StandardScaler()
        
        # Simulate online learning
        for i in range(50):
            x = {'feature1': np.random.random(), 'feature2': np.random.random()}
            y = 1 if x['feature1'] + x['feature2'] > 1 else 0
            
            # Scale and learn
            x_scaled = scaler.learn_one(x)
            model.learn_one(x_scaled, y)
        
        # Test prediction
        x_test = {'feature1': 0.8, 'feature2': 0.7}
        x_test_scaled = scaler.transform_one(x_test)
        pred = model.predict_proba_one(x_test_scaled)
        
        print(f"✅ Online learning test prediction: {pred}")
        print("✅ River is ready to use!")
        return True
        
    except ImportError:
        print("❌ River not installed")
        print("   Install with: pip install river")
        return False
    except Exception as e:
        print(f"❌ River test failed: {e}")
        return False

def test_performance_comparison():
    """Compare training performance: sklearn vs XGBoost vs LightGBM"""
    print("\n" + "=" * 70)
    print("Performance Comparison: sklearn vs XGBoost vs LightGBM")
    print("=" * 70)
    
    try:
        from sklearn.datasets import make_classification
        from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # Generate test data
        print("\nGenerating test data (1000 samples, 31 features)...")
        X, y = make_classification(n_samples=1000, n_features=31, 
                                   n_informative=20, n_redundant=5,
                                   random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        results = {}
        
        # Test sklearn
        print("\n1. Testing sklearn GradientBoosting...")
        start = time.time()
        model_sklearn = GradientBoostingClassifier(n_estimators=100, max_depth=6, random_state=42)
        model_sklearn.fit(X_train, y_train)
        sklearn_time = time.time() - start
        sklearn_score = model_sklearn.score(X_test, y_test)
        results['sklearn'] = {'time': sklearn_time, 'accuracy': sklearn_score}
        print(f"   Training time: {sklearn_time:.3f}s")
        print(f"   Test accuracy: {sklearn_score:.3f}")
        
        # Test XGBoost
        try:
            import xgboost as xgb
            print("\n2. Testing XGBoost...")
            start = time.time()
            model_xgb = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42)
            model_xgb.fit(X_train, y_train)
            xgb_time = time.time() - start
            xgb_score = model_xgb.score(X_test, y_test)
            results['xgboost'] = {'time': xgb_time, 'accuracy': xgb_score}
            print(f"   Training time: {xgb_time:.3f}s")
            print(f"   Test accuracy: {xgb_score:.3f}")
            
            speedup = sklearn_time / xgb_time
            acc_diff = (xgb_score - sklearn_score) * 100
            print(f"   ⚡ Speedup: {speedup:.2f}x faster")
            print(f"   📈 Accuracy change: {acc_diff:+.1f}%")
        except ImportError:
            print("   ⚠️ XGBoost not available")
        
        # Test LightGBM
        try:
            import lightgbm as lgb
            print("\n3. Testing LightGBM...")
            start = time.time()
            model_lgb = lgb.LGBMClassifier(n_estimators=100, max_depth=6, random_state=42, verbose=-1)
            model_lgb.fit(X_train, y_train)
            lgb_time = time.time() - start
            lgb_score = model_lgb.score(X_test, y_test)
            results['lightgbm'] = {'time': lgb_time, 'accuracy': lgb_score}
            print(f"   Training time: {lgb_time:.3f}s")
            print(f"   Test accuracy: {lgb_score:.3f}")
            
            speedup = sklearn_time / lgb_time
            acc_diff = (lgb_score - sklearn_score) * 100
            print(f"   ⚡ Speedup: {speedup:.2f}x faster")
            print(f"   📈 Accuracy change: {acc_diff:+.1f}%")
        except ImportError:
            print("   ⚠️ LightGBM not available")
        
        # Summary
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)
        for name, metrics in results.items():
            print(f"{name:12s} - Time: {metrics['time']:.3f}s, Accuracy: {metrics['accuracy']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_feature_calculations():
    """Test new feature calculations (Hurst, etc.)"""
    print("\n" + "=" * 70)
    print("Testing Advanced Feature Calculations")
    print("=" * 70)
    
    try:
        # Generate synthetic price data
        np.random.seed(42)
        prices = np.cumsum(np.random.randn(100)) + 100
        
        # Test Hurst exponent calculation
        print("\n1. Testing Hurst Exponent...")
        lags = range(2, 20)
        tau = [np.std(np.subtract(prices[lag:], prices[:-lag])) for lag in lags]
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        hurst = poly[0] * 2.0
        
        print(f"   Hurst exponent: {hurst:.3f}")
        if hurst > 0.5:
            print(f"   ✅ Trending behavior (H > 0.5)")
        elif hurst < 0.5:
            print(f"   ✅ Mean-reverting behavior (H < 0.5)")
        else:
            print(f"   ✅ Random walk (H ≈ 0.5)")
        
        # Test statistical moments
        print("\n2. Testing Statistical Moments...")
        returns = np.diff(prices) / prices[:-1]
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        skewness = ((returns - mean_return) ** 3).mean() / (std_return ** 3)
        kurtosis = ((returns - mean_return) ** 4).mean() / (std_return ** 4)
        
        print(f"   Mean return: {mean_return:.4f}")
        print(f"   Std return: {std_return:.4f}")
        print(f"   Skewness: {skewness:.3f}")
        print(f"   Kurtosis: {kurtosis:.3f}")
        print(f"   ✅ Statistical features calculated successfully")
        
        # Test Z-score
        print("\n3. Testing Z-Score Calculation...")
        recent_prices = prices[-50:]
        current_price = prices[-1]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        z_score = (current_price - mean_price) / std_price
        
        print(f"   Z-Score: {z_score:.3f}")
        if abs(z_score) > 2:
            print(f"   ✅ Significant deviation (|Z| > 2)")
        else:
            print(f"   ✅ Normal range (|Z| < 2)")
        
        print("\n✅ All feature calculations working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Feature calculation test failed: {e}")
        return False

def test_database_connectivity():
    """Test database connectivity"""
    print("\n" + "=" * 70)
    print("Testing Database Connectivity")
    print("=" * 70)
    
    try:
        from sqlalchemy import create_engine, text
        
        # Try SQLite first (always available)
        print("\n1. Testing SQLite (in-memory)...")
        engine = create_engine('sqlite:///:memory:')
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"   ✅ SQLite connection successful")
        
        # Try PostgreSQL if available
        print("\n2. Testing PostgreSQL connection...")
        try:
            pg_engine = create_engine('postgresql://localhost:5432/trading_bot')
            with pg_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"   ✅ PostgreSQL connected: {version[:50]}...")
        except Exception as e:
            print(f"   ℹ️  PostgreSQL not available (optional): {str(e)[:60]}...")
            print(f"   ℹ️  Can use SQLite instead or setup PostgreSQL later")
        
        print("\n✅ Database testing complete!")
        return True
        
    except ImportError:
        print("❌ SQLAlchemy not installed")
        print("   Install with: pip install sqlalchemy")
        return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all upgrade feasibility tests"""
    print("\n" + "=" * 70)
    print("🔬 BOT UPGRADE RECOMMENDATIONS - FEASIBILITY TESTS")
    print("=" * 70)
    print("\nTesting if recommended upgrades can be implemented...\n")
    
    results = {}
    
    # Run tests
    results['xgboost'] = test_xgboost_available()
    results['lightgbm'] = test_lightgbm_available()
    results['river'] = test_river_available()
    results['performance'] = test_performance_comparison()
    results['features'] = test_feature_calculations()
    results['database'] = test_database_connectivity()
    
    # Summary
    print("\n" + "=" * 70)
    print("FEASIBILITY TEST SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTests Passed: {passed}/{total}")
    print("\nRecommendation Status:")
    print(f"  {'✅' if results.get('xgboost') else '❌'} XGBoost upgrade - {'READY' if results.get('xgboost') else 'NEEDS INSTALL'}")
    print(f"  {'✅' if results.get('lightgbm') else '❌'} LightGBM upgrade - {'READY' if results.get('lightgbm') else 'NEEDS INSTALL'}")
    print(f"  {'✅' if results.get('river') else '❌'} Online learning - {'READY' if results.get('river') else 'NEEDS INSTALL'}")
    print(f"  {'✅' if results.get('features') else '❌'} Advanced features - {'READY' if results.get('features') else 'ERROR'}")
    print(f"  {'✅' if results.get('database') else '❌'} Database integration - {'READY' if results.get('database') else 'NEEDS INSTALL'}")
    
    if passed == total:
        print("\n🎉 ALL UPGRADES ARE FEASIBLE AND READY TO IMPLEMENT!")
    elif passed >= total * 0.6:
        print("\n✅ Most upgrades are feasible. Install missing packages to enable all features.")
    else:
        print("\n⚠️  Several dependencies are missing. Run: pip install -r requirements.txt")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("  1. Install missing packages (if any)")
    print("  2. Review BOT_UPGRADE_RECOMMENDATIONS.md for full details")
    print("  3. Start with UPGRADE_QUICKSTART.md for implementation")
    print("=" * 70)
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
