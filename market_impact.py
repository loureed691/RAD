"""
Market impact estimation for optimal order sizing
"""
import numpy as np
from typing import Dict, Optional
from logger import Logger

class MarketImpact:
    """Estimate and minimize market impact of trades"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
    
    def estimate_price_impact(self, order_size: float, 
                             avg_volume: float,
                             volatility: float,
                             spread_pct: float) -> float:
        """
        Estimate price impact of an order using Kyle's lambda model
        
        Args:
            order_size: Size of order in USD
            avg_volume: Average daily volume in USD
            volatility: Price volatility (std of returns)
            spread_pct: Bid-ask spread as percentage
            
        Returns:
            Estimated price impact as percentage
        """
        if avg_volume <= 0:
            return 0.0
        
        # Kyle's lambda: measure of market depth
        # Higher volatility and lower volume = higher impact
        lambda_param = volatility / (avg_volume ** 0.5)
        
        # Linear impact component
        linear_impact = lambda_param * order_size
        
        # Quadratic impact (market impact grows non-linearly for large orders)
        quadratic_impact = 0.5 * (order_size / avg_volume) ** 2
        
        # Spread cost (immediate cost of crossing spread)
        spread_cost = spread_pct / 2  # Half spread
        
        # Total impact
        total_impact = linear_impact + quadratic_impact + spread_cost
        
        return total_impact
    
    def calculate_optimal_order_size(self, desired_size: float,
                                    avg_volume: float,
                                    volatility: float,
                                    spread_pct: float,
                                    max_impact_pct: float = 0.002) -> Dict:
        """
        Calculate optimal order size to keep impact below threshold
        
        Args:
            desired_size: Desired position size in USD
            avg_volume: Average daily volume in USD
            volatility: Price volatility
            spread_pct: Bid-ask spread percentage
            max_impact_pct: Maximum acceptable impact (default 0.2%)
            
        Returns:
            Dict with optimal_size, estimated_impact, should_split, num_orders
        """
        # Estimate impact of full order
        full_impact = self.estimate_price_impact(
            desired_size, avg_volume, volatility, spread_pct
        )
        
        if full_impact <= max_impact_pct:
            return {
                'optimal_size': desired_size,
                'estimated_impact': full_impact,
                'should_split': False,
                'num_orders': 1,
                'impact_reduction': 0.0
            }
        
        # Need to split order
        # Calculate how many orders needed
        num_orders = int(np.ceil(full_impact / max_impact_pct))
        split_size = desired_size / num_orders
        
        # Estimate impact per split order
        split_impact = self.estimate_price_impact(
            split_size, avg_volume, volatility, spread_pct
        )
        
        # Total impact with splitting (accounting for multiple executions)
        total_split_impact = split_impact * num_orders * 0.8  # 20% efficiency from splitting
        
        impact_reduction = (full_impact - total_split_impact) / full_impact
        
        return {
            'optimal_size': split_size,
            'estimated_impact': total_split_impact,
            'should_split': True,
            'num_orders': num_orders,
            'impact_reduction': impact_reduction,
            'original_impact': full_impact
        }
    
    def estimate_slippage(self, order_size: float,
                         orderbook: Dict,
                         side: str = 'buy') -> Dict:
        """
        Estimate slippage from order book data
        
        Args:
            order_size: Size of order in base currency
            orderbook: Dict with 'bids' and 'asks' arrays
            side: 'buy' or 'sell'
            
        Returns:
            Dict with slippage_pct, avg_price, worst_price
        """
        if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
            return {
                'slippage_pct': 0.0,
                'avg_price': 0.0,
                'worst_price': 0.0,
                'liquidity_sufficient': False
            }
        
        try:
            # Get relevant side of order book
            book_side = orderbook['asks'] if side == 'buy' else orderbook['bids']
            
            if not book_side:
                return {
                    'slippage_pct': 0.0,
                    'avg_price': 0.0,
                    'worst_price': 0.0,
                    'liquidity_sufficient': False
                }
            
            # Best price (start)
            best_price = float(book_side[0][0])
            
            # Calculate average execution price
            remaining = order_size
            total_cost = 0.0
            worst_price = best_price
            
            for price, size in book_side:
                price = float(price)
                size = float(size)
                
                if remaining <= 0:
                    break
                
                fill_size = min(remaining, size)
                total_cost += price * fill_size
                remaining -= fill_size
                worst_price = price
            
            if remaining > 0:
                # Not enough liquidity
                return {
                    'slippage_pct': 0.0,
                    'avg_price': 0.0,
                    'worst_price': 0.0,
                    'liquidity_sufficient': False,
                    'shortfall': remaining
                }
            
            avg_price = total_cost / order_size
            slippage_pct = abs(avg_price - best_price) / best_price
            
            return {
                'slippage_pct': slippage_pct,
                'avg_price': avg_price,
                'best_price': best_price,
                'worst_price': worst_price,
                'liquidity_sufficient': True
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating slippage: {e}")
            return {
                'slippage_pct': 0.0,
                'avg_price': 0.0,
                'worst_price': 0.0,
                'liquidity_sufficient': False
            }
    
    def calculate_participation_rate(self, order_size: float,
                                    avg_volume: float,
                                    max_participation: float = 0.1) -> Dict:
        """
        Calculate optimal participation rate in market volume
        
        Args:
            order_size: Size of order in USD
            avg_volume: Average market volume in USD
            max_participation: Maximum % of volume to trade (default 10%)
            
        Returns:
            Dict with participation_rate, time_to_complete_minutes, is_acceptable
        """
        if avg_volume <= 0:
            return {
                'participation_rate': 0.0,
                'time_to_complete_minutes': float('inf'),
                'is_acceptable': False
            }
        
        participation_rate = order_size / avg_volume
        
        # Estimate time to complete if we trade at max participation
        # Assume we trade during active hours (16 hours = 960 minutes per day)
        active_minutes_per_day = 960
        
        if participation_rate <= max_participation:
            # Can execute in one go
            time_to_complete = 1  # 1 minute
            is_acceptable = True
        else:
            # Need to break up over time
            num_days = participation_rate / max_participation
            time_to_complete = num_days * active_minutes_per_day
            is_acceptable = time_to_complete <= 60  # Max 1 hour
        
        return {
            'participation_rate': participation_rate,
            'time_to_complete_minutes': time_to_complete,
            'is_acceptable': is_acceptable,
            'exceeds_threshold': participation_rate > max_participation
        }
    
    def get_execution_strategy(self, order_size: float,
                               avg_volume: float,
                               volatility: float,
                               spread_pct: float,
                               orderbook: Optional[Dict] = None) -> Dict:
        """
        Get comprehensive execution strategy recommendation
        
        Args:
            order_size: Desired order size in USD
            avg_volume: Average daily volume in USD
            volatility: Price volatility
            spread_pct: Bid-ask spread percentage
            orderbook: Optional order book data
            
        Returns:
            Dict with full execution strategy
        """
        # Calculate optimal sizing
        sizing = self.calculate_optimal_order_size(
            order_size, avg_volume, volatility, spread_pct
        )
        
        # Check participation rate
        participation = self.calculate_participation_rate(
            order_size, avg_volume
        )
        
        # Estimate slippage if order book provided
        slippage = None
        if orderbook:
            slippage = self.estimate_slippage(
                sizing['optimal_size'], orderbook
            )
        
        # Determine strategy
        if not participation['is_acceptable']:
            strategy = 'REJECT'
            reason = 'Order too large relative to market volume'
        elif sizing['should_split']:
            strategy = 'TWAP'  # Time-weighted average price
            reason = f'Split into {sizing["num_orders"]} orders to minimize impact'
        elif participation['exceeds_threshold']:
            strategy = 'VWAP'  # Volume-weighted average price
            reason = 'Execute gradually throughout the day'
        else:
            strategy = 'IMMEDIATE'
            reason = 'Market impact acceptable, execute immediately'
        
        return {
            'strategy': strategy,
            'reason': reason,
            'optimal_order_size': sizing['optimal_size'],
            'num_orders': sizing['num_orders'],
            'estimated_impact': sizing['estimated_impact'],
            'participation_rate': participation['participation_rate'],
            'execution_time_minutes': participation['time_to_complete_minutes'],
            'slippage_estimate': slippage,
            'should_proceed': strategy != 'REJECT'
        }
    
    def estimate_total_cost(self, order_size: float,
                          avg_volume: float,
                          volatility: float,
                          spread_pct: float,
                          commission_pct: float = 0.001) -> Dict:
        """
        Estimate total cost of execution including all factors
        
        Args:
            order_size: Order size in USD
            avg_volume: Average daily volume
            volatility: Price volatility
            spread_pct: Bid-ask spread
            commission_pct: Commission rate (default 0.1%)
            
        Returns:
            Dict with cost breakdown
        """
        # Market impact
        impact = self.estimate_price_impact(
            order_size, avg_volume, volatility, spread_pct
        )
        
        # Commission
        commission = commission_pct
        
        # Spread cost
        spread_cost = spread_pct / 2
        
        # Total transaction cost
        total_cost_pct = impact + commission + spread_cost
        total_cost_usd = order_size * total_cost_pct
        
        return {
            'market_impact_pct': impact,
            'commission_pct': commission,
            'spread_cost_pct': spread_cost,
            'total_cost_pct': total_cost_pct,
            'total_cost_usd': total_cost_usd,
            'cost_per_trade': total_cost_pct * 100  # In basis points
        }
