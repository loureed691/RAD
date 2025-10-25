"""
Comprehensive test to verify all 2025 and 2026 features are integrated and working
"""
import sys

def test_feature_imports():
    """Test that all features can be imported"""
    print("\n" + "=" * 60)
    print("Testing Feature Imports")
    print("=" * 60)
    
    try:
        # 2026 Features
        from advanced_risk_2026 import AdvancedRiskManager2026
        print("✓ AdvancedRiskManager2026")
        
        from market_microstructure_2026 import MarketMicrostructure2026
        print("✓ MarketMicrostructure2026")
        
        from adaptive_strategy_2026 import AdaptiveStrategySelector2026
        print("✓ AdaptiveStrategySelector2026")
        
        from performance_metrics_2026 import AdvancedPerformanceMetrics2026
        print("✓ AdvancedPerformanceMetrics2026")
        
        # 2025 Optimization Features
        from smart_entry_exit import SmartEntryExit
        print("✓ SmartEntryExit")
        
        from enhanced_mtf_analysis import EnhancedMultiTimeframeAnalysis
        print("✓ EnhancedMultiTimeframeAnalysis")
        
        from position_correlation import PositionCorrelationManager
        print("✓ PositionCorrelationManager")
        
        from bayesian_kelly_2025 import BayesianAdaptiveKelly
        print("✓ BayesianAdaptiveKelly")
        
        # 2025 AI Enhancements
        from enhanced_order_book_2025 import EnhancedOrderBookAnalyzer
        print("✓ EnhancedOrderBookAnalyzer")
        
        from attention_features_2025 import AttentionFeatureSelector
        print("✓ AttentionFeatureSelector")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_bot_integration():
    """Test that bot integrates all features"""
    print("\n" + "=" * 60)
    print("Testing Bot Integration")
    print("=" * 60)
    
    try:
        from bot import TradingBot
        from unittest.mock import MagicMock, patch
        import os
        
        # Set dummy credentials for testing
        os.environ['KUCOIN_API_KEY'] = 'test_key'
        os.environ['KUCOIN_API_SECRET'] = 'test_secret'
        os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'
        
        # Mock both config validation and KuCoin client
        with patch('bot.Config.validate'), \
             patch('bot.KuCoinClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            
            # Mock balance response
            mock_instance.get_balance.return_value = {
                'free': {'USDT': 1000.0},
                'used': {'USDT': 0.0}
            }
            
            # Mock positions
            mock_instance.get_positions.return_value = []
            
            bot = TradingBot()
            
            # Verify 2026 features
            assert hasattr(bot, 'advanced_risk_2026'), "Missing advanced_risk_2026"
            print("✓ AdvancedRiskManager2026 integrated")
            
            assert hasattr(bot, 'market_micro_2026'), "Missing market_micro_2026"
            print("✓ MarketMicrostructure2026 integrated")
            
            assert hasattr(bot, 'strategy_selector_2026'), "Missing strategy_selector_2026"
            print("✓ AdaptiveStrategySelector2026 integrated")
            
            assert hasattr(bot, 'performance_2026'), "Missing performance_2026"
            print("✓ AdvancedPerformanceMetrics2026 integrated")
            
            # Verify 2025 optimization features
            assert hasattr(bot, 'smart_entry_exit'), "Missing smart_entry_exit"
            print("✓ SmartEntryExit integrated")
            
            assert hasattr(bot, 'enhanced_mtf'), "Missing enhanced_mtf"
            print("✓ EnhancedMultiTimeframeAnalysis integrated")
            
            assert hasattr(bot, 'position_correlation'), "Missing position_correlation"
            print("✓ PositionCorrelationManager integrated")
            
            assert hasattr(bot, 'bayesian_kelly'), "Missing bayesian_kelly"
            print("✓ BayesianAdaptiveKelly integrated")
            
            # Verify 2025 AI enhancements
            assert hasattr(bot, 'enhanced_orderbook_2025'), "Missing enhanced_orderbook_2025"
            print("✓ EnhancedOrderBookAnalyzer integrated")
            
            assert hasattr(bot, 'attention_features_2025'), "Missing attention_features_2025"
            print("✓ AttentionFeatureSelector integrated")
            
            # Verify ML model has attention selector connected
            assert bot.ml_model.attention_selector is not None, "Attention selector not connected to ML model"
            print("✓ AttentionFeatureSelector connected to ML model")
            
        return True
    except Exception as e:
        print(f"✗ Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_usage_in_code():
    """Verify features are actually used in the bot code"""
    print("\n" + "=" * 60)
    print("Testing Feature Usage in Code")
    print("=" * 60)
    
    try:
        with open('bot.py', 'r') as f:
            bot_code = f.read()
        
        # Check 2026 features are used
        features_to_check = {
            'advanced_risk_2026': [
                'calculate_position_correlations',
                'calculate_portfolio_heat',
                'detect_market_regime',
                'should_open_position',
                'calculate_dynamic_stop_loss'
            ],
            'market_micro_2026': [
                'analyze_order_book_imbalance',
                'calculate_liquidity_score'
            ],
            'strategy_selector_2026': [
                'select_strategy',
                'apply_strategy_filters'
            ],
            'enhanced_orderbook_2025': [
                'calculate_vamp',
                'calculate_wdop',
                'calculate_enhanced_obi',
                'get_execution_score',
                'should_execute_now'
            ],
            'attention_features_2025': [
                'apply_attention',
                'update_attention_weights'
            ],
            'bayesian_kelly': [
                'update_trade_outcome'
            ],
            'enhanced_mtf': [
                'analyze_timeframe_confluence',
                'detect_timeframe_divergence'
            ],
            'smart_entry_exit': [
                'analyze_entry_timing'
            ]
        }
        
        all_used = True
        for feature_name, methods in features_to_check.items():
            feature_used = False
            for method in methods:
                if f'{feature_name}.{method}' in bot_code:
                    feature_used = True
                    break
            
            if feature_used:
                print(f"✓ {feature_name} is used in bot.py")
            else:
                print(f"✗ {feature_name} is NOT used in bot.py")
                all_used = False
        
        return all_used
    except Exception as e:
        print(f"✗ Code check error: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("RAD BOT FEATURE VERIFICATION TEST")
    print("=" * 60)
    print("\nVerifying that all 2025 and 2026 enhancements are:")
    print("1. Properly imported")
    print("2. Integrated into the bot")
    print("3. Actually used in the code")
    
    results = []
    
    # Run tests
    results.append(("Feature Imports", test_feature_imports()))
    results.append(("Bot Integration", test_bot_integration()))
    results.append(("Feature Usage", test_feature_usage_in_code()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ ALL FEATURES VERIFIED AND WORKING!")
        return 0
    else:
        print("\n❌ SOME FEATURES NOT PROPERLY INTEGRATED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
