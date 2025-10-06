"""
Position management with trailing stop loss
"""
import time
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime
from kucoin_client import KuCoinClient
from logger import Logger
from advanced_exit_strategy import AdvancedExitStrategy

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
                elif current_price == self.take_profit:
                    # Bug fix: Price is exactly at TP - allow extension if conditions are favorable
                    # This enables TP to extend when price reaches the initial target
                    self.take_profit = new_take_profit
                else:
                    # Price past TP - only allow if new TP brings it closer
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
                elif current_price == self.take_profit:
                    # Bug fix: Price is exactly at TP - allow extension if conditions are favorable
                    # This enables TP to extend when price reaches the initial target
                    self.take_profit = new_take_profit
                else:
                    # Price past TP - only allow if new TP brings it closer
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
        self.advanced_exit_strategy = AdvancedExitStrategy()
    
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
                
                # Skip if we already have this position tracked
                if symbol in self.positions:
                    self.logger.debug(f"Position {symbol} already tracked, skipping sync")
                    continue
                
                # Extract position details
                contracts = float(pos.get('contracts', 0))
                if contracts == 0:
                    continue
                
                side = pos.get('side', 'long')  # 'long' or 'short'
                entry_price = float(pos.get('entryPrice', 0))
                leverage = int(pos.get('leverage', 10))
                
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
                
                self.positions[symbol] = position
                synced_count += 1
                
                # Calculate current P/L
                pnl = position.get_pnl(current_price)
                
                self.logger.info(
                    f"Synced {side} position: {symbol} @ {entry_price:.2f}, "
                    f"Current: {current_price:.2f}, Amount: {abs(contracts)}, "
                    f"Leverage: {leverage}x, P/L: {pnl:.2%}, "
                    f"Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}"
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
            # Get current price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return False
            
            # Bug fix: Safely access 'last' price
            current_price = ticker.get('last')
            if not current_price or current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}: {current_price}")
                return False
            side = 'buy' if signal == 'BUY' else 'sell'
            
            # Create order (market or limit)
            if use_limit:
                # Place limit order slightly better than market price
                if side == 'buy':
                    limit_price = current_price * (1 - limit_offset)
                else:
                    limit_price = current_price * (1 + limit_offset)
                
                order = self.client.create_limit_order(
                    symbol, side, amount, limit_price, leverage, post_only=True
                )
                
                if not order:
                    self.logger.warning(f"Limit order failed, falling back to market order")
                    order = self.client.create_market_order(symbol, side, amount, leverage)
                elif 'id' in order:
                    # Bug fix: Check order has 'id' key before accessing
                    # Wait briefly for fill, cancel if not filled
                    order_status = self.client.wait_for_order_fill(
                        order['id'], symbol, timeout=10, check_interval=2
                    )
                    
                    if not order_status or order_status.get('status') != 'closed':
                        # Bug fix: Use .get() for status access
                        # Not filled, cancel and use market order
                        self.client.cancel_order(order['id'], symbol)
                        self.logger.info(f"Limit order not filled, using market order instead")
                        order = self.client.create_market_order(symbol, side, amount, leverage)
                else:
                    self.logger.warning(f"Limit order missing 'id', falling back to market order")
                    order = self.client.create_market_order(symbol, side, amount, leverage)
            else:
                order = self.client.create_market_order(symbol, side, amount, leverage)
            
            if not order:
                return False
            
            # Get actual fill price
            fill_price = order.get('average') or current_price
            
            # Calculate stop loss and take profit
            if signal == 'BUY':
                stop_loss = fill_price * (1 - stop_loss_percentage)
                take_profit = fill_price * (1 + stop_loss_percentage * 2)
            else:
                stop_loss = fill_price * (1 + stop_loss_percentage)
                take_profit = fill_price * (1 - stop_loss_percentage * 2)
            
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
            
            self.positions[symbol] = position
            
            self.logger.info(
                f"Opened {position.side} position: {symbol} @ {fill_price:.2f}, "
                f"Amount: {amount}, Leverage: {leverage}x, "
                f"Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return False
    
    def close_position(self, symbol: str, reason: str = 'manual') -> Optional[float]:
        """Close a position and return P/L"""
        try:
            if symbol not in self.positions:
                return None
            
            position = self.positions[symbol]
            
            # Get current price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return None
            
            # Bug fix: Safely access 'last' price
            current_price = ticker.get('last')
            if not current_price or current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}: {current_price}")
                return None
            
            # Close position on exchange
            success = self.client.close_position(symbol)
            if not success:
                return None
            
            # Calculate P/L
            pnl = position.get_pnl(current_price)
            
            self.logger.info(
                f"Closed {position.side} position: {symbol} @ {current_price:.2f}, "
                f"Entry: {position.entry_price:.2f}, P/L: {pnl:.2%}, Reason: {reason}"
            )
            
            # Remove from positions
            del self.positions[symbol]
            
            return pnl
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
    
    def update_positions(self):
        """Update all positions and manage trailing stops with adaptive parameters"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                
                # Get current price
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    continue
                
                # Bug fix: Safely access 'last' price
                current_price = ticker.get('last')
                if not current_price or current_price <= 0:
                    self.logger.warning(f"Invalid price for {symbol}: {current_price}, skipping")
                    continue
                
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
                        
                        # Update trailing stop with adaptive parameters
                        position.update_trailing_stop(
                            current_price, 
                            self.trailing_stop_percentage,
                            volatility=volatility,
                            momentum=momentum
                        )
                        
                        # Update take profit dynamically with all parameters
                        position.update_take_profit(
                            current_price,
                            momentum=momentum,
                            trend_strength=trend_strength,
                            volatility=volatility,
                            rsi=rsi,
                            support_resistance=support_resistance
                        )
                    else:
                        # Fallback to simple update if indicators fail
                        position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                else:
                    # Fallback to simple update if no market data
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
                
                # Update stop loss if breakeven+ suggests a new level
                if suggested_stop is not None and suggested_stop != position.stop_loss:
                    old_stop = position.stop_loss
                    position.stop_loss = suggested_stop
                    self.logger.info(f"🔒 Updated {symbol} stop loss: {old_stop:.2f} -> {suggested_stop:.2f} ({exit_reason})")
                
                # If advanced strategy says exit, do it
                if should_exit_advanced:
                    pnl = self.close_position(symbol, exit_reason)
                    if pnl is not None:
                        yield symbol, pnl, position
                    continue
                
                # Check standard stop loss and take profit conditions
                should_close, reason = position.should_close(current_price)
                if should_close:
                    pnl = self.close_position(symbol, reason)
                    if pnl is not None:
                        yield symbol, pnl, position
                
            except Exception as e:
                self.logger.error(f"Error updating position {symbol}: {e}")
                # Try simple update as fallback
                try:
                    position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                except Exception:
                    pass
    
    def get_open_positions_count(self) -> int:
        """Get number of open positions"""
        return len(self.positions)
    
    def has_position(self, symbol: str) -> bool:
        """Check if a position is open for a symbol"""
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
        if symbol not in self.positions:
            self.logger.error(f"No position found for {symbol} to scale into")
            return False
        
        try:
            position = self.positions[symbol]
            
            # Execute the additional order
            side = 'buy' if position.side == 'long' else 'sell'
            order = self.client.create_market_order(
                symbol, side, additional_amount, position.leverage
            )
            
            if not order:
                return False
            
            # Update position with new average entry price
            total_old = position.amount * position.entry_price
            total_new = additional_amount * current_price
            total_amount = position.amount + additional_amount
            
            position.entry_price = (total_old + total_new) / total_amount
            position.amount = total_amount
            
            self.logger.info(
                f"Scaled into {symbol}: added {additional_amount} contracts, "
                f"new avg entry: {position.entry_price:.2f}, total: {total_amount}"
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
        if symbol not in self.positions:
            self.logger.error(f"No position found for {symbol} to scale out of")
            return None
        
        try:
            position = self.positions[symbol]
            
            if amount_to_close >= position.amount:
                # Closing entire position
                return self.close_position(symbol, reason)
            
            # Get current price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return None
            
            # Bug fix: Safely access 'last' price
            current_price = ticker.get('last')
            if not current_price or current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}: {current_price}")
                return None
            
            # Close partial position
            side = 'sell' if position.side == 'long' else 'buy'
            order = self.client.create_market_order(symbol, side, amount_to_close)
            
            if not order:
                return None
            
            # Calculate P/L for closed portion
            pnl = position.get_pnl(current_price)
            
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
