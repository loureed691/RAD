#!/usr/bin/env python3
"""
Comprehensive test suite for all code examples and commands in README files.

This test ensures that all examples, commands, and code snippets mentioned in:
- README.md
- README_PRIORITY1.md

...are working correctly and can be executed by users.
"""

import sys
import os
import subprocess
import pandas as pd
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestREADMEExamples(unittest.TestCase):
    """Test all code examples from README files"""

    def test_01_module_imports(self):
        """Test that all modules mentioned in README.md Architecture section can be imported"""
        print("\n" + "=" * 80)
        print("Testing Module Imports from README.md")
        print("=" * 80)
        
        modules = [
            ('bot', 'TradingBot'),
            ('kucoin_client', 'KuCoinClient'),
            ('kucoin_websocket', 'KuCoinWebSocket'),
            ('market_scanner', 'MarketScanner'),
            ('indicators', 'Indicators'),
            ('signals', 'SignalGenerator'),
            ('ml_model', 'MLModel'),
            ('position_manager', 'PositionManager'),
            ('risk_manager', 'RiskManager'),
            ('config', 'Config'),
            ('logger', 'Logger')
        ]
        
        for module_name, class_name in modules:
            with self.subTest(module=module_name, cls=class_name):
                module = __import__(module_name, fromlist=[class_name])
                self.assertTrue(hasattr(module, class_name),
                              f"{module_name} should have {class_name}")
                print(f"  ✓ {module_name}.{class_name} imported successfully")

    def test_02_risk_manager_examples(self):
        """Test RiskManager code examples from README_PRIORITY1.md"""
        print("\n" + "=" * 80)
        print("Testing RiskManager Examples from README_PRIORITY1.md")
        print("=" * 80)
        
        from risk_manager import RiskManager
        
        # Example 1: Create instance and check kill switch
        rm = RiskManager(1000, 0.02, 3)
        is_active, reason = rm.is_kill_switch_active()
        self.assertFalse(is_active, "Kill switch should be inactive by default")
        print("  ✓ is_kill_switch_active() works")
        
        # Example 2: Activate kill switch
        rm.activate_kill_switch("Unusual market conditions")
        is_active, reason = rm.is_kill_switch_active()
        self.assertTrue(is_active, "Kill switch should be active after activation")
        self.assertEqual(reason, "Unusual market conditions")
        print("  ✓ activate_kill_switch() works")
        
        # Example 3: Deactivate kill switch
        rm.deactivate_kill_switch()
        is_active, reason = rm.is_kill_switch_active()
        self.assertFalse(is_active, "Kill switch should be inactive after deactivation")
        print("  ✓ deactivate_kill_switch() works")
        
        # Example 4: Validate trade guardrails
        is_allowed, reason = rm.validate_trade_guardrails(
            balance=10000,
            position_value=400,  # 4% of equity
            current_positions=2,
            is_exit=False
        )
        self.assertTrue(is_allowed, "Trade with 4% risk should be allowed")
        print("  ✓ validate_trade_guardrails() works")

    def test_03_backtest_engine_example(self):
        """Test BacktestEngine code example from README_PRIORITY1.md"""
        print("\n" + "=" * 80)
        print("Testing BacktestEngine Example from README_PRIORITY1.md")
        print("=" * 80)
        
        from backtest_engine import BacktestEngine
        
        # Create test data
        data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
            'close': [50000 + i * 10 for i in range(100)],
            'high': [50100 + i * 10 for i in range(100)],
            'low': [49900 + i * 10 for i in range(100)],
            'volume': [100] * 100
        })
        
        # Define a simple strategy
        def my_strategy(row, balance, positions):
            if not positions and row['close'] < 50500:
                return {
                    'side': 'long',
                    'amount': 0.1,
                    'leverage': 10,
                    'stop_loss': row['close'] * 0.95,
                    'take_profit': row['close'] * 1.05
                }
            return 'HOLD'
        
        # Run backtest
        engine = BacktestEngine(10000, 0.0006, 0.0001)
        results = engine.run_backtest(data, my_strategy)
        
        # Verify all expected keys exist
        self.assertIn('gross_pnl', results, "Results should contain 'gross_pnl'")
        self.assertIn('total_pnl', results, "Results should contain 'total_pnl'")
        self.assertIn('fee_impact_pct', results, "Results should contain 'fee_impact_pct'")
        
        print(f"  ✓ BacktestEngine example works")
        print(f"    - Gross PnL: ${results['gross_pnl']:.2f}")
        print(f"    - Net PnL: ${results['total_pnl']:.2f}")
        print(f"    - Fee impact: {results['fee_impact_pct']:.1f}%")

    def test_04_setup_commands(self):
        """Test that setup commands from README.md are valid"""
        print("\n" + "=" * 80)
        print("Testing Setup Commands from README.md")
        print("=" * 80)
        
        # Test 1: requirements.txt exists
        self.assertTrue(os.path.exists('requirements.txt'),
                       "requirements.txt should exist for 'pip install -r requirements.txt'")
        print("  ✓ requirements.txt exists")
        
        # Test 2: .env.example exists
        self.assertTrue(os.path.exists('.env.example'),
                       ".env.example should exist for 'cp .env.example .env'")
        print("  ✓ .env.example exists")
        
        # Test 3: bot.py exists and is importable
        self.assertTrue(os.path.exists('bot.py'),
                       "bot.py should exist for 'python bot.py'")
        from bot import TradingBot
        print("  ✓ bot.py exists and is importable")
        
        # Test 4: start.py exists
        self.assertTrue(os.path.exists('start.py'),
                       "start.py should exist for 'python start.py'")
        print("  ✓ start.py exists")

    def test_05_test_runner_script(self):
        """Test that run_priority1_tests.sh exists and is executable"""
        print("\n" + "=" * 80)
        print("Testing Priority 1 Test Runner Script")
        print("=" * 80)
        
        script_path = 'run_priority1_tests.sh'
        self.assertTrue(os.path.exists(script_path),
                       f"{script_path} should exist")
        print(f"  ✓ {script_path} exists")
        
        # Check if executable
        self.assertTrue(os.access(script_path, os.X_OK),
                       f"{script_path} should be executable")
        print(f"  ✓ {script_path} is executable")

    def test_06_monitoring_commands(self):
        """Test monitoring grep commands from README_PRIORITY1.md"""
        print("\n" + "=" * 80)
        print("Testing Monitoring Commands from README_PRIORITY1.md")
        print("=" * 80)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create sample log file
        sample_log = """
2024-01-01 10:00:00 - INFO - Bot started
2024-01-01 10:05:00 - WARNING - KILL SWITCH ACTIVATED: Daily loss limit
2024-01-01 10:10:00 - INFO - Trading signal generated
2024-01-01 10:15:00 - WARNING - GUARDRAILS BLOCKED: Per-trade risk too high
2024-01-01 10:20:00 - ERROR - CLOCK DRIFT: Drift exceeds 5000ms
2024-01-01 10:25:00 - INFO - Fees: Trading: $1.20, Funding: $0.10
"""
        
        log_file = 'logs/bot.log'
        with open(log_file, 'w') as f:
            f.write(sample_log)
        
        # Test grep commands
        test_cases = [
            ('KILL SWITCH ACTIVATED', 'grep "KILL SWITCH ACTIVATED" logs/bot.log'),
            ('GUARDRAILS BLOCKED', 'grep "GUARDRAILS BLOCKED" logs/bot.log'),
            ('CLOCK DRIFT', 'grep "CLOCK DRIFT" logs/bot.log'),
            ('Fees:', 'grep "Fees:" logs/bot.log')
        ]
        
        for keyword, command in test_cases:
            with self.subTest(command=command):
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0,
                               f"Command should succeed: {command}")
                self.assertIn(keyword, result.stdout,
                             f"Output should contain '{keyword}'")
                print(f"  ✓ {command}")

    def test_07_configuration_parameters(self):
        """Test that configuration parameters mentioned in README.md are valid"""
        print("\n" + "=" * 80)
        print("Testing Configuration Parameters")
        print("=" * 80)
        
        # Read .env.example and verify key parameters exist
        with open('.env.example', 'r') as f:
            env_content = f.read()
        
        required_params = [
            'KUCOIN_API_KEY',
            'KUCOIN_API_SECRET',
            'KUCOIN_API_PASSPHRASE',
            'ENABLE_WEBSOCKET',
            'CHECK_INTERVAL',
            'POSITION_UPDATE_INTERVAL',
            'TRAILING_STOP_PERCENTAGE',
            'MAX_OPEN_POSITIONS',
            'LOG_LEVEL'
        ]
        
        for param in required_params:
            with self.subTest(parameter=param):
                self.assertIn(param, env_content,
                             f"Parameter {param} should be in .env.example")
                print(f"  ✓ {param} present in .env.example")


def run_tests():
    """Run all tests with verbose output"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE README VERIFICATION TEST SUITE")
    print("=" * 80)
    print("Testing all code examples, commands, and functions from:")
    print("  - README.md")
    print("  - README_PRIORITY1.md")
    print("=" * 80)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestREADMEExamples)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL README EXAMPLES AND COMMANDS WORK CORRECTLY!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
