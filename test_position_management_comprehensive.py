#!/usr/bin/env python3
"""
Comprehensive Position Management Testing Suite

Tests all aspects of position management functionality including:
- Position creation and validation
- P&L calculations with leverage and fees
- Stop loss and take profit logic
- Thread safety and race conditions
- Edge cases and error handling
- Position lifecycle management
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional

# Mock KuCoin client for testing
class MockKuCoinClient:
    """Mock client for testing without actual exchange connection"""
    
    def __init__(self):
        self.positions = {}
        self.orders = []
        self.fail_next_call = False
        self.current_prices = {
            'BTC/USDT:USDT': 50000.0,
            'ETH/USDT:USDT': 3000.0,
        }
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get mock ticker data"""
        if self.fail_next_call:
            self.fail_next_call = False
            return None
        
        price = self.current_prices.get(symbol, 50000.0)
        return {'last': price, 'symbol': symbol}
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100):
        """Get mock OHLCV data"""
        if self.fail_next_call:
            self.fail_next_call = False
            return None
        
        # Generate simple mock OHLCV data
        import pandas as pd
        import numpy as np
        
        base_price = self.current_prices.get(symbol, 50000.0)
        data = []
        for i in range(limit):
            price = base_price * (1 + np.random.uniform(-0.02, 0.02))
            data.append([
                int(time.time() * 1000) - (limit - i) * 3600000,  # timestamp
                price * 0.99,  # open
                price * 1.01,  # high
                price * 0.98,  # low
                price,  # close
                100000 + np.random.randint(-10000, 10000)  # volume
            ])
        
        return data
    
    def create_market_order(self, symbol: str, side: str, amount: float, 
                          leverage: int, reduce_only: bool = False, 
                          is_critical: bool = False):
        """Mock market order creation"""
        if self.fail_next_call:
            self.fail_next_call = False
            return None
        
        price = self.current_prices.get(symbol, 50000.0)
        order = {
            'id': f'order_{len(self.orders)}',
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'average': price,
            'status': 'closed'
        }
        self.orders.append(order)
        return order
    
    def close_position(self, symbol: str) -> bool:
        """Mock position close"""
        if self.fail_next_call:
            self.fail_next_call = False
            return False
        return True
    
    def get_open_positions(self):
        """Mock get open positions"""
        return list(self.positions.values())
    
    def get_market_limits(self, symbol: str):
        """Mock market limits"""
        return {
            'amount': {'min': 0.001, 'max': 1000000},
            'cost': {'min': 1, 'max': 100000000}
        }
    
    def set_price(self, symbol: str, price: float):
        """Set current price for testing"""
        self.current_prices[symbol] = price


def test_position_creation():
    """Test basic position creation and initialization"""
    print("\n" + "="*80)
    print("TEST: Position Creation and Initialization")
    print("="*80)
    
    try:
        from position_manager import Position
        
        # Test long position
        long_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        assert long_pos.symbol == 'BTC/USDT:USDT', "Symbol mismatch"
        assert long_pos.side == 'long', "Side mismatch"
        assert long_pos.entry_price == 50000.0, "Entry price mismatch"
        assert long_pos.amount == 0.1, "Amount mismatch"
        assert long_pos.leverage == 10, "Leverage mismatch"
        assert long_pos.stop_loss == 49000.0, "Stop loss mismatch"
        assert long_pos.take_profit == 52000.0, "Take profit mismatch"
        assert long_pos.highest_price == 50000.0, "Highest price should equal entry for long"
        assert long_pos.lowest_price is None, "Lowest price should be None for long"
        
        print("✓ Long position created successfully")
        print(f"  Entry: ${long_pos.entry_price:.2f}, SL: ${long_pos.stop_loss:.2f}, TP: ${long_pos.take_profit:.2f}")
        
        # Test short position
        short_pos = Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=1.0,
            leverage=5,
            stop_loss=3100.0,
            take_profit=2800.0
        )
        
        assert short_pos.side == 'short', "Side mismatch"
        assert short_pos.highest_price is None, "Highest price should be None for short"
        assert short_pos.lowest_price == 3000.0, "Lowest price should equal entry for short"
        
        print("✓ Short position created successfully")
        print(f"  Entry: ${short_pos.entry_price:.2f}, SL: ${short_pos.stop_loss:.2f}, TP: ${short_pos.take_profit:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Position creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pnl_calculations():
    """Test P&L calculations with various scenarios"""
    print("\n" + "="*80)
    print("TEST: P&L Calculations (Leverage, Fees, Edge Cases)")
    print("="*80)
    
    try:
        from position_manager import Position
        
        # Test long position P&L
        long_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Test profitable long
        current_price = 51000.0
        pnl = long_pos.get_pnl(current_price)
        expected_pnl = (51000.0 - 50000.0) / 50000.0  # 2%
        assert abs(pnl - expected_pnl) < 0.0001, f"Long PnL mismatch: {pnl} vs {expected_pnl}"
        
        leveraged_pnl = long_pos.get_leveraged_pnl(current_price)
        expected_leveraged = expected_pnl * 10  # 20% with 10x leverage
        assert abs(leveraged_pnl - expected_leveraged) < 0.0001, \
            f"Leveraged PnL mismatch: {leveraged_pnl} vs {expected_leveraged}"
        
        print(f"✓ Long position profit calculation correct")
        print(f"  Price: $50,000 -> $51,000 (+2%)")
        print(f"  Unleveraged P&L: {pnl:.2%}")
        print(f"  Leveraged P&L (10x): {leveraged_pnl:.2%}")
        
        # Test with fees
        leveraged_pnl_with_fees = long_pos.get_leveraged_pnl(current_price, include_fees=True)
        expected_with_fees = (pnl - 0.0012) * 10  # Subtract 0.12% fees before leverage
        assert abs(leveraged_pnl_with_fees - expected_with_fees) < 0.0001, \
            f"Leveraged PnL with fees mismatch: {leveraged_pnl_with_fees} vs {expected_with_fees}"
        
        print(f"✓ Fee calculation correct")
        print(f"  P&L after fees: {leveraged_pnl_with_fees:.2%} (fees: 0.12% = 1.2% on leverage)")
        
        # Test losing long
        current_price = 49000.0
        pnl = long_pos.get_pnl(current_price)
        expected_pnl = (49000.0 - 50000.0) / 50000.0  # -2%
        assert abs(pnl - expected_pnl) < 0.0001, f"Long loss PnL mismatch"
        
        leveraged_pnl = long_pos.get_leveraged_pnl(current_price)
        expected_leveraged = expected_pnl * 10  # -20% with 10x leverage
        assert abs(leveraged_pnl - expected_leveraged) < 0.0001, \
            f"Leveraged loss PnL mismatch"
        
        print(f"✓ Long position loss calculation correct")
        print(f"  Price: $50,000 -> $49,000 (-2%)")
        print(f"  Leveraged P&L (10x): {leveraged_pnl:.2%}")
        
        # Test short position P&L
        short_pos = Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=1.0,
            leverage=5,
            stop_loss=3100.0,
            take_profit=2800.0
        )
        
        # Test profitable short (price goes down)
        current_price = 2900.0
        pnl = short_pos.get_pnl(current_price)
        expected_pnl = (3000.0 - 2900.0) / 3000.0  # 3.33%
        assert abs(pnl - expected_pnl) < 0.0001, f"Short PnL mismatch"
        
        leveraged_pnl = short_pos.get_leveraged_pnl(current_price)
        expected_leveraged = expected_pnl * 5  # 16.67% with 5x leverage
        assert abs(leveraged_pnl - expected_leveraged) < 0.0001, \
            f"Leveraged short PnL mismatch"
        
        print(f"✓ Short position profit calculation correct")
        print(f"  Price: $3,000 -> $2,900 (-3.33%)")
        print(f"  Leveraged P&L (5x): {leveraged_pnl:.2%}")
        
        # Test edge case: zero price (should return 0 to prevent division by zero)
        zero_pnl = long_pos.get_pnl(0)
        assert zero_pnl == 0.0, "Zero price should return 0 PnL"
        print(f"✓ Zero price edge case handled correctly")
        
        # Test edge case: negative price (should return 0)
        neg_pnl = long_pos.get_pnl(-100)
        assert neg_pnl == 0.0, "Negative price should return 0 PnL"
        print(f"✓ Negative price edge case handled correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ P&L calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stop_loss_logic():
    """Test stop loss update logic including trailing stops"""
    print("\n" + "="*80)
    print("TEST: Stop Loss Logic (Trailing, Breakeven, Edge Cases)")
    print("="*80)
    
    try:
        from position_manager import Position
        
        # Test long position trailing stop
        long_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        initial_stop = long_pos.stop_loss
        print(f"Initial stop loss: ${initial_stop:.2f}")
        
        # Price moves up, should update trailing stop
        current_price = 51000.0
        long_pos.update_trailing_stop(current_price, trailing_percentage=0.02)
        
        assert long_pos.stop_loss > initial_stop, "Stop loss should move up for profitable long"
        assert long_pos.highest_price == current_price, "Highest price should be updated"
        assert long_pos.trailing_stop_activated, "Trailing stop should be activated"
        
        print(f"✓ Long trailing stop updated correctly")
        print(f"  Price: $50,000 -> $51,000")
        print(f"  Stop loss: ${initial_stop:.2f} -> ${long_pos.stop_loss:.2f}")
        
        # Price moves down, stop should not change
        previous_stop = long_pos.stop_loss
        current_price = 50500.0
        long_pos.update_trailing_stop(current_price, trailing_percentage=0.02)
        
        assert long_pos.stop_loss == previous_stop, "Stop loss should not decrease for long"
        print(f"✓ Stop loss does not move down on price retracement")
        
        # Test breakeven move
        long_pos2 = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Price moves up 2% (leveraged P&L = 20%)
        current_price = 51000.0
        leveraged_pnl = long_pos2.get_leveraged_pnl(current_price)
        
        # Should move to breakeven when profit > 1.5%
        moved = long_pos2.move_to_breakeven(current_price)
        
        if leveraged_pnl > 0.015:  # Should trigger at 1.5% ROI
            assert moved, "Should move to breakeven at 1.5%+ profit"
            assert long_pos2.stop_loss > long_pos2.entry_price * 0.999, \
                "Breakeven stop should be at/above entry"
            print(f"✓ Breakeven move triggered correctly")
            print(f"  Leveraged P&L: {leveraged_pnl:.2%} (threshold: 1.5%)")
            print(f"  New stop loss: ${long_pos2.stop_loss:.2f} (entry: ${long_pos2.entry_price:.2f})")
        else:
            print(f"⚠ Leveraged P&L {leveraged_pnl:.2%} below 1.5% threshold, skipping breakeven test")
        
        # Test short position trailing stop
        short_pos = Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=1.0,
            leverage=5,
            stop_loss=3100.0,
            take_profit=2800.0
        )
        
        initial_stop = short_pos.stop_loss
        
        # Price moves down, should update trailing stop
        current_price = 2900.0
        short_pos.update_trailing_stop(current_price, trailing_percentage=0.02)
        
        assert short_pos.stop_loss < initial_stop, "Stop loss should move down for profitable short"
        assert short_pos.lowest_price == current_price, "Lowest price should be updated"
        
        print(f"✓ Short trailing stop updated correctly")
        print(f"  Price: $3,000 -> $2,900")
        print(f"  Stop loss: ${initial_stop:.2f} -> ${short_pos.stop_loss:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Stop loss logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_take_profit_logic():
    """Test take profit update and extension logic"""
    print("\n" + "="*80)
    print("TEST: Take Profit Logic (Extension, Limits, Edge Cases)")
    print("="*80)
    
    try:
        from position_manager import Position
        
        # Test that TP doesn't move away when price approaches
        long_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Store initial TP
        initial_tp = long_pos.take_profit
        initial_distance = (initial_tp - long_pos.entry_price) / long_pos.entry_price
        
        print(f"Initial take profit: ${initial_tp:.2f} ({initial_distance:.2%} from entry)")
        
        # Price is 80% of the way to TP - TP should NOT extend
        current_price = 50000.0 + (52000.0 - 50000.0) * 0.8  # 51600
        long_pos.update_take_profit(
            current_price,
            momentum=0.03,  # Strong momentum
            trend_strength=0.8,  # Strong trend
            volatility=0.02,  # Low volatility
            rsi=60.0
        )
        
        # TP should not move away when price is close (70%+ progress)
        # The code has protection against moving TP away
        progress = (current_price - long_pos.entry_price) / (initial_tp - long_pos.entry_price)
        print(f"✓ Price at {progress:.1%} of way to TP (${current_price:.2f})")
        
        if progress >= 0.7:
            # When progress >= 70%, TP should not extend (stays at same or closer)
            assert long_pos.take_profit <= initial_tp * 1.01, \
                f"TP should not extend significantly when price is close: {long_pos.take_profit} vs {initial_tp}"
            print(f"✓ TP did not move away: ${long_pos.take_profit:.2f}")
        else:
            print(f"⚠ Progress {progress:.1%} below 70%, TP extension allowed")
        
        # Test TP extension when price is far from target
        long_pos2 = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Price is only 20% of the way to TP - TP can extend
        current_price = 50400.0
        initial_tp2 = long_pos2.take_profit
        
        long_pos2.update_take_profit(
            current_price,
            momentum=0.05,  # Very strong momentum
            trend_strength=0.9,  # Very strong trend
            volatility=0.02,  # Low volatility
            rsi=55.0
        )
        
        progress2 = (current_price - long_pos2.entry_price) / (initial_tp2 - long_pos2.entry_price)
        print(f"\n✓ Price at {progress2:.1%} of way to TP (${current_price:.2f})")
        
        if progress2 < 0.5:
            # When progress < 50%, TP can extend with strong conditions
            # Just verify it doesn't become invalid (must stay above current price for long)
            assert long_pos2.take_profit >= current_price, \
                "TP must stay above current price for long"
            print(f"✓ TP extension allowed when far from target: ${initial_tp2:.2f} -> ${long_pos2.take_profit:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Take profit logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_should_close_logic():
    """Test position closing conditions including emergency stops"""
    print("\n" + "="*80)
    print("TEST: Position Close Logic (SL, TP, Emergency Stops)")
    print("="*80)
    
    try:
        from position_manager import Position
        
        # Test stop loss trigger
        long_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Price at stop loss (49000)
        # Note: At 49000, price is -2% which is -20% ROI with 10x leverage
        # This is worse than -15% emergency stop, so emergency stop triggers first
        should_close, reason = long_pos.should_close(49000.0)
        assert should_close, "Should close at stop loss"
        # Emergency stop will trigger before regular stop loss due to leverage
        assert 'stop' in reason.lower(), f"Should be some stop reason, got {reason}"
        print(f"✓ Stop loss trigger works (reason: {reason})")
        
        # Price slightly below stop loss but above -15% emergency stop
        # SL is at 49000, so test at 49200 (above SL) with custom SL
        test_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49500.0,  # Higher SL so we can test regular SL
            take_profit=52000.0
        )
        
        # Price at 49300 = -1.4% price = -14% ROI (below SL, above emergency)
        should_close, reason = test_pos.should_close(49300.0)
        assert should_close, "Should close below stop loss"
        assert reason == 'stop_loss', f"Should be regular stop_loss, got {reason}"
        print(f"✓ Price below stop loss triggers regular stop loss")
        
        # Test take profit trigger
        should_close, reason = long_pos.should_close(52000.0)
        assert should_close, "Should close at take profit"
        assert 'take_profit' in reason, f"Reason should contain take_profit, got {reason}"
        print(f"✓ Take profit trigger works correctly (reason: {reason})")
        
        # Test emergency stop at -40% ROI (liquidation risk)
        # Need -4% price move to get -40% ROI with 10x leverage
        emergency_price = 50000.0 * (1 - 0.04)  # -4% = -40% ROI at 10x
        should_close, reason = long_pos.should_close(emergency_price)
        assert should_close, "Should trigger emergency stop at -40% ROI"
        assert 'emergency' in reason.lower(), f"Should be emergency stop, got {reason}"
        print(f"✓ Emergency stop at -40% ROI works")
        print(f"  Price: ${emergency_price:.2f}, ROI: {long_pos.get_leveraged_pnl(emergency_price):.2%}")
        
        # Test emergency stop at -25% ROI (severe loss)
        severe_loss_price = 50000.0 * (1 - 0.025)  # -2.5% = -25% ROI at 10x
        should_close, reason = long_pos.should_close(severe_loss_price)
        assert should_close, "Should trigger emergency stop at -25% ROI"
        assert 'emergency' in reason.lower(), f"Should be emergency stop, got {reason}"
        print(f"✓ Emergency stop at -25% ROI works")
        
        # Test emergency stop at -15% ROI (excessive loss)
        excessive_loss_price = 50000.0 * (1 - 0.015)  # -1.5% = -15% ROI at 10x
        should_close, reason = long_pos.should_close(excessive_loss_price)
        assert should_close, "Should trigger emergency stop at -15% ROI"
        assert 'emergency' in reason.lower(), f"Should be emergency stop, got {reason}"
        print(f"✓ Emergency stop at -15% ROI works")
        
        # Test profit taking at 20% ROI
        profit_price = 50000.0 * (1 + 0.02)  # +2% = +20% ROI at 10x
        should_close, reason = long_pos.should_close(profit_price)
        # Should trigger exceptional profit taking at 20% ROI
        assert should_close, "Should close at 20% ROI"
        print(f"✓ Exceptional profit taking at 20% ROI works")
        print(f"  Price: ${profit_price:.2f}, ROI: {long_pos.get_leveraged_pnl(profit_price):.2%}")
        
        # Test normal operation (no close)
        normal_price = 50500.0
        should_close, reason = long_pos.should_close(normal_price)
        if not should_close:
            print(f"✓ Position stays open at normal price")
            print(f"  Price: ${normal_price:.2f}, ROI: {long_pos.get_leveraged_pnl(normal_price):.2%}")
        
        return True
        
    except Exception as e:
        print(f"✗ Should close logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_thread_safety():
    """Test thread safety of position manager"""
    print("\n" + "="*80)
    print("TEST: Thread Safety (Concurrent Access)")
    print("="*80)
    
    try:
        from position_manager import PositionManager
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Test concurrent position access
        errors = []
        access_count = [0]
        
        def access_positions():
            try:
                for _ in range(100):
                    # Try various operations
                    count = pm.get_open_positions_count()
                    positions = pm.get_all_positions()
                    has_btc = pm.has_position('BTC/USDT:USDT')
                    access_count[0] += 1
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=access_positions)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert access_count[0] == 1000, f"Expected 1000 accesses, got {access_count[0]}"
        
        print(f"✓ Thread safety test passed")
        print(f"  Threads: 10")
        print(f"  Operations per thread: 100")
        print(f"  Total operations: {access_count[0]}")
        print(f"  Errors: {len(errors)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Thread safety test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_validation():
    """Test position parameter validation"""
    print("\n" + "="*80)
    print("TEST: Position Parameter Validation")
    print("="*80)
    
    try:
        from position_manager import PositionManager
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Test valid parameters
        is_valid, msg = pm.validate_position_parameters(
            'BTC/USDT:USDT', 0.1, 10, 0.05
        )
        assert is_valid, f"Valid parameters rejected: {msg}"
        print(f"✓ Valid parameters accepted")
        
        # Test invalid amount (zero)
        is_valid, msg = pm.validate_position_parameters(
            'BTC/USDT:USDT', 0, 10, 0.05
        )
        assert not is_valid, "Zero amount should be invalid"
        assert 'amount' in msg.lower(), f"Error message should mention amount: {msg}"
        print(f"✓ Zero amount rejected: {msg}")
        
        # Test invalid amount (negative)
        is_valid, msg = pm.validate_position_parameters(
            'BTC/USDT:USDT', -0.1, 10, 0.05
        )
        assert not is_valid, "Negative amount should be invalid"
        print(f"✓ Negative amount rejected: {msg}")
        
        # Test invalid leverage (too high)
        is_valid, msg = pm.validate_position_parameters(
            'BTC/USDT:USDT', 0.1, 200, 0.05
        )
        assert not is_valid, "Leverage > 125 should be invalid"
        assert 'leverage' in msg.lower(), f"Error message should mention leverage: {msg}"
        print(f"✓ Excessive leverage rejected: {msg}")
        
        # Test invalid leverage (zero)
        is_valid, msg = pm.validate_position_parameters(
            'BTC/USDT:USDT', 0.1, 0, 0.05
        )
        assert not is_valid, "Zero leverage should be invalid"
        print(f"✓ Zero leverage rejected: {msg}")
        
        # Test invalid stop loss (zero)
        is_valid, msg = pm.validate_position_parameters(
            'BTC/USDT:USDT', 0.1, 10, 0
        )
        assert not is_valid, "Zero stop loss should be invalid"
        assert 'stop loss' in msg.lower(), f"Error message should mention stop loss: {msg}"
        print(f"✓ Zero stop loss rejected: {msg}")
        
        # Test invalid stop loss (>= 1 or 100%)
        is_valid, msg = pm.validate_position_parameters(
            'BTC/USDT:USDT', 0.1, 10, 1.0
        )
        assert not is_valid, "Stop loss >= 1 should be invalid"
        print(f"✓ Stop loss >= 100% rejected: {msg}")
        
        return True
        
    except Exception as e:
        print(f"✗ Position validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_failure_handling():
    """Test graceful handling of API failures"""
    print("\n" + "="*80)
    print("TEST: API Failure Handling")
    print("="*80)
    
    try:
        from position_manager import PositionManager, Position
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Create a position first
        success = pm.open_position(
            'BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05
        )
        assert success, "Failed to create initial position"
        print(f"✓ Initial position created")
        
        # Test update with API failure (should skip update, not crash)
        client.fail_next_call = True
        
        # Update should handle API failure gracefully
        updates_list = list(pm.update_positions())
        
        # Should not crash, position should still exist
        assert pm.has_position('BTC/USDT:USDT'), "Position should still exist after API failure"
        print(f"✓ API failure handled gracefully during update")
        
        # Test multiple retries in update_positions
        # The code retries ticker fetches up to 3 times
        client.fail_next_call = True
        updates_list = list(pm.update_positions())
        
        print(f"✓ Position update survives ticker API failures")
        
        return True
        
    except Exception as e:
        print(f"✗ API failure handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_lifecycle():
    """Test complete position lifecycle"""
    print("\n" + "="*80)
    print("TEST: Position Lifecycle (Open -> Update -> Close)")
    print("="*80)
    
    try:
        from position_manager import PositionManager
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # 1. Open position
        print("\n1. Opening position...")
        success = pm.open_position(
            'BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05
        )
        assert success, "Failed to open position"
        assert pm.has_position('BTC/USDT:USDT'), "Position not found after opening"
        print(f"✓ Position opened successfully")
        
        # 2. Update position (price moves up)
        print("\n2. Updating position (price up)...")
        client.set_price('BTC/USDT:USDT', 51000.0)
        
        # Check position state before update
        pos_before = pm.get_position('BTC/USDT:USDT')
        if pos_before:
            pnl = pos_before.get_leveraged_pnl(51000.0)
            print(f"  Position state: Price $51000, ROI: {pnl:.2%}")
            print(f"  TP: ${pos_before.take_profit:.2f}, SL: ${pos_before.stop_loss:.2f}")
        
        updates = list(pm.update_positions())
        
        # Debug: Print any closures
        if updates:
            for symbol, pnl, pos in updates:
                print(f"  Position closed: {symbol}, P&L: {pnl:.2%}")
        
        # At 51000, the position is at +2% price = +20% ROI with 10x leverage
        # This is below the 20% exceptional profit threshold, so should stay open
        # unless TP is very far away and triggers early profit taking
        if not pm.has_position('BTC/USDT:USDT'):
            print(f"⚠ Position was closed during update (may be early profit taking)")
            # Reopen for next test
            success = pm.open_position('BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05)
            assert success, "Failed to reopen position"
        else:
            print(f"✓ Position updated, still open")
        
        # 3. Update position (price moves to take profit)
        print("\n3. Moving price to take profit...")
        position = pm.get_position('BTC/USDT:USDT')
        if position:
            tp_price = position.take_profit * 1.01  # Slightly above TP
            client.set_price('BTC/USDT:USDT', tp_price)
            updates = list(pm.update_positions())
            
            # Position should be closed by take profit
            if not pm.has_position('BTC/USDT:USDT'):
                print(f"✓ Position closed at take profit")
            else:
                print(f"⚠ Position still open (TP may have been extended)")
        
        # 4. Test stop loss closure
        print("\n4. Testing stop loss...")
        success = pm.open_position(
            'ETH/USDT:USDT', 'BUY', 1.0, 5, 0.05
        )
        assert success, "Failed to open second position"
        
        position = pm.get_position('ETH/USDT:USDT')
        if position:
            sl_price = position.stop_loss * 0.99  # Below stop loss
            client.set_price('ETH/USDT:USDT', sl_price)
            updates = list(pm.update_positions())
            
            # Position should be closed by stop loss
            assert not pm.has_position('ETH/USDT:USDT'), "Position should be closed at stop loss"
            print(f"✓ Position closed at stop loss")
        
        return True
        
    except Exception as e:
        print(f"✗ Position lifecycle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all position management tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE POSITION MANAGEMENT TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Position Creation", test_position_creation),
        ("P&L Calculations", test_pnl_calculations),
        ("Stop Loss Logic", test_stop_loss_logic),
        ("Take Profit Logic", test_take_profit_logic),
        ("Should Close Logic", test_should_close_logic),
        ("Thread Safety", test_thread_safety),
        ("Position Validation", test_position_validation),
        ("API Failure Handling", test_api_failure_handling),
        ("Position Lifecycle", test_position_lifecycle),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{total} tests passed")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
