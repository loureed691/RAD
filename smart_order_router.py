"""
Smart Order Router (SOR)

Intelligent order routing to achieve best execution across multiple venues.

Features:
- Multi-venue price comparison
- Liquidity analysis across exchanges
- Order splitting for large trades
- Transaction cost analysis (TCA)
- Adaptive routing based on market conditions
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from logger import Logger


class Venue:
    """Represents a trading venue (exchange)."""
    
    def __init__(
        self,
        name: str,
        bid: float,
        ask: float,
        bid_size: float,
        ask_size: float,
        fee: float = 0.001,  # 0.1% default
        latency_ms: float = 50.0
    ):
        """
        Initialize venue.
        
        Args:
            name: Venue name
            bid: Best bid price
            ask: Best ask price
            bid_size: Size available at bid
            ask_size: Size available at ask
            fee: Trading fee (as decimal)
            latency_ms: Expected latency in milliseconds
        """
        self.name = name
        self.bid = bid
        self.ask = ask
        self.bid_size = bid_size
        self.ask_size = ask_size
        self.fee = fee
        self.latency_ms = latency_ms
        self.mid_price = (bid + ask) / 2
        self.spread = ask - bid
        self.spread_bps = (self.spread / self.mid_price) * 10000 if self.mid_price > 0 else 0


class SmartOrderRouter:
    """
    Smart Order Router for optimal execution across venues.
    
    Routes orders to achieve best net execution price considering:
    - Price
    - Liquidity
    - Fees
    - Latency
    - Market impact
    """
    
    def __init__(
        self,
        enable_order_splitting: bool = True,
        max_venues_per_order: int = 3,
        latency_weight: float = 0.1,
        min_venue_allocation_pct: float = 0.05  # 5% minimum
    ):
        """
        Initialize Smart Order Router.
        
        Args:
            enable_order_splitting: Allow splitting orders across venues
            max_venues_per_order: Maximum number of venues to use for one order
            latency_weight: Weight for latency in routing decision (0-1)
            min_venue_allocation_pct: Minimum allocation per venue (as fraction)
        """
        self.enable_order_splitting = enable_order_splitting
        self.max_venues_per_order = max_venues_per_order
        self.latency_weight = latency_weight
        self.min_venue_allocation_pct = min_venue_allocation_pct
        
        self.logger = Logger.get_logger()
        
        # Statistics
        self.total_orders_routed = 0
        self.total_savings_bps = 0.0
        
        self.logger.info("🧭 Smart Order Router Initialized")
        self.logger.info(f"   Order Splitting: {'Enabled' if enable_order_splitting else 'Disabled'}")
        self.logger.info(f"   Max Venues/Order: {max_venues_per_order}")
        self.logger.info(f"   Latency Weight: {latency_weight:.2f}")
    
    # Slippage factor for price impact estimation
    SLIPPAGE_FACTOR = 0.001  # 0.1% per 1x overflow
    
    def calculate_effective_price(
        self,
        venue: Venue,
        side: str,
        size: float
    ) -> Dict:
        """
        Calculate effective price including fees and available liquidity.
        
        Args:
            venue: Venue object
            side: 'buy' or 'sell'
            size: Order size
            
        Returns:
            Dictionary with effective price and execution details
        """
        if side.lower() == 'buy':
            base_price = venue.ask
            available_size = venue.ask_size
        else:
            base_price = venue.bid
            available_size = venue.bid_size
        
        # Check if venue has enough liquidity
        can_fill = size <= available_size
        fillable_size = min(size, available_size)
        
        # Calculate price after fees
        if side.lower() == 'buy':
            effective_price = base_price * (1 + venue.fee)
        else:
            effective_price = base_price * (1 - venue.fee)
        
        # Estimate slippage for large orders (simple model)
        size_ratio = size / available_size if available_size > 0 else 1.0
        if size_ratio > 1.0:
            # Order larger than available - significant slippage expected
            slippage_factor = 1 + (size_ratio - 1) * self.SLIPPAGE_FACTOR
            if side.lower() == 'buy':
                effective_price *= slippage_factor
            else:
                effective_price /= slippage_factor
        
        return {
            'venue': venue.name,
            'base_price': base_price,
            'effective_price': effective_price,
            'fee': venue.fee,
            'fee_amount': base_price * venue.fee * fillable_size,
            'fillable_size': fillable_size,
            'can_fill_completely': can_fill,
            'latency_ms': venue.latency_ms,
            'spread_bps': venue.spread_bps
        }
    
    def find_best_venue(
        self,
        venues: List[Venue],
        side: str,
        size: float
    ) -> Tuple[Venue, Dict]:
        """
        Find single best venue for execution.
        
        Args:
            venues: List of available venues
            side: 'buy' or 'sell'
            size: Order size
            
        Returns:
            Tuple of (best_venue, execution_details)
        """
        best_venue = None
        best_score = float('-inf') if side.lower() == 'buy' else float('inf')
        best_details = None
        
        for venue in venues:
            details = self.calculate_effective_price(venue, side, size)
            effective_price = details['effective_price']
            
            # Score = effective price adjusted for latency
            # For buys: lower is better
            # For sells: higher is better
            latency_penalty = venue.latency_ms * self.latency_weight * 0.0001  # Small penalty
            
            if side.lower() == 'buy':
                score = effective_price * (1 + latency_penalty)
                if score < best_score or best_venue is None:
                    best_score = score
                    best_venue = venue
                    best_details = details
            else:
                score = effective_price * (1 - latency_penalty)
                if score > best_score or best_venue is None:
                    best_score = score
                    best_venue = venue
                    best_details = details
        
        return best_venue, best_details
    
    def route_order_split(
        self,
        venues: List[Venue],
        side: str,
        size: float
    ) -> List[Dict]:
        """
        Route order with splitting across multiple venues.
        
        Allocates order across venues to minimize total cost.
        
        Args:
            venues: List of available venues
            side: 'buy' or 'sell'
            size: Total order size
            
        Returns:
            List of allocations per venue
        """
        remaining_size = size
        allocations = []
        
        # Sort venues by effective price
        venue_scores = []
        for venue in venues:
            details = self.calculate_effective_price(venue, side, size)
            venue_scores.append({
                'venue': venue,
                'details': details,
                'effective_price': details['effective_price']
            })
        
        # Sort: lowest price for buys, highest for sells
        reverse = side.lower() == 'sell'
        venue_scores.sort(key=lambda x: x['effective_price'], reverse=reverse)
        
        # Allocate to venues in order of best price
        for i, item in enumerate(venue_scores):
            if i >= self.max_venues_per_order:
                break
            
            if remaining_size <= 0:
                break
            
            venue = item['venue']
            details = item['details']
            
            # Allocate up to available liquidity
            allocation_size = min(remaining_size, details['fillable_size'])
            
            # Ensure minimum allocation size
            min_size = size * self.min_venue_allocation_pct
            if allocation_size < min_size and remaining_size >= min_size:
                allocation_size = min(min_size, remaining_size)
            
            if allocation_size > 0:
                allocations.append({
                    'venue': venue.name,
                    'size': allocation_size,
                    'price': details['effective_price'],
                    'fee': details['fee_amount'],
                    'allocation_pct': (allocation_size / size) * 100
                })
                
                remaining_size -= allocation_size
        
        # If we couldn't fill completely, note it
        if remaining_size > 0.01:  # Small threshold for rounding
            self.logger.warning(
                f"⚠️  Could not fill complete order: {remaining_size:.4f} remaining of {size:.4f}"
            )
        
        return allocations
    
    def route_order(
        self,
        venues: List[Venue],
        side: str,
        size: float,
        symbol: str = "UNKNOWN"
    ) -> Dict:
        """
        Route order to best execution venue(s).
        
        Args:
            venues: List of available venues
            side: 'buy' or 'sell'
            size: Order size
            symbol: Trading symbol
            
        Returns:
            Dictionary with routing decision
        """
        if not venues:
            return {
                'success': False,
                'error': 'No venues available',
                'symbol': symbol,
                'side': side,
                'size': size
            }
        
        # Determine routing strategy
        if self.enable_order_splitting and len(venues) > 1:
            # Try split routing
            allocations = self.route_order_split(venues, side, size)
            
            if not allocations:
                return {
                    'success': False,
                    'error': 'Could not allocate order to any venue',
                    'symbol': symbol,
                    'side': side,
                    'size': size
                }
            
            # Calculate weighted average price
            total_cost = sum(alloc['size'] * alloc['price'] for alloc in allocations)
            total_size_allocated = sum(alloc['size'] for alloc in allocations)
            avg_price = total_cost / total_size_allocated if total_size_allocated > 0 else 0
            
            routing_decision = {
                'success': True,
                'strategy': 'split',
                'symbol': symbol,
                'side': side,
                'size': size,
                'size_allocated': total_size_allocated,
                'fill_rate': total_size_allocated / size if size > 0 else 0,
                'allocations': allocations,
                'num_venues': len(allocations),
                'weighted_avg_price': avg_price,
                'total_fees': sum(alloc['fee'] for alloc in allocations),
                'timestamp': datetime.now()
            }
        else:
            # Single venue routing
            best_venue, details = self.find_best_venue(venues, side, size)
            
            if best_venue is None:
                return {
                    'success': False,
                    'error': 'No suitable venue found',
                    'symbol': symbol,
                    'side': side,
                    'size': size
                }
            
            routing_decision = {
                'success': True,
                'strategy': 'single',
                'symbol': symbol,
                'side': side,
                'size': size,
                'venue': best_venue.name,
                'price': details['effective_price'],
                'fee': details['fee_amount'],
                'fillable_size': details['fillable_size'],
                'can_fill_completely': details['can_fill_completely'],
                'latency_ms': details['latency_ms'],
                'timestamp': datetime.now()
            }
        
        self.total_orders_routed += 1
        
        # Log routing decision
        if routing_decision['strategy'] == 'split':
            self.logger.info(
                f"🧭 SOR: {side.upper()} {size:.4f} {symbol} split across "
                f"{routing_decision['num_venues']} venues @ avg {routing_decision['weighted_avg_price']:.4f}"
            )
        else:
            self.logger.info(
                f"🧭 SOR: {side.upper()} {size:.4f} {symbol} routed to "
                f"{routing_decision['venue']} @ {routing_decision['price']:.4f}"
            )
        
        return routing_decision
    
    def compare_venues(self, venues: List[Venue]) -> Dict:
        """
        Compare all venues and return analysis.
        
        Args:
            venues: List of venues to compare
            
        Returns:
            Dictionary with comparison metrics
        """
        if not venues:
            return {'error': 'No venues provided'}
        
        venue_comparison = []
        
        for venue in venues:
            venue_comparison.append({
                'name': venue.name,
                'bid': venue.bid,
                'ask': venue.ask,
                'mid': venue.mid_price,
                'spread_bps': venue.spread_bps,
                'bid_size': venue.bid_size,
                'ask_size': venue.ask_size,
                'fee': venue.fee,
                'latency_ms': venue.latency_ms
            })
        
        # Find best bid and ask
        best_bid_venue = max(venues, key=lambda v: v.bid)
        best_ask_venue = min(venues, key=lambda v: v.ask)
        
        return {
            'venues': venue_comparison,
            'best_bid': {
                'venue': best_bid_venue.name,
                'price': best_bid_venue.bid,
                'size': best_bid_venue.bid_size
            },
            'best_ask': {
                'venue': best_ask_venue.name,
                'price': best_ask_venue.ask,
                'size': best_ask_venue.ask_size
            },
            'venue_count': len(venues)
        }
    
    def get_status(self) -> Dict:
        """
        Get router status and statistics.
        
        Returns:
            Dictionary with status
        """
        avg_savings = self.total_savings_bps / self.total_orders_routed if self.total_orders_routed > 0 else 0
        
        return {
            'order_splitting_enabled': self.enable_order_splitting,
            'max_venues_per_order': self.max_venues_per_order,
            'latency_weight': self.latency_weight,
            'total_orders_routed': self.total_orders_routed,
            'average_savings_bps': avg_savings
        }
