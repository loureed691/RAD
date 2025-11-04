"""
Avellaneda-Stoikov Market Making Strategy

Implementation of the seminal market making model from:
"High-frequency trading in a limit order book" by Marco Avellaneda and Sasha Stoikov (2008)

Features:
- Optimal bid/ask spread calculation based on volatility and inventory
- Risk-adjusted quoting with inventory skew
- Dynamic reservation price based on position
- Time-to-expiry aware pricing (T parameter)
"""

import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger


class AvellanedaStoikovStrategy:
    """
    Avellaneda-Stoikov market making strategy with optimal spread and inventory management.
    
    Key parameters:
    - gamma: Risk aversion parameter (higher = wider spreads)
    - sigma: Volatility estimate
    - k: Market order arrival rate parameter
    - T: Time horizon (remaining trading time)
    - q: Current inventory position
    """
    
    def __init__(
        self,
        risk_aversion: float = 0.1,
        time_horizon_minutes: float = 60.0,
        order_arrival_rate: float = 1.0,
        max_inventory: int = 5,
        min_spread_bps: float = 5.0,
        max_spread_bps: float = 100.0
    ):
        """
        Initialize Avellaneda-Stoikov strategy.
        
        Args:
            risk_aversion: Risk aversion parameter gamma (0.01-1.0, higher = more conservative)
            time_horizon_minutes: Trading horizon T in minutes
            order_arrival_rate: Market order arrival rate k (orders per minute)
            max_inventory: Maximum absolute inventory position
            min_spread_bps: Minimum spread in basis points (e.g., 5 = 0.05%)
            max_spread_bps: Maximum spread in basis points (e.g., 100 = 1%)
        """
        self.gamma = risk_aversion
        self.T = time_horizon_minutes * 60  # Convert to seconds
        self.k = order_arrival_rate / 60  # Convert to per-second rate
        self.max_inventory = max_inventory
        self.min_spread = min_spread_bps / 10000  # Convert bps to decimal
        self.max_spread = max_spread_bps / 10000
        
        self.logger = Logger.get_logger()
        
        # State variables
        self.current_inventory = 0
        self.session_start_time = datetime.now()
        self.volatility_estimate = 0.02  # Default 2% volatility
        
        self.logger.info("📊 Avellaneda-Stoikov Market Making Strategy Initialized")
        self.logger.info(f"   Risk aversion (γ): {self.gamma}")
        self.logger.info(f"   Time horizon (T): {time_horizon_minutes} minutes")
        self.logger.info(f"   Order arrival rate (k): {order_arrival_rate} orders/min")
        self.logger.info(f"   Max inventory: ±{self.max_inventory}")
        self.logger.info(f"   Spread range: {min_spread_bps}-{max_spread_bps} bps")
    
    def update_volatility(self, price_history: list, window: int = 20) -> float:
        """
        Update volatility estimate from recent price history.
        
        Args:
            price_history: List of recent prices
            window: Lookback window for volatility calculation
            
        Returns:
            Estimated volatility (annualized)
        """
        if len(price_history) < 2:
            return self.volatility_estimate
        
        prices = np.array(price_history[-window:])
        if len(prices) < 2:
            return self.volatility_estimate
        
        # Calculate log returns
        log_returns = np.diff(np.log(prices))
        
        # Estimate volatility (standard deviation of returns)
        # Annualize assuming 1-minute bars: sqrt(525600) for minutes in a year
        volatility = np.std(log_returns) * np.sqrt(525600)
        
        # Exponential moving average for smoothing
        alpha = 0.1
        self.volatility_estimate = alpha * volatility + (1 - alpha) * self.volatility_estimate
        
        return self.volatility_estimate
    
    def calculate_reservation_price(
        self,
        mid_price: float,
        inventory: int,
        time_remaining: Optional[float] = None
    ) -> float:
        """
        Calculate the reservation price r(s,t,q) which is the indifference price.
        
        r = s - q * gamma * sigma^2 * (T - t)
        
        Where:
        - s: current mid price
        - q: inventory position
        - gamma: risk aversion
        - sigma: volatility
        - (T-t): time remaining
        
        Args:
            mid_price: Current market mid price
            inventory: Current inventory position
            time_remaining: Time remaining in seconds (auto-calculated if None)
            
        Returns:
            Reservation price
        """
        if time_remaining is None:
            elapsed = (datetime.now() - self.session_start_time).total_seconds()
            time_remaining = max(0, self.T - elapsed)
        
        # Reservation price adjustment based on inventory and risk
        adjustment = inventory * self.gamma * (self.volatility_estimate ** 2) * time_remaining
        reservation_price = mid_price - adjustment
        
        return reservation_price
    
    def calculate_optimal_spread(
        self,
        mid_price: float,
        time_remaining: Optional[float] = None
    ) -> float:
        """
        Calculate optimal half-spread δ*.
        
        δ* = (γ * σ^2 * (T-t) + (2/γ) * ln(1 + γ/k)) / 2
        
        Simplified approximation when γ/k is small:
        δ* ≈ γ * σ^2 * (T-t) / 2 + 1/k
        
        Args:
            mid_price: Current market mid price
            time_remaining: Time remaining in seconds
            
        Returns:
            Optimal half-spread (in price units)
        """
        if time_remaining is None:
            elapsed = (datetime.now() - self.session_start_time).total_seconds()
            time_remaining = max(0, self.T - elapsed)
        
        # Bounds checking for numerical stability
        if self.gamma <= 0 or self.k <= 0:
            self.logger.warning(f"Invalid parameters: gamma={self.gamma}, k={self.k}")
            return self.min_spread * mid_price
        
        # Prevent numerical overflow in log calculation
        gamma_over_k = self.gamma / self.k
        if gamma_over_k > 100:
            # Use approximation for large gamma/k
            term2 = (2 / self.gamma) * np.log(gamma_over_k)
        else:
            term2 = (2 / self.gamma) * np.log(1 + gamma_over_k)
        
        # Calculate optimal spread using the AS formula
        term1 = self.gamma * (self.volatility_estimate ** 2) * time_remaining
        
        half_spread = (term1 + term2) / 2
        
        # Convert to price units
        half_spread_price = half_spread * mid_price
        
        # Apply min/max constraints
        min_half_spread = self.min_spread * mid_price
        max_half_spread = self.max_spread * mid_price
        half_spread_price = np.clip(half_spread_price, min_half_spread, max_half_spread)
        
        return half_spread_price
    
    def calculate_quotes(
        self,
        mid_price: float,
        inventory: int,
        price_history: Optional[list] = None
    ) -> Dict[str, float]:
        """
        Calculate optimal bid and ask quotes based on AS model.
        
        bid = r - δ*
        ask = r + δ*
        
        Where r is the reservation price and δ* is the optimal half-spread.
        
        Args:
            mid_price: Current market mid price
            inventory: Current inventory position
            price_history: Recent price history for volatility estimation
            
        Returns:
            Dictionary with bid, ask, mid, spread, and reservation price
        """
        # Update volatility if price history provided
        if price_history and len(price_history) > 0:
            self.update_volatility(price_history)
        
        # Calculate time remaining
        elapsed = (datetime.now() - self.session_start_time).total_seconds()
        time_remaining = max(0, self.T - elapsed)
        
        # Calculate reservation price (indifference price with inventory risk)
        reservation_price = self.calculate_reservation_price(
            mid_price, inventory, time_remaining
        )
        
        # Calculate optimal spread
        half_spread = self.calculate_optimal_spread(mid_price, time_remaining)
        
        # Calculate bid and ask
        bid_price = reservation_price - half_spread
        ask_price = reservation_price + half_spread
        
        # Inventory-based skew factor (makes quotes more aggressive when away from target)
        inventory_ratio = inventory / self.max_inventory if self.max_inventory > 0 else 0
        skew = inventory_ratio * half_spread * 0.5  # Additional skew up to 50% of spread
        
        bid_price -= skew
        ask_price -= skew
        
        full_spread = ask_price - bid_price
        spread_bps = (full_spread / mid_price) * 10000
        
        result = {
            'bid': bid_price,
            'ask': ask_price,
            'mid': mid_price,
            'reservation_price': reservation_price,
            'half_spread': half_spread,
            'full_spread': full_spread,
            'spread_bps': spread_bps,
            'inventory': inventory,
            'inventory_ratio': inventory_ratio,
            'volatility': self.volatility_estimate,
            'time_remaining': time_remaining,
            'skew': skew
        }
        
        return result
    
    def should_quote(self, inventory: int) -> bool:
        """
        Determine if we should place quotes based on inventory limits.
        
        Args:
            inventory: Current inventory position
            
        Returns:
            True if we should continue quoting, False if inventory limit reached
        """
        return abs(inventory) < self.max_inventory
    
    def get_quote_sizes(
        self,
        base_size: float,
        inventory: int,
        inventory_target: int = 0
    ) -> Tuple[float, float]:
        """
        Calculate bid and ask sizes based on inventory position.
        
        When inventory is positive (long), reduce ask size and increase bid size to rebalance.
        When inventory is negative (short), increase ask size and reduce bid size.
        
        Args:
            base_size: Base order size
            inventory: Current inventory position
            inventory_target: Target inventory level (default 0 for market neutral)
            
        Returns:
            Tuple of (bid_size, ask_size)
        """
        inventory_deviation = inventory - inventory_target
        inventory_ratio = inventory_deviation / self.max_inventory if self.max_inventory > 0 else 0
        
        # Adjust sizes to encourage rebalancing
        # When long (positive inventory), decrease bid size and increase ask size to rebalance
        # When short (negative inventory), increase bid size and decrease ask size to rebalance
        bid_adjustment = 1.0 - (inventory_ratio * 0.5)  # Reduce bid when long
        ask_adjustment = 1.0 + (inventory_ratio * 0.5)  # Reduce ask when short
        
        # Ensure sizes are positive and reasonable
        bid_size = max(base_size * bid_adjustment, base_size * 0.5)
        ask_size = max(base_size * ask_adjustment, base_size * 0.5)
        
        return bid_size, ask_size
    
    def reset_session(self, time_horizon_minutes: Optional[float] = None):
        """
        Reset the trading session (e.g., at start of new trading period).
        
        Args:
            time_horizon_minutes: New time horizon in minutes (uses existing if None)
        """
        self.session_start_time = datetime.now()
        if time_horizon_minutes is not None:
            self.T = time_horizon_minutes * 60
        
        self.logger.info(f"🔄 AS Strategy session reset. Time horizon: {self.T/60:.1f} minutes")
    
    def update_inventory(self, new_inventory: int):
        """
        Update the current inventory position.
        
        Args:
            new_inventory: New inventory position
        """
        old_inventory = self.current_inventory
        self.current_inventory = new_inventory
        
        if abs(new_inventory - old_inventory) > 0:
            self.logger.debug(
                f"Inventory updated: {old_inventory} → {new_inventory} "
                f"(ratio: {new_inventory/self.max_inventory:.1%})"
            )
    
    def get_status(self) -> Dict:
        """
        Get current strategy status and parameters.
        
        Returns:
            Dictionary with strategy status
        """
        elapsed = (datetime.now() - self.session_start_time).total_seconds()
        time_remaining = max(0, self.T - elapsed)
        
        return {
            'strategy': 'Avellaneda-Stoikov',
            'risk_aversion': self.gamma,
            'volatility': self.volatility_estimate,
            'order_arrival_rate': self.k * 60,  # Convert back to per minute
            'time_horizon_minutes': self.T / 60,
            'time_remaining_minutes': time_remaining / 60,
            'session_elapsed_minutes': elapsed / 60,
            'current_inventory': self.current_inventory,
            'max_inventory': self.max_inventory,
            'inventory_utilization': abs(self.current_inventory) / self.max_inventory if self.max_inventory > 0 else 0,
            'min_spread_bps': self.min_spread * 10000,
            'max_spread_bps': self.max_spread * 10000
        }
