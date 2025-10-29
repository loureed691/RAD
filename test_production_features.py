"""
Production Feature Verification Test

Tests that all production-grade features are properly integrated and working.
This is a comprehensive test to verify the bot is production-ready.
"""
import pytest
from datetime import datetime
from data_validator import DataValidator
from production_monitor import ProductionMonitor


class TestProductionFeatures:
    """Test all production-grade features"""
    
    def test_data_validator_price_validation(self):
        """Test price validation catches invalid values"""
        validator = DataValidator()
        
        # Valid prices
        assert validator.is_valid_price(100.50)[0] == True
        assert validator.is_valid_price(0.001)[0] == True
        assert validator.is_valid_price(50000)[0] == True
        
        # Invalid prices
        assert validator.is_valid_price(-10)[0] == False
        assert validator.is_valid_price(0)[0] == False
        assert validator.is_valid_price(float('nan'))[0] == False
        assert validator.is_valid_price(float('inf'))[0] == False
        assert validator.is_valid_price(None)[0] == False
        assert validator.is_valid_price('invalid')[0] == False
    
    def test_data_validator_signal_validation(self):
        """Test signal validation"""
        validator = DataValidator()
        
        # Valid signals
        assert validator.validate_signal('BUY', 0.75)[0] == True
        assert validator.validate_signal('SELL', 0.80)[0] == True
        assert validator.validate_signal('HOLD', 0.50)[0] == True
        
        # Invalid signals
        assert validator.validate_signal('INVALID', 0.75)[0] == False
        assert validator.validate_signal('BUY', 1.5)[0] == False
        assert validator.validate_signal('BUY', -0.1)[0] == False
    
    def test_data_validator_ticker_validation(self):
        """Test ticker data validation"""
        validator = DataValidator()
        
        # Valid ticker
        valid_ticker = {
            'last': 100.50,
            'bid': 100.45,
            'ask': 100.55,
            'timestamp': datetime.now().timestamp() * 1000
        }
        assert validator.validate_ticker_data(valid_ticker, 'BTCUSDT')[0] == True
        
        # Invalid tickers
        assert validator.validate_ticker_data(None, 'BTCUSDT')[0] == False
        assert validator.validate_ticker_data({}, 'BTCUSDT')[0] == False
        
        invalid_ticker = {
            'last': -10,
            'bid': 100,
            'ask': 101
        }
        assert validator.validate_ticker_data(invalid_ticker, 'BTCUSDT')[0] == False
        
        # Invalid spread
        bad_spread = {
            'last': 100,
            'bid': 101,  # Bid > Ask
            'ask': 100
        }
        assert validator.validate_ticker_data(bad_spread, 'BTCUSDT')[0] == False
    
    def test_data_validator_position_validation(self):
        """Test position parameter validation"""
        validator = DataValidator()
        
        # Valid long position
        is_valid, reason = validator.validate_position_parameters(
            symbol='BTCUSDT',
            side='long',
            amount=0.1,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            leverage=10
        )
        assert is_valid == True
        
        # Valid short position
        is_valid, reason = validator.validate_position_parameters(
            symbol='BTCUSDT',
            side='short',
            amount=0.1,
            entry_price=100.0,
            stop_loss=105.0,
            take_profit=90.0,
            leverage=10
        )
        assert is_valid == True
        
        # Invalid: stop loss on wrong side
        is_valid, reason = validator.validate_position_parameters(
            symbol='BTCUSDT',
            side='long',
            amount=0.1,
            entry_price=100.0,
            stop_loss=105.0,  # Should be below entry for long
            take_profit=110.0,
            leverage=10
        )
        assert is_valid == False
        
        # Invalid: negative amount
        is_valid, reason = validator.validate_position_parameters(
            symbol='BTCUSDT',
            side='long',
            amount=-0.1,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            leverage=10
        )
        assert is_valid == False
    
    def test_production_monitor_health_tracking(self):
        """Test production monitor health tracking"""
        monitor = ProductionMonitor()
        
        # Initially healthy
        is_healthy, issues = monitor.check_health()
        assert is_healthy == True
        assert len(issues) == 0
        
        # Record successful operations
        monitor.record_scan_success()
        monitor.record_api_success()
        monitor.record_position_update_success()
        
        is_healthy, issues = monitor.check_health()
        assert is_healthy == True
    
    def test_production_monitor_failure_tracking(self):
        """Test production monitor failure tracking"""
        monitor = ProductionMonitor()
        
        # Record API failures
        for i in range(5):
            monitor.record_api_failure()
        
        # Should have failure count
        assert monitor.api_failures == 5
    
    def test_production_monitor_trade_tracking(self):
        """Test production monitor trade tracking"""
        monitor = ProductionMonitor()
        
        # Record winning trade
        monitor.record_trade(0.05, 1000)  # 5% profit, $1000 balance
        assert monitor.total_trades == 1
        assert monitor.winning_trades == 1
        assert monitor.losing_trades == 0
        
        # Record losing trade
        monitor.record_trade(-0.02, 980)  # -2% loss, $980 balance
        assert monitor.total_trades == 2
        assert monitor.winning_trades == 1
        assert monitor.losing_trades == 1
    
    def test_production_monitor_state_persistence(self):
        """Test production monitor saves and loads state"""
        import tempfile
        import os
        
        # Create temporary state file
        temp_dir = tempfile.mkdtemp()
        state_file = os.path.join(temp_dir, 'test_monitor_state.json')
        
        # Create monitor and record some trades
        monitor1 = ProductionMonitor()
        monitor1.state_file = state_file
        monitor1.record_trade(0.05, 1000)
        monitor1.record_trade(-0.02, 980)
        monitor1.save_state()
        
        # Create new monitor and load state
        monitor2 = ProductionMonitor()
        monitor2.state_file = state_file
        monitor2.load_state()
        
        # Verify state was restored
        assert monitor2.total_trades == 2
        assert monitor2.winning_trades == 1
        assert monitor2.losing_trades == 1
        
        # Cleanup
        os.remove(state_file)
        os.rmdir(temp_dir)
    
    def test_production_monitor_status_report(self):
        """Test production monitor generates status report"""
        monitor = ProductionMonitor()
        
        # Record some activity
        monitor.record_scan_success()
        monitor.record_trade(0.05, 1000)
        
        # Get status report
        status = monitor.get_status_report()
        
        assert 'status' in status
        assert 'uptime_hours' in status
        assert 'metrics' in status
        assert 'timestamps' in status
        
        assert status['metrics']['total_trades'] == 1
        assert status['metrics']['win_rate'] == 1.0


class TestFeatureIntegration:
    """Test that production features integrate correctly with bot"""
    
    def test_bot_imports_all_production_modules(self):
        """Test bot successfully imports all production modules"""
        try:
            from bot import TradingBot
            # If we get here, all imports succeeded
            assert True
        except ImportError as e:
            pytest.fail(f"Bot failed to import production module: {e}")
    
    def test_position_manager_has_state_methods(self):
        """Test PositionManager has save/load state methods"""
        from position_manager import PositionManager
        
        assert hasattr(PositionManager, 'save_state')
        assert hasattr(PositionManager, 'load_state')
    
    def test_all_production_modules_import(self):
        """Test all production modules import successfully"""
        modules = [
            'data_validator',
            'production_monitor',
            'bot',
            'config',
            'position_manager',
            'risk_manager',
            'kucoin_client'
        ]
        
        for module_name in modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
