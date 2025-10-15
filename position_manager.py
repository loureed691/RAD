"""
Position management with trailing stop loss
"""
import time
import threading
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime
from kucoin_client import KuCoinClient
from logger import Logger
from advanced_exit_strategy import AdvancedExitStrategy
from volume_profile import VolumeProfile

def format_price(price: float) -> str:
    """
    Format price with appropriate precision based on magnitude.
    
    Args:
        price: Price value to format
        
    Returns:
        Formatted price string with appropriate decimal places
    """
    if price == 0:
        return "0.00"
    
    abs_price = abs(price)
    
    # For prices >= 1000, use 2 decimals (e.g., 1213.68)
    if abs_price >= 1000:
        return f"{price:.2f}"
    # For prices >= 1, use 2 decimals (e.g., 5.33, 16.78)
    elif abs_price >= 1:
        return f"{price:.2f}"
    # For prices >= 0.1, use 2 decimals (e.g., 0.88, 0.50)
    elif abs_price >= 0.1:
        return f"{price:.2f}"
    # For prices >= 0.01, use 4 decimals (e.g., 0.0567)
    elif abs_price >= 0.01:
        return f"{price:.4f}"
    # For prices >= 0.001, use 5 decimals (e.g., 0.00567)
    elif abs_price >= 0.001:
        return f"{price:.5f}"
    # For very small prices, use 6 decimals (e.g., 0.001234)
    else:
        return f"{price:.6f}"

def format_pnl_usd(pnl_usd: float) -> str:
    """
    Format P/L USD amount with sign prefix and appropriate precision.
    
    Args:
        pnl_usd: P/L in USD
        
    Returns:
        Formatted P/L string with sign (e.g., "$+1.23", "$-0.0045")
    """
    sign = "+" if pnl_usd >= 0 else "-"
    abs_value = abs(pnl_usd)
    formatted = format_price(abs_value)
    return f"${sign}{formatted}"

class Position:
    """Represents an open trading position"""
    
    def __init__(self, symbol: str, side: str, entry_price: float, 
                 amount: float, leverage: int, stop_loss: float, 
                 take_profit: Optional[float] = None):
        self.symbol = symbol
        self.side = side  # 'long' or 'short'
        self.entry_price = entry_price
        self.amount = amount
        self.leverage = leverage
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.highest_price = entry_price if side == 'long' else None
        self.lowest_price = entry_price if side == 'short' else None
        self.entry_time = datetime.now()
        self.trailing_stop_activated = False
        
        # Track maximum favorable excursion for adaptive adjustments
        self.max_favorable_excursion = 0.0  # Peak profit %
        self.initial_stop_loss = stop_loss  # Store initial stop loss
        self.initial_take_profit = take_profit  # Store initial take profit
        
        # Track profit velocity for smarter adjustments
        self.last_pnl = 0.0  # Last recorded P/L
        self.last_pnl_time = datetime.now()  # Time of last P/L update
        self.profit_velocity = 0.0  # Rate of profit change (% per hour)
        
        # Breakeven and profit scaling
        self.breakeven_moved = False
        self.profit_acceleration = 0.0  # Rate of change of profit velocity
        self.partial_exits_taken = 0  # Track partial profit taking
        
        # Volume profile analyzer for smarter exits
        self.volume_profile_analyzer = VolumeProfile()
    
    def move_to_breakeven(self, current_price: float, buffer: float = 0.001) -> bool:
        """
        Move stop loss to breakeven (entry price) with small buffer
        
        Args:
            current_price: Current market price
            buffer: Small buffer above/below entry (default 0.1%)
        
        Returns:
            True if moved, False otherwise
        """
        if self.breakeven_moved:
            return False
        
        current_pnl = self.get_pnl(current_price)
        
        # PROFITABILITY FIX: Move to breakeven earlier at 1.5% profit (was 2%)
        if current_pnl > 0.015:  # Changed from 0.02
            if self.side == 'long':
                new_stop = self.entry_price * (1 + buffer)
                if new_stop > self.stop_loss:
                    self.stop_loss = new_stop
                    self.breakeven_moved = True
                    return True
            else:  # short
                new_stop = self.entry_price * (1 - buffer)
                if new_stop < self.stop_loss:
                    self.stop_loss = new_stop
                    self.breakeven_moved = True
                    return True
        
        return False
    
    def update_trailing_stop(self, current_price: float, trailing_percentage: float, 
                            volatility: float = 0.03, momentum: float = 0.0):
        """
        Update trailing stop loss with adaptive parameters
        
        Args:
            current_price: Current market price
            trailing_percentage: Base trailing stop percentage
            volatility: Market volatility (e.g., ATR or BB width)
            momentum: Current price momentum (-1 to 1)
        """
        # Calculate current P/L percentage
        current_pnl = self.get_pnl(current_price)
        
        # Update max favorable excursion
        if current_pnl > self.max_favorable_excursion:
            self.max_favorable_excursion = current_pnl
        
        # PROFITABILITY FIX: More aggressive trailing to lock profits
        adaptive_trailing = trailing_percentage
        
        # 1. Volatility adjustment - tighter overall for profit protection
        if volatility > 0.05:
            adaptive_trailing *= 1.3  # REDUCED from 1.5 - tighter in high volatility
        elif volatility < 0.02:
            adaptive_trailing *= 0.7  # TIGHTER from 0.8 in low volatility
        
        # 2. Profit-based adjustment - MORE AGGRESSIVE tightening
        if current_pnl > 0.10:  # >10% profit
            adaptive_trailing *= 0.5  # TIGHTER from 0.7 to lock in more profit
        elif current_pnl > 0.05:  # >5% profit
            adaptive_trailing *= 0.7  # TIGHTER from 0.85
        elif current_pnl > 0.03:  # >3% profit (NEW threshold)
            adaptive_trailing *= 0.85  # Start tightening earlier
        
        # 3. Momentum adjustment - more conservative
        if abs(momentum) > 0.03:  # Strong momentum
            adaptive_trailing *= 1.1  # REDUCED from 1.2
        elif abs(momentum) < 0.01:  # Weak momentum
            adaptive_trailing *= 0.8  # TIGHTER from 0.9 when momentum fades
        
        # Cap adaptive trailing between tighter bounds (0.4% to 4%)
        adaptive_trailing = max(0.004, min(adaptive_trailing, 0.04))  # Changed from 0.005-0.05
        
        if self.side == 'long':
            if current_price > self.highest_price:
                self.highest_price = current_price
                new_stop = current_price * (1 - adaptive_trailing)
                if new_stop > self.stop_loss:
                    self.stop_loss = new_stop
                    self.trailing_stop_activated = True
        else:  # short
            if current_price < self.lowest_price:
                self.lowest_price = current_price
                new_stop = current_price * (1 + adaptive_trailing)
                if new_stop < self.stop_loss:
                    self.stop_loss = new_stop
                    self.trailing_stop_activated = True
    
    def update_take_profit(self, current_price: float, momentum: float = 0.0, 
                          trend_strength: float = 0.5, volatility: float = 0.03,
                          rsi: float = 50.0, support_resistance: Optional[Dict] = None):
        """
        Dynamically adjust take profit based on market conditions
        
        Args:
            current_price: Current market price
            momentum: Current price momentum
            trend_strength: Strength of current trend (0-1)
            volatility: Market volatility
            rsi: RSI indicator value (0-100)
            support_resistance: Dict with support/resistance levels
        """
        if not self.take_profit:
            return
        
        # Calculate current P/L (leveraged ROI) and initial target
        # Use leveraged PNL for consistency with should_close() and profit-based logic
        current_pnl = self.get_leveraged_pnl(current_price)
        initial_distance = abs(self.initial_take_profit - self.entry_price) / self.entry_price
        
        # Update profit velocity tracking
        now = datetime.now()
        time_delta = (now - self.last_pnl_time).total_seconds() / 3600  # hours
        if time_delta > 0:
            pnl_change = current_pnl - self.last_pnl
            self.profit_velocity = pnl_change / time_delta  # % per hour
            self.last_pnl = current_pnl
            self.last_pnl_time = now
        
        # Base multiplier for extending take profit
        tp_multiplier = 1.0
        
        # 1. Strong momentum - extend take profit target (REDUCED from 1.5/1.25)
        if self.side == 'long' and momentum > 0.03:
            tp_multiplier = 1.2  # Extend 20% further (was 50%)
        elif self.side == 'short' and momentum < -0.03:
            tp_multiplier = 1.2
        elif abs(momentum) > 0.02:
            tp_multiplier = 1.1  # Moderate extension (was 25%)
        
        # 2. Trend strength - extend in strong trends (REDUCED from 1.3/1.15)
        if trend_strength > 0.7:
            tp_multiplier *= 1.15  # Strong trend bonus (was 1.3)
        elif trend_strength > 0.5:
            tp_multiplier *= 1.08  # Moderate trend bonus (was 1.15)
        
        # 3. High volatility - extend target to capture bigger moves (REDUCED from 1.2)
        if volatility > 0.05:
            tp_multiplier *= 1.1  # (was 1.2)
        
        # 4. RSI-based adjustments - tighten when overbought/oversold (reversal risk)
        if self.side == 'long' and rsi > 75:
            # Overbought - high reversal risk, be more conservative
            tp_multiplier *= 0.9
        elif self.side == 'short' and rsi < 25:
            # Oversold in short - high reversal risk
            tp_multiplier *= 0.9
        elif self.side == 'long' and rsi < 40:
            # Oversold in long - still room to run
            tp_multiplier *= 1.1
        elif self.side == 'short' and rsi > 60:
            # Overbought in short - still room to run
            tp_multiplier *= 1.1
        
        # 5. Profit velocity and acceleration (REDUCED multipliers)
        if abs(self.profit_velocity) > 0.05:  # >5% per hour - fast move
            tp_multiplier *= 1.1  # (was 1.2)
        elif abs(self.profit_velocity) < 0.01:  # <1% per hour - slow move
            tp_multiplier *= 0.96  # Slightly tighter (was 0.95)
        
        # NEW: Profit acceleration - detect if profit is accelerating (REDUCED from 1.15)
        if time_delta > 0.1:  # At least 6 minutes between updates
            old_velocity = (self.last_pnl - 0) / max(time_delta, 0.1)
            self.profit_acceleration = (self.profit_velocity - old_velocity) / time_delta
            
            # If profit is accelerating rapidly, extend TP more
            if self.profit_acceleration > 0.02:  # Rapid acceleration
                tp_multiplier *= 1.08  # (was 1.15)
                
        # 6. Time-based adjustment - be more conservative on aging positions (MORE AGGRESSIVE)
        position_age_hours = (now - self.entry_time).total_seconds() / 3600
        if position_age_hours > 48:  # > 2 days old
            tp_multiplier *= 0.80  # Tighten 20% on very old positions (was 15%)
        elif position_age_hours > 24:  # > 1 day old
            tp_multiplier *= 0.85  # Tighten 15% on old positions (was 10%)
        elif position_age_hours > 12:  # > 12 hours old - NEW
            tp_multiplier *= 0.92  # Tighten 8% on aging positions
        
        # 7. Already profitable - be more conservative with extensions (CAP EARLIER)
        if current_pnl > 0.10:  # High profit (>10%) - start capping earlier
            tp_multiplier = min(tp_multiplier, 1.03)  # Very minimal extension (was 1.1)
        elif current_pnl > 0.05:  # Moderate profit (>5%)
            tp_multiplier = min(tp_multiplier, 1.08)  # Limited extension (was 1.2)
        elif current_pnl > 0.03:  # Small profit (>3%) - NEW
            tp_multiplier = min(tp_multiplier, 1.15)  # Cap moderate extensions
        
        # Additional safeguard: never extend TP if it would move beyond current price by too much
        # This prevents the scenario where TP keeps moving away as price approaches it
        # Be very conservative when price is close to or beyond original TP
        if self.side == 'long':
            # Check how close current price is to the original TP
            if current_price > self.entry_price:
                progress_to_tp = (current_price - self.entry_price) / (self.initial_take_profit - self.entry_price) if self.initial_take_profit > self.entry_price else 0
                # If we've passed the original TP, minimal extension only (for S/R capping)
                if progress_to_tp >= 1.05:  # 5% beyond original TP
                    tp_multiplier = min(tp_multiplier, 1.01)  # Almost no extension
                elif progress_to_tp >= 1.0:  # At or just past original TP
                    tp_multiplier = min(tp_multiplier, 1.03)  # Minimal extension for S/R capping
                # If we're 90%+ of the way to original TP, very limited extension
                elif progress_to_tp >= 0.9:
                    tp_multiplier = min(tp_multiplier, 1.05)  # Very limited extension
                # If we're 80%+ of the way to original TP, limited extension
                elif progress_to_tp >= 0.8:
                    tp_multiplier = min(tp_multiplier, 1.08)  # Limited extension
                # If we're 70%+ of the way to original TP, moderate limitation
                elif progress_to_tp >= 0.7:
                    tp_multiplier = min(tp_multiplier, 1.1)  # Moderate limitation
                # If we're more than 50% of the way to original TP, some limitation
                elif progress_to_tp > 0.5:
                    tp_multiplier = min(tp_multiplier, 1.15)  # Some limitation
        else:  # short
            if current_price < self.entry_price:
                progress_to_tp = (self.entry_price - current_price) / (self.entry_price - self.initial_take_profit) if self.entry_price > self.initial_take_profit else 0
                # If we've passed the original TP, minimal extension only (for S/R capping)
                if progress_to_tp >= 1.05:  # 5% beyond original TP
                    tp_multiplier = min(tp_multiplier, 1.01)  # Almost no extension
                elif progress_to_tp >= 1.0:  # At or just past original TP
                    tp_multiplier = min(tp_multiplier, 1.03)  # Minimal extension for S/R capping
                # If we're 90%+ of the way to original TP, very limited extension
                elif progress_to_tp >= 0.9:
                    tp_multiplier = min(tp_multiplier, 1.05)  # Very limited extension
                # If we're 80%+ of the way to original TP, limited extension
                elif progress_to_tp >= 0.8:
                    tp_multiplier = min(tp_multiplier, 1.08)  # Limited extension
                # If we're 70%+ of the way to original TP, moderate limitation
                elif progress_to_tp >= 0.7:
                    tp_multiplier = min(tp_multiplier, 1.1)  # Moderate limitation
                # If we're more than 50% of the way to original TP, some limitation
                elif progress_to_tp > 0.5:
                    tp_multiplier = min(tp_multiplier, 1.15)  # Some limitation
        
        # 8. Support/Resistance awareness - adjust near key levels
        if support_resistance:
            resistance_levels = support_resistance.get('resistance', [])
            support_levels = support_resistance.get('support', [])
            
            if self.side == 'long' and resistance_levels:
                # Check if TP is near a resistance level
                nearest_resistance = None
                for level in resistance_levels:
                    level_price = level['price']
                    if level_price > current_price:
                        if nearest_resistance is None or level_price < nearest_resistance:
                            nearest_resistance = level_price
                
                # If we found a resistance level, don't extend TP beyond it
                if nearest_resistance:
                    # Set TP slightly before resistance (98% of distance to resistance)
                    max_tp = current_price + (nearest_resistance - current_price) * 0.98
                    calculated_tp = self.entry_price * (1 + initial_distance * tp_multiplier)
                    
                    # Use the more conservative target
                    if calculated_tp > max_tp:
                        if initial_distance > 0:
                            tp_multiplier = (max_tp / self.entry_price - 1) / initial_distance
            
            elif self.side == 'short' and support_levels:
                # Check if TP is near a support level
                nearest_support = None
                for level in support_levels:
                    level_price = level['price']
                    if level_price < current_price:
                        if nearest_support is None or level_price > nearest_support:
                            nearest_support = level_price
                
                # If we found a support level, don't extend TP beyond it
                if nearest_support:
                    # Set TP slightly above support (98% of distance to support)
                    max_tp = current_price - (current_price - nearest_support) * 0.98
                    calculated_tp = self.entry_price * (1 - initial_distance * tp_multiplier)
                    
                    # Use the more conservative target
                    if calculated_tp < max_tp:
                        if initial_distance > 0:
                            tp_multiplier = (1 - max_tp / self.entry_price) / initial_distance
        
        # Calculate new take profit
        new_distance = initial_distance * tp_multiplier
        
        if self.side == 'long':
            new_take_profit = self.entry_price * (1 + new_distance)
            # Only move take profit up (more favorable)
            if new_take_profit > self.take_profit:
                # Critical fix: Don't move TP further away when price is approaching it
                # For LONG: TP is above current price, so check if price is getting close
                # Edge case: if current_price == take_profit, allow extension
                if current_price == self.take_profit:
                    # At take profit exactly - allow extension if beneficial
                    self.take_profit = new_take_profit
                elif current_price < self.take_profit:
                    # Price hasn't reached TP yet
                    # Calculate how close: be very conservative to prevent TP from moving away
                    distance_to_tp = self.take_profit - current_price
                    progress_pct = (current_price - self.entry_price) / (self.take_profit - self.entry_price) if self.take_profit > self.entry_price else 0
                    
                    if progress_pct < 0.7:  # Less than 70% of way to TP - allow extension
                        self.take_profit = new_take_profit
                    else:
                        # Close to TP (70%+) - don't allow extension to prevent moving TP away
                        # This is the critical fix for "bot doesn't sell" issue
                        pass  # Keep TP at current value
                else:
                    # Price at or past TP - only allow if new TP brings it closer
                    old_distance_to_tp = abs(current_price - self.take_profit)
                    new_distance_to_tp = abs(current_price - new_take_profit)
                    if new_distance_to_tp <= old_distance_to_tp:
                        self.take_profit = new_take_profit
        else:  # short
            new_take_profit = self.entry_price * (1 - new_distance)
            # Only move take profit down (more favorable)
            if new_take_profit < self.take_profit:
                # Critical fix: Don't move TP further away when price is approaching it
                # For SHORT: TP is below current price, so check if price is getting close
                # Edge case: if current_price == take_profit, allow extension
                if current_price == self.take_profit:
                    # At take profit exactly - allow extension if beneficial
                    self.take_profit = new_take_profit
                elif current_price > self.take_profit:
                    # Price hasn't reached TP yet
                    # Calculate how close: be very conservative to prevent TP from moving away
                    distance_to_tp = current_price - self.take_profit
                    progress_pct = (self.entry_price - current_price) / (self.entry_price - self.take_profit) if self.entry_price > self.take_profit else 0
                    
                    if progress_pct < 0.7:  # Less than 70% of way to TP - allow extension
                        self.take_profit = new_take_profit
                    else:
                        # Close to TP (70%+) - don't allow extension to prevent moving TP away
                        # This is the critical fix for "bot doesn't sell" issue
                        pass  # Keep TP at current value
                else:
                    # Price at or past TP - only allow if new TP brings it closer
                    old_distance_to_tp = abs(current_price - self.take_profit)
                    new_distance_to_tp = abs(current_price - new_take_profit)
                    if new_distance_to_tp <= old_distance_to_tp:
                        self.take_profit = new_take_profit
    
    def calculate_intelligent_targets(self, current_price: float, support_resistance: Dict, 
                                     side: str) -> Tuple[float, float]:
        """
        Calculate intelligent take profit and stop loss based on S/R levels
        
        Args:
            current_price: Current market price
            support_resistance: Dict with support/resistance levels
            side: 'long' or 'short'
        
        Returns:
            Tuple of (stop_loss, take_profit)
        """
        # Default targets
        default_stop = current_price * 0.97 if side == 'long' else current_price * 1.03
        default_tp = current_price * 1.05 if side == 'long' else current_price * 0.95
        
        if not support_resistance or (not support_resistance.get('support') and 
                                      not support_resistance.get('resistance')):
            return default_stop, default_tp
        
        if side == 'long':
            # For longs: use nearest support below as stop, nearest resistance above as target
            support_levels = support_resistance.get('support', [])
            resistance_levels = support_resistance.get('resistance', [])
            
            # Find nearest support below current price
            nearest_support = None
            for level in support_levels:
                if level['price'] < current_price:
                    if nearest_support is None or level['price'] > nearest_support:
                        nearest_support = level['price']
            
            # Find nearest resistance above current price
            nearest_resistance = None
            for level in resistance_levels:
                if level['price'] > current_price:
                    if nearest_resistance is None or level['price'] < nearest_resistance:
                        nearest_resistance = level['price']
            
            # Set stop slightly below support
            stop_loss = (nearest_support * 0.995) if nearest_support else default_stop
            
            # Set take profit slightly before resistance
            take_profit = (nearest_resistance * 0.995) if nearest_resistance else default_tp
            
        else:  # short
            # For shorts: use nearest resistance above as stop, nearest support below as target
            support_levels = support_resistance.get('support', [])
            resistance_levels = support_resistance.get('resistance', [])
            
            # Find nearest resistance above current price
            nearest_resistance = None
            for level in resistance_levels:
                if level['price'] > current_price:
                    if nearest_resistance is None or level['price'] < nearest_resistance:
                        nearest_resistance = level['price']
            
            # Find nearest support below current price
            nearest_support = None
            for level in support_levels:
                if level['price'] < current_price:
                    if nearest_support is None or level['price'] > nearest_support:
                        nearest_support = level['price']
            
            # Set stop slightly above resistance
            stop_loss = (nearest_resistance * 1.005) if nearest_resistance else default_stop
            
            # Set take profit slightly above support
            take_profit = (nearest_support * 1.005) if nearest_support else default_tp
        
        return stop_loss, take_profit
    
    def adjust_take_profit_with_volume_profile(self, current_price: float, df: pd.DataFrame) -> bool:
        """
        Adjust take profit using volume profile analysis for smarter exits
        
        Args:
            current_price: Current market price
            df: DataFrame with OHLCV data for volume profile calculation
        
        Returns:
            bool: True if TP was adjusted, False otherwise
        """
        if not self.take_profit or df.empty or len(df) < 20:
            return False
        
        try:
            # Calculate volume profile
            volume_profile = self.volume_profile_analyzer.calculate_volume_profile(df, num_bins=50)
            
            if not volume_profile or volume_profile.get('poc') is None:
                return False
            
            # Get volume-based support/resistance
            vol_sr = self.volume_profile_analyzer.get_support_resistance_from_volume(
                current_price, volume_profile
            )
            
            current_pnl = self.get_pnl(current_price)
            
            # For LONG: use volume-based resistance as TP target
            if self.side == 'long' and vol_sr.get('resistance'):
                resistance_price = vol_sr['resistance']
                resistance_strength = vol_sr.get('resistance_strength', 0.5)
                
                # Only consider resistance above current price
                if resistance_price > current_price and resistance_price > self.entry_price:
                    potential_pnl = (resistance_price - self.entry_price) / self.entry_price
                    
                    # Only adjust if resistance offers good profit and is strong
                    if potential_pnl > 0.02 and resistance_strength > 0.6:
                        # If TP is way beyond strong resistance, bring it back to be more realistic
                        # Only adjust if new TP would still be above current price
                        new_tp = resistance_price * 0.98
                        if self.take_profit > resistance_price * 1.15 and new_tp > current_price:
                            self.take_profit = new_tp
                            return True
                        
                        # If we're in good profit and approaching resistance, lock it in
                        if current_pnl > 0.03:
                            distance_to_resistance = (resistance_price - current_price) / current_price
                            if distance_to_resistance < 0.02:  # Within 2% of resistance
                                new_tp = resistance_price * 0.99
                                if new_tp > current_price:
                                    self.take_profit = new_tp
                                    return True
            
            # For SHORT: use volume-based support as TP target
            elif self.side == 'short' and vol_sr.get('support'):
                support_price = vol_sr['support']
                support_strength = vol_sr.get('support_strength', 0.5)
                
                # Only consider support below current price
                if support_price < current_price and support_price < self.entry_price:
                    potential_pnl = (self.entry_price - support_price) / self.entry_price
                    
                    # Only adjust if support offers good profit and is strong
                    if potential_pnl > 0.02 and support_strength > 0.6:
                        # If TP is way beyond strong support, bring it back to be more realistic
                        # Only adjust if new TP would still be below current price
                        new_tp = support_price * 1.02
                        if self.take_profit < support_price * 0.85 and new_tp < current_price:
                            self.take_profit = new_tp
                            return True
                        
                        # If we're in good profit and approaching support, lock it in
                        if current_pnl > 0.03:
                            distance_to_support = (current_price - support_price) / current_price
                            if distance_to_support < 0.02:  # Within 2% of support
                                new_tp = support_price * 1.01
                                if new_tp < current_price:
                                    self.take_profit = new_tp
                                    return True
            
            return False
        except (KeyError, ValueError, ZeroDivisionError, TypeError, pd.errors.EmptyDataError):
            return False


    def should_close(self, current_price: float) -> tuple[bool, str]:
        """Check if position should be closed"""
        # Calculate current P/L percentage
        # CRITICAL FIX: Use leveraged P&L to check ROI-based thresholds (20% profit = 20% ROI, not 20% price movement)
        # This ensures positions close at the correct profit/loss levels the user expects
        current_pnl = self.get_leveraged_pnl(current_price)
        
        # CRITICAL SAFETY: Tiered emergency stop loss based on ROI to prevent catastrophic losses
        # These are absolute maximum loss caps that override all other logic
        # Protects against extreme scenarios where stop loss fails or leverage magnifies losses
        
        # TIGHTENED: Emergency stops adjusted based on leverage to prevent excessive losses
        # With high leverage, price moves are amplified, so we need tighter emergency stops
        
        # Level 1: Emergency stop at -40% ROI (liquidation danger zone)
        # This is reduced from -50% to prevent getting too close to liquidation
        if current_pnl <= -0.40:
            return True, 'emergency_stop_liquidation_risk'
        
        # Level 2: Critical stop at -25% ROI (severe loss)
        # Reduced from -35% - this should catch failing positions before catastrophic loss
        if current_pnl <= -0.25:
            return True, 'emergency_stop_severe_loss'
        
        # Level 3: Warning stop at -15% ROI (unacceptable loss)
        # Reduced from -20% - if regular stops fail, this catches it earlier
        # This should almost never trigger if stop losses are working correctly
        if current_pnl <= -0.15:
            return True, 'emergency_stop_excessive_loss'
        
        # Update favorable excursion tracking for smarter profit taking
        if current_pnl > self.max_favorable_excursion:
            self.max_favorable_excursion = current_pnl
        
        # Intelligent profit taking - take profits at key ROI levels when TP is far away
        # This prevents scenarios where TP gets extended too far and price retraces
        if current_pnl > 0 and self.take_profit:
            # Calculate distance to take profit
            if self.side == 'long':
                distance_to_tp = (self.take_profit - current_price) / current_price
            else:  # short
                distance_to_tp = (current_price - self.take_profit) / current_price
            
            # Exceptional profit levels - always take profit (no override)
            if current_pnl >= 0.20:  # 20% price movement
                return True, 'take_profit_20pct_exceptional'
            
            # Very high profit - take if TP is far (>2%)
            if current_pnl >= 0.15:
                if distance_to_tp > 0.02:
                    return True, 'take_profit_15pct_far_tp'
            
            # Profit velocity check - take profit if we're losing momentum
            # Check this at various profit levels to catch retracements early
            # This takes priority over flat ROI thresholds when losing significant momentum
            if self.max_favorable_excursion >= 0.10:  # Had at least 10% profit (significant)
                profit_drawdown = self.max_favorable_excursion - current_pnl
                drawdown_pct = profit_drawdown / self.max_favorable_excursion
                
                # If we've given back ~50% of peak profit and still above breakeven
                # This is checked FIRST as it's more critical than 30% drawdown
                # Use 0.499 to handle floating point precision issues
                if drawdown_pct >= 0.499 and current_pnl >= 0.01:
                    return True, 'take_profit_major_retracement'
                
                # If we've given back ~30% of peak profit and in 3-15% ROI range
                # Exit before hitting other thresholds to protect profits from further decline
                # Use 0.299 to handle floating point precision issues
                if drawdown_pct >= 0.299 and 0.03 <= current_pnl < 0.15:
                    return True, 'take_profit_momentum_loss'
            
            # 10% price movement - take profit if TP is >2% away
            if current_pnl >= 0.10:
                if distance_to_tp > 0.02:
                    return True, 'take_profit_10pct'
            
            # 8% price movement - take profit if TP is >3% away
            if current_pnl >= 0.08:
                if distance_to_tp > 0.03:
                    return True, 'take_profit_8pct'
            
            # 5% price movement - take profit if TP is >5% away
            if current_pnl >= 0.05:
                if distance_to_tp > 0.05:
                    return True, 'take_profit_5pct'
        
        # Standard stop loss and take profit checks (primary logic)
        # Enhanced stop loss with time-based awareness
        if self.side == 'long':
            # Check stop loss
            if current_price <= self.stop_loss:
                return True, 'stop_loss'
            
            # Smart stop loss: tighten stop if position has been open for a while with no progress
            time_in_trade = (datetime.now() - self.entry_time).total_seconds() / 3600  # hours
            # current_pnl is already leveraged ROI, so check against 2% ROI directly
            if time_in_trade >= 4.0 and current_pnl < 0.02:  # 4 hours with < 2% ROI
                # Calculate a tighter stop loss for stalled positions
                tighter_stop = self.entry_price * 0.99  # 1% below entry
                if current_price <= tighter_stop:
                    return True, 'stop_loss_stalled_position'
            
            # Check take profit (with small tolerance for floating point precision)
            # Tolerance of 0.00001 (0.001%) handles floating point errors without being too permissive
            if self.take_profit and current_price >= self.take_profit * 0.99999:
                return True, 'take_profit'
        else:  # short
            # Check stop loss
            if current_price >= self.stop_loss:
                return True, 'stop_loss'
            
            # Smart stop loss: tighten stop if position has been open for a while with no progress
            time_in_trade = (datetime.now() - self.entry_time).total_seconds() / 3600  # hours
            # current_pnl is already leveraged ROI, so check against 2% ROI directly
            if time_in_trade >= 4.0 and current_pnl < 0.02:  # 4 hours with < 2% ROI
                # Calculate a tighter stop loss for stalled positions
                tighter_stop = self.entry_price * 1.01  # 1% above entry
                if current_price >= tighter_stop:
                    return True, 'stop_loss_stalled_position'
            
            # Check take profit (with small tolerance for floating point precision)
            # Tolerance of 0.00001 (0.001%) handles floating point errors without being too permissive
            if self.take_profit and current_price <= self.take_profit * 1.00001:
                return True, 'take_profit'
        
        # Emergency profit protection - only trigger if TP is unreachable or position has extreme profit
        # This is a safety mechanism for when TP extension logic fails, not normal operation
        if self.take_profit and current_pnl >= 0.05:  # Only check if we have 5%+ ROI
            # Calculate how far we are from the take profit target
            if self.side == 'long':
                distance_to_tp = (self.take_profit - current_price) / current_price
                # Use small tolerance for floating point precision (0.001%)
                passed_tp = current_price >= self.take_profit * 0.99999
            else:  # short
                distance_to_tp = (current_price - self.take_profit) / current_price
                # Use small tolerance for floating point precision (0.001%)
                passed_tp = current_price <= self.take_profit * 1.00001
            
            # Only use emergency profit protection if:
            # 1. We've already passed TP (should have closed above, but just in case), OR
            # 2. We have extreme profits (>50% ROI) AND TP is far away (>10%)
            if passed_tp:
                # Already at/past TP - close immediately
                return True, 'take_profit'
            elif current_pnl >= 0.50 and distance_to_tp > 0.10:
                # Extreme profit (50%+ ROI) but TP is 10%+ away - protect profits
                return True, 'emergency_profit_protection'
        
        return False, ''
    
    def get_pnl(self, current_price: float) -> float:
        """Calculate profit/loss percentage (price movement only, without leverage)
        
        Returns the percentage change in price. This is the base price movement
        that should be multiplied by leverage to get the leveraged ROI (return on investment).
        
        Note: This returns the unleveraged price change. To calculate the actual P/L in USD,
        multiply the result by leverage to get the leveraged P/L percentage, then multiply by position_value:
            pnl_usd = get_pnl(current_price) * leverage * position_value
        """
        if self.side == 'long':
            pnl = (current_price - self.entry_price) / self.entry_price
        else:
            pnl = (self.entry_price - current_price) / self.entry_price
        return pnl
    
    def get_leveraged_pnl(self, current_price: float) -> float:
        """Calculate actual ROI including leverage effect
        
        Returns the actual return on investment considering leverage.
        For a 3x leveraged position with 1% price move, this returns 3%.
        """
        base_pnl = self.get_pnl(current_price)
        return base_pnl * self.leverage

class PositionManager:
    """Manage open positions with trailing stops and advanced exit strategies"""
    
    def __init__(self, client: KuCoinClient, trailing_stop_percentage: float = 0.02):
        self.client = client
        self.trailing_stop_percentage = trailing_stop_percentage
        self.positions: Dict[str, Position] = {}
        self.logger = Logger.get_logger()
        self.position_logger = Logger.get_position_logger()
        self.advanced_exit_strategy = AdvancedExitStrategy()
        
        # Thread lock for positions dictionary to prevent race conditions
        # Note: This is mainly for safety, as the bot is typically single-threaded
        # but protects against future multi-threaded enhancements
        self._positions_lock = threading.Lock()
    
    def sync_existing_positions(self):
        """Sync existing positions from the exchange and import them into management
        
        This allows the bot to manage positions that were opened manually or by
        a previous bot session. Existing positions will be tracked with trailing
        stops and managed intelligently.
        """
        try:
            self.logger.info("Syncing existing positions from exchange...")
            
            # Fetch open positions from exchange
            exchange_positions = self.client.get_open_positions()
            
            if not exchange_positions:
                self.logger.info("No existing positions found on exchange")
                return 0
            
            synced_count = 0
            for pos in exchange_positions:
                symbol = pos.get('symbol')
                if not symbol:
                    continue
                
                # Thread-safe check if position is already tracked
                with self._positions_lock:
                    if symbol in self.positions:
                        self.logger.debug(f"Position {symbol} already tracked, skipping sync")
                        continue
                
                # Extract position details
                contracts = float(pos.get('contracts', 0))
                if contracts == 0:
                    continue
                
                side = pos.get('side', 'long')  # 'long' or 'short'
                entry_price = float(pos.get('entryPrice', 0))
                
                # Extract leverage with multiple fallback options
                # 1. Try CCXT unified 'leverage' field
                leverage = pos.get('leverage')
                if leverage is not None:
                    try:
                        leverage = int(leverage)
                    except (ValueError, TypeError):
                        self.logger.warning(
                            f"Invalid leverage value '{leverage}' for {symbol}, defaulting to 10x. "
                            f"Position data: contracts={contracts}, side={side}"
                        )
                        leverage = 10
                else:
                    # 2. Try KuCoin-specific 'realLeverage' in raw info
                    info = pos.get('info', {})
                    real_leverage = info.get('realLeverage')
                    if real_leverage is not None:
                        try:
                            leverage = int(real_leverage)
                        except (ValueError, TypeError):
                            self.logger.warning(
                                f"Invalid realLeverage value '{real_leverage}' for {symbol}, defaulting to 10x. "
                                f"Position data: contracts={contracts}, side={side}"
                            )
                            leverage = 10
                    else:
                        # 3. Default to 10x with warning
                        leverage = 10
                        self.logger.warning(
                            f"Leverage not found for {symbol}, defaulting to 10x. "
                            f"Position data: contracts={contracts}, side={side}"
                        )
                
                # Get current price for calculating stop loss
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    self.logger.warning(f"Could not get ticker for {symbol}, skipping")
                    continue
                
                # Bug fix: Safely access 'last' price
                current_price = ticker.get('last')
                if not current_price or current_price <= 0:
                    self.logger.warning(f"Invalid price for {symbol}: {current_price}, skipping")
                    continue
                
                # Calculate intelligent stop loss based on current price
                # Use a conservative 5% stop loss for imported positions
                # Using 3x risk/reward ratio for better profitability
                stop_loss_percentage = 0.05
                if side == 'long':
                    stop_loss = current_price * (1 - stop_loss_percentage)
                    take_profit = current_price * (1 + stop_loss_percentage * 3)
                else:
                    stop_loss = current_price * (1 + stop_loss_percentage)
                    take_profit = current_price * (1 - stop_loss_percentage * 3)
                
                # Create Position object
                position = Position(
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    amount=abs(contracts),
                    leverage=leverage,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                # If position is already profitable, set highest/lowest price
                # to current price so trailing stop can activate
                if side == 'long' and current_price > entry_price:
                    position.highest_price = current_price
                elif side == 'short' and current_price < entry_price:
                    position.lowest_price = current_price
                
                # Thread-safe position addition
                with self._positions_lock:
                    self.positions[symbol] = position
                
                synced_count += 1
                
                self.logger.info(
                    f"Synced position: {symbol} {side} @ {entry_price:.2f}, "
                    f"Contracts: {abs(contracts):.4f}, Leverage: {leverage}x, "
                    f"SL: {stop_loss:.2f}, TP: {take_profit:.2f}"
                )
                
                # Calculate current P/L (use leveraged P/L for accurate ROI reporting)
                pnl = position.get_pnl(current_price)  # Base price change %
                leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
                
                self.logger.info(
                    f"Synced {side} position: {symbol} @ {format_price(entry_price)}, "
                    f"Current: {format_price(current_price)}, Amount: {abs(contracts)}, "
                    f"Leverage: {leverage}x, P/L: {leveraged_pnl:.2%}, "
                    f"Stop Loss: {format_price(stop_loss)}, Take Profit: {format_price(take_profit)}"
                )
            
            if synced_count > 0:
                self.logger.info(f"Successfully synced {synced_count} existing position(s)")
            
            return synced_count
            
        except Exception as e:
            self.logger.error(f"Error syncing existing positions: {e}", exc_info=True)
            return 0
    
    def open_position(self, symbol: str, signal: str, amount: float, 
                     leverage: int, stop_loss_percentage: float = 0.05,
                     use_limit: bool = False, limit_offset: float = 0.001) -> bool:
        """Open a new position with optional limit order
        
        Args:
            symbol: Trading pair symbol
            signal: 'BUY' or 'SELL'
            amount: Position size in contracts
            leverage: Leverage to use
            stop_loss_percentage: Stop loss distance as percentage
            use_limit: If True, uses limit order instead of market order
            limit_offset: Price offset for limit orders (default 0.1%)
        
        Returns:
            True if position opened successfully, False otherwise
        """
        try:
            # Validate position parameters
            is_valid, error_msg = self.validate_position_parameters(
                symbol, amount, leverage, stop_loss_percentage
            )
            if not is_valid:
                self.logger.error(f"Invalid position parameters: {error_msg}")
                self.position_logger.error(f"  ✗ Invalid parameters: {error_msg}")
                return False
            
            # Log position opening attempt
            self.position_logger.info(f"=" * 80)
            self.position_logger.info(f"OPENING POSITION: {symbol}")
            self.position_logger.info(f"  Signal: {signal} ({'LONG' if signal == 'BUY' else 'SHORT'})")
            self.position_logger.info(f"  Amount: {amount:.4f} contracts")
            self.position_logger.info(f"  Leverage: {leverage}x")
            self.position_logger.info(f"  Stop Loss %: {stop_loss_percentage:.2%}")
            self.position_logger.info(f"  Order Type: {'LIMIT' if use_limit else 'MARKET'}")
            
            # Get current price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                self.position_logger.error(f"  Failed to get ticker for {symbol}")
                return False
            
            # Bug fix: Safely access 'last' price
            current_price = ticker.get('last')
            if not current_price or current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}: {current_price}")
                self.position_logger.error(f"  Invalid price: {current_price}")
                return False
            
            self.position_logger.info(f"  Current Price: {format_price(current_price)}")
            
            side = 'buy' if signal == 'BUY' else 'sell'
            
            # Create order (market or limit)
            if use_limit:
                # Place limit order slightly better than market price
                if side == 'buy':
                    limit_price = current_price * (1 - limit_offset)
                else:
                    limit_price = current_price * (1 + limit_offset)
                
                self.position_logger.info(f"  Placing LIMIT order at {format_price(limit_price)} (offset: {limit_offset:.2%})")
                
                order = self.client.create_limit_order(
                    symbol, side, amount, limit_price, leverage, post_only=True
                )
                
                if not order:
                    self.logger.warning(f"Limit order failed, falling back to market order")
                    self.position_logger.warning(f"  Limit order failed, using MARKET order")
                    order = self.client.create_market_order(symbol, side, amount, leverage)
                elif 'id' in order:
                    # Bug fix: Check order has 'id' key before accessing
                    # Wait briefly for fill, cancel if not filled
                    self.position_logger.info(f"  Limit order placed, waiting for fill (Order ID: {order['id']})")
                    order_status = self.client.wait_for_order_fill(
                        order['id'], symbol, timeout=10, check_interval=2
                    )
                    
                    if not order_status or order_status.get('status') != 'closed':
                        # Bug fix: Use .get() for status access
                        # Not filled, cancel and use market order
                        self.client.cancel_order(order['id'], symbol)
                        self.logger.info(f"Limit order not filled, using market order instead")
                        self.position_logger.warning(f"  Limit order not filled, cancelled and using MARKET order")
                        order = self.client.create_market_order(symbol, side, amount, leverage)
                    else:
                        self.position_logger.info(f"  Limit order filled successfully")
                else:
                    self.logger.warning(f"Limit order missing 'id', falling back to market order")
                    self.position_logger.warning(f"  Limit order missing 'id', using MARKET order")
                    order = self.client.create_market_order(symbol, side, amount, leverage)
            else:
                self.position_logger.info(f"  Placing MARKET order")
                order = self.client.create_market_order(symbol, side, amount, leverage)
            
            if not order:
                self.position_logger.error(f"  Order creation failed")
                return False
            
            # Get actual fill price
            fill_price = order.get('average') or current_price
            self.position_logger.info(f"  Order filled at: {format_price(fill_price)}")
            
            # Calculate stop loss and take profit
            # Using 3x risk/reward ratio for better profitability (was 2x)
            if signal == 'BUY':
                stop_loss = fill_price * (1 - stop_loss_percentage)
                take_profit = fill_price * (1 + stop_loss_percentage * 3)
            else:
                stop_loss = fill_price * (1 + stop_loss_percentage)
                take_profit = fill_price * (1 - stop_loss_percentage * 3)
            
            stop_loss_pct = (1 - stop_loss/fill_price) if signal == 'SELL' else (stop_loss/fill_price - 1)
            take_profit_pct = (1 - take_profit/fill_price) if signal == 'SELL' else (take_profit/fill_price - 1)
            self.position_logger.info(f"  Stop Loss: {format_price(stop_loss)} ({stop_loss_pct:.2%})")
            self.position_logger.info(f"  Take Profit: {format_price(take_profit)} ({take_profit_pct:.2%})")
            
            # Log stop loss and take profit placement to orders logger
            from logger import Logger
            orders_logger = Logger.get_orders_logger()
            orders_logger.info("=" * 80)
            orders_logger.info(f"STOP LOSS & TAKE PROFIT SET: {symbol}")
            orders_logger.info("-" * 80)
            orders_logger.info(f"  Symbol: {symbol}")
            orders_logger.info(f"  Position Side: {signal} ({'LONG' if signal == 'BUY' else 'SHORT'})")
            orders_logger.info(f"  Entry Price: {format_price(fill_price)}")
            orders_logger.info(f"  Amount: {amount} contracts")
            orders_logger.info(f"  Leverage: {leverage}x")
            orders_logger.info("")
            orders_logger.info(f"  Stop Loss Price: {format_price(stop_loss)}")
            orders_logger.info(f"  Stop Loss %: {abs(stop_loss_pct):.2%} from entry")
            orders_logger.info(f"  Stop Loss Type: Monitored (closes position when price reaches SL)")
            orders_logger.info("")
            orders_logger.info(f"  Take Profit Price: {format_price(take_profit)}")
            orders_logger.info(f"  Take Profit %: {abs(take_profit_pct):.2%} from entry")
            orders_logger.info(f"  Take Profit Type: Monitored (closes position when price reaches TP)")
            orders_logger.info("")
            if abs(stop_loss_pct) < 1e-8:
                orders_logger.info("  Risk/Reward Ratio: N/A (stop loss percent is zero)")
            else:
                orders_logger.info(f"  Risk/Reward Ratio: 1:{abs(take_profit_pct / stop_loss_pct):.2f}")
            orders_logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            orders_logger.info("=" * 80)
            orders_logger.info("")
            
            # Create position object
            position = Position(
                symbol=symbol,
                side='long' if signal == 'BUY' else 'short',
                entry_price=fill_price,
                amount=amount,
                leverage=leverage,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Thread-safe position addition
            with self._positions_lock:
                self.positions[symbol] = position
            
            position_value = amount * fill_price
            self.position_logger.info(f"  Position Value: ${format_price(position_value)}")
            self.position_logger.info(f"  Leveraged Exposure: ${format_price(position_value * leverage)}")
            self.position_logger.info(f"✓ Position opened successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.position_logger.info(f"=" * 80)
            
            self.logger.info(
                f"Opened {position.side} position: {symbol} @ {format_price(fill_price)}, "
                f"Amount: {amount}, Leverage: {leverage}x, "
                f"Stop Loss: {format_price(stop_loss)}, Take Profit: {format_price(take_profit)}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            self.position_logger.error(f"✗ FAILED to open position: {e}")
            self.position_logger.info(f"=" * 80)
            return False
    
    def close_position(self, symbol: str, reason: str = 'manual') -> Optional[float]:
        """Close a position and return P/L"""
        try:
            # Thread-safe position check and retrieval
            with self._positions_lock:
                if symbol not in self.positions:
                    return None
                position = self.positions[symbol]
            
            self.position_logger.info(f"\n{'='*80}")
            self.position_logger.info(f"CLOSING POSITION: {symbol}")
            self.position_logger.info(f"  Reason: {reason}")
            self.position_logger.info(f"  Side: {position.side.upper()}")
            self.position_logger.info(f"  Entry Price: {format_price(position.entry_price)}")
            self.position_logger.info(f"  Entry Time: {position.entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get current price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                self.position_logger.error(f"  ✗ Failed to get ticker")
                return None
            
            # Bug fix: Safely access 'last' price
            current_price = ticker.get('last')
            if not current_price or current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}: {current_price}")
                self.position_logger.error(f"  ✗ Invalid price: {current_price}")
                return None
            
            self.position_logger.info(f"  Exit Price: {format_price(current_price)}")
            
            # Calculate P/L (with leverage for accurate ROI)
            pnl = position.get_pnl(current_price)  # Base price change %
            leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
            position_value = position.amount * position.entry_price
            pnl_usd = pnl * position_value * position.leverage  # USD P/L with leverage
            
            # Calculate duration
            duration = datetime.now() - position.entry_time
            duration_mins = duration.total_seconds() / 60
            
            self.position_logger.info(f"  P/L: {leveraged_pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
            self.position_logger.info(f"  Duration: {duration_mins:.1f} minutes")
            self.position_logger.info(f"  Max Favorable Excursion: {position.max_favorable_excursion:.2%}")
            
            # Close position on exchange
            self.position_logger.info(f"  Closing position on exchange...")
            success = self.client.close_position(symbol)
            if not success:
                self.position_logger.error(f"  ✗ Failed to close position on exchange")
                return None
            
            self.position_logger.info(f"  ✓ Position closed on exchange")
            
            # Log SL/TP trigger to orders logger if applicable
            if reason in ['stop_loss', 'take_profit']:
                from logger import Logger
                orders_logger = Logger.get_orders_logger()
                orders_logger.info("=" * 80)
                orders_logger.info(f"{'STOP LOSS' if reason == 'stop_loss' else 'TAKE PROFIT'} TRIGGERED: {symbol}")
                orders_logger.info("-" * 80)
                orders_logger.info(f"  Symbol: {symbol}")
                orders_logger.info(f"  Position Side: {position.side.upper()}")
                orders_logger.info(f"  Entry Price: {format_price(position.entry_price)}")
                orders_logger.info(f"  Exit Price: {format_price(current_price)}")
                orders_logger.info(f"  Amount: {position.amount} contracts")
                orders_logger.info(f"  Leverage: {position.leverage}x")
                if reason == 'stop_loss':
                    orders_logger.info(f"  Stop Loss Price: {format_price(position.stop_loss)}")
                    orders_logger.info(f"  Trigger: Price {'fell below' if position.side == 'long' else 'rose above'} stop loss")
                else:
                    orders_logger.info(f"  Take Profit Price: {format_price(position.take_profit)}")
                    orders_logger.info(f"  Trigger: Price {'rose above' if position.side == 'long' else 'fell below'} take profit")
                orders_logger.info(f"  P/L: {leveraged_pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
                orders_logger.info(f"  Duration: {duration_mins:.1f} minutes")
                orders_logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                orders_logger.info("=" * 80)
                orders_logger.info("")
            
            self.logger.info(
                f"Closed {position.side} position: {symbol} @ {format_price(current_price)}, "
                f"Entry: {format_price(position.entry_price)}, P/L: {leveraged_pnl:.2%}, Reason: {reason}"
            )
            
            self.position_logger.info(f"✓ Position closed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.position_logger.info(f"{'='*80}\n")
            
            # Thread-safe position removal
            with self._positions_lock:
                del self.positions[symbol]
            
            # CRITICAL FIX: Return leveraged P/L for accurate ROI tracking
            # The bot.py analytics and risk_manager expect ROI (return on investment),
            # not just price movement. With 5x leverage, a 2% price move = 10% ROI.
            return leveraged_pnl
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            self.position_logger.error(f"✗ FAILED to close position: {e}")
            self.position_logger.info(f"{'='*80}\n")
            return None
    
    def update_positions(self):
        """Update all positions and manage trailing stops with adaptive parameters"""
        # Get a thread-safe snapshot of positions to iterate over
        with self._positions_lock:
            positions_snapshot = list(self.positions.keys())
            position_count = len(self.positions)
        
        if position_count > 0:
            self.position_logger.info(f"\n{'='*80}")
            self.position_logger.info(f"UPDATING {position_count} OPEN POSITION(S) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.position_logger.info(f"{'='*80}")
        
        for symbol in positions_snapshot:
            try:
                # Thread-safe access to position
                with self._positions_lock:
                    if symbol not in self.positions:
                        # Position was closed by another thread
                        continue
                    position = self.positions[symbol]
                
                self.position_logger.info(f"\n--- Position: {symbol} ({position.side.upper()}) ---")
                self.position_logger.debug(f"  Entry Price: {format_price(position.entry_price)}")
                self.position_logger.debug(f"  Amount: {position.amount:.4f} contracts")
                self.position_logger.debug(f"  Leverage: {position.leverage}x")
                self.position_logger.debug(f"  Entry Time: {position.entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Get current price with retry logic - NEVER skip position monitoring
                current_price = None
                ticker = None
                
                # Try to get ticker with retries (max 3 attempts)
                for attempt in range(3):
                    try:
                        ticker = self.client.get_ticker(symbol)
                        if ticker:
                            current_price = ticker.get('last')
                            if current_price and current_price > 0:
                                break  # Got valid price, exit retry loop
                            else:
                                self.position_logger.debug(f"  Attempt {attempt + 1}: Invalid price in ticker: {current_price}")
                        else:
                            self.position_logger.debug(f"  Attempt {attempt + 1}: API returned None")
                    except Exception as e:
                        self.position_logger.debug(f"  Attempt {attempt + 1}: API error: {type(e).__name__}")
                    
                    # Wait before retry (exponential backoff: 0.5s, 1s, 2s)
                    if attempt < 2:  # Don't wait after last attempt
                        time.sleep(0.5 * (2 ** attempt))
                
                # CRITICAL FIX: If all retries failed, skip this update cycle
                # Using entry_price as fallback is DANGEROUS because it prevents stop losses from triggering
                # Better to skip one cycle and retry on next iteration than to use stale data
                if not current_price or current_price <= 0:
                    self.logger.warning(f"All ticker retries failed for {symbol}, skipping position update this cycle")
                    self.position_logger.warning(f"  ⚠ API failed to fetch price - SKIPPING update to avoid using stale data")
                    self.position_logger.warning(f"  ⚠ Stop loss protection: Will retry on next cycle")
                    continue  # Skip this position and try again next cycle
                
                self.position_logger.info(f"  Current Price: {format_price(current_price)}")
                
                # Calculate current P/L (with leverage for accurate ROI)
                current_pnl = position.get_pnl(current_price)  # Base price change %
                leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
                position_value = position.amount * position.entry_price
                pnl_usd = current_pnl * position_value * position.leverage  # USD P/L with leverage
                
                self.position_logger.info(f"  Current P/L: {leveraged_pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
                self.position_logger.debug(f"  Stop Loss: {format_price(position.stop_loss)}")
                self.position_logger.debug(f"  Take Profit: {format_price(position.take_profit)}")
                self.position_logger.debug(f"  Max Favorable Excursion: {position.max_favorable_excursion:.2%}")
                
                # Get market data for adaptive parameters with better error handling
                try:
                    ohlcv = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
                except Exception as e:
                    self.logger.warning(f"API error getting OHLCV for {symbol}: {type(e).__name__}: {e}")
                    self.position_logger.debug(f"  Using simple trailing stop (OHLCV API error: {type(e).__name__})")
                    # Fallback to simple update
                    position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                    # Check if position should be closed
                    should_close, reason = position.should_close(current_price)
                    if should_close:
                        self.position_logger.info(f"  ✓ Closing position: {reason}")
                        pnl = self.close_position(symbol, reason)
                        if pnl is not None:
                            yield symbol, pnl, position
                    else:
                        self.position_logger.info(f"  ✓ Position still open and healthy")
                    continue
                
                if ohlcv and len(ohlcv) >= 50:
                    from indicators import Indicators
                    df = Indicators.calculate_all(ohlcv)
                    if not df.empty:
                        indicators = Indicators.get_latest_indicators(df)
                        
                        # Extract adaptive parameters
                        volatility = indicators.get('bb_width', 0.03)
                        momentum = indicators.get('momentum', 0.0)
                        rsi = indicators.get('rsi', 50.0)
                        
                        self.position_logger.debug(f"  Market Indicators:")
                        self.position_logger.debug(f"    Volatility (BB Width): {volatility:.4f}")
                        self.position_logger.debug(f"    Momentum: {momentum:+.4f}")
                        self.position_logger.debug(f"    RSI: {rsi:.2f}")
                        
                        # Calculate support/resistance levels
                        support_resistance = Indicators.calculate_support_resistance(df)
                        
                        # Calculate trend strength from moving averages
                        close = indicators.get('close', current_price)
                        sma_20 = indicators.get('sma_20', close)
                        sma_50 = indicators.get('sma_50', close)
                        
                        # Trend strength: 0 (no trend) to 1 (strong trend)
                        # Check for valid sma_50 (not NaN, not zero)
                        if sma_50 > 0 and not pd.isna(sma_50) and not pd.isna(sma_20):
                            trend_strength = abs(sma_20 - sma_50) / sma_50
                            trend_strength = min(trend_strength * 10, 1.0)  # Scale to 0-1
                        else:
                            trend_strength = 0.5
                        
                        self.position_logger.debug(f"    Trend Strength: {trend_strength:.2f}")
                        
                        # Update trailing stop with adaptive parameters
                        old_stop = position.stop_loss
                        position.update_trailing_stop(
                            current_price, 
                            self.trailing_stop_percentage,
                            volatility=volatility,
                            momentum=momentum
                        )
                        
                        if position.stop_loss != old_stop:
                            self.position_logger.info(f"  🔄 Trailing stop updated: {old_stop:.2f} -> {position.stop_loss:.2f}")
                        
                        # Update take profit dynamically with all parameters
                        old_tp = position.take_profit
                        position.update_take_profit(
                            current_price,
                            momentum=momentum,
                            trend_strength=trend_strength,
                            volatility=volatility,
                            rsi=rsi,
                            support_resistance=support_resistance
                        )
                        
                        if position.take_profit != old_tp:
                            self.position_logger.info(f"  🎯 Take profit adjusted: {old_tp:.2f} -> {position.take_profit:.2f}")
                    else:
                        # Fallback to simple update if indicators fail
                        self.position_logger.debug(f"  Using simple trailing stop (indicators failed)")
                        position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                else:
                    # Fallback to simple update if no market data
                    self.position_logger.debug(f"  Using simple trailing stop (no market data)")
                    position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                
                # Check if position should be closed
                # First check advanced exit strategies
                current_pnl = position.get_pnl(current_price)  # Base price change %
                leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
                
                # Prepare data for advanced exit strategy
                position_data = {
                    'side': position.side,
                    'entry_price': position.entry_price,
                    'current_price': current_price,
                    'current_pnl_pct': leveraged_pnl,  # Leveraged P&L (ROI)
                    'peak_pnl_pct': position.max_favorable_excursion,
                    'leverage': position.leverage,
                    'entry_time': position.entry_time,
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit
                }
                
                market_data = {
                    'volatility': locals().get('volatility', 0.03),
                    'momentum': locals().get('momentum', 0.0),
                    'rsi': locals().get('rsi', 50.0),
                    'trend_strength': locals().get('trend_strength', 0.5)
                }
                
                # Check comprehensive exit signal (includes breakeven+, momentum reversal, profit lock, etc.)
                should_exit_advanced, exit_reason, suggested_action = self.advanced_exit_strategy.get_comprehensive_exit_signal(
                    position_data, market_data
                )
                
                if should_exit_advanced:
                    self.position_logger.info(f"  🚨 Advanced exit signal: {exit_reason}")
                
                # Handle the suggested_action based on context:
                # - If should_exit_advanced is True: suggested_action is scale percentage (1.0 for full)
                # - If should_exit_advanced is False and suggested_action is not None: it's a new stop loss price
                
                # Update stop loss if breakeven+ suggests a new level (not exiting)
                if not should_exit_advanced and suggested_action is not None and isinstance(suggested_action, (int, float)):
                    # Check if it's a stop loss price (typically close to entry price)
                    # vs a scale percentage (0 < x <= 1.0)
                    if 0 < suggested_action <= 1.0:
                        # This is a partial exit scale percentage
                        scale_pct = suggested_action
                        amount_to_close = position.amount * scale_pct
                        self.position_logger.info(f"  📊 Partial exit signal: {exit_reason} ({scale_pct*100:.0f}%)")
                        leveraged_pnl_result = self.scale_out_position(symbol, amount_to_close, exit_reason)
                        if leveraged_pnl_result is not None:
                            # Note: Don't yield here for partial exits, position still exists
                            self.logger.info(
                                f"Partial exit: {symbol}, closed {scale_pct*100:.0f}%, "
                                f"P/L: {leveraged_pnl_result:.2%}, Reason: {exit_reason}"
                            )
                    else:
                        # This is a new stop loss price
                        if suggested_action != position.stop_loss:
                            old_stop = position.stop_loss
                            position.stop_loss = suggested_action
                            self.logger.info(f"🔒 Updated {symbol} stop loss: {old_stop:.2f} -> {suggested_action:.2f} ({exit_reason})")
                            self.position_logger.info(f"  🔒 Stop loss adjusted: {old_stop:.2f} -> {suggested_action:.2f} ({exit_reason})")
                
                # If advanced strategy says exit (full exit), do it
                if should_exit_advanced:
                    self.position_logger.info(f"  ✓ Closing position: {exit_reason}")
                    pnl = self.close_position(symbol, exit_reason)
                    if pnl is not None:
                        yield symbol, pnl, position
                    continue
                
                # Check standard stop loss and take profit conditions
                should_close, reason = position.should_close(current_price)
                if should_close:
                    self.position_logger.info(f"  ✓ Closing position: {reason}")
                    pnl = self.close_position(symbol, reason)
                    if pnl is not None:
                        yield symbol, pnl, position
                else:
                    self.position_logger.info(f"  ✓ Position still open and healthy")
                
            except Exception as e:
                # Improved error context - log exception type and traceback
                self.logger.error(f"Error updating position {symbol}: {type(e).__name__}: {e}", exc_info=True)
                self.position_logger.error(f"  ✗ Error updating position: {type(e).__name__}: {e}")
                # Try simple update as fallback
                try:
                    # If we have current_price, attempt basic update
                    if 'current_price' in locals():
                        position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                        self.position_logger.info(f"  ✓ Fallback: Applied simple trailing stop update")
                except Exception as fallback_error:
                    # Log the fallback error rather than silently ignoring it
                    self.logger.error(f"Fallback update also failed for {symbol}: {type(fallback_error).__name__}: {fallback_error}")
                    self.position_logger.error(f"  ✗ Fallback update failed: {type(fallback_error).__name__}")
        
        # Thread-safe check for remaining positions
        with self._positions_lock:
            remaining_positions = len(self.positions)
        
        if remaining_positions > 0:
            self.position_logger.info(f"{'='*80}\n")
    
    def get_open_positions_count(self) -> int:
        """Get number of open positions (thread-safe)"""
        with self._positions_lock:
            return len(self.positions)
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a copy of position data for a symbol (thread-safe)
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Position object if found, None otherwise
        """
        with self._positions_lock:
            if symbol in self.positions:
                # Return a reference to the position
                # Note: The caller should not modify this directly
                return self.positions[symbol]
            return None
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get a snapshot of all positions (thread-safe)
        
        Returns:
            Dictionary of symbol -> Position
        """
        with self._positions_lock:
            # Return a shallow copy of the positions dict
            return dict(self.positions)
    
    def validate_position_parameters(self, symbol: str, amount: float, 
                                    leverage: int, stop_loss_percentage: float) -> tuple[bool, str]:
        """Validate position parameters before opening
        
        Args:
            symbol: Trading pair symbol
            amount: Position size in contracts
            leverage: Leverage to use
            stop_loss_percentage: Stop loss distance as percentage
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate amount
        if amount <= 0:
            return False, f"Invalid amount: {amount} (must be positive)"
        
        # Validate leverage
        if leverage < 1 or leverage > 125:
            return False, f"Invalid leverage: {leverage}x (must be between 1 and 125)"
        
        # Validate stop loss percentage
        if stop_loss_percentage <= 0 or stop_loss_percentage >= 1:
            return False, f"Invalid stop loss percentage: {stop_loss_percentage} (must be between 0 and 1)"
        
        # Check if position already exists
        with self._positions_lock:
            if symbol in self.positions:
                return False, f"Position for {symbol} already exists"
        
        return True, "Valid parameters"
    
    def reconcile_positions(self) -> int:
        """Reconcile tracked positions with exchange positions
        
        This method checks for discrepancies between locally tracked positions
        and positions on the exchange, helping recover from errors or crashes.
        
        Returns:
            Number of discrepancies found and reconciled
        """
        try:
            self.logger.info("Starting position reconciliation with exchange...")
            
            # Get positions from exchange
            exchange_positions = self.client.get_open_positions()
            exchange_symbols = {pos.get('symbol') for pos in exchange_positions if pos.get('symbol')}
            
            # Get locally tracked positions
            with self._positions_lock:
                local_symbols = set(self.positions.keys())
            
            # Find discrepancies
            only_on_exchange = exchange_symbols - local_symbols
            only_local = local_symbols - exchange_symbols
            
            discrepancies = 0
            
            # Handle positions only on exchange (not tracked locally)
            if only_on_exchange:
                self.logger.warning(
                    f"Found {len(only_on_exchange)} positions on exchange not tracked locally: {only_on_exchange}"
                )
                # Sync these positions
                for symbol in only_on_exchange:
                    try:
                        # Find the position details
                        for pos in exchange_positions:
                            if pos.get('symbol') == symbol:
                                contracts = float(pos.get('contracts', 0))
                                if contracts == 0:
                                    continue
                                
                                side = pos.get('side', 'long')
                                entry_price = float(pos.get('entryPrice', 0))
                                
                                # Get leverage
                                leverage = pos.get('leverage', 10)
                                if leverage is None:
                                    leverage = 10
                                else:
                                    try:
                                        leverage = int(leverage)
                                    except (ValueError, TypeError):
                                        leverage = 10
                                
                                # Get current price for stop loss calculation
                                ticker = self.client.get_ticker(symbol)
                                if not ticker:
                                    continue
                                
                                current_price = ticker.get('last')
                                if not current_price or current_price <= 0:
                                    continue
                                
                                # Calculate stop loss and take profit
                                # Using 3x risk/reward ratio for better profitability
                                stop_loss_pct = 0.05
                                if side == 'long':
                                    stop_loss = current_price * (1 - stop_loss_pct)
                                    take_profit = current_price * (1 + stop_loss_pct * 3)
                                else:
                                    stop_loss = current_price * (1 + stop_loss_pct)
                                    take_profit = current_price * (1 - stop_loss_pct * 3)
                                
                                # Create position object
                                position = Position(
                                    symbol=symbol,
                                    side=side,
                                    entry_price=entry_price,
                                    amount=abs(contracts),
                                    leverage=leverage,
                                    stop_loss=stop_loss,
                                    take_profit=take_profit
                                )
                                
                                # Add to tracked positions
                                with self._positions_lock:
                                    self.positions[symbol] = position
                                
                                self.logger.info(
                                    f"Reconciled position: {symbol} {side} @ {entry_price:.2f}, "
                                    f"Contracts: {abs(contracts):.4f}, Leverage: {leverage}x"
                                )
                                discrepancies += 1
                                break
                    except Exception as e:
                        self.logger.error(f"Error reconciling position {symbol}: {e}")
            
            # Handle positions only tracked locally (not on exchange)
            if only_local:
                self.logger.warning(
                    f"Found {len(only_local)} positions tracked locally but not on exchange: {only_local}"
                )
                # These might have been closed externally, remove from tracking
                with self._positions_lock:
                    for symbol in only_local:
                        if symbol in self.positions:
                            self.logger.warning(f"Removing orphaned position: {symbol}")
                            del self.positions[symbol]
                            discrepancies += 1
            
            if discrepancies == 0:
                self.logger.info("Position reconciliation complete: all positions in sync")
            else:
                self.logger.info(
                    f"Position reconciliation complete: {discrepancies} discrepancies resolved"
                )
            
            return discrepancies
            
        except Exception as e:
            self.logger.error(f"Error during position reconciliation: {e}", exc_info=True)
            return 0
    
    def safe_update_position_targets(self, symbol: str, new_stop_loss: Optional[float] = None,
                                    new_take_profit: Optional[float] = None,
                                    reason: str = 'manual') -> bool:
        """Safely update position targets with validation and logging
        
        Args:
            symbol: Trading pair symbol
            new_stop_loss: New stop loss price (optional)
            new_take_profit: New take profit price (optional)
            reason: Reason for the update
        
        Returns:
            True if successful, False otherwise
        """
        with self._positions_lock:
            if symbol not in self.positions:
                self.logger.error(f"Cannot update targets: position {symbol} not found")
                return False
            
            position = self.positions[symbol]
            
            try:
                # Validate new stop loss
                if new_stop_loss is not None:
                    # For long positions, stop loss should be below entry
                    # For short positions, stop loss should be above entry
                    if position.side == 'long' and new_stop_loss >= position.entry_price:
                        self.logger.warning(
                            f"Invalid stop loss for long position {symbol}: "
                            f"{new_stop_loss} >= entry {position.entry_price}"
                        )
                        return False
                    elif position.side == 'short' and new_stop_loss <= position.entry_price:
                        self.logger.warning(
                            f"Invalid stop loss for short position {symbol}: "
                            f"{new_stop_loss} <= entry {position.entry_price}"
                        )
                        return False
                
                # Validate new take profit
                if new_take_profit is not None:
                    # For long positions, take profit should be above entry
                    # For short positions, take profit should be below entry
                    if position.side == 'long' and new_take_profit <= position.entry_price:
                        self.logger.warning(
                            f"Invalid take profit for long position {symbol}: "
                            f"{new_take_profit} <= entry {position.entry_price}"
                        )
                        return False
                    elif position.side == 'short' and new_take_profit >= position.entry_price:
                        self.logger.warning(
                            f"Invalid take profit for short position {symbol}: "
                            f"{new_take_profit} >= entry {position.entry_price}"
                        )
                        return False
                
                # Apply updates
                if new_stop_loss is not None:
                    old_sl = position.stop_loss
                    position.stop_loss = new_stop_loss
                    self.logger.info(
                        f"Updated stop loss for {symbol}: {format_price(old_sl)} -> "
                        f"{format_price(new_stop_loss)} (reason: {reason})"
                    )
                
                if new_take_profit is not None:
                    old_tp = position.take_profit
                    position.take_profit = new_take_profit
                    self.logger.info(
                        f"Updated take profit for {symbol}: {format_price(old_tp)} -> "
                        f"{format_price(new_take_profit)} (reason: {reason})"
                    )
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating position targets for {symbol}: {e}")
                return False
    
    def has_position(self, symbol: str) -> bool:
        """Check if a position is open for a symbol (thread-safe)"""
        with self._positions_lock:
            return symbol in self.positions
    
    def scale_in_position(self, symbol: str, additional_amount: float, 
                         current_price: float) -> bool:
        """Add to an existing position (scale in)
        
        Args:
            symbol: Trading pair symbol
            additional_amount: Additional contracts to add
            current_price: Current market price for updating average entry
        
        Returns:
            True if successful, False otherwise
        """
        # Thread-safe position check
        with self._positions_lock:
            if symbol not in self.positions:
                self.logger.error(f"No position found for {symbol} to scale into")
                return False
            position = self.positions[symbol]
            
        try:
            # Execute the additional order
            side = 'buy' if position.side == 'long' else 'sell'
            order = self.client.create_market_order(
                symbol, side, additional_amount, position.leverage
            )
            
            if not order:
                return False
            
            # Thread-safe position update
            with self._positions_lock:
                # Re-check position still exists
                if symbol not in self.positions:
                    self.logger.warning(f"Position {symbol} was closed during scale-in")
                    return False
                
                # Update position with new average entry price
                total_old = position.amount * position.entry_price
                total_new = additional_amount * current_price
                total_amount = position.amount + additional_amount
                
                position.entry_price = (total_old + total_new) / total_amount
                position.amount = total_amount
            
            self.logger.info(
                f"Scaled into {symbol}: added {additional_amount} contracts, "
                f"new avg entry: {format_price(position.entry_price)}, total: {total_amount}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error scaling into position {symbol}: {e}")
            return False
    
    def scale_out_position(self, symbol: str, amount_to_close: float, 
                          reason: str = 'scale_out') -> Optional[float]:
        """Reduce position size (scale out / partial close)
        
        Args:
            symbol: Trading pair symbol
            amount_to_close: Contracts to close (partial)
            reason: Reason for scaling out
        
        Returns:
            P/L percentage for the closed portion, or None if failed
        """
        # Thread-safe position check
        with self._positions_lock:
            if symbol not in self.positions:
                self.logger.error(f"No position found for {symbol} to scale out of")
                return None
            position = self.positions[symbol]
            
            # Check if we're closing the entire position
            # Need to check outside the lock to avoid deadlock since close_position acquires the lock
            closing_entire_position = amount_to_close >= position.amount
        
        # If closing entire position, use close_position method
        if closing_entire_position:
            return self.close_position(symbol, reason)
        
        # Check minimum order size before attempting to scale out
        limits = self.client.get_market_limits(symbol)
        if limits:
            min_amount = limits['amount']['min']
            if min_amount and amount_to_close < min_amount:
                # Adjust order size to meet minimum instead of skipping
                original_amount = amount_to_close
                amount_to_close = min_amount
                
                # Check if adjusted amount exceeds position size (thread-safe check)
                with self._positions_lock:
                    if symbol not in self.positions:
                        self.logger.error(f"No position found for {symbol} to scale out of")
                        return None
                    position = self.positions[symbol]
                    should_close_entire = amount_to_close >= position.amount
                
                # If adjusted amount would close entire position, use close_position instead
                # (must be outside lock to avoid deadlock)
                if should_close_entire:
                    self.logger.info(
                        f"Adjusted scale-out amount {amount_to_close:.4f} would close entire position "
                        f"for {symbol} (position size: {position.amount:.4f}). Closing full position."
                    )
                    return self.close_position(symbol, reason)
                
                self.logger.warning(
                    f"Scale-out amount {original_amount:.4f} below minimum {min_amount} for {symbol}. "
                    f"Adjusting to minimum {amount_to_close:.4f}. Reason: {reason}"
                )
        
        try:
            # Get current price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return None
            
            # Bug fix: Safely access 'last' price
            current_price = ticker.get('last')
            if not current_price or current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}: {current_price}")
                return None
            
            # Close partial position with correct leverage (mark as critical)
            side = 'sell' if position.side == 'long' else 'buy'
            order = self.client.create_market_order(
                symbol, side, amount_to_close, position.leverage, 
                reduce_only=True, is_critical=True
            )
            
            if not order:
                return None
            
            # Calculate P/L for closed portion (use leveraged P/L for accurate ROI)
            pnl = position.get_pnl(current_price)  # Base price change %
            leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
            
            # Thread-safe position update
            with self._positions_lock:
                # Re-check position still exists
                if symbol not in self.positions:
                    self.logger.warning(f"Position {symbol} was closed during scale-out")
                    return None
                
                # Update position amount
                position.amount -= amount_to_close
            
            self.logger.info(
                f"Scaled out of {symbol}: closed {amount_to_close} contracts "
                f"(P/L: {leveraged_pnl:.2%}), remaining: {position.amount}, Reason: {reason}"
            )
            
            return leveraged_pnl
            
        except Exception as e:
            self.logger.error(f"Error scaling out of position {symbol}: {e}")
            return None
    
    def modify_position_targets(self, symbol: str, new_stop_loss: Optional[float] = None,
                               new_take_profit: Optional[float] = None) -> bool:
        """Modify stop loss and/or take profit without closing position
        
        Args:
            symbol: Trading pair symbol
            new_stop_loss: New stop loss price (optional)
            new_take_profit: New take profit price (optional)
        
        Returns:
            True if successful, False otherwise
        """
        # Thread-safe position check and modification
        with self._positions_lock:
            if symbol not in self.positions:
                self.logger.error(f"No position found for {symbol} to modify")
                return False
            
            try:
                position = self.positions[symbol]
                
                if new_stop_loss is not None:
                    old_sl = position.stop_loss
                    position.stop_loss = new_stop_loss
                    self.logger.info(
                        f"Modified stop loss for {symbol}: {old_sl:.2f} -> {new_stop_loss:.2f}"
                    )
                
                if new_take_profit is not None:
                    old_tp = position.take_profit
                    position.take_profit = new_take_profit
                    self.logger.info(
                        f"Modified take profit for {symbol}: {old_tp:.2f} -> {new_take_profit:.2f}"
                    )
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error modifying position targets for {symbol}: {e}")
                return False
