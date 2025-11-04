"""
Hedging Strategy Implementation
Portfolio-level protective hedging during high-risk periods
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger
import numpy as np


class HedgingStrategy:
    """
    Portfolio-level hedging strategy for risk protection

    NOT pair-level hedging (too costly and complex)

    Use cases:
    1. Drawdown protection - Hedge when portfolio drawdown exceeds threshold
    2. Volatility protection - Hedge during extreme volatility events
    3. Event protection - Hedge during known high-risk events
    4. Correlation protection - Hedge when portfolio too concentrated in one direction
    """

    def __init__(self):
        self.logger = Logger.get_logger()

        # Hedging configuration
        self.hedging_enabled = True
        self.hedge_instrument = 'BTC-USDT'  # Use BTC as hedge instrument

        # Drawdown protection
        self.drawdown_hedge_threshold = 0.10  # Hedge at 10% drawdown
        self.drawdown_hedge_ratio = 0.5  # Hedge 50% of portfolio

        # Volatility protection
        self.volatility_hedge_threshold = 0.08  # Hedge when volatility > 8%
        self.volatility_hedge_ratio = 0.3  # Hedge 30% of portfolio

        # Correlation protection
        self.correlation_threshold = 0.7  # Hedge when 70%+ portfolio in one direction
        self.correlation_hedge_ratio = 0.4  # Hedge 40% of exposure

        # Event protection
        self.event_hedge_duration = timedelta(hours=4)  # Hedge for 4 hours during events

        # Track active hedges
        self.active_hedges = {}  # hedge_id -> hedge info
        self.hedge_counter = 0

        # Hedge cooldown (prevent too frequent hedging)
        self.hedge_cooldown = timedelta(hours=2)
        self.last_hedge_time = None

        self.logger.info("🛡️ Hedging Strategy initialized")
        self.logger.info(f"   Drawdown hedge: {self.drawdown_hedge_threshold*100:.0f}% threshold, {self.drawdown_hedge_ratio*100:.0f}% ratio")
        self.logger.info(f"   Volatility hedge: {self.volatility_hedge_threshold*100:.0f}% threshold, {self.volatility_hedge_ratio*100:.0f}% ratio")
        self.logger.info(f"   Correlation hedge: {self.correlation_threshold*100:.0f}% threshold, {self.correlation_hedge_ratio*100:.0f}% ratio")

    def should_hedge_drawdown(self, current_drawdown: float,
                             portfolio_value: float) -> Optional[Dict]:
        """
        Check if should hedge due to drawdown

        Args:
            current_drawdown: Current portfolio drawdown (0-1)
            portfolio_value: Current portfolio value in USDT

        Returns:
            Hedge recommendation dict or None
        """
        if not self.hedging_enabled:
            return None

        if current_drawdown < self.drawdown_hedge_threshold:
            return None

        # Check cooldown
        if self.last_hedge_time:
            time_since_last = datetime.now() - self.last_hedge_time
            if time_since_last < self.hedge_cooldown:
                return None

        hedge_size = portfolio_value * self.drawdown_hedge_ratio

        recommendation = {
            'reason': 'drawdown_protection',
            'trigger_value': current_drawdown,
            'threshold': self.drawdown_hedge_threshold,
            'hedge_size': hedge_size,
            'hedge_ratio': self.drawdown_hedge_ratio,
            'instrument': self.hedge_instrument,
            'urgency': 'high' if current_drawdown > 0.15 else 'medium'
        }

        self.logger.warning(f"⚠️ Drawdown hedge recommended!")
        self.logger.warning(f"   Drawdown: {current_drawdown*100:.2f}% (threshold: {self.drawdown_hedge_threshold*100:.0f}%)")
        self.logger.warning(f"   Hedge size: ${hedge_size:.2f} ({self.drawdown_hedge_ratio*100:.0f}% of portfolio)")

        return recommendation

    def should_hedge_volatility(self, current_volatility: float,
                               portfolio_value: float,
                               portfolio_beta: float = 1.0) -> Optional[Dict]:
        """
        Check if should hedge due to extreme volatility

        Args:
            current_volatility: Current market volatility (e.g., ATR or realized vol)
            portfolio_value: Current portfolio value in USDT
            portfolio_beta: Portfolio beta relative to BTC (default 1.0)

        Returns:
            Hedge recommendation dict or None
        """
        if not self.hedging_enabled:
            return None

        if current_volatility < self.volatility_hedge_threshold:
            return None

        # Check cooldown
        if self.last_hedge_time:
            time_since_last = datetime.now() - self.last_hedge_time
            if time_since_last < self.hedge_cooldown:
                return None

        # Adjust hedge size based on portfolio beta
        base_hedge_size = portfolio_value * self.volatility_hedge_ratio
        adjusted_hedge_size = base_hedge_size * portfolio_beta

        recommendation = {
            'reason': 'volatility_protection',
            'trigger_value': current_volatility,
            'threshold': self.volatility_hedge_threshold,
            'hedge_size': adjusted_hedge_size,
            'hedge_ratio': self.volatility_hedge_ratio,
            'portfolio_beta': portfolio_beta,
            'instrument': self.hedge_instrument,
            'urgency': 'high' if current_volatility > 0.12 else 'medium'
        }

        self.logger.warning(f"⚠️ Volatility hedge recommended!")
        self.logger.warning(f"   Volatility: {current_volatility*100:.2f}% (threshold: {self.volatility_hedge_threshold*100:.0f}%)")
        self.logger.warning(f"   Hedge size: ${adjusted_hedge_size:.2f}")

        return recommendation

    def should_hedge_correlation(self, open_positions: Dict,
                                portfolio_value: float) -> Optional[Dict]:
        """
        Check if portfolio is too concentrated in one direction

        Args:
            open_positions: Dict of open positions {symbol: position_info}
            portfolio_value: Current portfolio value in USDT

        Returns:
            Hedge recommendation dict or None
        """
        if not self.hedging_enabled:
            return None

        if not open_positions:
            return None

        # Calculate directional exposure
        long_exposure = 0.0
        short_exposure = 0.0

        for symbol, position in open_positions.items():
            position_value = position.get('notional_value', 0)
            side = position.get('side', 'long')

            if side == 'long':
                long_exposure += position_value
            else:
                short_exposure += position_value

        total_exposure = long_exposure + short_exposure

        if total_exposure == 0:
            return None

        # Calculate concentration
        long_ratio = long_exposure / total_exposure
        short_ratio = short_exposure / total_exposure

        max_concentration = max(long_ratio, short_ratio)

        if max_concentration < self.correlation_threshold:
            return None

        # Determine hedge direction (opposite of concentration)
        if long_ratio > short_ratio:
            hedge_side = 'short'
            concentrated_side = 'long'
            concentrated_exposure = long_exposure
        else:
            hedge_side = 'long'
            concentrated_side = 'short'
            concentrated_exposure = short_exposure

        hedge_size = concentrated_exposure * self.correlation_hedge_ratio

        recommendation = {
            'reason': 'correlation_protection',
            'trigger_value': max_concentration,
            'threshold': self.correlation_threshold,
            'hedge_size': hedge_size,
            'hedge_ratio': self.correlation_hedge_ratio,
            'hedge_side': hedge_side,
            'concentrated_side': concentrated_side,
            'long_exposure': long_exposure,
            'short_exposure': short_exposure,
            'instrument': self.hedge_instrument,
            'urgency': 'medium'
        }

        self.logger.warning(f"⚠️ Correlation hedge recommended!")
        self.logger.warning(f"   Portfolio concentration: {max_concentration*100:.1f}% {concentrated_side}")
        self.logger.warning(f"   Long exposure: ${long_exposure:.2f}, Short exposure: ${short_exposure:.2f}")
        self.logger.warning(f"   Hedge: {hedge_side} ${hedge_size:.2f}")

        return recommendation

    def create_hedge(self, recommendation: Dict) -> Optional[str]:
        """
        Create a hedge based on recommendation

        Args:
            recommendation: Hedge recommendation dict

        Returns:
            Hedge ID if created, None otherwise
        """
        self.hedge_counter += 1
        hedge_id = f"hedge_{self.hedge_counter}_{int(datetime.now().timestamp())}"

        hedge_info = {
            'hedge_id': hedge_id,
            'reason': recommendation['reason'],
            'instrument': recommendation['instrument'],
            'hedge_size': recommendation['hedge_size'],
            'hedge_side': recommendation.get('hedge_side', 'short'),  # Default to short
            'created_at': datetime.now(),
            'trigger_value': recommendation['trigger_value'],
            'threshold': recommendation['threshold'],
            'urgency': recommendation['urgency'],
            'status': 'active',
            'pnl': 0.0,
            'entry_price': None,  # Will be set when actually executed
            'position_id': None    # Will be set when position opened
        }

        self.active_hedges[hedge_id] = hedge_info
        self.last_hedge_time = datetime.now()

        self.logger.info(f"🛡️ Hedge created: {hedge_id}")
        self.logger.info(f"   Reason: {recommendation['reason']}")
        self.logger.info(f"   Size: ${recommendation['hedge_size']:.2f}")
        self.logger.info(f"   Instrument: {recommendation['instrument']}")

        return hedge_id

    def should_close_hedge(self, hedge_id: str, current_conditions: Dict) -> bool:
        """
        Check if hedge should be closed

        Args:
            hedge_id: Hedge ID
            current_conditions: Current market/portfolio conditions

        Returns:
            True if should close hedge
        """
        if hedge_id not in self.active_hedges:
            return False

        hedge = self.active_hedges[hedge_id]

        if hedge['status'] != 'active':
            return False

        reason = hedge['reason']

        # Check reason-specific close conditions
        if reason == 'drawdown_protection':
            # Close hedge when drawdown recovers
            current_drawdown = current_conditions.get('drawdown', 0)
            if current_drawdown < self.drawdown_hedge_threshold * 0.7:  # 70% recovery
                self.logger.info(f"✅ Closing drawdown hedge {hedge_id} - drawdown recovered")
                return True

        elif reason == 'volatility_protection':
            # Close hedge when volatility normalizes
            current_volatility = current_conditions.get('volatility', 0)
            if current_volatility < self.volatility_hedge_threshold * 0.8:  # 80% of threshold
                self.logger.info(f"✅ Closing volatility hedge {hedge_id} - volatility normalized")
                return True

        elif reason == 'correlation_protection':
            # Close hedge when portfolio rebalances
            concentration = current_conditions.get('concentration', 0)
            if concentration < self.correlation_threshold * 0.85:  # 85% of threshold
                self.logger.info(f"✅ Closing correlation hedge {hedge_id} - portfolio rebalanced")
                return True

        elif reason == 'event_protection':
            # Close hedge after event duration
            age = datetime.now() - hedge['created_at']
            if age > self.event_hedge_duration:
                self.logger.info(f"✅ Closing event hedge {hedge_id} - event duration elapsed")
                return True

        # Check for stop loss on hedge itself (prevent hedge from losing too much)
        if hedge['pnl'] < -0.05:  # Hedge losing more than 5%
            self.logger.warning(f"⚠️ Closing hedge {hedge_id} - stop loss triggered ({hedge['pnl']*100:.2f}%)")
            return True

        return False

    def close_hedge(self, hedge_id: str, final_pnl: float = 0.0) -> bool:
        """
        Close a hedge position

        Args:
            hedge_id: Hedge ID
            final_pnl: Final P&L of the hedge

        Returns:
            True if closed successfully
        """
        if hedge_id not in self.active_hedges:
            return False

        hedge = self.active_hedges[hedge_id]
        hedge['status'] = 'closed'
        hedge['closed_at'] = datetime.now()
        hedge['final_pnl'] = final_pnl

        duration = hedge['closed_at'] - hedge['created_at']

        self.logger.info(f"🛡️ Hedge closed: {hedge_id}")
        self.logger.info(f"   Duration: {duration.total_seconds()/3600:.1f} hours")
        self.logger.info(f"   Final P&L: {final_pnl*100:.2f}%")
        self.logger.info(f"   Reason: {hedge['reason']}")

        return True

    def get_active_hedges(self) -> List[Dict]:
        """Get list of active hedges"""
        return [hedge for hedge in self.active_hedges.values()
                if hedge['status'] == 'active']

    def get_total_hedge_exposure(self) -> float:
        """Calculate total hedge exposure in USDT"""
        return sum(hedge['hedge_size'] for hedge in self.get_active_hedges())

    def update_hedge_pnl(self, hedge_id: str, current_pnl: float):
        """Update hedge P&L"""
        if hedge_id in self.active_hedges:
            self.active_hedges[hedge_id]['pnl'] = current_pnl

    def cleanup_old_hedges(self, max_age_hours: int = 48):
        """Remove old closed hedges from tracking"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        hedges_to_remove = []
        for hedge_id, hedge in self.active_hedges.items():
            if hedge['status'] == 'closed' and hedge.get('closed_at', datetime.now()) < cutoff_time:
                hedges_to_remove.append(hedge_id)

        for hedge_id in hedges_to_remove:
            del self.active_hedges[hedge_id]
            self.logger.debug(f"🧹 Cleaned up old hedge {hedge_id}")

    def schedule_event_hedge(self, event_name: str, start_time: datetime,
                            portfolio_value: float,
                            hedge_ratio: float = 0.5) -> Optional[Dict]:
        """
        Schedule a hedge for a known event

        Args:
            event_name: Name of event (e.g., "Fed Announcement")
            start_time: When event starts
            portfolio_value: Current portfolio value
            hedge_ratio: Portion of portfolio to hedge

        Returns:
            Hedge recommendation dict
        """
        time_until_event = start_time - datetime.now()

        if time_until_event.total_seconds() < 0:
            self.logger.warning(f"Event {event_name} already started")
            return None

        hedge_size = portfolio_value * hedge_ratio

        recommendation = {
            'reason': 'event_protection',
            'event_name': event_name,
            'start_time': start_time,
            'hedge_size': hedge_size,
            'hedge_ratio': hedge_ratio,
            'instrument': self.hedge_instrument,
            'urgency': 'medium',
            'trigger_value': time_until_event.total_seconds() / 3600,  # Hours until event
            'threshold': 0
        }

        self.logger.info(f"📅 Event hedge scheduled for {event_name}")
        self.logger.info(f"   Start time: {start_time}")
        self.logger.info(f"   Hedge size: ${hedge_size:.2f}")

        return recommendation
