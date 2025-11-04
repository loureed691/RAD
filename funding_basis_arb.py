"""
Funding Rate and Basis Arbitrage Module

Implements arbitrage strategies based on:
1. Funding rate arbitrage (perp ↔ spot)
2. Basis trading (perp ↔ perp across exchanges or timeframes)
3. Capital efficiency optimization

Features:
- Funding rate monitoring and prediction
- Basis spread calculation and tracking
- Entry/exit signal generation
- Position sizing based on expected returns
- Risk management for arbitrage positions
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from logger import Logger


class FundingBasisArbitrage:
    """
    Funding rate and basis arbitrage strategy.
    
    Captures funding rate premiums and basis spreads through market-neutral positions.
    """
    
    def __init__(
        self,
        min_funding_rate: float = 0.01,  # 1% daily APR
        min_basis_bps: float = 10.0,  # 10 basis points
        max_leverage: float = 3.0,
        capital_allocation: float = 0.3  # 30% of portfolio
    ):
        """
        Initialize funding/basis arbitrage module.
        
        Args:
            min_funding_rate: Minimum funding rate to enter position (annualized %)
            min_basis_bps: Minimum basis spread in basis points
            max_leverage: Maximum leverage for arb positions
            capital_allocation: Fraction of capital to allocate to arb strategies
        """
        self.min_funding_rate = min_funding_rate
        self.min_basis_bps = min_basis_bps / 10000  # Convert to decimal
        self.max_leverage = max_leverage
        self.capital_allocation = capital_allocation
        
        self.logger = Logger.get_logger()
        
        # State tracking
        self.funding_rate_history = {}  # symbol -> deque of funding rates
        self.basis_history = {}  # (symbol1, symbol2) -> deque of basis spreads
        self.active_positions = {}  # position_id -> position info
        self.realized_pnl = 0.0
        
        self.logger.info("💰 Funding/Basis Arbitrage Module Initialized")
        self.logger.info(f"   Min Funding Rate: {min_funding_rate:.2%} APR")
        self.logger.info(f"   Min Basis Spread: {min_basis_bps:.1f} bps")
        self.logger.info(f"   Max Leverage: {max_leverage}x")
        self.logger.info(f"   Capital Allocation: {capital_allocation:.1%}")
    
    def update_funding_rate(
        self,
        symbol: str,
        funding_rate: float,
        next_funding_time: Optional[datetime] = None
    ):
        """
        Update funding rate for a symbol.
        
        Args:
            symbol: Trading symbol
            funding_rate: Current funding rate (as decimal, e.g., 0.0001 = 0.01%)
            next_funding_time: Time of next funding payment
        """
        if symbol not in self.funding_rate_history:
            self.funding_rate_history[symbol] = deque(maxlen=100)
        
        entry = {
            'rate': funding_rate,
            'timestamp': datetime.now(),
            'next_funding_time': next_funding_time,
            'annualized_rate': funding_rate * 365 * 3  # 3 funding periods per day
        }
        
        self.funding_rate_history[symbol].append(entry)
        
        # Log significant funding rates
        annualized_pct = entry['annualized_rate'] * 100
        if abs(annualized_pct) > 10:  # > 10% APR
            self.logger.info(
                f"💰 Significant funding rate: {symbol} = {funding_rate*100:.4f}% "
                f"({annualized_pct:.1f}% APR)"
            )
    
    def get_funding_rate(self, symbol: str) -> Optional[Dict]:
        """
        Get current funding rate info for symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with funding rate info or None
        """
        if symbol not in self.funding_rate_history or not self.funding_rate_history[symbol]:
            return None
        
        return self.funding_rate_history[symbol][-1]
    
    def predict_funding_rate(self, symbol: str, periods_ahead: int = 1) -> Optional[float]:
        """
        Predict future funding rate using historical average.
        
        Args:
            symbol: Trading symbol
            periods_ahead: Number of funding periods to predict ahead
            
        Returns:
            Predicted funding rate or None
        """
        if symbol not in self.funding_rate_history or len(self.funding_rate_history[symbol]) < 10:
            return None
        
        # Simple moving average of recent funding rates
        recent_rates = [entry['rate'] for entry in list(self.funding_rate_history[symbol])[-20:]]
        avg_rate = np.mean(recent_rates)
        std_rate = np.std(recent_rates)
        
        # Mean reversion assumption: extreme rates revert to mean
        current_rate = recent_rates[-1]
        
        # Weighted prediction: 70% current, 30% mean
        predicted_rate = 0.7 * current_rate + 0.3 * avg_rate
        
        return predicted_rate
    
    def calculate_basis(
        self,
        price1: float,
        price2: float,
        symbol1: str = "perp",
        symbol2: str = "spot"
    ) -> Dict:
        """
        Calculate basis spread between two instruments.
        
        Basis = (Price_perp - Price_spot) / Price_spot
        
        Args:
            price1: Price of first instrument (typically perp)
            price2: Price of second instrument (typically spot)
            symbol1: Name of first instrument
            symbol2: Name of second instrument
            
        Returns:
            Dictionary with basis metrics
        """
        if price2 == 0:
            return {
                'basis': 0.0,
                'basis_bps': 0.0,
                'basis_pct': 0.0,
                'error': 'Invalid spot price'
            }
        
        basis = (price1 - price2) / price2
        basis_bps = basis * 10000
        
        # Store in history
        key = (symbol1, symbol2)
        if key not in self.basis_history:
            self.basis_history[key] = deque(maxlen=100)
        
        entry = {
            'basis': basis,
            'basis_bps': basis_bps,
            'price1': price1,
            'price2': price2,
            'timestamp': datetime.now()
        }
        
        self.basis_history[key].append(entry)
        
        return {
            'basis': basis,
            'basis_bps': basis_bps,
            'basis_pct': basis * 100,
            'price1': price1,
            'price2': price2,
            'symbol1': symbol1,
            'symbol2': symbol2
        }
    
    def check_funding_opportunity(
        self,
        symbol: str,
        spot_price: float,
        perp_price: float,
        capital_available: float
    ) -> Dict:
        """
        Check for funding rate arbitrage opportunity.
        
        Strategy: When funding rate is positive (longs pay shorts):
        - Short perp, long spot (earn funding + basis if any)
        When funding rate is negative (shorts pay longs):
        - Long perp, short spot (earn funding + basis if any)
        
        Args:
            symbol: Trading symbol
            spot_price: Spot price
            perp_price: Perpetual price
            capital_available: Available capital
            
        Returns:
            Dictionary with opportunity analysis
        """
        funding_info = self.get_funding_rate(symbol)
        
        if not funding_info:
            return {
                'opportunity': False,
                'reason': 'No funding rate data available'
            }
        
        funding_rate = funding_info['rate']
        annualized_rate = funding_info['annualized_rate']
        
        # Calculate basis
        basis_info = self.calculate_basis(perp_price, spot_price, f"{symbol}_perp", f"{symbol}_spot")
        basis = basis_info['basis']
        
        # Check if funding rate meets minimum threshold
        if abs(annualized_rate) < self.min_funding_rate:
            return {
                'opportunity': False,
                'reason': f'Funding rate {annualized_rate:.3%} below threshold {self.min_funding_rate:.3%}',
                'funding_rate': funding_rate,
                'annualized_rate': annualized_rate
            }
        
        # Determine strategy direction
        if funding_rate > 0:
            # Positive funding: longs pay shorts
            # Strategy: Short perp, long spot
            strategy = 'short_perp_long_spot'
            perp_side = 'short'
            spot_side = 'long'
            expected_funding_pnl = funding_rate  # We receive funding
        else:
            # Negative funding: shorts pay longs
            # Strategy: Long perp, short spot
            strategy = 'long_perp_short_spot'
            perp_side = 'long'
            spot_side = 'short'
            expected_funding_pnl = -funding_rate  # We receive funding (negative of negative)
        
        # Calculate position size
        max_position_value = capital_available * self.capital_allocation * self.max_leverage
        position_size_usd = min(max_position_value, capital_available * self.capital_allocation)
        
        # Expected profit per funding period
        expected_profit = position_size_usd * abs(funding_rate)
        
        # Account for basis convergence if any
        # If basis is in our favor, additional profit; if against us, reduce profit
        basis_pnl = 0.0
        if funding_rate > 0 and basis < 0:
            # We short perp (higher) and long spot (lower) - basis convergence helps
            basis_pnl = position_size_usd * abs(basis)
        elif funding_rate < 0 and basis > 0:
            # We long perp (higher) and short spot (lower) - basis convergence hurts
            basis_pnl = -position_size_usd * abs(basis)
        
        total_expected_profit = expected_profit + basis_pnl
        
        # Calculate expected APR
        expected_apr = annualized_rate + (basis_pnl / position_size_usd * 365 * 3 if position_size_usd > 0 else 0)
        
        return {
            'opportunity': True,
            'strategy': strategy,
            'perp_side': perp_side,
            'spot_side': spot_side,
            'symbol': symbol,
            'funding_rate': funding_rate,
            'annualized_rate': annualized_rate,
            'basis': basis,
            'basis_bps': basis_info['basis_bps'],
            'position_size_usd': position_size_usd,
            'expected_profit_per_period': expected_profit,
            'basis_pnl_potential': basis_pnl,
            'total_expected_profit': total_expected_profit,
            'expected_apr': expected_apr,
            'perp_price': perp_price,
            'spot_price': spot_price,
            'next_funding_time': funding_info.get('next_funding_time')
        }
    
    def check_basis_opportunity(
        self,
        symbol: str,
        price1: float,
        price2: float,
        exchange1: str,
        exchange2: str,
        capital_available: float
    ) -> Dict:
        """
        Check for basis arbitrage opportunity between exchanges.
        
        Args:
            symbol: Trading symbol
            price1: Price on exchange 1
            price2: Price on exchange 2
            exchange1: Name of exchange 1
            exchange2: Name of exchange 2
            capital_available: Available capital
            
        Returns:
            Dictionary with opportunity analysis
        """
        # Calculate basis
        basis_info = self.calculate_basis(price1, price2, exchange1, exchange2)
        basis = basis_info['basis']
        
        # Check if basis meets minimum threshold
        if abs(basis) < self.min_basis_bps:
            return {
                'opportunity': False,
                'reason': f'Basis {basis*10000:.1f} bps below threshold {self.min_basis_bps*10000:.1f} bps',
                'basis': basis,
                'basis_bps': basis_info['basis_bps']
            }
        
        # Determine strategy
        if price1 > price2:
            # Exchange 1 trading at premium
            strategy = 'short_ex1_long_ex2'
            ex1_side = 'short'
            ex2_side = 'long'
        else:
            # Exchange 2 trading at premium
            strategy = 'short_ex2_long_ex1'
            ex1_side = 'long'
            ex2_side = 'short'
        
        # Calculate position size
        position_size_usd = capital_available * self.capital_allocation * self.max_leverage
        
        # Expected profit from basis convergence
        expected_profit = position_size_usd * abs(basis)
        
        # Estimate holding period (basis typically converges within hours to days)
        estimated_hold_hours = 24  # Conservative estimate
        hourly_return = expected_profit / estimated_hold_hours
        daily_apr = (hourly_return * 24 / position_size_usd) * 365 * 100
        
        return {
            'opportunity': True,
            'strategy': strategy,
            'ex1_side': ex1_side,
            'ex2_side': ex2_side,
            'symbol': symbol,
            'basis': basis,
            'basis_bps': basis_info['basis_bps'],
            'price1': price1,
            'price2': price2,
            'exchange1': exchange1,
            'exchange2': exchange2,
            'position_size_usd': position_size_usd,
            'expected_profit': expected_profit,
            'estimated_hold_hours': estimated_hold_hours,
            'estimated_apr': daily_apr
        }
    
    def get_active_positions(self) -> Dict:
        """
        Get all active arbitrage positions.
        
        Returns:
            Dictionary of active positions
        """
        return self.active_positions
    
    def get_status(self) -> Dict:
        """
        Get current module status.
        
        Returns:
            Dictionary with status info
        """
        # Get symbols with recent funding rates
        symbols_tracked = list(self.funding_rate_history.keys())
        
        # Get latest funding rates
        latest_funding = {}
        for symbol in symbols_tracked:
            funding_info = self.get_funding_rate(symbol)
            if funding_info:
                latest_funding[symbol] = {
                    'rate': funding_info['rate'],
                    'rate_pct': funding_info['rate'] * 100,
                    'annualized_pct': funding_info['annualized_rate'] * 100
                }
        
        return {
            'min_funding_rate': self.min_funding_rate,
            'min_basis_bps': self.min_basis_bps * 10000,
            'max_leverage': self.max_leverage,
            'capital_allocation': self.capital_allocation,
            'active_positions': len(self.active_positions),
            'realized_pnl': self.realized_pnl,
            'symbols_tracked': symbols_tracked,
            'latest_funding_rates': latest_funding,
            'basis_pairs_tracked': len(self.basis_history)
        }
