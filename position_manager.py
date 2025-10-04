"""
Position management with trailing stop loss
"""
import time
from typing import Dict, Optional, Tuple
from datetime import datetime
from kucoin_client import KuCoinClient
from logger import Logger

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
                          trend_strength: float = 0.5, volatility: float = 0.03):
        """
        Dynamically adjust take profit based on market conditions
        
        Args:
            current_price: Current market price
            momentum: Current price momentum
            trend_strength: Strength of current trend (0-1)
            volatility: Market volatility
        """
        if not self.take_profit:
            return
        
        # Calculate current P/L and initial target
        current_pnl = self.get_pnl(current_price)
        initial_distance = abs(self.initial_take_profit - self.entry_price) / self.entry_price
        
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
        
        # 4. Already profitable - be more conservative with extensions
        if current_pnl > 0.05:
            tp_multiplier = min(tp_multiplier, 1.2)  # Cap extension when already in profit
        
        # Calculate new take profit
        new_distance = initial_distance * tp_multiplier
        
        if self.side == 'long':
            new_take_profit = self.entry_price * (1 + new_distance)
            # Only move take profit up (more favorable)
            if new_take_profit > self.take_profit:
                self.take_profit = new_take_profit
        else:  # short
            new_take_profit = self.entry_price * (1 - new_distance)
            # Only move take profit down (more favorable)
            if new_take_profit < self.take_profit:
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
        
        return False, ''
    
    def get_pnl(self, current_price: float) -> float:
        """Calculate profit/loss percentage"""
        if self.side == 'long':
            pnl = ((current_price - self.entry_price) / self.entry_price) * self.leverage
        else:
            pnl = ((self.entry_price - current_price) / self.entry_price) * self.leverage
        return pnl

class PositionManager:
    """Manage open positions with trailing stops"""
    
    def __init__(self, client: KuCoinClient, trailing_stop_percentage: float = 0.02):
        self.client = client
        self.trailing_stop_percentage = trailing_stop_percentage
        self.positions: Dict[str, Position] = {}
        self.logger = Logger.get_logger()
    
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
                
                current_price = ticker['last']
                
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
                     leverage: int, stop_loss_percentage: float = 0.05) -> bool:
        """Open a new position"""
        try:
            # Get current price
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return False
            
            current_price = ticker['last']
            side = 'buy' if signal == 'BUY' else 'sell'
            
            # Create order
            order = self.client.create_market_order(symbol, side, amount, leverage)
            if not order:
                return False
            
            # Calculate stop loss
            if signal == 'BUY':
                stop_loss = current_price * (1 - stop_loss_percentage)
                take_profit = current_price * (1 + stop_loss_percentage * 2)
            else:
                stop_loss = current_price * (1 + stop_loss_percentage)
                take_profit = current_price * (1 - stop_loss_percentage * 2)
            
            # Create position object
            position = Position(
                symbol=symbol,
                side='long' if signal == 'BUY' else 'short',
                entry_price=current_price,
                amount=amount,
                leverage=leverage,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            self.positions[symbol] = position
            
            self.logger.info(
                f"Opened {position.side} position: {symbol} @ {current_price:.2f}, "
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
            
            current_price = ticker['last']
            
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
                
                current_price = ticker['last']
                
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
                        
                        # Calculate trend strength from moving averages
                        close = indicators.get('close', current_price)
                        sma_20 = indicators.get('sma_20', close)
                        sma_50 = indicators.get('sma_50', close)
                        
                        # Trend strength: 0 (no trend) to 1 (strong trend)
                        if sma_50 > 0:
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
                        
                        # Update take profit dynamically
                        position.update_take_profit(
                            current_price,
                            momentum=momentum,
                            trend_strength=trend_strength,
                            volatility=volatility
                        )
                    else:
                        # Fallback to simple update if indicators fail
                        position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                else:
                    # Fallback to simple update if no market data
                    position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                
                # Check if position should be closed
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
