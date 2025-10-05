"""
Advanced exit strategies for position management
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from logger import Logger

class AdvancedExitStrategy:
    """Sophisticated exit strategies beyond simple trailing stops"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
    
    def time_based_exit(self, position_entry_time: datetime, 
                       current_time: datetime,
                       max_hold_minutes: int = 1440) -> Tuple[bool, str]:
        """
        Determine if position should be closed based on time
        
        Args:
            position_entry_time: When position was opened
            current_time: Current time
            max_hold_minutes: Maximum hold time in minutes (default 24 hours)
            
        Returns:
            Tuple of (should_exit, reason)
        """
        hold_duration = (current_time - position_entry_time).total_seconds() / 60
        
        if hold_duration > max_hold_minutes:
            return True, f"Max hold time reached ({hold_duration:.0f} minutes)"
        
        return False, ""
    
    def volatility_based_exit(self, entry_volatility: float,
                            current_volatility: float,
                            threshold_multiplier: float = 2.0) -> Tuple[bool, str]:
        """
        Exit if volatility increases significantly (risk management)
        
        Args:
            entry_volatility: Volatility when position was opened
            current_volatility: Current market volatility
            threshold_multiplier: Exit if volatility increases by this factor
            
        Returns:
            Tuple of (should_exit, reason)
        """
        if current_volatility > entry_volatility * threshold_multiplier:
            increase_pct = ((current_volatility / entry_volatility) - 1) * 100
            return True, f"Volatility spike detected (+{increase_pct:.1f}%)"
        
        return False, ""
    
    def momentum_reversal_exit(self, position_side: str,
                              momentum: float,
                              rsi: float) -> Tuple[bool, str]:
        """
        Exit on momentum reversal signals
        
        Args:
            position_side: 'long' or 'short'
            momentum: Current price momentum
            rsi: Current RSI value
            
        Returns:
            Tuple of (should_exit, reason)
        """
        if position_side == 'long':
            # Exit long if momentum turns negative and RSI is overbought
            if momentum < -0.02 and rsi > 70:
                return True, f"Momentum reversal (RSI: {rsi:.1f}, momentum: {momentum:.3f})"
        else:  # short
            # Exit short if momentum turns positive and RSI is oversold
            if momentum > 0.02 and rsi < 30:
                return True, f"Momentum reversal (RSI: {rsi:.1f}, momentum: {momentum:.3f})"
        
        return False, ""
    
    def profit_target_scaling(self, current_pnl_pct: float,
                            entry_price: float,
                            current_price: float,
                            position_side: str,
                            targets: list = None) -> Tuple[Optional[float], str]:
        """
        Scale out of position at multiple profit targets
        
        Args:
            current_pnl_pct: Current P&L percentage
            entry_price: Entry price
            current_price: Current price
            position_side: 'long' or 'short'
            targets: List of target percentages to scale out at
            
        Returns:
            Tuple of (scale_out_percentage, reason) or (None, "") if no action
        """
        if targets is None:
            # Default targets: 25% at +2%, 25% at +4%, 50% at +6%
            targets = [
                (0.02, 0.25, "First target"),
                (0.04, 0.25, "Second target"),
                (0.06, 0.50, "Third target")
            ]
        
        for target_pct, scale_pct, reason in targets:
            if current_pnl_pct >= target_pct:
                return scale_pct, f"{reason} reached ({current_pnl_pct:.2%})"
        
        return None, ""
    
    def chandelier_exit(self, current_price: float,
                       highest_price: float,
                       atr: float,
                       multiplier: float = 3.0,
                       position_side: str = 'long') -> Tuple[bool, float, str]:
        """
        Chandelier exit - trailing stop based on ATR from highest point
        
        Args:
            current_price: Current price
            highest_price: Highest price since entry (for long)
            atr: Average True Range
            multiplier: ATR multiplier for stop distance
            position_side: 'long' or 'short'
            
        Returns:
            Tuple of (should_exit, stop_price, reason)
        """
        if position_side == 'long':
            stop_price = highest_price - (atr * multiplier)
            if current_price < stop_price:
                return True, stop_price, f"Chandelier exit triggered (price below {stop_price:.2f})"
            return False, stop_price, ""
        else:  # short
            lowest_price = highest_price  # Actually lowest in this context
            stop_price = lowest_price + (atr * multiplier)
            if current_price > stop_price:
                return True, stop_price, f"Chandelier exit triggered (price above {stop_price:.2f})"
            return False, stop_price, ""
    
    def parabolic_sar_exit(self, current_price: float,
                          sar_value: float,
                          position_side: str = 'long') -> Tuple[bool, str]:
        """
        Exit based on Parabolic SAR crossing
        
        Args:
            current_price: Current price
            sar_value: Current Parabolic SAR value
            position_side: 'long' or 'short'
            
        Returns:
            Tuple of (should_exit, reason)
        """
        if position_side == 'long':
            if current_price < sar_value:
                return True, f"Parabolic SAR exit (price {current_price:.2f} < SAR {sar_value:.2f})"
        else:  # short
            if current_price > sar_value:
                return True, f"Parabolic SAR exit (price {current_price:.2f} > SAR {sar_value:.2f})"
        
        return False, ""
    
    def profit_lock_exit(self, current_pnl_pct: float,
                        peak_pnl_pct: float,
                        lock_threshold: float = 0.03,
                        retracement_pct: float = 0.3) -> Tuple[bool, str]:
        """
        Lock in profits after reaching threshold, exit on retracement
        
        Args:
            current_pnl_pct: Current P&L percentage
            peak_pnl_pct: Peak P&L achieved
            lock_threshold: P&L threshold to start locking (default 3%)
            retracement_pct: Allow this much retracement from peak (default 30%)
            
        Returns:
            Tuple of (should_exit, reason)
        """
        if peak_pnl_pct > lock_threshold:
            # We're in profit-lock mode
            allowed_retracement = peak_pnl_pct * retracement_pct
            if current_pnl_pct < (peak_pnl_pct - allowed_retracement):
                return True, f"Profit lock triggered (retraced from {peak_pnl_pct:.2%} to {current_pnl_pct:.2%})"
        
        return False, ""
    
    def breakeven_plus_exit(self, current_pnl_pct: float,
                           entry_price: float,
                           current_price: float,
                           position_side: str,
                           activation_threshold: float = 0.015,
                           lock_at_pct: float = 0.005) -> Tuple[Optional[float], str]:
        """
        Move stop to breakeven + small profit after reaching threshold
        
        Args:
            current_pnl_pct: Current P&L percentage
            entry_price: Entry price
            current_price: Current price
            position_side: 'long' or 'short'
            activation_threshold: P&L threshold to activate (default 1.5%)
            lock_at_pct: Lock profit at this level (default 0.5%)
            
        Returns:
            Tuple of (new_stop_price, reason) or (None, "") if not activated
        """
        if current_pnl_pct >= activation_threshold:
            if position_side == 'long':
                new_stop = entry_price * (1 + lock_at_pct)
                return new_stop, f"Breakeven+{lock_at_pct*100:.1f}% stop activated"
            else:  # short
                new_stop = entry_price * (1 - lock_at_pct)
                return new_stop, f"Breakeven+{lock_at_pct*100:.1f}% stop activated"
        
        return None, ""
    
    def get_comprehensive_exit_signal(self, position_data: Dict,
                                     market_data: Dict) -> Tuple[bool, str, Optional[float]]:
        """
        Combine multiple exit strategies for optimal exit timing
        
        Args:
            position_data: Dict with position info (entry_time, entry_price, side, etc.)
            market_data: Dict with current market data (price, volatility, momentum, etc.)
            
        Returns:
            Tuple of (should_exit, reason, scale_out_percentage)
        """
        exit_signals = []
        
        # Time-based exit
        if 'entry_time' in position_data:
            should_exit, reason = self.time_based_exit(
                position_data['entry_time'],
                datetime.now(),
                max_hold_minutes=position_data.get('max_hold_minutes', 1440)
            )
            if should_exit:
                exit_signals.append(('time', reason, 1.0))
        
        # Volatility-based exit
        if 'entry_volatility' in position_data and 'current_volatility' in market_data:
            should_exit, reason = self.volatility_based_exit(
                position_data['entry_volatility'],
                market_data['current_volatility']
            )
            if should_exit:
                exit_signals.append(('volatility', reason, 1.0))
        
        # Momentum reversal
        if 'momentum' in market_data and 'rsi' in market_data:
            should_exit, reason = self.momentum_reversal_exit(
                position_data.get('side', 'long'),
                market_data['momentum'],
                market_data['rsi']
            )
            if should_exit:
                exit_signals.append(('momentum_reversal', reason, 1.0))
        
        # Profit lock
        if 'current_pnl_pct' in position_data and 'peak_pnl_pct' in position_data:
            should_exit, reason = self.profit_lock_exit(
                position_data['current_pnl_pct'],
                position_data['peak_pnl_pct']
            )
            if should_exit:
                exit_signals.append(('profit_lock', reason, 1.0))
        
        # Profit target scaling
        if 'current_pnl_pct' in position_data:
            scale_pct, reason = self.profit_target_scaling(
                position_data['current_pnl_pct'],
                position_data.get('entry_price', 0),
                market_data.get('current_price', 0),
                position_data.get('side', 'long')
            )
            if scale_pct:
                exit_signals.append(('profit_scaling', reason, scale_pct))
        
        # If any full exit signal, take it
        full_exits = [sig for sig in exit_signals if sig[2] >= 1.0]
        # Define priority for exit signal types (lower index = higher priority)
        priority_order = [
            'time',
            'volatility',
            'momentum_reversal',
            'profit_lock',
            'profit_scaling'
        ]
        if full_exits:
            # Sort full exits by priority
            full_exits_sorted = sorted(
                full_exits,
                key=lambda x: priority_order.index(x[0]) if x[0] in priority_order else len(priority_order)
            )
            signal_type, reason, scale = full_exits_sorted[0]
            self.logger.info(f"Exit signal: {signal_type} - {reason}")
            return True, reason, 1.0
        
        # If any partial exit signal, take the largest
        if exit_signals:
            signal_type, reason, scale = max(exit_signals, key=lambda x: x[2])
            self.logger.info(f"Partial exit signal: {signal_type} - {reason} ({scale*100:.0f}%)")
            return False, reason, scale
        
        return False, "", None
    
    def calculate_dynamic_trailing_stop(self, current_pnl_pct: float,
                                       base_trailing_pct: float = 0.02,
                                       profit_tiers: list = None) -> float:
        """
        Calculate dynamic trailing stop that tightens as profit increases
        
        Args:
            current_pnl_pct: Current P&L percentage
            base_trailing_pct: Base trailing stop percentage
            profit_tiers: List of (profit_threshold, trailing_pct) tuples
            
        Returns:
            Trailing stop percentage to use
        """
        if profit_tiers is None:
            # Default tiers: tighten stop as profits increase
            profit_tiers = [
                (0.05, 0.015),  # At +5% profit, trail by 1.5%
                (0.08, 0.01),   # At +8% profit, trail by 1.0%
                (0.10, 0.008),  # At +10% profit, trail by 0.8%
            ]
        
        # Find applicable tier
        applicable_trailing = base_trailing_pct
        for threshold, trailing_pct in sorted(profit_tiers, reverse=True):
            if current_pnl_pct >= threshold:
                applicable_trailing = trailing_pct
                break
        
        return applicable_trailing
