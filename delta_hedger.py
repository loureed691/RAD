"""
Delta Hedging Module

Implements delta-neutral hedging strategies for managing directional risk in portfolios.
Useful for:
- Options trading (hedging delta exposure)
- Market making (maintaining inventory neutrality)  
- Arbitrage strategies (hedging legs)

Features:
- Delta calculation and monitoring
- Automatic rehedging triggers
- Greeks estimation (delta, gamma, vega)
- Position aggregation across symbols
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
from logger import Logger


class DeltaHedger:
    """
    Delta hedging module for managing directional risk.
    
    Maintains delta-neutral positions through automatic hedging.
    """
    
    def __init__(
        self,
        hedge_symbol: str = "BTCUSDT",
        delta_threshold: float = 0.1,
        rehedge_frequency_minutes: int = 15,
        enable_auto_hedge: bool = True
    ):
        """
        Initialize delta hedger.
        
        Args:
            hedge_symbol: Symbol to use for hedging (e.g., BTC perpetual)
            delta_threshold: Rehedge when |delta| exceeds this threshold
            rehedge_frequency_minutes: Minimum time between rehedges
            enable_auto_hedge: Enable automatic rehedging
        """
        self.hedge_symbol = hedge_symbol
        self.delta_threshold = delta_threshold
        self.rehedge_frequency = rehedge_frequency_minutes * 60  # Convert to seconds
        self.enable_auto_hedge = enable_auto_hedge
        
        self.logger = Logger.get_logger()
        
        # State tracking
        self.positions = {}  # symbol -> position info
        self.hedge_position = 0.0  # Current hedge position size
        self.last_hedge_time = None
        self.total_delta = 0.0
        
        self.logger.info("🛡️ Delta Hedger Initialized")
        self.logger.info(f"   Hedge Symbol: {hedge_symbol}")
        self.logger.info(f"   Delta Threshold: ±{delta_threshold}")
        self.logger.info(f"   Rehedge Frequency: {rehedge_frequency_minutes} minutes")
        self.logger.info(f"   Auto Hedge: {'Enabled' if enable_auto_hedge else 'Disabled'}")
    
    def calculate_position_delta(
        self,
        position_size: float,
        position_side: str,
        price: float,
        volatility: Optional[float] = None
    ) -> float:
        """
        Calculate delta for a position.
        
        For spot/perpetual positions, delta = ±1 per contract.
        For options, delta depends on moneyness and volatility.
        
        Args:
            position_size: Position size in contracts
            position_side: 'long' or 'short'
            price: Current price
            volatility: Implied volatility (for options)
            
        Returns:
            Position delta
        """
        # For perpetual futures, delta is simply the position size
        # Long = positive delta, Short = negative delta
        if position_side.lower() == 'long':
            delta = position_size
        else:
            delta = -position_size
        
        return delta
    
    def update_position(
        self,
        symbol: str,
        size: float,
        side: str,
        price: float,
        volatility: Optional[float] = None
    ):
        """
        Update position information and recalculate delta.
        
        Args:
            symbol: Trading symbol
            size: Position size
            side: 'long' or 'short'
            price: Current price
            volatility: Implied volatility (optional)
        """
        delta = self.calculate_position_delta(size, side, price, volatility)
        
        self.positions[symbol] = {
            'size': size,
            'side': side,
            'price': price,
            'delta': delta,
            'updated_at': datetime.now()
        }
        
        # Recalculate total delta
        self.total_delta = sum(pos['delta'] for pos in self.positions.values())
        
        self.logger.debug(
            f"Position updated: {symbol} {side} {size} @ {price:.2f}, "
            f"delta: {delta:.4f}, total delta: {self.total_delta:.4f}"
        )
    
    def remove_position(self, symbol: str):
        """
        Remove a position from tracking.
        
        Args:
            symbol: Symbol to remove
        """
        if symbol in self.positions:
            del self.positions[symbol]
            self.total_delta = sum(pos['delta'] for pos in self.positions.values())
            self.logger.info(f"Position removed: {symbol}, new total delta: {self.total_delta:.4f}")
    
    def get_total_delta(self) -> float:
        """
        Get total portfolio delta.
        
        Returns:
            Total delta across all positions
        """
        return self.total_delta
    
    def calculate_hedge_size(self) -> float:
        """
        Calculate required hedge size to neutralize delta.
        
        Returns:
            Hedge size needed (positive = buy, negative = sell)
        """
        # To neutralize delta, we need to take opposite position
        # If total_delta = +10 (net long), we need to sell 10 (short hedge)
        # If total_delta = -10 (net short), we need to buy 10 (long hedge)
        required_hedge = -self.total_delta
        
        # Account for existing hedge position
        adjustment = required_hedge - self.hedge_position
        
        return adjustment
    
    def should_rehedge(self) -> Tuple[bool, str]:
        """
        Determine if rehedging is needed.
        
        Returns:
            Tuple of (should_hedge, reason)
        """
        # Check if auto-hedging is enabled
        if not self.enable_auto_hedge:
            return False, "Auto-hedging disabled"
        
        # Check delta threshold
        if abs(self.total_delta) < self.delta_threshold:
            return False, f"Delta {self.total_delta:.4f} within threshold ±{self.delta_threshold}"
        
        # Check rehedge frequency
        if self.last_hedge_time is not None:
            time_since_hedge = (datetime.now() - self.last_hedge_time).total_seconds()
            if time_since_hedge < self.rehedge_frequency:
                return False, f"Too soon since last hedge ({time_since_hedge:.0f}s < {self.rehedge_frequency:.0f}s)"
        
        return True, f"Delta {self.total_delta:.4f} exceeds threshold ±{self.delta_threshold}"
    
    def execute_hedge(self, hedge_size: float) -> Dict:
        """
        Execute hedge trade (to be implemented with actual trading client).
        
        This is a placeholder that returns the hedge order details.
        In production, this would call the trading client to place orders.
        
        Args:
            hedge_size: Size to hedge (positive = buy, negative = sell)
            
        Returns:
            Dictionary with hedge execution details
        """
        side = 'buy' if hedge_size > 0 else 'sell'
        abs_size = abs(hedge_size)
        
        hedge_order = {
            'symbol': self.hedge_symbol,
            'side': side,
            'size': abs_size,
            'type': 'market',
            'timestamp': datetime.now(),
            'status': 'pending'
        }
        
        self.logger.info(
            f"🛡️ Hedge order: {side.upper()} {abs_size:.4f} {self.hedge_symbol} "
            f"to neutralize delta {self.total_delta:.4f}"
        )
        
        # Update hedge position (assuming fill)
        if side == 'buy':
            self.hedge_position += abs_size
        else:
            self.hedge_position -= abs_size
        
        self.last_hedge_time = datetime.now()
        
        return hedge_order
    
    def calculate_gamma(self) -> float:
        """
        Calculate portfolio gamma (rate of change of delta).
        
        For perpetual futures, gamma is 0.
        For options, gamma = d(delta)/d(price).
        
        Returns:
            Portfolio gamma
        """
        # For spot/perp positions, gamma is zero
        # This is a placeholder for options implementation
        return 0.0
    
    def calculate_vega(self) -> float:
        """
        Calculate portfolio vega (sensitivity to volatility).
        
        For perpetual futures, vega is 0.
        For options, vega = d(value)/d(volatility).
        
        Returns:
            Portfolio vega
        """
        # For spot/perp positions, vega is zero
        # This is a placeholder for options implementation
        return 0.0
    
    def get_greeks(self) -> Dict:
        """
        Get all Greeks for the portfolio.
        
        Returns:
            Dictionary with delta, gamma, vega
        """
        return {
            'delta': self.total_delta,
            'gamma': self.calculate_gamma(),
            'vega': self.calculate_vega(),
            'hedge_position': self.hedge_position,
            'hedge_symbol': self.hedge_symbol
        }
    
    def get_hedge_recommendation(self) -> Dict:
        """
        Get hedge recommendation without executing.
        
        Returns:
            Dictionary with hedge analysis and recommendation
        """
        should_hedge, reason = self.should_rehedge()
        hedge_size = self.calculate_hedge_size()
        
        recommendation = {
            'should_hedge': should_hedge,
            'reason': reason,
            'total_delta': self.total_delta,
            'hedge_position': self.hedge_position,
            'recommended_hedge_size': hedge_size,
            'hedge_symbol': self.hedge_symbol,
            'delta_threshold': self.delta_threshold,
            'positions_count': len(self.positions)
        }
        
        if should_hedge:
            side = 'BUY' if hedge_size > 0 else 'SELL'
            recommendation['action'] = f"{side} {abs(hedge_size):.4f} {self.hedge_symbol}"
        else:
            recommendation['action'] = "No hedge needed"
        
        return recommendation
    
    def get_status(self) -> Dict:
        """
        Get current hedger status.
        
        Returns:
            Dictionary with current state
        """
        should_hedge, reason = self.should_rehedge()
        
        return {
            'enabled': self.enable_auto_hedge,
            'hedge_symbol': self.hedge_symbol,
            'total_delta': self.total_delta,
            'delta_threshold': self.delta_threshold,
            'hedge_position': self.hedge_position,
            'should_rehedge': should_hedge,
            'rehedge_reason': reason,
            'positions_count': len(self.positions),
            'last_hedge_time': self.last_hedge_time.isoformat() if self.last_hedge_time else None,
            'positions': {
                symbol: {
                    'size': pos['size'],
                    'side': pos['side'],
                    'delta': pos['delta']
                }
                for symbol, pos in self.positions.items()
            }
        }
    
    def reset(self):
        """Reset hedger state."""
        self.positions = {}
        self.hedge_position = 0.0
        self.total_delta = 0.0
        self.last_hedge_time = None
        self.logger.info("Delta hedger reset")
    
    def enable(self):
        """Enable auto-hedging."""
        self.enable_auto_hedge = True
        self.logger.info("Auto-hedging enabled")
    
    def disable(self):
        """Disable auto-hedging."""
        self.enable_auto_hedge = False
        self.logger.info("Auto-hedging disabled")
