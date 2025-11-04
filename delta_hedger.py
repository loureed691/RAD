"""
Delta Hedging System for Market Making

Maintains near-flat delta exposure by automatically hedging inventory.
This is critical for market makers to avoid directional risk.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger


class DeltaHedger:
    """
    Automatic delta hedging system to maintain market-neutral positions.
    
    For market makers, the goal is to earn spread without taking directional bets.
    This hedger automatically offsets inventory to keep net delta near zero.
    
    Features:
    - Threshold-based hedging (only hedge when inventory exceeds threshold)
    - Cost-aware hedging (considers transaction costs)
    - Smart timing (waits for favorable prices when possible)
    - Multiple hedging strategies (immediate, TWAP, opportunistic)
    """
    
    def __init__(self,
                 hedge_threshold: float = 1.0,
                 target_delta: float = 0.0,
                 hedge_ratio: float = 0.8,
                 min_hedge_size: float = 0.1,
                 max_hedge_latency: float = 60.0,
                 transaction_cost: float = 0.0005):
        """
        Initialize delta hedger
        
        Args:
            hedge_threshold: Minimum inventory to trigger hedge (in base units)
            target_delta: Target delta (usually 0 for market neutral)
            hedge_ratio: Fraction of inventory to hedge (0-1)
            min_hedge_size: Minimum hedge size (avoid tiny hedges)
            max_hedge_latency: Maximum time before forced hedge (seconds)
            transaction_cost: Estimated transaction cost (fraction)
        """
        self.hedge_threshold = hedge_threshold
        self.target_delta = target_delta
        self.hedge_ratio = hedge_ratio
        self.min_hedge_size = min_hedge_size
        self.max_hedge_latency = max_hedge_latency
        self.transaction_cost = transaction_cost
        
        # State tracking
        self.current_inventory = 0.0
        self.pending_hedges = []
        self.hedge_history = []
        self.last_hedge_time = None
        self.threshold_breached_time = None
        
        # Performance metrics
        self.total_hedges = 0
        self.total_hedge_pnl = 0.0
        self.total_hedge_costs = 0.0
        
        self.logger = Logger.get_logger()
        self.logger.info("🛡️ Delta Hedger initialized")
        self.logger.info(f"   Hedge threshold: {self.hedge_threshold}")
        self.logger.info(f"   Target delta: {self.target_delta}")
        self.logger.info(f"   Hedge ratio: {self.hedge_ratio*100:.0f}%")
    
    def update_inventory(self, inventory: float):
        """
        Update current inventory
        
        Args:
            inventory: Current inventory position
        """
        self.current_inventory = inventory
        
        # Check if threshold breached
        inventory_deviation = abs(inventory - self.target_delta)
        
        if inventory_deviation > self.hedge_threshold:
            if self.threshold_breached_time is None:
                self.threshold_breached_time = datetime.now()
                self.logger.info(
                    f"⚠️ Hedge threshold breached: inventory={inventory:.4f}, "
                    f"threshold={self.hedge_threshold:.4f}"
                )
        else:
            self.threshold_breached_time = None
    
    def should_hedge(self) -> bool:
        """
        Determine if we should hedge now
        
        Returns:
            True if hedging is needed
        """
        inventory_deviation = abs(self.current_inventory - self.target_delta)
        
        # Check threshold
        if inventory_deviation < self.hedge_threshold:
            return False
        
        # Check if we have pending hedges
        if self.pending_hedges:
            return False
        
        # Check forced hedge due to latency
        if self.threshold_breached_time is not None:
            time_since_breach = (datetime.now() - self.threshold_breached_time).total_seconds()
            if time_since_breach > self.max_hedge_latency:
                self.logger.warning(
                    f"⏰ Forced hedge due to latency: {time_since_breach:.1f}s > "
                    f"{self.max_hedge_latency:.1f}s"
                )
                return True
        
        return True
    
    def calculate_hedge_size(self) -> Tuple[float, str]:
        """
        Calculate optimal hedge size and side
        
        Returns:
            Tuple of (hedge_size, side) where side is 'buy' or 'sell'
        """
        inventory_deviation = self.current_inventory - self.target_delta
        
        # Hedge to bring inventory closer to target
        hedge_size = abs(inventory_deviation) * self.hedge_ratio
        
        # Ensure minimum size
        if hedge_size < self.min_hedge_size:
            return 0.0, None
        
        # Determine side (opposite of current position)
        if inventory_deviation > 0:
            # We're long, need to sell
            side = 'sell'
        else:
            # We're short, need to buy
            side = 'buy'
        
        return hedge_size, side
    
    def get_hedge_recommendation(self, current_price: float,
                                microprice: Optional[float] = None) -> Optional[Dict]:
        """
        Get hedge recommendation with timing and execution strategy
        
        Args:
            current_price: Current market price
            microprice: Microprice if available (better reference)
        
        Returns:
            Hedge recommendation dict or None
        """
        if not self.should_hedge():
            return None
        
        hedge_size, side = self.calculate_hedge_size()
        
        if hedge_size == 0 or side is None:
            return None
        
        # Use microprice if available, otherwise mid price
        ref_price = microprice if microprice is not None else current_price
        
        # Estimate cost
        estimated_cost = hedge_size * ref_price * self.transaction_cost
        
        # Determine urgency
        inventory_deviation = abs(self.current_inventory - self.target_delta)
        urgency_ratio = inventory_deviation / self.hedge_threshold
        
        if urgency_ratio > 3.0:
            urgency = 'critical'
            strategy = 'market'
        elif urgency_ratio > 2.0:
            urgency = 'high'
            strategy = 'aggressive_limit'
        elif urgency_ratio > 1.5:
            urgency = 'medium'
            strategy = 'limit'
        else:
            urgency = 'low'
            strategy = 'opportunistic'
        
        # Calculate limit price with slippage tolerance
        if side == 'buy':
            if strategy == 'market':
                limit_price = ref_price * 1.001  # 0.1% slippage tolerance
            elif strategy == 'aggressive_limit':
                limit_price = ref_price * 1.0005
            else:
                limit_price = ref_price * 0.9995  # Try to get a better price
        else:  # sell
            if strategy == 'market':
                limit_price = ref_price * 0.999
            elif strategy == 'aggressive_limit':
                limit_price = ref_price * 0.9995
            else:
                limit_price = ref_price * 1.0005
        
        recommendation = {
            'hedge_size': hedge_size,
            'side': side,
            'urgency': urgency,
            'strategy': strategy,
            'limit_price': limit_price,
            'estimated_cost': estimated_cost,
            'current_inventory': self.current_inventory,
            'target_inventory': self.target_delta,
            'inventory_deviation': inventory_deviation,
            'timestamp': datetime.now()
        }
        
        self.logger.info(
            f"💱 Hedge recommendation: {side} {hedge_size:.4f} @ ${limit_price:.4f} "
            f"(urgency: {urgency}, strategy: {strategy})"
        )
        
        return recommendation
    
    def record_hedge(self, hedge_size: float, side: str, price: float,
                    cost: float, pnl: float = 0.0):
        """
        Record a completed hedge
        
        Args:
            hedge_size: Size of hedge executed
            side: 'buy' or 'sell'
            price: Execution price
            cost: Transaction cost
            pnl: Realized P&L from hedge (if any)
        """
        hedge_record = {
            'timestamp': datetime.now(),
            'size': hedge_size,
            'side': side,
            'price': price,
            'cost': cost,
            'pnl': pnl,
            'inventory_before': self.current_inventory,
            'inventory_after': self.current_inventory + (hedge_size if side == 'buy' else -hedge_size)
        }
        
        self.hedge_history.append(hedge_record)
        self.total_hedges += 1
        self.total_hedge_pnl += pnl
        self.total_hedge_costs += cost
        self.last_hedge_time = datetime.now()
        
        # Update inventory
        if side == 'buy':
            self.current_inventory += hedge_size
        else:
            self.current_inventory -= hedge_size
        
        self.logger.info(
            f"✅ Hedge executed: {side} {hedge_size:.4f} @ ${price:.4f}, "
            f"cost=${cost:.4f}, new_inventory={self.current_inventory:.4f}"
        )
    
    def get_hedge_metrics(self) -> Dict:
        """
        Get hedging performance metrics
        
        Returns:
            Dictionary of hedge metrics
        """
        avg_hedge_cost = self.total_hedge_costs / self.total_hedges if self.total_hedges > 0 else 0
        net_hedge_pnl = self.total_hedge_pnl - self.total_hedge_costs
        
        return {
            'current_inventory': self.current_inventory,
            'target_inventory': self.target_delta,
            'inventory_deviation': abs(self.current_inventory - self.target_delta),
            'is_hedged': abs(self.current_inventory - self.target_delta) < self.hedge_threshold,
            'total_hedges': self.total_hedges,
            'total_hedge_pnl': self.total_hedge_pnl,
            'total_hedge_costs': self.total_hedge_costs,
            'net_hedge_pnl': net_hedge_pnl,
            'avg_hedge_cost': avg_hedge_cost,
            'last_hedge_time': self.last_hedge_time,
            'pending_hedges': len(self.pending_hedges)
        }
    
    def reset(self):
        """Reset hedger state"""
        self.current_inventory = 0.0
        self.pending_hedges = []
        self.threshold_breached_time = None
        self.logger.info("🔄 Delta hedger reset")


class CrossVenueDeltaHedger(DeltaHedger):
    """
    Enhanced delta hedger that can hedge across multiple venues.
    
    This is useful for basis/funding arbitrage where you might be
    long on one venue and short on another.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.venue_inventories = {}  # venue_id -> inventory
        self.logger.info("🌐 Cross-venue delta hedger initialized")
    
    def update_venue_inventory(self, venue_id: str, inventory: float):
        """
        Update inventory for a specific venue
        
        Args:
            venue_id: Venue identifier
            inventory: Inventory at that venue
        """
        self.venue_inventories[venue_id] = inventory
        
        # Calculate total inventory across all venues
        total_inventory = sum(self.venue_inventories.values())
        self.update_inventory(total_inventory)
    
    def get_venue_inventories(self) -> Dict[str, float]:
        """Get inventory breakdown by venue"""
        return self.venue_inventories.copy()
    
    def suggest_venue_hedge(self) -> Optional[Dict]:
        """
        Suggest which venue to hedge on based on current positions
        
        Returns:
            Hedge suggestion with venue information
        """
        if not self.venue_inventories:
            return None
        
        # Find venue with largest absolute inventory
        max_inventory_venue = max(
            self.venue_inventories.items(),
            key=lambda x: abs(x[1])
        )
        
        venue_id, inventory = max_inventory_venue
        
        if abs(inventory) < self.hedge_threshold:
            return None
        
        hedge_size, side = self.calculate_hedge_size()
        
        if hedge_size == 0:
            return None
        
        return {
            'venue_id': venue_id,
            'hedge_size': hedge_size,
            'side': side,
            'current_venue_inventory': inventory,
            'total_inventory': self.current_inventory
        }
