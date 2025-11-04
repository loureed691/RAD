"""
Smart Order Router (SOR) for optimal execution.

Routes orders to the best venue(s) based on:
- Price
- Liquidity
- Latency
- Fees
- Slippage estimates
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from logger import Logger


class SmartOrderRouter:
    """
    Smart Order Router for multi-venue execution optimization.
    
    The SOR determines the optimal way to execute an order across
    potentially multiple venues to minimize costs and maximize fill quality.
    
    Features:
    - Best price routing
    - Liquidity-aware routing
    - Split order execution
    - Cost estimation (fees + slippage)
    - Latency consideration
    """
    
    def __init__(self, venue_manager):
        """
        Initialize Smart Order Router
        
        Args:
            venue_manager: VenueManager instance
        """
        self.venue_manager = venue_manager
        self.logger = Logger.get_logger()
        
        # Routing history for analytics
        self.routing_history = []
        self.execution_stats = {
            'total_orders': 0,
            'single_venue': 0,
            'multi_venue': 0,
            'total_savings': 0.0
        }
        
        self.logger.info("🎯 Smart Order Router initialized")
    
    def estimate_execution_cost(self, venue_id: str, symbol: str,
                               side: str, amount: float,
                               orderbook: Dict = None) -> Dict:
        """
        Estimate execution cost on a venue
        
        Args:
            venue_id: Venue identifier
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            orderbook: Orderbook data (optional, will fetch if not provided)
        
        Returns:
            Cost estimation dict
        """
        try:
            connector = self.venue_manager.get_venue(venue_id)
            if not connector or not connector.connected:
                return {'viable': False, 'reason': 'venue_disconnected'}
            
            # Get orderbook if not provided
            if orderbook is None:
                orderbook = connector.get_orderbook(symbol)
            
            if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
                return {'viable': False, 'reason': 'no_orderbook'}
            
            # Get exchange info for fees
            exchange_info = connector.get_exchange_info()
            taker_fee = exchange_info.get('taker_fee', 0.001)
            
            # Walk through orderbook to estimate execution
            levels = orderbook.get('asks') if side == 'buy' else orderbook.get('bids')
            
            remaining_amount = amount
            total_cost = 0.0
            weighted_price = 0.0
            levels_used = 0
            
            for price_str, qty_str in levels:
                price = float(price_str)
                qty = float(qty_str)
                
                fill_qty = min(remaining_amount, qty)
                total_cost += fill_qty * price
                weighted_price += fill_qty * price
                remaining_amount -= fill_qty
                levels_used += 1
                
                if remaining_amount <= 0:
                    break
            
            if remaining_amount > 0:
                # Not enough liquidity
                return {
                    'viable': False,
                    'reason': 'insufficient_liquidity',
                    'max_fillable': amount - remaining_amount
                }
            
            # Calculate average execution price
            avg_price = total_cost / amount
            
            # Get reference price (mid or best)
            best_price = float(levels[0][0])
            
            # Calculate slippage
            slippage = abs(avg_price - best_price) / best_price
            
            # Calculate total cost including fees
            fee_cost = total_cost * taker_fee
            total_with_fees = total_cost + fee_cost
            
            return {
                'viable': True,
                'venue_id': venue_id,
                'avg_price': avg_price,
                'best_price': best_price,
                'slippage': slippage,
                'slippage_bps': slippage * 10000,
                'levels_used': levels_used,
                'fee_rate': taker_fee,
                'fee_cost': fee_cost,
                'gross_cost': total_cost,
                'total_cost': total_with_fees,
                'amount': amount
            }
        
        except Exception as e:
            self.logger.error(f"Error estimating cost for {venue_id}: {e}")
            return {'viable': False, 'reason': str(e)}
    
    def route_order(self, symbol: str, side: str, amount: float,
                   strategy: str = 'best_price') -> List[Dict]:
        """
        Route an order to optimal venue(s)
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            strategy: Routing strategy
                - 'best_price': Single venue with best price
                - 'split': Split across multiple venues
                - 'min_cost': Minimize total cost (fees + slippage)
        
        Returns:
            List of execution plans [{venue_id, amount, price}]
        """
        self.logger.info(f"🎯 Routing order: {side} {amount} {symbol} (strategy: {strategy})")
        
        connected_venues = self.venue_manager.get_connected_venues()
        
        if not connected_venues:
            self.logger.error("No connected venues available")
            return []
        
        # Get costs for all venues
        venue_costs = {}
        for venue_id in connected_venues:
            cost_est = self.estimate_execution_cost(venue_id, symbol, side, amount)
            if cost_est.get('viable'):
                venue_costs[venue_id] = cost_est
        
        if not venue_costs:
            self.logger.error("No viable venues for execution")
            return []
        
        # Route based on strategy
        if strategy == 'best_price':
            return self._route_best_price(venue_costs)
        elif strategy == 'min_cost':
            return self._route_min_cost(venue_costs)
        elif strategy == 'split':
            return self._route_split(venue_costs, amount, symbol, side)
        else:
            self.logger.warning(f"Unknown strategy {strategy}, using best_price")
            return self._route_best_price(venue_costs)
    
    def _route_best_price(self, venue_costs: Dict) -> List[Dict]:
        """Route to venue with best price"""
        best_venue = min(venue_costs.items(), key=lambda x: x[1]['avg_price'])
        
        plan = [{
            'venue_id': best_venue[0],
            'amount': best_venue[1]['amount'],
            'expected_price': best_venue[1]['avg_price'],
            'expected_cost': best_venue[1]['total_cost'],
            'slippage_bps': best_venue[1]['slippage_bps']
        }]
        
        self.execution_stats['total_orders'] += 1
        self.execution_stats['single_venue'] += 1
        
        self.logger.info(
            f"✅ Routed to {best_venue[0]}: "
            f"price=${best_venue[1]['avg_price']:.4f}, "
            f"slippage={best_venue[1]['slippage_bps']:.1f}bps"
        )
        
        return plan
    
    def _route_min_cost(self, venue_costs: Dict) -> List[Dict]:
        """Route to venue with minimum total cost (price + fees + slippage)"""
        best_venue = min(venue_costs.items(), key=lambda x: x[1]['total_cost'])
        
        plan = [{
            'venue_id': best_venue[0],
            'amount': best_venue[1]['amount'],
            'expected_price': best_venue[1]['avg_price'],
            'expected_cost': best_venue[1]['total_cost'],
            'slippage_bps': best_venue[1]['slippage_bps']
        }]
        
        self.execution_stats['total_orders'] += 1
        self.execution_stats['single_venue'] += 1
        
        return plan
    
    def _route_split(self, venue_costs: Dict, total_amount: float,
                     symbol: str, side: str) -> List[Dict]:
        """
        Split order across multiple venues
        
        Uses a simple heuristic: allocate proportional to liquidity/cost
        """
        # Sort venues by cost
        sorted_venues = sorted(venue_costs.items(), key=lambda x: x[1]['total_cost'])
        
        # For simplicity, split between top 2 venues
        if len(sorted_venues) < 2:
            return self._route_best_price(venue_costs)
        
        venue1_id, venue1_cost = sorted_venues[0]
        venue2_id, venue2_cost = sorted_venues[1]
        
        # Allocate 70% to best venue, 30% to second best
        amount1 = total_amount * 0.7
        amount2 = total_amount * 0.3
        
        # Re-estimate costs for partial amounts with correct side
        cost1 = self.estimate_execution_cost(venue1_id, symbol, side, amount1)
        cost2 = self.estimate_execution_cost(venue2_id, symbol, side, amount2)
        
        if not cost1.get('viable') or not cost2.get('viable'):
            # Fallback to single venue
            return self._route_best_price(venue_costs)
        
        plan = [
            {
                'venue_id': venue1_id,
                'amount': amount1,
                'expected_price': cost1['avg_price'],
                'expected_cost': cost1['total_cost'],
                'slippage_bps': cost1['slippage_bps']
            },
            {
                'venue_id': venue2_id,
                'amount': amount2,
                'expected_price': cost2['avg_price'],
                'expected_cost': cost2['total_cost'],
                'slippage_bps': cost2['slippage_bps']
            }
        ]
        
        self.execution_stats['total_orders'] += 1
        self.execution_stats['multi_venue'] += 1
        
        self.logger.info(
            f"✅ Split routing: {amount1:.4f} @ {venue1_id}, "
            f"{amount2:.4f} @ {venue2_id}"
        )
        
        return plan
    
    def execute_routing_plan(self, symbol: str, side: str,
                            routing_plan: List[Dict],
                            order_type: str = 'limit') -> List[Dict]:
        """
        Execute a routing plan
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            routing_plan: Plan from route_order()
            order_type: 'limit' or 'market'
        
        Returns:
            List of order results
        """
        results = []
        
        for plan in routing_plan:
            venue_id = plan['venue_id']
            amount = plan['amount']
            expected_price = plan.get('expected_price')
            
            connector = self.venue_manager.get_venue(venue_id)
            if not connector:
                self.logger.error(f"Venue {venue_id} not found")
                continue
            
            try:
                if order_type == 'limit':
                    # Place limit order at expected price
                    order = connector.place_limit_order(
                        symbol, side, expected_price, amount, post_only=False
                    )
                else:
                    # Place market order
                    order = connector.place_market_order(symbol, side, amount)
                
                results.append({
                    'venue_id': venue_id,
                    'order': order,
                    'plan': plan,
                    'success': bool(order.get('order_id'))
                })
                
                if order.get('order_id'):
                    self.logger.info(
                        f"✅ Order placed on {venue_id}: {order['order_id']}"
                    )
                else:
                    self.logger.error(f"❌ Failed to place order on {venue_id}")
            
            except Exception as e:
                self.logger.error(f"Error placing order on {venue_id}: {e}")
                results.append({
                    'venue_id': venue_id,
                    'plan': plan,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def get_stats(self) -> Dict:
        """Get SOR statistics"""
        return {
            'total_orders_routed': self.execution_stats['total_orders'],
            'single_venue_orders': self.execution_stats['single_venue'],
            'multi_venue_orders': self.execution_stats['multi_venue'],
            'total_estimated_savings': self.execution_stats['total_savings']
        }
