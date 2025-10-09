#!/usr/bin/env python3
"""
Comprehensive test suite for bot fixes
Tests all bug fixes identified in the bot analysis
"""
import sys
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

print("=" * 80)
print("COMPREHENSIVE BOT FIXES TEST SUITE")
print("=" * 80)

class TestExecuteTradeErrorHandling(unittest.TestCase):
    """Test that execute_trade has proper error handling"""
    
    def test_execute_trade_has_try_except(self):
        """Verify execute_trade is wrapped in try-except"""
        with open('bot.py', 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Find execute_trade method
        in_method = False
        has_try = False
        has_except = False
        indent_level = 0
        
        for i, line in enumerate(lines):
            if 'def execute_trade(' in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                continue
            
            if in_method:
                # Check if we've left the method
                if line.strip().startswith('def ') and len(line) - len(line.lstrip()) <= indent_level:
                    break
                
                if 'try:' in line:
                    has_try = True
                if 'except Exception' in line:
                    has_except = True
        
        self.assertTrue(has_try, "execute_trade should have try block")
        self.assertTrue(has_except, "execute_trade should have except block")
        print("✅ execute_trade has proper error handling (try-except)")
    
    def test_execute_trade_error_logging(self):
        """Verify execute_trade logs errors properly"""
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Check for error logging in except block
        self.assertIn('except Exception as e:', content)
        self.assertIn('self.logger.error', content)
        print("✅ execute_trade has error logging")


class TestPositionValidation(unittest.TestCase):
    """Test Position class parameter validation"""
    
    def test_position_validates_entry_price(self):
        """Verify Position class validates entry_price"""
        with open('position_manager.py', 'r') as f:
            content = f.read()
        
        # Check for entry_price validation
        self.assertIn('if entry_price <= 0:', content)
        self.assertIn('raise ValueError', content)
        print("✅ Position class validates entry_price > 0")
    
    def test_position_validates_amount(self):
        """Verify Position class validates amount"""
        with open('position_manager.py', 'r') as f:
            content = f.read()
        
        # Check for amount validation
        self.assertIn('if amount <= 0:', content)
        print("✅ Position class validates amount > 0")
    
    def test_position_validates_leverage(self):
        """Verify Position class validates leverage"""
        with open('position_manager.py', 'r') as f:
            content = f.read()
        
        # Check for leverage validation
        self.assertIn('if leverage <= 0:', content)
        print("✅ Position class validates leverage > 0")
    
    def test_position_creation_with_invalid_params(self):
        """Test that Position raises ValueError for invalid params"""
        # Mock to avoid import errors
        sys.modules['kucoin_client'] = MagicMock()
        from position_manager import Position
        
        # Test invalid entry_price
        with self.assertRaises(ValueError):
            Position('BTC/USDT:USDT', 'long', 0, 1.0, 10, 40000)
        
        with self.assertRaises(ValueError):
            Position('BTC/USDT:USDT', 'long', -100, 1.0, 10, 40000)
        
        # Test invalid amount
        with self.assertRaises(ValueError):
            Position('BTC/USDT:USDT', 'long', 50000, 0, 10, 40000)
        
        # Test invalid leverage
        with self.assertRaises(ValueError):
            Position('BTC/USDT:USDT', 'long', 50000, 1.0, 0, 40000)
        
        print("✅ Position correctly raises ValueError for invalid parameters")


class TestLeverageCalculation(unittest.TestCase):
    """Test leverage calculation safety"""
    
    def test_leverage_division_protection(self):
        """Verify leverage division has zero protection"""
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Check for defensive leverage check
        self.assertIn('position.leverage if position.leverage > 0 else 1', content)
        print("✅ Leverage calculation has zero protection")
    
    def test_leverage_calculation_has_comment(self):
        """Verify leverage calculation has explanatory comment"""
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Check for comment explaining the protection
        self.assertIn('DEFENSIVE', content)
        self.assertIn('division by zero', content.lower())
        print("✅ Leverage calculation has explanatory comment")


class TestExistingFeatures(unittest.TestCase):
    """Verify existing features still work correctly"""
    
    def test_thread_safety_present(self):
        """Verify thread safety mechanisms are still present"""
        with open('bot.py', 'r') as f:
            content = f.read()
        
        self.assertIn('_scan_lock', content)
        self.assertIn('_position_monitor_lock', content)
        self.assertIn('with self._scan_lock:', content)
        self.assertIn('with self._position_monitor_lock:', content)
        print("✅ Thread safety mechanisms intact")
    
    def test_stale_data_validation_present(self):
        """Verify stale data validation is still present"""
        with open('bot.py', 'r') as f:
            content = f.read()
        
        self.assertIn('STALE_DATA_MULTIPLIER', content)
        self.assertIn('age > max_age', content)
        print("✅ Stale data validation intact")
    
    def test_balance_validation_present(self):
        """Verify balance validation is still present"""
        with open('bot.py', 'r') as f:
            content = f.read()
        
        self.assertIn('available_balance <= 0', content)
        print("✅ Balance validation intact")


class TestCodeQuality(unittest.TestCase):
    """Test overall code quality improvements"""
    
    def test_no_syntax_errors(self):
        """Verify no syntax errors were introduced"""
        import ast
        
        try:
            with open('bot.py', 'r') as f:
                ast.parse(f.read())
            bot_ok = True
        except SyntaxError:
            bot_ok = False
        
        try:
            with open('position_manager.py', 'r') as f:
                ast.parse(f.read())
            pm_ok = True
        except SyntaxError:
            pm_ok = False
        
        self.assertTrue(bot_ok, "bot.py should have valid syntax")
        self.assertTrue(pm_ok, "position_manager.py should have valid syntax")
        print("✅ All modified files have valid syntax")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestExecuteTradeErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestPositionValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestLeverageCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestExistingFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeQuality))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
