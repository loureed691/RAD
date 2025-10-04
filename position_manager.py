"""
Position management with trailing stop loss
"""
import time
from typing import Dict, Optional
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
    
    def update_trailing_stop(self, current_price: float, trailing_percentage: float):
        """Update trailing stop loss based on current price"""
        if self.side == 'long':
            if current_price > self.highest_price:
                self.highest_price = current_price
                new_stop = current_price * (1 - trailing_percentage)
                if new_stop > self.stop_loss:
                    self.stop_loss = new_stop
                    self.trailing_stop_activated = True
        else:  # short
            if current_price < self.lowest_price:
                self.lowest_price = current_price
                new_stop = current_price * (1 + trailing_percentage)
                if new_stop < self.stop_loss:
                    self.stop_loss = new_stop
                    self.trailing_stop_activated = True
    
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
        """Update all positions and manage trailing stops"""
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                
                # Get current price
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    continue
                
                current_price = ticker['last']
                
                # Update trailing stop
                position.update_trailing_stop(current_price, self.trailing_stop_percentage)
                
                # Check if position should be closed
                should_close, reason = position.should_close(current_price)
                if should_close:
                    pnl = self.close_position(symbol, reason)
                    if pnl is not None:
                        yield symbol, pnl, position
                
            except Exception as e:
                self.logger.error(f"Error updating position {symbol}: {e}")
    
    def get_open_positions_count(self) -> int:
        """Get number of open positions"""
        return len(self.positions)
    
    def has_position(self, symbol: str) -> bool:
        """Check if a position is open for a symbol"""
        return symbol in self.positions
