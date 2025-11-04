"""
Avellaneda-Stoikov Market Making Strategy

Implements the seminal market making model from:
"High-frequency trading in a limit order book" by Avellaneda & Stoikov (2008)

Key Features:
- Dynamic bid/ask spread based on inventory and volatility
- Risk-averse optimal quoting
- Inventory management with target position
- Integration with microstructure signals
"""
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from logger import Logger


class AvellanedaStoikovMarketMaker:
    """
    Avellaneda-Stoikov optimal market making strategy
    
    The model computes optimal bid/ask quotes around a reference price
    to maximize expected utility while managing inventory risk.
    
    Key parameters:
    - gamma: Risk aversion parameter (higher = more conservative)
    - k: Order book liquidity parameter (market depth)
    - T: Time horizon until end of trading period
    - sigma: Volatility of the underlying asset
    """
    
    def __init__(self,
                 risk_aversion: float = 0.1,
                 terminal_time: float = 1.0,
                 dt: float = 1/252,  # Daily increment
                 target_inventory: float = 0.0,
                 max_inventory: float = 10.0,
                 min_spread: float = 0.0001,
                 max_spread: float = 0.01):
        """
        Initialize Avellaneda-Stoikov market maker
        
        Args:
            risk_aversion: Risk aversion parameter gamma (typical: 0.01-1.0)
            terminal_time: Time horizon T in years (e.g., 1.0 = 1 year)
            dt: Time increment (e.g., 1/252 for daily)
            target_inventory: Target inventory level (usually 0 for market neutral)
            max_inventory: Maximum allowed inventory deviation
            min_spread: Minimum bid-ask spread (to ensure profitability)
            max_spread: Maximum bid-ask spread (to stay competitive)
        """
        self.gamma = risk_aversion
        self.T = terminal_time
        self.dt = dt
        self.target_inventory = target_inventory
        self.max_inventory = max_inventory
        self.min_spread = min_spread
        self.max_spread = max_spread
        
        # State variables
        self.current_inventory = 0.0
        self.current_time = 0.0
        self.reference_price = None
        self.volatility = None
        self.order_book_liquidity = 1.0  # k parameter
        
        # Microstructure enhancements
        self.microprice = None
        self.order_flow_imbalance = 0.0
        self.kyle_lambda = 0.0  # Price impact coefficient
        self.short_vol = None
        
        # Performance tracking
        self.quotes_generated = 0
        self.inventory_history = []
        self.pnl_history = []
        self.last_update_time = datetime.now()
        
        self.logger = Logger.get_logger()
        self.logger.info("📊 Avellaneda-Stoikov Market Maker initialized")
        self.logger.info(f"   Risk aversion (γ): {self.gamma}")
        self.logger.info(f"   Terminal time (T): {self.T} years")
        self.logger.info(f"   Target inventory: {self.target_inventory}")
        self.logger.info(f"   Max inventory: ±{self.max_inventory}")
    
    def update_market_data(self,
                          mid_price: float,
                          volatility: float,
                          inventory: float,
                          microprice: Optional[float] = None,
                          order_flow_imbalance: float = 0.0,
                          kyle_lambda: float = 0.0,
                          short_volatility: Optional[float] = None):
        """
        Update market data and microstructure signals
        
        Args:
            mid_price: Current mid-market price
            volatility: Estimated volatility (annualized)
            inventory: Current inventory position
            microprice: Microprice from order book (if available)
            order_flow_imbalance: Order flow/queue imbalance (-1 to 1)
            kyle_lambda: Kyle's lambda (price impact coefficient)
            short_volatility: Short-horizon volatility estimate
        """
        self.reference_price = microprice if microprice is not None else mid_price
        self.volatility = short_volatility if short_volatility is not None else volatility
        self.current_inventory = inventory
        self.microprice = microprice
        self.order_flow_imbalance = order_flow_imbalance
        self.kyle_lambda = kyle_lambda
        self.short_vol = short_volatility
        
        # Update time (simplified - in practice would track actual time)
        now = datetime.now()
        time_elapsed = (now - self.last_update_time).total_seconds() / (365.25 * 24 * 3600)
        self.current_time += time_elapsed
        self.last_update_time = now
        
        # Reset time if we've exceeded terminal time
        if self.current_time >= self.T:
            self.current_time = 0.0
    
    def compute_reservation_price(self) -> float:
        """
        Compute reservation price (indifference price)
        
        r = s - q * γ * σ² * (T - t)
        
        where:
        - s = reference price (mid or microprice)
        - q = current inventory
        - γ = risk aversion
        - σ = volatility
        - T - t = time remaining
        
        Returns:
            Reservation price
        """
        if self.reference_price is None or self.volatility is None:
            return None
        
        time_remaining = max(self.T - self.current_time, self.dt)
        inventory_deviation = self.current_inventory - self.target_inventory
        
        # Classical A-S reservation price
        reservation_price = (
            self.reference_price 
            - inventory_deviation * self.gamma * (self.volatility ** 2) * time_remaining
        )
        
        # Microstructure adjustment: incorporate order flow imbalance
        # Positive OFI (more buying) -> increase reservation price
        ofi_adjustment = self.order_flow_imbalance * 0.1 * self.reference_price * self.volatility
        reservation_price += ofi_adjustment
        
        return reservation_price
    
    def compute_optimal_spread(self) -> float:
        """
        Compute optimal half-spread
        
        δ = γ * σ² * (T - t) + (2/γ) * ln(1 + γ/k)
        
        Simplified approximation:
        δ ≈ γ * σ² * (T - t) + 2/k  (when γ/k is small)
        
        Returns:
            Optimal half-spread
        """
        if self.volatility is None:
            return self.min_spread / 2
        
        time_remaining = max(self.T - self.current_time, self.dt)
        
        # Classical A-S spread component
        spread_term1 = self.gamma * (self.volatility ** 2) * time_remaining
        
        # Order book liquidity component
        spread_term2 = 2.0 / self.order_book_liquidity
        
        half_spread = spread_term1 + spread_term2
        
        # Microstructure enhancement: adjust for Kyle's lambda (price impact)
        # Higher impact -> wider spread to compensate
        impact_adjustment = abs(self.kyle_lambda) * abs(self.current_inventory) * 0.5
        half_spread += impact_adjustment
        
        # Volatility regime adjustment: widen spread in high short-term vol
        if self.short_vol is not None and self.volatility > 0:
            vol_ratio = self.short_vol / self.volatility
            if vol_ratio > 1.5:  # Short-term vol spike
                half_spread *= (1.0 + 0.3 * (vol_ratio - 1.0))
        
        # Ensure spread is within bounds
        half_spread = max(self.min_spread / 2, min(half_spread, self.max_spread / 2))
        
        return half_spread
    
    def compute_quotes(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Compute optimal bid and ask quotes
        
        bid = r - δ
        ask = r + δ
        
        where:
        - r = reservation price
        - δ = optimal half-spread
        
        Returns:
            Tuple of (bid_price, ask_price)
        """
        reservation_price = self.compute_reservation_price()
        if reservation_price is None:
            return None, None
        
        half_spread = self.compute_optimal_spread()
        
        bid_price = reservation_price - half_spread
        ask_price = reservation_price + half_spread
        
        # Inventory skew: if we're long, shade quotes to sell; if short, shade to buy
        inventory_skew = self.compute_inventory_skew()
        bid_price *= (1 - inventory_skew)
        ask_price *= (1 + inventory_skew)
        
        self.quotes_generated += 1
        
        # Logging
        if self.quotes_generated % 100 == 0:
            self.logger.debug(
                f"A-S Quotes: bid=${bid_price:.4f}, ask=${ask_price:.4f}, "
                f"spread={2*half_spread*100:.3f}%, inventory={self.current_inventory:.2f}, "
                f"r=${reservation_price:.4f}"
            )
        
        return bid_price, ask_price
    
    def compute_inventory_skew(self) -> float:
        """
        Compute inventory-based quote skew
        
        When inventory is positive (long), skew quotes to facilitate selling.
        When inventory is negative (short), skew quotes to facilitate buying.
        
        Returns:
            Skew factor (0 to 0.1 typical)
        """
        if self.max_inventory <= 0:
            return 0.0
        
        inventory_deviation = self.current_inventory - self.target_inventory
        normalized_inventory = inventory_deviation / self.max_inventory
        
        # Cap at ±1
        normalized_inventory = max(-1.0, min(1.0, normalized_inventory))
        
        # Apply non-linear skew (quadratic to avoid excessive skewing)
        skew = 0.05 * normalized_inventory * abs(normalized_inventory)
        
        return skew
    
    def should_quote_side(self, side: str) -> bool:
        """
        Determine if we should quote on a given side based on inventory limits
        
        Args:
            side: 'bid' or 'ask'
        
        Returns:
            True if we should quote on this side
        """
        inventory_deviation = self.current_inventory - self.target_inventory
        
        if side == 'bid':
            # Don't bid if we're at max long inventory
            if inventory_deviation >= self.max_inventory:
                return False
        elif side == 'ask':
            # Don't ask if we're at max short inventory
            if inventory_deviation <= -self.max_inventory:
                return False
        
        return True
    
    def update_inventory(self, trade_quantity: float, trade_price: float):
        """
        Update inventory after a trade
        
        Args:
            trade_quantity: Quantity traded (positive for buy, negative for sell)
            trade_price: Execution price
        """
        self.current_inventory += trade_quantity
        self.inventory_history.append({
            'timestamp': datetime.now(),
            'inventory': self.current_inventory,
            'price': trade_price
        })
        
        # Log significant inventory changes
        if abs(trade_quantity) > self.max_inventory * 0.2:
            self.logger.info(
                f"📦 Inventory update: {trade_quantity:+.4f} @ ${trade_price:.4f}, "
                f"new inventory: {self.current_inventory:.4f}"
            )
    
    def get_position_value(self, current_price: float) -> float:
        """
        Calculate current position value
        
        Args:
            current_price: Current market price
        
        Returns:
            Position value in quote currency
        """
        return self.current_inventory * current_price
    
    def get_metrics(self) -> Dict:
        """
        Get current market making metrics
        
        Returns:
            Dictionary of performance metrics
        """
        return {
            'inventory': self.current_inventory,
            'inventory_deviation': self.current_inventory - self.target_inventory,
            'inventory_utilization': abs(self.current_inventory - self.target_inventory) / self.max_inventory if self.max_inventory > 0 else 0,
            'quotes_generated': self.quotes_generated,
            'current_time': self.current_time,
            'time_remaining': max(0, self.T - self.current_time),
            'risk_aversion': self.gamma,
            'reference_price': self.reference_price,
            'volatility': self.volatility,
            'microprice': self.microprice,
            'order_flow_imbalance': self.order_flow_imbalance,
            'kyle_lambda': self.kyle_lambda
        }
    
    def reset(self):
        """Reset the market maker state"""
        self.current_inventory = 0.0
        self.current_time = 0.0
        self.quotes_generated = 0
        self.inventory_history = []
        self.pnl_history = []
        self.last_update_time = datetime.now()
        
        self.logger.info("🔄 Avellaneda-Stoikov market maker reset")
