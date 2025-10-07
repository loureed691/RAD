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
        
        # Adaptive trailing percentage based on multiple factors
        adaptive_trailing = trailing_percentage
        
        # 1. Volatility adjustment - wider stops in high volatility
        if volatility > 0.05:
            adaptive_trailing *= 1.5  # 50% wider in high volatility
        elif volatility < 0.02:
            adaptive_trailing *= 0.8  # 20% tighter in low volatility
        
        # 2. Profit-based adjustment - tighten as profit increases
        if current_pnl > 0.10:  # >10% profit
            adaptive_trailing *= 0.7  # Tighten to 70% to lock in more profit
        elif current_pnl > 0.05:  # >5% profit
            adaptive_trailing *= 0.85  # Moderate tightening
        
        # 3. Momentum adjustment - adapt to trend strength
        if abs(momentum) > 0.03:  # Strong momentum
            adaptive_trailing *= 1.2  # Wider to let trend run
        elif abs(momentum) < 0.01:  # Weak momentum
            adaptive_trailing *= 0.9  # Tighter when momentum fades
        
        # Cap adaptive trailing between reasonable bounds (0.5% to 5%)
        adaptive_trailing = max(0.005, min(adaptive_trailing, 0.05))
        
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
        
        # Calculate current P/L and initial target
        current_pnl = self.get_pnl(current_price)
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
        
        # 1. Strong momentum - extend take profit target
        if self.side == 'long' and momentum > 0.03:
            tp_multiplier = 1.5  # Extend 50% further
        elif self.side == 'short' and momentum < -0.03:
            tp_multiplier = 1.5
        elif abs(momentum) > 0.02:
            tp_multiplier = 1.25  # Moderate extension
        
        # 2. Trend strength - extend in strong trends
        if trend_strength > 0.7:
            tp_multiplier *= 1.3  # Strong trend bonus
        elif trend_strength > 0.5:
            tp_multiplier *= 1.15  # Moderate trend bonus
        
        # 3. High volatility - extend target to capture bigger moves
        if volatility > 0.05:
            tp_multiplier *= 1.2
        
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
        
        # 5. Profit velocity - fast profit accumulation suggests strong move
        if abs(self.profit_velocity) > 0.05:  # >5% per hour
            tp_multiplier *= 1.2  # Extend target for fast-moving trades
        elif abs(self.profit_velocity) < 0.01:  # <1% per hour
            tp_multiplier *= 0.95  # Tighten for slow moves
        
        # 6. Time-based adjustment - be more conservative on aging positions
        position_age_hours = (now - self.entry_time).total_seconds() / 3600
        if position_age_hours > 48:  # > 2 days old
            tp_multiplier *= 0.85  # Tighten 15% on very old positions
        elif position_age_hours > 24:  # > 1 day old
            tp_multiplier *= 0.9  # Tighten 10% on old positions
        
        # 7. Already profitable - be more conservative with extensions
        if current_pnl > 0.05:
            tp_multiplier = min(tp_multiplier, 1.2)  # Cap extension when already in profit
        
        # Additional safeguard: never extend TP if it would move beyond current price by too much
        # This prevents the scenario where TP keeps moving away as price approaches it
        # However, allow minimal extension even at 100% to let S/R capping work
        if self.side == 'long':
            # Check how close current price is to the original TP
            if current_price > self.entry_price:
                progress_to_tp = (current_price - self.entry_price) / (self.initial_take_profit - self.entry_price) if self.initial_take_profit > self.entry_price else 0
                # If we've passed the original TP, minimal extension only (for S/R capping)
                if progress_to_tp >= 1.0:
                    tp_multiplier = min(tp_multiplier, 1.03)  # Minimal extension for S/R capping
                # If we're 90%+ of the way to original TP, limited extension
                elif progress_to_tp >= 0.9:
                    tp_multiplier = min(tp_multiplier, 1.05)  # Very limited extension
                # If we're more than 50% of the way to original TP, limit extension
                elif progress_to_tp > 0.5:
                    tp_multiplier = min(tp_multiplier, 1.1)  # Limited extension
        else:  # short
            if current_price < self.entry_price:
                progress_to_tp = (self.entry_price - current_price) / (self.entry_price - self.initial_take_profit) if self.entry_price > self.initial_take_profit else 0
                # If we've passed the original TP, minimal extension only (for S/R capping)
                if progress_to_tp >= 1.0:
                    tp_multiplier = min(tp_multiplier, 1.03)  # Minimal extension for S/R capping
                # If we're 90%+ of the way to original TP, limited extension
                elif progress_to_tp >= 0.9:
                    tp_multiplier = min(tp_multiplier, 1.05)  # Very limited extension
                # If we're more than 50% of the way to original TP, limit extension
                elif progress_to_tp > 0.5:
                    tp_multiplier = min(tp_multiplier, 1.1)  # Limited extension
        
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
                if current_price < self.take_profit:
                    # Price hasn't reached TP yet
                    # Calculate how close: if price is within 10% of the distance to TP, don't extend further
                    distance_to_tp = self.take_profit - current_price
                    progress_pct = (current_price - self.entry_price) / (self.take_profit - self.entry_price) if self.take_profit > self.entry_price else 0
                    
                    if progress_pct < 0.75:  # Less than 75% of way to TP - allow extension
                        self.take_profit = new_take_profit
                    else:
                        # Close to TP (75%+) - don't allow extension to prevent moving TP away
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
                if current_price > self.take_profit:
                    # Price hasn't reached TP yet
                    # Calculate how close: if price is within 10% of the distance to TP, don't extend further
                    distance_to_tp = current_price - self.take_profit
                    progress_pct = (self.entry_price - current_price) / (self.entry_price - self.take_profit) if self.entry_price > self.take_profit else 0
                    
                    if progress_pct < 0.75:  # Less than 75% of way to TP - allow extension
                        self.take_profit = new_take_profit
                    else:
                        # Close to TP (75%+) - don't allow extension to prevent moving TP away
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

    def should_close(self, current_price: float) -> tuple[bool, str]:
        """Check if position should be closed"""
        # Calculate current P/L percentage (with leverage)
        current_pnl = self.get_pnl(current_price)
        
        # Standard stop loss and take profit checks (primary logic)
        if self.side == 'long':
            if current_price <= self.stop_loss:
                return True, 'stop_loss'
            if self.take_profit and current_price >= self.take_profit:
                return True, 'take_profit'
        else:  # short
            if current_price >= self.stop_loss:
                return True, 'stop_loss'
            if self.take_profit and current_price <= self.take_profit:
                return True, 'take_profit'
        
        # Emergency profit protection - only trigger if TP is unreachable or position has extreme profit
        # This is a safety mechanism for when TP extension logic fails, not normal operation
        if self.take_profit and current_pnl >= 0.05:  # Only check if we have 5%+ ROI
            # Calculate how far we are from the take profit target
            if self.side == 'long':
                distance_to_tp = (self.take_profit - current_price) / current_price
                passed_tp = current_price >= self.take_profit
            else:  # short
                distance_to_tp = (current_price - self.take_profit) / current_price
                passed_tp = current_price <= self.take_profit
            
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
        """Calculate profit/loss percentage"""
        if self.side == 'long':
            pnl = ((current_price - self.entry_price) / self.entry_price) * self.leverage
        else:
            pnl = ((self.entry_price - current_price) / self.entry_price) * self.leverage
        return pnl

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
                stop_loss_percentage = 0.05
                if side == 'long':
                    stop_loss = current_price * (1 - stop_loss_percentage)
                    take_profit = current_price * (1 + stop_loss_percentage * 2)
                else:
                    stop_loss = current_price * (1 + stop_loss_percentage)
                    take_profit = current_price * (1 - stop_loss_percentage * 2)
                
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
                
                # Calculate current P/L
                pnl = position.get_pnl(current_price)
                
                self.logger.info(
                    f"Synced {side} position: {symbol} @ {format_price(entry_price)}, "
                    f"Current: {format_price(current_price)}, Amount: {abs(contracts)}, "
                    f"Leverage: {leverage}x, P/L: {pnl:.2%}, "
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
            if signal == 'BUY':
                stop_loss = fill_price * (1 - stop_loss_percentage)
                take_profit = fill_price * (1 + stop_loss_percentage * 2)
            else:
                stop_loss = fill_price * (1 + stop_loss_percentage)
                take_profit = fill_price * (1 - stop_loss_percentage * 2)
            
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
            
            # Calculate P/L
            pnl = position.get_pnl(current_price)
            position_value = position.amount * position.entry_price
            pnl_usd = (pnl / position.leverage) * position_value if position.leverage > 0 else 0
            
            # Calculate duration
            duration = datetime.now() - position.entry_time
            duration_mins = duration.total_seconds() / 60
            
            self.position_logger.info(f"  P/L: {pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
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
                orders_logger.info(f"  P/L: {pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
                orders_logger.info(f"  Duration: {duration_mins:.1f} minutes")
                orders_logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                orders_logger.info("=" * 80)
                orders_logger.info("")
            
            self.logger.info(
                f"Closed {position.side} position: {symbol} @ {format_price(current_price)}, "
                f"Entry: {format_price(position.entry_price)}, P/L: {pnl:.2%}, Reason: {reason}"
            )
            
            self.position_logger.info(f"✓ Position closed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.position_logger.info(f"{'='*80}\n")
            
            # Thread-safe position removal
            with self._positions_lock:
                del self.positions[symbol]
            
            return pnl
            
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
                
                # Get current price
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    self.position_logger.warning(f"  ⚠ Failed to get ticker")
                    continue
                
                # Bug fix: Safely access 'last' price
                current_price = ticker.get('last')
                if not current_price or current_price <= 0:
                    self.logger.warning(f"Invalid price for {symbol}: {current_price}, skipping")
                    self.position_logger.warning(f"  ⚠ Invalid price: {current_price}")
                    continue
                
                self.position_logger.info(f"  Current Price: {format_price(current_price)}")
                
                # Calculate current P/L
                current_pnl = position.get_pnl(current_price)
                position_value = position.amount * position.entry_price
                pnl_usd = (current_pnl / position.leverage) * position_value if position.leverage > 0 else 0
                
                self.position_logger.info(f"  Current P/L: {current_pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
                self.position_logger.debug(f"  Stop Loss: {format_price(position.stop_loss)}")
                self.position_logger.debug(f"  Take Profit: {format_price(position.take_profit)}")
                self.position_logger.debug(f"  Max Favorable Excursion: {position.max_favorable_excursion:.2%}")
                
                # Get market data for adaptive parameters
                ohlcv = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
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
                current_pnl = position.get_pnl(current_price)
                
                # Prepare data for advanced exit strategy
                position_data = {
                    'side': position.side,
                    'entry_price': position.entry_price,
                    'current_price': current_price,
                    'current_pnl_pct': current_pnl,  # Leveraged P&L
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
                should_exit_advanced, exit_reason, suggested_stop = self.advanced_exit_strategy.get_comprehensive_exit_signal(
                    position_data, market_data
                )
                
                if should_exit_advanced:
                    self.position_logger.info(f"  🚨 Advanced exit signal: {exit_reason}")
                
                # Update stop loss if breakeven+ suggests a new level
                if suggested_stop is not None and suggested_stop != position.stop_loss:
                    old_stop = position.stop_loss
                    position.stop_loss = suggested_stop
                    self.logger.info(f"🔒 Updated {symbol} stop loss: {old_stop:.2f} -> {suggested_stop:.2f} ({exit_reason})")
                    self.position_logger.info(f"  🔒 Stop loss adjusted: {old_stop:.2f} -> {suggested_stop:.2f} ({exit_reason})")
                
                # If advanced strategy says exit, do it
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
                self.logger.error(f"Error updating position {symbol}: {e}")
                self.position_logger.error(f"  ✗ Error updating position: {e}")
                # Try simple update as fallback
                try:
                    position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                except Exception as fallback_error:
                    # Log the fallback error rather than silently ignoring it
                    self.logger.error(f"Fallback update also failed for {symbol}: {fallback_error}")
                    self.position_logger.error(f"  ✗ Fallback update failed: {fallback_error}")
        
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
                                stop_loss_pct = 0.05
                                if side == 'long':
                                    stop_loss = current_price * (1 - stop_loss_pct)
                                    take_profit = current_price * (1 + stop_loss_pct * 2)
                                else:
                                    stop_loss = current_price * (1 + stop_loss_pct)
                                    take_profit = current_price * (1 - stop_loss_pct * 2)
                                
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
            if amount_to_close >= position.amount:
                # Release lock before calling close_position (it will acquire its own lock)
                pass
        
        # If closing entire position, use close_position method
        if amount_to_close >= position.amount:
            return self.close_position(symbol, reason)
        
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
            
            # Close partial position with correct leverage
            side = 'sell' if position.side == 'long' else 'buy'
            order = self.client.create_market_order(symbol, side, amount_to_close, position.leverage)
            
            if not order:
                return None
            
            # Calculate P/L for closed portion
            pnl = position.get_pnl(current_price)
            
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
                f"(P/L: {pnl:.2%}), remaining: {position.amount}, Reason: {reason}"
            )
            
            return pnl
            
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
