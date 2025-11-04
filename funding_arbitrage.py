"""
Funding Rate Arbitrage and Basis Trading

Captures funding rate premiums and basis between:
1. Perpetual futures vs spot
2. Perpetual futures across different venues
3. Quarterly futures vs perpetuals

This is a natural complement to market making as it provides
steady returns while maintaining delta-neutral positions.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger


class FundingArbitrage:
    """
    Funding rate arbitrage system for perpetual futures.
    
    Perpetual futures use funding rates to keep their price anchored to spot.
    When funding is positive (perp > spot), longs pay shorts.
    When funding is negative (perp < spot), shorts pay longs.
    
    Strategy:
    - Monitor funding rates across venues
    - Enter positions when funding > threshold
    - Hold delta-neutral position to collect funding
    - Exit when funding normalizes
    """
    
    def __init__(self,
                 min_funding_rate: float = 0.0001,  # 0.01% per funding period
                 funding_period_hours: int = 8,
                 min_apr_threshold: float = 0.05,  # 5% APR minimum
                 max_basis_risk: float = 0.002,  # 0.2% basis risk tolerance
                 position_size_pct: float = 0.3):  # 30% of capital per trade
        """
        Initialize funding arbitrage system
        
        Args:
            min_funding_rate: Minimum funding rate to trigger trade
            funding_period_hours: Hours per funding period (usually 8)
            min_apr_threshold: Minimum APR required to enter trade
            max_basis_risk: Maximum basis divergence risk
            position_size_pct: Position size as % of capital
        """
        self.min_funding_rate = min_funding_rate
        self.funding_period_hours = funding_period_hours
        self.min_apr_threshold = min_apr_threshold
        self.max_basis_risk = max_basis_risk
        self.position_size_pct = position_size_pct
        
        # Active positions
        self.active_positions = {}  # position_id -> position_info
        self.position_counter = 0
        
        # Performance tracking
        self.total_funding_collected = 0.0
        self.total_basis_pnl = 0.0
        self.total_trades = 0
        
        self.logger = Logger.get_logger()
        self.logger.info("💰 Funding Arbitrage system initialized")
        self.logger.info(f"   Min funding rate: {self.min_funding_rate*100:.3f}%")
        self.logger.info(f"   Min APR threshold: {self.min_apr_threshold*100:.1f}%")
    
    def calculate_funding_apr(self, funding_rate: float) -> float:
        """
        Convert funding rate to annualized percentage rate (APR)
        
        Args:
            funding_rate: Funding rate per period (e.g., 0.0001 = 0.01%)
        
        Returns:
            Annualized rate
        """
        periods_per_year = (365.25 * 24) / self.funding_period_hours
        apr = funding_rate * periods_per_year
        return apr
    
    def evaluate_perp_spot_opportunity(self,
                                      perp_price: float,
                                      spot_price: float,
                                      funding_rate: float,
                                      predicted_funding: Optional[float] = None) -> Optional[Dict]:
        """
        Evaluate perp-spot arbitrage opportunity
        
        Args:
            perp_price: Perpetual futures price
            spot_price: Spot price
            funding_rate: Current funding rate
            predicted_funding: Predicted next funding rate
        
        Returns:
            Opportunity dict or None
        """
        # Calculate basis
        basis = (perp_price - spot_price) / spot_price
        
        # Calculate funding APR
        funding_apr = self.calculate_funding_apr(funding_rate)
        
        # Check if funding rate meets threshold
        if abs(funding_apr) < self.min_apr_threshold:
            return None
        
        # Check basis risk
        if abs(basis) > self.max_basis_risk:
            self.logger.warning(
                f"⚠️ Basis risk too high: {basis*100:.3f}% > {self.max_basis_risk*100:.3f}%"
            )
            return None
        
        # Determine position direction
        if funding_rate > 0:
            # Longs pay shorts -> short perp, long spot
            direction = 'short_perp_long_spot'
            expected_pnl_rate = funding_apr
        else:
            # Shorts pay longs -> long perp, short spot
            direction = 'long_perp_short_spot'
            expected_pnl_rate = -funding_apr
        
        # Use predicted funding if available
        if predicted_funding is not None:
            predicted_apr = self.calculate_funding_apr(predicted_funding)
            expected_pnl_rate = (expected_pnl_rate + predicted_apr) / 2
        
        opportunity = {
            'type': 'perp_spot_arbitrage',
            'direction': direction,
            'perp_price': perp_price,
            'spot_price': spot_price,
            'basis': basis,
            'basis_bps': basis * 10000,
            'funding_rate': funding_rate,
            'funding_apr': funding_apr,
            'expected_pnl_rate': expected_pnl_rate,
            'timestamp': datetime.now(),
            'recommended_position_size': self.position_size_pct
        }
        
        self.logger.info(
            f"💡 Perp-spot opportunity: {direction}, "
            f"funding APR: {funding_apr*100:.2f}%, basis: {basis*100:.3f}%"
        )
        
        return opportunity
    
    def evaluate_cross_venue_opportunity(self,
                                        venue1_price: float,
                                        venue1_funding: float,
                                        venue1_name: str,
                                        venue2_price: float,
                                        venue2_funding: float,
                                        venue2_name: str) -> Optional[Dict]:
        """
        Evaluate cross-venue perpetual arbitrage opportunity
        
        Args:
            venue1_price: Price on venue 1
            venue1_funding: Funding rate on venue 1
            venue1_name: Name of venue 1
            venue2_price: Price on venue 2
            venue2_funding: Funding rate on venue 2
            venue2_name: Name of venue 2
        
        Returns:
            Opportunity dict or None
        """
        # Calculate price basis
        basis = (venue1_price - venue2_price) / venue2_price
        
        # Calculate funding differential
        funding_diff = venue1_funding - venue2_funding
        funding_diff_apr = self.calculate_funding_apr(funding_diff)
        
        # Check if funding differential meets threshold
        if abs(funding_diff_apr) < self.min_apr_threshold:
            return None
        
        # Check basis risk (prices should be similar)
        if abs(basis) > self.max_basis_risk:
            self.logger.warning(
                f"⚠️ Cross-venue basis risk too high: {basis*100:.3f}%"
            )
            return None
        
        # Determine position direction
        if funding_diff > 0:
            # Venue 1 funding higher -> short venue 1, long venue 2
            direction = f'short_{venue1_name}_long_{venue2_name}'
            long_venue = venue2_name
            short_venue = venue1_name
            expected_pnl_rate = funding_diff_apr
        else:
            # Venue 2 funding higher -> long venue 1, short venue 2
            direction = f'long_{venue1_name}_short_{venue2_name}'
            long_venue = venue1_name
            short_venue = venue2_name
            expected_pnl_rate = -funding_diff_apr
        
        opportunity = {
            'type': 'cross_venue_arbitrage',
            'direction': direction,
            'long_venue': long_venue,
            'short_venue': short_venue,
            'venue1_price': venue1_price,
            'venue2_price': venue2_price,
            'venue1_funding': venue1_funding,
            'venue2_funding': venue2_funding,
            'basis': basis,
            'basis_bps': basis * 10000,
            'funding_diff': funding_diff,
            'funding_diff_apr': funding_diff_apr,
            'expected_pnl_rate': expected_pnl_rate,
            'timestamp': datetime.now(),
            'recommended_position_size': self.position_size_pct
        }
        
        self.logger.info(
            f"💡 Cross-venue opportunity: {direction}, "
            f"funding diff: {funding_diff_apr*100:.2f}%, basis: {basis*100:.3f}%"
        )
        
        return opportunity
    
    def open_position(self, opportunity: Dict, position_size: float) -> str:
        """
        Open a funding arbitrage position
        
        Args:
            opportunity: Opportunity dict from evaluate_* method
            position_size: Position size in quote currency
        
        Returns:
            Position ID
        """
        self.position_counter += 1
        position_id = f"funding_{self.position_counter}"
        
        position = {
            'id': position_id,
            'type': opportunity['type'],
            'direction': opportunity['direction'],
            'entry_time': datetime.now(),
            'position_size': position_size,
            'entry_basis': opportunity.get('basis', 0),
            'entry_funding_rate': opportunity.get('funding_rate') or opportunity.get('funding_diff'),
            'expected_pnl_rate': opportunity['expected_pnl_rate'],
            'funding_collected': 0.0,
            'unrealized_pnl': 0.0,
            'metadata': opportunity
        }
        
        self.active_positions[position_id] = position
        self.total_trades += 1
        
        self.logger.info(
            f"📈 Opened funding position {position_id}: {opportunity['direction']}, "
            f"size=${position_size:.2f}, expected APR={opportunity['expected_pnl_rate']*100:.2f}%"
        )
        
        return position_id
    
    def update_position(self, position_id: str,
                       current_funding_rate: float,
                       current_basis: float,
                       funding_payment: float = 0.0):
        """
        Update position with new funding payment and basis
        
        Args:
            position_id: Position ID
            current_funding_rate: Current funding rate
            current_basis: Current price basis
            funding_payment: Funding payment received/paid this period
        """
        if position_id not in self.active_positions:
            self.logger.error(f"Position {position_id} not found")
            return
        
        position = self.active_positions[position_id]
        
        # Update funding collected
        position['funding_collected'] += funding_payment
        self.total_funding_collected += funding_payment
        
        # Update unrealized PnL from basis change
        basis_change = current_basis - position['entry_basis']
        position['unrealized_pnl'] = basis_change * position['position_size']
        
        # Update position metadata
        position['current_funding_rate'] = current_funding_rate
        position['current_basis'] = current_basis
        position['last_update'] = datetime.now()
        
        # Calculate realized APR so far
        time_held = (datetime.now() - position['entry_time']).total_seconds() / 3600  # hours
        if time_held > 0:
            realized_apr = (position['funding_collected'] / position['position_size']) * (365.25 * 24 / time_held)
            position['realized_apr'] = realized_apr
    
    def should_close_position(self, position_id: str,
                             current_funding_rate: float,
                             current_basis: float) -> bool:
        """
        Determine if position should be closed
        
        Args:
            position_id: Position ID
            current_funding_rate: Current funding rate
            current_basis: Current price basis
        
        Returns:
            True if position should be closed
        """
        if position_id not in self.active_positions:
            return False
        
        position = self.active_positions[position_id]
        
        # Close if funding rate flipped or became too small
        funding_apr = self.calculate_funding_apr(current_funding_rate)
        if abs(funding_apr) < self.min_apr_threshold * 0.5:
            self.logger.info(
                f"💼 Closing {position_id}: funding too low ({funding_apr*100:.2f}%)"
            )
            return True
        
        # Close if basis risk increased significantly
        basis_change = abs(current_basis - position['entry_basis'])
        if basis_change > self.max_basis_risk * 2:
            self.logger.warning(
                f"💼 Closing {position_id}: basis risk too high ({basis_change*100:.3f}%)"
            )
            return True
        
        # Close if funding flipped direction (sign change)
        entry_funding = position['entry_funding_rate']
        if np.sign(entry_funding) != np.sign(current_funding_rate):
            self.logger.info(
                f"💼 Closing {position_id}: funding flipped direction"
            )
            return True
        
        return False
    
    def close_position(self, position_id: str,
                      exit_basis: float,
                      exit_price: float = None) -> Dict:
        """
        Close a funding arbitrage position
        
        Args:
            position_id: Position ID
            exit_basis: Exit basis
            exit_price: Exit price (optional)
        
        Returns:
            Position summary dict
        """
        if position_id not in self.active_positions:
            self.logger.error(f"Position {position_id} not found")
            return {}
        
        position = self.active_positions[position_id]
        
        # Calculate final PnL
        basis_pnl = (exit_basis - position['entry_basis']) * position['position_size']
        total_pnl = position['funding_collected'] + basis_pnl
        
        # Calculate holding time
        holding_time = datetime.now() - position['entry_time']
        holding_hours = holding_time.total_seconds() / 3600
        
        # Calculate realized APR
        if holding_hours > 0:
            realized_apr = (total_pnl / position['position_size']) * (365.25 * 24 / holding_hours)
        else:
            realized_apr = 0.0
        
        summary = {
            'position_id': position_id,
            'type': position['type'],
            'direction': position['direction'],
            'entry_time': position['entry_time'],
            'exit_time': datetime.now(),
            'holding_hours': holding_hours,
            'position_size': position['position_size'],
            'funding_collected': position['funding_collected'],
            'basis_pnl': basis_pnl,
            'total_pnl': total_pnl,
            'realized_apr': realized_apr,
            'expected_apr': position['expected_pnl_rate']
        }
        
        # Update totals
        self.total_basis_pnl += basis_pnl
        
        # Remove position
        del self.active_positions[position_id]
        
        self.logger.info(
            f"✅ Closed funding position {position_id}: "
            f"PnL=${total_pnl:.2f} (funding=${position['funding_collected']:.2f}, "
            f"basis=${basis_pnl:.2f}), APR={realized_apr*100:.2f}%"
        )
        
        return summary
    
    def get_metrics(self) -> Dict:
        """
        Get funding arbitrage performance metrics
        
        Returns:
            Dictionary of metrics
        """
        active_count = len(self.active_positions)
        total_active_size = sum(p['position_size'] for p in self.active_positions.values())
        
        # Calculate total unrealized PnL
        total_unrealized_pnl = sum(
            p.get('funding_collected', 0) + p.get('unrealized_pnl', 0)
            for p in self.active_positions.values()
        )
        
        return {
            'active_positions': active_count,
            'total_active_size': total_active_size,
            'total_trades': self.total_trades,
            'total_funding_collected': self.total_funding_collected,
            'total_basis_pnl': self.total_basis_pnl,
            'total_pnl': self.total_funding_collected + self.total_basis_pnl,
            'total_unrealized_pnl': total_unrealized_pnl,
            'positions': list(self.active_positions.keys())
        }
