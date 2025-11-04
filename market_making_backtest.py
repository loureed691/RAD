"""
Market Making Backtesting Engine

Realistic backtesting for market making strategies with:
- Order book simulation
- Fill simulation based on queue position
- Inventory tracking
- Funding rate simulation
- Transaction costs
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger
from avellaneda_stoikov import AvellanedaStoikovMarketMaker
from delta_hedger import DeltaHedger


class MarketMakingBacktest:
    """
    Backtesting engine for market making strategies.
    
    Unlike directional trading backtests, market making requires:
    - Realistic fill simulation (not all orders fill)
    - Queue position modeling
    - Inventory risk tracking
    - Adverse selection costs
    - Funding rate costs (for perps)
    """
    
    def __init__(self,
                 initial_capital: float = 100000.0,
                 maker_fee: float = 0.0002,
                 taker_fee: float = 0.0006,
                 funding_rate: float = 0.0001):
        """
        Initialize backtesting engine
        
        Args:
            initial_capital: Starting capital in quote currency
            maker_fee: Maker fee rate
            taker_fee: Taker fee rate
            funding_rate: Funding rate per period (for perps)
        """
        self.initial_capital = initial_capital
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.funding_rate = funding_rate
        
        # State
        self.capital = initial_capital
        self.inventory = 0.0
        self.pending_orders = []
        self.filled_orders = []
        self.trades = []
        
        # Metrics
        self.total_fees_paid = 0.0
        self.total_funding_paid = 0.0
        self.total_pnl = 0.0
        self.maker_fills = 0
        self.taker_fills = 0
        
        # Tracking
        self.equity_curve = []
        self.inventory_curve = []
        self.timestamp_curve = []
        
        self.logger = Logger.get_logger()
        self.logger.info("📊 Market Making Backtest initialized")
        self.logger.info(f"   Initial capital: ${initial_capital:,.2f}")
        self.logger.info(f"   Maker fee: {maker_fee*100:.3f}%")
        self.logger.info(f"   Taker fee: {taker_fee*100:.3f}%")
    
    def simulate_fill_probability(self, order_price: float, market_price: float,
                                  side: str, orderbook: Dict,
                                  time_in_market: float = 1.0) -> float:
        """
        Simulate probability of order fill based on market conditions.
        
        Factors:
        - Distance from best bid/ask
        - Order book depth at that level
        - Market volatility
        - Time in market
        
        Args:
            order_price: Limit order price
            market_price: Current market price
            side: 'buy' or 'sell'
            orderbook: Order book snapshot
            time_in_market: Time order has been in market (periods)
        
        Returns:
            Fill probability (0-1)
        """
        try:
            levels = orderbook.get('bids') if side == 'buy' else orderbook.get('asks')
            if not levels:
                return 0.0
            
            best_price = float(levels[0][0])
            
            # Calculate distance from best
            if side == 'buy':
                distance_bps = ((best_price - order_price) / best_price) * 10000
            else:
                distance_bps = ((order_price - best_price) / best_price) * 10000
            
            # Base probability decreases with distance
            if distance_bps <= 0:
                # At or better than best - high probability
                base_prob = 0.9
            elif distance_bps <= 5:
                # Within 5 bps - good probability
                base_prob = 0.6
            elif distance_bps <= 10:
                # Within 10 bps - moderate
                base_prob = 0.3
            elif distance_bps <= 20:
                # Within 20 bps - low
                base_prob = 0.1
            else:
                # Too far - very low
                base_prob = 0.02
            
            # Adjust for time in market (longer = higher probability)
            time_factor = min(1.0, time_in_market / 10.0)  # Saturates at 10 periods
            
            fill_prob = base_prob * (0.5 + 0.5 * time_factor)
            
            return min(1.0, fill_prob)
        
        except Exception as e:
            self.logger.error(f"Error calculating fill probability: {e}")
            return 0.1  # Default low probability
    
    def place_order(self, side: str, price: float, amount: float,
                   order_type: str = 'limit', timestamp: datetime = None):
        """
        Place an order
        
        Args:
            side: 'buy' or 'sell'
            price: Limit price (for limit orders)
            amount: Order amount
            order_type: 'limit' or 'market'
            timestamp: Order timestamp
        """
        order = {
            'id': len(self.pending_orders) + len(self.filled_orders),
            'side': side,
            'price': price,
            'amount': amount,
            'type': order_type,
            'timestamp': timestamp or datetime.now(),
            'time_in_market': 0,
            'status': 'open'
        }
        
        if order_type == 'market':
            # Market orders fill immediately (in simulation)
            self._fill_order(order, price, timestamp)
        else:
            self.pending_orders.append(order)
    
    def _fill_order(self, order: Dict, fill_price: float, timestamp: datetime):
        """
        Fill an order
        
        Args:
            order: Order dict
            fill_price: Execution price
            timestamp: Fill timestamp
        """
        side = order['side']
        amount = order['amount']
        
        # Calculate fee
        if order['type'] == 'market':
            fee_rate = self.taker_fee
            self.taker_fills += 1
        else:
            fee_rate = self.maker_fee
            self.maker_fills += 1
        
        fee = amount * fill_price * fee_rate
        self.total_fees_paid += fee
        
        # Update inventory
        if side == 'buy':
            self.inventory += amount
            self.capital -= (amount * fill_price + fee)
        else:
            self.inventory -= amount
            self.capital += (amount * fill_price - fee)
        
        # Record trade
        trade = {
            'timestamp': timestamp,
            'side': side,
            'price': fill_price,
            'amount': amount,
            'fee': fee,
            'inventory_after': self.inventory,
            'capital_after': self.capital
        }
        self.trades.append(trade)
        
        # Update order status
        order['status'] = 'filled'
        order['fill_price'] = fill_price
        order['fill_timestamp'] = timestamp
        self.filled_orders.append(order)
    
    def update_pending_orders(self, orderbook: Dict, current_price: float,
                             timestamp: datetime):
        """
        Update pending orders and simulate fills
        
        Args:
            orderbook: Current order book
            current_price: Current market price
            timestamp: Current timestamp
        """
        still_pending = []
        
        for order in self.pending_orders:
            order['time_in_market'] += 1
            
            # Check if order should fill
            fill_prob = self.simulate_fill_probability(
                order['price'],
                current_price,
                order['side'],
                orderbook,
                order['time_in_market']
            )
            
            # Simulate fill with probability
            if np.random.random() < fill_prob:
                self._fill_order(order, order['price'], timestamp)
            else:
                still_pending.append(order)
        
        self.pending_orders = still_pending
    
    def cancel_all_orders(self):
        """Cancel all pending orders"""
        self.pending_orders = []
    
    def apply_funding_payment(self, mark_price: float, funding_rate: float = None):
        """
        Apply funding payment
        
        Args:
            mark_price: Mark price
            funding_rate: Funding rate (uses default if None)
        """
        if funding_rate is None:
            funding_rate = self.funding_rate
        
        # Funding payment = position_value * funding_rate
        position_value = self.inventory * mark_price
        funding_payment = position_value * funding_rate
        
        # Long pays funding if positive, receives if negative
        self.capital -= funding_payment
        self.total_funding_paid += abs(funding_payment)
    
    def run_backtest(self, market_data: pd.DataFrame,
                    market_maker: AvellanedaStoikovMarketMaker,
                    hedger: Optional[DeltaHedger] = None,
                    apply_funding: bool = True) -> Dict:
        """
        Run backtest with market making strategy
        
        Args:
            market_data: DataFrame with columns: timestamp, open, high, low, close, volume,
                        bid, ask, orderbook_snapshot
            market_maker: Market maker strategy
            hedger: Delta hedger (optional)
            apply_funding: Apply funding payments
        
        Returns:
            Backtest results dict
        """
        self.logger.info("🎬 Starting market making backtest")
        self.logger.info(f"   Data points: {len(market_data)}")
        
        for idx, row in market_data.iterrows():
            timestamp = row['timestamp']
            mid_price = (row['bid'] + row['ask']) / 2
            orderbook = row.get('orderbook_snapshot', {'bids': [], 'asks': []})
            
            # Update market maker with current market data
            volatility = row.get('volatility', 0.3)  # Default 30% annual vol
            microprice = row.get('microprice', mid_price)
            
            market_maker.update_market_data(
                mid_price=mid_price,
                volatility=volatility,
                inventory=self.inventory,
                microprice=microprice,
                order_flow_imbalance=row.get('ofi', 0.0),
                kyle_lambda=row.get('kyle_lambda', 0.0),
                short_volatility=row.get('short_vol', volatility)
            )
            
            # Get quotes
            bid_price, ask_price = market_maker.compute_quotes()
            
            if bid_price and ask_price:
                # Cancel old orders and place new quotes
                self.cancel_all_orders()
                
                # Place bid if we should quote this side
                if market_maker.should_quote_side('bid'):
                    self.place_order('buy', bid_price, 1.0, 'limit', timestamp)
                
                # Place ask if we should quote this side
                if market_maker.should_quote_side('ask'):
                    self.place_order('sell', ask_price, 1.0, 'limit', timestamp)
            
            # Update pending orders (simulate fills)
            self.update_pending_orders(orderbook, mid_price, timestamp)
            
            # Apply funding if enabled
            if apply_funding and idx % 24 == 0:  # Every 24 periods (assuming hourly data)
                self.apply_funding_payment(mid_price)
            
            # Hedge if needed
            if hedger:
                hedger.update_inventory(self.inventory)
                if hedger.should_hedge():
                    hedge_rec = hedger.get_hedge_recommendation(mid_price, microprice)
                    if hedge_rec:
                        # Execute hedge as market order
                        self.place_order(
                            hedge_rec['side'],
                            mid_price,
                            hedge_rec['hedge_size'],
                            'market',
                            timestamp
                        )
                        hedger.record_hedge(
                            hedge_rec['hedge_size'],
                            hedge_rec['side'],
                            mid_price,
                            hedge_rec['estimated_cost']
                        )
            
            # Track metrics
            equity = self.capital + self.inventory * mid_price
            self.equity_curve.append(equity)
            self.inventory_curve.append(self.inventory)
            self.timestamp_curve.append(timestamp)
        
        # Calculate final metrics
        results = self._calculate_metrics()
        
        self.logger.info("✅ Backtest complete")
        self.logger.info(f"   Total P&L: ${results['total_pnl']:.2f}")
        self.logger.info(f"   Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        self.logger.info(f"   Max Drawdown: {results['max_drawdown']*100:.2f}%")
        
        return results
    
    def _calculate_metrics(self) -> Dict:
        """Calculate backtest metrics"""
        if not self.equity_curve:
            return {}
        
        equity_series = pd.Series(self.equity_curve)
        
        # P&L
        final_equity = self.equity_curve[-1]
        total_pnl = final_equity - self.initial_capital
        pnl_pct = (total_pnl / self.initial_capital) * 100
        
        # Returns
        returns = equity_series.pct_change().dropna()
        
        # Sharpe ratio (assuming daily returns, annualize with sqrt(365))
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(365)
        else:
            sharpe_ratio = 0.0
        
        # Max drawdown
        cummax = equity_series.expanding().max()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # Win rate
        total_trades = len(self.trades)
        if total_trades > 1:
            # Calculate per-trade P&L
            trade_pnls = []
            for i in range(1, len(self.trades)):
                # Simplified: compare execution prices
                if self.trades[i]['side'] != self.trades[i-1]['side']:
                    if self.trades[i]['side'] == 'sell':
                        pnl = (self.trades[i]['price'] - self.trades[i-1]['price']) * self.trades[i]['amount']
                    else:
                        pnl = (self.trades[i-1]['price'] - self.trades[i]['price']) * self.trades[i]['amount']
                    trade_pnls.append(pnl)
            
            wins = sum(1 for pnl in trade_pnls if pnl > 0)
            win_rate = wins / len(trade_pnls) if trade_pnls else 0.0
        else:
            win_rate = 0.0
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_pnl': total_pnl,
            'pnl_pct': pnl_pct,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'maker_fills': self.maker_fills,
            'taker_fills': self.taker_fills,
            'win_rate': win_rate,
            'total_fees_paid': self.total_fees_paid,
            'total_funding_paid': self.total_funding_paid,
            'avg_inventory': np.mean(self.inventory_curve) if self.inventory_curve else 0,
            'max_inventory': max(self.inventory_curve) if self.inventory_curve else 0,
            'min_inventory': min(self.inventory_curve) if self.inventory_curve else 0,
            'equity_curve': self.equity_curve,
            'inventory_curve': self.inventory_curve,
            'timestamps': self.timestamp_curve
        }
