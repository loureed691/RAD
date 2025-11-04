"""
Paper Trading Mode

Simulates real trading without executing actual orders on exchange.
Useful for:
- Strategy testing without risk
- Algorithm validation
- Performance evaluation
- Live testing before going to production

Features:
- Realistic order fills based on market prices
- Simulated slippage and fees
- Order book impact simulation
- Portfolio tracking
- Performance metrics
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from logger import Logger
import numpy as np


class PaperTradingEngine:
    """
    Paper trading engine that simulates order execution.
    
    Simulates fills, tracks positions, and calculates P&L without real trades.
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        fee_rate: float = 0.001,  # 0.1% fees
        slippage_bps: float = 5.0,  # 5 bps default slippage
        enable_partial_fills: bool = True
    ):
        """
        Initialize paper trading engine.
        
        Args:
            initial_balance: Starting account balance in USD
            fee_rate: Trading fee rate (as decimal)
            slippage_bps: Slippage in basis points
            enable_partial_fills: Allow partial order fills
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.fee_rate = fee_rate
        self.slippage = slippage_bps / 10000  # Convert to decimal
        self.enable_partial_fills = enable_partial_fills
        
        self.logger = Logger.get_logger()
        
        # State tracking
        self.positions = {}  # symbol -> {size, avg_entry, side, unrealized_pnl}
        self.orders = {}  # order_id -> order details
        self.trades = []  # List of completed trades
        self.order_id_counter = 1
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.total_fees = 0.0
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        
        self.start_time = datetime.now()
        
        self.logger.info("📝 Paper Trading Mode Initialized")
        self.logger.info(f"   Initial Balance: ${initial_balance:,.2f}")
        self.logger.info(f"   Fee Rate: {fee_rate*100:.3f}%")
        self.logger.info(f"   Slippage: {slippage_bps:.1f} bps")
        self.logger.warning("⚠️  Paper Trading: No real orders will be executed")
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        order_id = f"PAPER_{self.order_id_counter:08d}"
        self.order_id_counter += 1
        return order_id
    
    def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        order_type: str = "market",
        price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Dict:
        """
        Place a paper trade order.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            size: Order size
            order_type: 'market' or 'limit'
            price: Limit price (for limit orders)
            current_price: Current market price (required for market orders)
            
        Returns:
            Dictionary with order details
        """
        order_id = self._generate_order_id()
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side.lower(),
            'size': size,
            'type': order_type.lower(),
            'limit_price': price,
            'status': 'pending',
            'filled_size': 0.0,
            'avg_fill_price': 0.0,
            'timestamp': datetime.now(),
            'fees': 0.0
        }
        
        self.orders[order_id] = order
        
        # For market orders, simulate immediate fill
        if order_type.lower() == 'market':
            if current_price is None:
                self.logger.error("Market order requires current_price")
                order['status'] = 'rejected'
                order['reject_reason'] = 'Missing current price'
                return order
            
            self._simulate_fill(order_id, current_price)
        
        self.logger.info(
            f"📝 Paper Order: {side.upper()} {size:.4f} {symbol} @ "
            f"{price if order_type == 'limit' else 'MARKET'} [{order_id}]"
        )
        
        return order
    
    def _simulate_fill(self, order_id: str, market_price: float) -> bool:
        """
        Simulate order fill with realistic slippage and fees.
        
        Args:
            order_id: Order ID to fill
            market_price: Current market price
            
        Returns:
            True if filled, False otherwise
        """
        order = self.orders.get(order_id)
        if not order:
            return False
        
        if order['status'] != 'pending':
            return False
        
        # Check if limit order can be filled
        if order['type'] == 'limit':
            limit_price = order['limit_price']
            if order['side'] == 'buy' and market_price > limit_price:
                return False  # Can't buy above limit
            if order['side'] == 'sell' and market_price < limit_price:
                return False  # Can't sell below limit
        
        # Calculate fill price with slippage
        if order['side'] == 'buy':
            # Buying - pay slippage above market
            fill_price = market_price * (1 + self.slippage)
        else:
            # Selling - get slippage below market
            fill_price = market_price * (1 - self.slippage)
        
        # For limit orders, can't be worse than limit price
        if order['type'] == 'limit':
            if order['side'] == 'buy':
                fill_price = min(fill_price, order['limit_price'])
            else:
                fill_price = max(fill_price, order['limit_price'])
        
        # Calculate fees
        trade_value = fill_price * order['size']
        fees = trade_value * self.fee_rate
        
        # Check if we have enough balance for buy orders
        if order['side'] == 'buy':
            total_cost = trade_value + fees
            if total_cost > self.balance:
                order['status'] = 'rejected'
                order['reject_reason'] = 'Insufficient balance'
                self.logger.warning(f"Order {order_id} rejected: insufficient balance")
                return False
        
        # Update order
        order['status'] = 'filled'
        order['filled_size'] = order['size']
        order['avg_fill_price'] = fill_price
        order['fees'] = fees
        order['fill_time'] = datetime.now()
        
        # Update position
        self._update_position(
            order['symbol'],
            order['side'],
            order['filled_size'],
            fill_price
        )
        
        # Update balance
        if order['side'] == 'buy':
            self.balance -= (trade_value + fees)
        else:
            self.balance += (trade_value - fees)
        
        self.total_fees += fees
        
        # Record trade
        trade = {
            'trade_id': order_id,
            'symbol': order['symbol'],
            'side': order['side'],
            'size': order['filled_size'],
            'price': fill_price,
            'value': trade_value,
            'fees': fees,
            'timestamp': order['fill_time']
        }
        self.trades.append(trade)
        self.total_trades += 1
        
        self.logger.info(
            f"✅ Paper Fill: {order['side'].upper()} {order['filled_size']:.4f} "
            f"{order['symbol']} @ {fill_price:.2f} (fee: ${fees:.2f})"
        )
        
        return True
    
    def _update_position(self, symbol: str, side: str, size: float, price: float):
        """
        Update position after a fill.
        
        Args:
            symbol: Trading symbol
            side: Trade side
            size: Trade size
            price: Trade price
        """
        if symbol not in self.positions:
            # New position
            self.positions[symbol] = {
                'size': size if side == 'buy' else -size,
                'avg_entry': price,
                'side': 'long' if side == 'buy' else 'short',
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0
            }
        else:
            pos = self.positions[symbol]
            current_size = pos['size']
            
            # Calculate new position
            if side == 'buy':
                new_size = current_size + size
            else:
                new_size = current_size - size
            
            # Check if closing or reversing position
            if current_size * new_size < 0:
                # Position reversed - realize P&L
                close_size = min(abs(current_size), size)
                pnl = close_size * (price - pos['avg_entry']) * (-1 if current_size < 0 else 1)
                pos['realized_pnl'] += pnl
                self.total_pnl += pnl
                
                if pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
            
            # Update position
            if new_size == 0:
                # Position closed
                del self.positions[symbol]
            else:
                # Update position size and avg entry
                if abs(new_size) > abs(current_size):
                    # Adding to position - update avg entry
                    added_size = abs(new_size) - abs(current_size)
                    total_cost = (pos['avg_entry'] * abs(current_size) + price * added_size)
                    pos['avg_entry'] = total_cost / abs(new_size)
                
                pos['size'] = new_size
                pos['side'] = 'long' if new_size > 0 else 'short'
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Update market prices and calculate unrealized P&L.
        
        Args:
            prices: Dictionary of symbol -> current price
        """
        total_unrealized = 0.0
        
        for symbol, pos in self.positions.items():
            if symbol in prices:
                current_price = prices[symbol]
                pnl = pos['size'] * (current_price - pos['avg_entry'])
                pos['unrealized_pnl'] = pnl
                total_unrealized += pnl
        
        # Update peak balance and drawdown
        equity = self.balance + total_unrealized
        if equity > self.peak_balance:
            self.peak_balance = equity
        
        drawdown = (self.peak_balance - equity) / self.peak_balance
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        order = self.orders.get(order_id)
        if not order:
            return False
        
        if order['status'] != 'pending':
            return False
        
        order['status'] = 'cancelled'
        self.logger.info(f"❌ Paper Order Cancelled: {order_id}")
        return True
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get current position for symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position dict or None
        """
        return self.positions.get(symbol)
    
    def get_balance(self) -> float:
        """Get current account balance."""
        return self.balance
    
    def get_equity(self, prices: Optional[Dict[str, float]] = None) -> float:
        """
        Get total account equity (balance + unrealized P&L).
        
        Args:
            prices: Current market prices
            
        Returns:
            Total equity
        """
        if prices:
            self.update_prices(prices)
        
        unrealized = sum(pos['unrealized_pnl'] for pos in self.positions.values())
        return self.balance + unrealized
    
    def get_performance(self) -> Dict:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        equity = self.get_equity()
        total_return = (equity - self.initial_balance) / self.initial_balance
        
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds() / 86400  # days
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'current_equity': equity,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_pnl': self.total_pnl,
            'total_fees': self.total_fees,
            'net_pnl': self.total_pnl - self.total_fees,
            'open_positions': len(self.positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown * 100,
            'days_running': elapsed_time
        }
    
    def get_status(self) -> Dict:
        """
        Get paper trading engine status.
        
        Returns:
            Dictionary with current state
        """
        return {
            'mode': 'paper_trading',
            'balance': self.balance,
            'equity': self.get_equity(),
            'positions': len(self.positions),
            'pending_orders': sum(1 for o in self.orders.values() if o['status'] == 'pending'),
            'total_orders': len(self.orders),
            'total_trades': self.total_trades,
            'fee_rate': self.fee_rate,
            'slippage_bps': self.slippage * 10000
        }
    
    def reset(self):
        """Reset paper trading engine to initial state."""
        self.balance = self.initial_balance
        self.positions = {}
        self.orders = {}
        self.trades = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.total_fees = 0.0
        self.peak_balance = self.initial_balance
        self.max_drawdown = 0.0
        self.start_time = datetime.now()
        
        self.logger.info("Paper trading engine reset")
