"""
Smart and Adaptive Exit Management System

This module enhances take profit, stop loss, and emergency stops with:
1. Threshold-based regime detection for adaptive thresholds
2. ATR-based dynamic stop placement
3. Volume profile integration for profit targets
4. Volatility percentile-based adjustments
5. Support/resistance awareness

Author: RAD Trading Bot
Version: 1.0
"""

import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

# Try to import logger, use print fallback if not available
try:
    from logger import Logger
except ImportError:
    # Fallback logger for testing environments
    class Logger:
        @staticmethod
        def get_logger():
            class SimpleLogger:
                def debug(self, msg): pass
                def info(self, msg): pass
                def warning(self, msg): pass
                def error(self, msg): print(f"ERROR: {msg}")
            return SimpleLogger()


class MarketRegimeDetector:
    """Detect market regime for adaptive parameter adjustment"""

    def __init__(self):
        self.logger = Logger.get_logger()
        self.regimes = ['low_vol', 'normal', 'high_vol', 'extreme_vol']

    def detect_regime(self, volatility: float, returns: List[float] = None) -> Dict:
        """
        Detect current market regime based on volatility and price action

        Args:
            volatility: Current volatility measure (e.g., ATR, BB width)
            returns: Recent returns for additional analysis

        Returns:
            Dict with regime info and adaptive parameters
        """
        try:
            # Volatility-based regime classification
            if volatility > 0.08:
                regime = 'extreme_vol'
                stop_loss_multiplier = 1.5  # Wider stops in extreme volatility
                take_profit_multiplier = 1.3  # Higher targets
                emergency_threshold_adj = 0.7  # Tighter emergency (70% of normal)
            elif volatility > 0.05:
                regime = 'high_vol'
                stop_loss_multiplier = 1.3
                take_profit_multiplier = 1.2
                emergency_threshold_adj = 0.8
            elif volatility > 0.02:
                regime = 'normal'
                stop_loss_multiplier = 1.0
                take_profit_multiplier = 1.0
                emergency_threshold_adj = 1.0
            else:
                regime = 'low_vol'
                stop_loss_multiplier = 0.8  # Tighter stops in low volatility
                take_profit_multiplier = 0.9  # Lower targets
                emergency_threshold_adj = 1.2  # Looser emergency (120% of normal)

            # Analyze trend if returns provided
            trend_strength = 0.5
            trend_direction = 0
            if returns and len(returns) >= 10:
                recent_return = np.mean(returns[-10:])
                trend_strength = min(abs(recent_return) * 20, 1.0)  # Scale to 0-1
                trend_direction = np.sign(recent_return)

            return {
                'regime': regime,
                'volatility': volatility,
                'stop_loss_multiplier': stop_loss_multiplier,
                'take_profit_multiplier': take_profit_multiplier,
                'emergency_threshold_adj': emergency_threshold_adj,
                'trend_strength': trend_strength,
                'trend_direction': trend_direction
            }

        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            # Return neutral regime on error
            return {
                'regime': 'normal',
                'volatility': volatility,
                'stop_loss_multiplier': 1.0,
                'take_profit_multiplier': 1.0,
                'emergency_threshold_adj': 1.0,
                'trend_strength': 0.5,
                'trend_direction': 0
            }


class SmartStopLossManager:
    """
    Intelligent stop loss management with ATR and support/resistance awareness
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.regime_detector = MarketRegimeDetector()

    def calculate_adaptive_stop(self, entry_price: float, side: str,
                               atr: float, volatility: float,
                               support_resistance: Optional[Dict] = None,
                               base_stop_pct: float = 0.02) -> Dict:
        """
        Calculate adaptive stop loss using ATR and market conditions

        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            atr: Average True Range
            volatility: Current market volatility
            support_resistance: Dict with support/resistance levels
            base_stop_pct: Base stop loss percentage (default 2%)

        Returns:
            Dict with stop loss price and reasoning
        """
        try:
            # Detect market regime
            regime_info = self.regime_detector.detect_regime(volatility)

            # ATR-based stop loss (2-3x ATR from entry)
            atr_multiplier = 2.5 * regime_info['stop_loss_multiplier']
            atr_stop_distance = atr * atr_multiplier

            # Percentage-based stop loss
            pct_stop_distance = entry_price * base_stop_pct * regime_info['stop_loss_multiplier']

            # Use wider of ATR or percentage
            stop_distance = max(atr_stop_distance, pct_stop_distance)

            # Calculate initial stop price
            if side == 'long':
                stop_price = entry_price - stop_distance
            else:
                stop_price = entry_price + stop_distance

            # Adjust for support/resistance if available
            adjusted = False
            if support_resistance:
                if side == 'long' and support_resistance.get('support'):
                    # Find nearest support below entry
                    nearest_support = None
                    for level in support_resistance['support']:
                        support_price = level['price']
                        if support_price < entry_price:
                            if nearest_support is None or support_price > nearest_support:
                                nearest_support = support_price

                    # Place stop slightly below support (0.5%)
                    if nearest_support and nearest_support > stop_price:
                        stop_price = nearest_support * 0.995
                        adjusted = True
                        self.logger.debug(f"Stop adjusted to support level: {stop_price:.2f}")

                elif side == 'short' and support_resistance.get('resistance'):
                    # Find nearest resistance above entry
                    nearest_resistance = None
                    for level in support_resistance['resistance']:
                        resistance_price = level['price']
                        if resistance_price > entry_price:
                            if nearest_resistance is None or resistance_price < nearest_resistance:
                                nearest_resistance = resistance_price

                    # Place stop slightly above resistance (0.5%)
                    if nearest_resistance and nearest_resistance < stop_price:
                        stop_price = nearest_resistance * 1.005
                        adjusted = True
                        self.logger.debug(f"Stop adjusted to resistance level: {stop_price:.2f}")

            # Calculate stop loss percentage
            stop_pct = abs(stop_price - entry_price) / entry_price

            return {
                'stop_price': stop_price,
                'stop_pct': stop_pct,
                'atr_distance': atr_stop_distance,
                'pct_distance': pct_stop_distance,
                'regime': regime_info['regime'],
                'adjusted_for_sr': adjusted,
                'reasoning': f"{regime_info['regime']} regime, ATR={atr:.2f}, stop={stop_pct:.2%}"
            }

        except Exception as e:
            self.logger.error(f"Error calculating adaptive stop: {e}")
            # Fallback to simple percentage stop
            if side == 'long':
                stop_price = entry_price * (1 - base_stop_pct)
            else:
                stop_price = entry_price * (1 + base_stop_pct)

            return {
                'stop_price': stop_price,
                'stop_pct': base_stop_pct,
                'atr_distance': 0,
                'pct_distance': entry_price * base_stop_pct,
                'regime': 'normal',
                'adjusted_for_sr': False,
                'reasoning': 'Fallback to base stop'
            }


class SmartTakeProfitManager:
    """
    Intelligent take profit management with volume profile and trend awareness
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.regime_detector = MarketRegimeDetector()

    def calculate_adaptive_target(self, entry_price: float, side: str,
                                 atr: float, volatility: float,
                                 trend_strength: float = 0.5,
                                 volume_profile: Optional[Dict] = None,
                                 support_resistance: Optional[Dict] = None,
                                 base_target_pct: float = 0.04) -> Dict:
        """
        Calculate adaptive take profit using volume profile and trend analysis

        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            atr: Average True Range
            volatility: Current market volatility
            trend_strength: Strength of current trend (0-1)
            volume_profile: Volume profile data
            support_resistance: Support/resistance levels
            base_target_pct: Base take profit percentage (default 4%)

        Returns:
            Dict with take profit price and reasoning
        """
        try:
            # Detect market regime
            regime_info = self.regime_detector.detect_regime(volatility)

            # Base target from ATR (3-5x ATR from entry, scaled by regime)
            atr_multiplier = 4.0 * regime_info['take_profit_multiplier']
            atr_target_distance = atr * atr_multiplier

            # Percentage-based target
            pct_target_distance = entry_price * base_target_pct * regime_info['take_profit_multiplier']

            # Trend strength adjustment - hold longer in strong trends
            if trend_strength > 0.7:
                trend_multiplier = 1.4  # 40% higher target in strong trends
            elif trend_strength > 0.5:
                trend_multiplier = 1.2
            else:
                trend_multiplier = 1.0

            pct_target_distance *= trend_multiplier

            # Use wider of ATR or percentage
            target_distance = max(atr_target_distance, pct_target_distance)

            # Calculate initial target price
            if side == 'long':
                target_price = entry_price + target_distance
            else:
                target_price = entry_price - target_distance

            # Adjust for volume profile if available
            vp_adjusted = False
            if volume_profile and volume_profile.get('high_volume_nodes'):
                # Find high volume node near our target
                hvn = volume_profile['high_volume_nodes']
                for node in hvn:
                    node_price = node.get('price', 0)
                    if node_price == 0:
                        continue

                    # Check if node is in target direction and within range
                    if side == 'long' and node_price > entry_price:
                        distance_from_entry = node_price - entry_price
                        distance_from_target = abs(node_price - target_price)

                        # If node is 10-150% of current target distance
                        if 0.10 * target_distance <= distance_from_entry <= 1.5 * target_distance:
                            # Adjust target to high volume node (97% to be conservative)
                            target_price = node_price * 0.97
                            vp_adjusted = True
                            self.logger.debug(f"TP adjusted to volume node: {target_price:.2f}")
                            break

                    elif side == 'short' and node_price < entry_price:
                        distance_from_entry = entry_price - node_price
                        distance_from_target = abs(target_price - node_price)

                        if 0.10 * target_distance <= distance_from_entry <= 1.5 * target_distance:
                            target_price = node_price * 1.03
                            vp_adjusted = True
                            self.logger.debug(f"TP adjusted to volume node: {target_price:.2f}")
                            break

            # Final adjustment for support/resistance
            sr_adjusted = False
            if not vp_adjusted and support_resistance:
                if side == 'long' and support_resistance.get('resistance'):
                    # Find nearest resistance above entry
                    for level in support_resistance['resistance']:
                        resistance_price = level['price']
                        if entry_price < resistance_price < target_price * 1.1:
                            # Cap target slightly below resistance
                            target_price = resistance_price * 0.97
                            sr_adjusted = True
                            self.logger.debug(f"TP capped at resistance: {target_price:.2f}")
                            break

                elif side == 'short' and support_resistance.get('support'):
                    # Find nearest support below entry
                    for level in support_resistance['support']:
                        support_price = level['price']
                        if target_price * 0.9 < support_price < entry_price:
                            # Cap target slightly above support
                            target_price = support_price * 1.03
                            sr_adjusted = True
                            self.logger.debug(f"TP capped at support: {target_price:.2f}")
                            break

            # Calculate take profit percentage
            target_pct = abs(target_price - entry_price) / entry_price

            return {
                'target_price': target_price,
                'target_pct': target_pct,
                'atr_distance': atr_target_distance,
                'pct_distance': pct_target_distance,
                'regime': regime_info['regime'],
                'trend_multiplier': trend_multiplier,
                'vp_adjusted': vp_adjusted,
                'sr_adjusted': sr_adjusted,
                'reasoning': f"{regime_info['regime']} regime, trend_str={trend_strength:.1f}, target={target_pct:.2%}"
            }

        except Exception as e:
            self.logger.error(f"Error calculating adaptive target: {e}")
            # Fallback to simple percentage target
            if side == 'long':
                target_price = entry_price * (1 + base_target_pct)
            else:
                target_price = entry_price * (1 - base_target_pct)

            return {
                'target_price': target_price,
                'target_pct': base_target_pct,
                'atr_distance': 0,
                'pct_distance': entry_price * base_target_pct,
                'regime': 'normal',
                'trend_multiplier': 1.0,
                'vp_adjusted': False,
                'sr_adjusted': False,
                'reasoning': 'Fallback to base target'
            }


class AdaptiveEmergencyManager:
    """
    Adaptive emergency stop system with regime-aware thresholds
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.regime_detector = MarketRegimeDetector()

        # Base emergency thresholds (ROI percentages)
        self.base_emergency_levels = {
            'level_1': -0.40,  # Liquidation risk
            'level_2': -0.25,  # Severe loss
            'level_3': -0.15   # Excessive loss
        }

    def get_adaptive_thresholds(self, volatility: float,
                               current_drawdown: float = 0.0,
                               portfolio_correlation: float = 0.5) -> Dict:
        """
        Calculate adaptive emergency thresholds based on market conditions

        Args:
            volatility: Current market volatility
            current_drawdown: Current account drawdown (0-1)
            portfolio_correlation: Portfolio correlation measure (0-1)

        Returns:
            Dict with adaptive emergency levels and reasoning
        """
        try:
            # Detect market regime
            regime_info = self.regime_detector.detect_regime(volatility)
            regime_adj = regime_info['emergency_threshold_adj']

            # Drawdown adjustment - tighten if in drawdown
            if current_drawdown > 0.15:
                drawdown_adj = 0.7  # 30% tighter
            elif current_drawdown > 0.10:
                drawdown_adj = 0.85  # 15% tighter
            else:
                drawdown_adj = 1.0

            # Correlation adjustment - tighten if portfolio is concentrated
            if portfolio_correlation > 0.8:
                correlation_adj = 0.8  # 20% tighter
            elif portfolio_correlation > 0.6:
                correlation_adj = 0.9  # 10% tighter
            else:
                correlation_adj = 1.0

            # Combined adjustment (take most conservative)
            combined_adj = min(regime_adj, drawdown_adj, correlation_adj)

            # Apply adjustments to base levels
            adaptive_levels = {
                'level_1': self.base_emergency_levels['level_1'] * combined_adj,
                'level_2': self.base_emergency_levels['level_2'] * combined_adj,
                'level_3': self.base_emergency_levels['level_3'] * combined_adj
            }

            return {
                'thresholds': adaptive_levels,
                'regime': regime_info['regime'],
                'regime_adj': regime_adj,
                'drawdown_adj': drawdown_adj,
                'correlation_adj': correlation_adj,
                'combined_adj': combined_adj,
                'reasoning': (
                    f"{regime_info['regime']} regime, "
                    f"drawdown={current_drawdown:.1%}, "
                    f"correlation={portfolio_correlation:.1%}"
                )
            }

        except Exception as e:
            self.logger.error(f"Error calculating adaptive thresholds: {e}")
            # Return base levels on error
            return {
                'thresholds': self.base_emergency_levels.copy(),
                'regime': 'normal',
                'regime_adj': 1.0,
                'drawdown_adj': 1.0,
                'correlation_adj': 1.0,
                'combined_adj': 1.0,
                'reasoning': 'Fallback to base thresholds'
            }

    def should_trigger_emergency(self, current_pnl: float,
                                volatility: float,
                                current_drawdown: float = 0.0,
                                portfolio_correlation: float = 0.5) -> Tuple[bool, str]:
        """
        Check if emergency stop should trigger based on adaptive thresholds

        Args:
            current_pnl: Current position P&L (leveraged ROI)
            volatility: Current market volatility
            current_drawdown: Current account drawdown
            portfolio_correlation: Portfolio correlation measure

        Returns:
            Tuple of (should_trigger, reason)
        """
        try:
            # Get adaptive thresholds
            threshold_info = self.get_adaptive_thresholds(
                volatility, current_drawdown, portfolio_correlation
            )

            thresholds = threshold_info['thresholds']

            # Check each level
            if current_pnl <= thresholds['level_1']:
                return True, f"Emergency Level 1: {current_pnl:.1%} ≤ {thresholds['level_1']:.1%} (liquidation risk, {threshold_info['regime']})"

            if current_pnl <= thresholds['level_2']:
                return True, f"Emergency Level 2: {current_pnl:.1%} ≤ {thresholds['level_2']:.1%} (severe loss, {threshold_info['regime']})"

            if current_pnl <= thresholds['level_3']:
                return True, f"Emergency Level 3: {current_pnl:.1%} ≤ {thresholds['level_3']:.1%} (excessive loss, {threshold_info['regime']})"

            return False, ""

        except Exception as e:
            self.logger.error(f"Error checking emergency trigger: {e}")
            # Fallback to base levels
            if current_pnl <= self.base_emergency_levels['level_1']:
                return True, f"Emergency Level 1 (fallback): {current_pnl:.1%}"
            if current_pnl <= self.base_emergency_levels['level_2']:
                return True, f"Emergency Level 2 (fallback): {current_pnl:.1%}"
            if current_pnl <= self.base_emergency_levels['level_3']:
                return True, f"Emergency Level 3 (fallback): {current_pnl:.1%}"

            return False, ""


class SmartAdaptiveExitManager:
    """
    Main coordinator for smart and adaptive exit management
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.stop_loss_manager = SmartStopLossManager()
        self.take_profit_manager = SmartTakeProfitManager()
        self.emergency_manager = AdaptiveEmergencyManager()

    def calculate_smart_targets(self, entry_price: float, side: str,
                               atr: float, volatility: float,
                               trend_strength: float = 0.5,
                               volume_profile: Optional[Dict] = None,
                               support_resistance: Optional[Dict] = None,
                               current_drawdown: float = 0.0,
                               portfolio_correlation: float = 0.5) -> Dict:
        """
        Calculate complete set of smart and adaptive targets

        Args:
            entry_price: Position entry price
            side: 'long' or 'short'
            atr: Average True Range
            volatility: Current market volatility
            trend_strength: Strength of current trend
            volume_profile: Volume profile data
            support_resistance: Support/resistance levels
            current_drawdown: Current account drawdown
            portfolio_correlation: Portfolio correlation measure

        Returns:
            Dict with stop loss, take profit, and emergency thresholds
        """
        try:
            # Calculate adaptive stop loss
            stop_info = self.stop_loss_manager.calculate_adaptive_stop(
                entry_price, side, atr, volatility, support_resistance
            )

            # Calculate adaptive take profit
            target_info = self.take_profit_manager.calculate_adaptive_target(
                entry_price, side, atr, volatility, trend_strength,
                volume_profile, support_resistance
            )

            # Get adaptive emergency thresholds
            emergency_info = self.emergency_manager.get_adaptive_thresholds(
                volatility, current_drawdown, portfolio_correlation
            )

            return {
                'stop_loss': stop_info,
                'take_profit': target_info,
                'emergency': emergency_info,
                'summary': {
                    'stop_price': stop_info['stop_price'],
                    'stop_pct': stop_info['stop_pct'],
                    'target_price': target_info['target_price'],
                    'target_pct': target_info['target_pct'],
                    'risk_reward_ratio': target_info['target_pct'] / stop_info['stop_pct'],
                    'regime': stop_info['regime']
                }
            }

        except Exception as e:
            self.logger.error(f"Error calculating smart targets: {e}")
            # Return minimal safe defaults
            if side == 'long':
                stop_price = entry_price * 0.98
                target_price = entry_price * 1.04
            else:
                stop_price = entry_price * 1.02
                target_price = entry_price * 0.96

            return {
                'stop_loss': {'stop_price': stop_price, 'stop_pct': 0.02, 'reasoning': 'Fallback'},
                'take_profit': {'target_price': target_price, 'target_pct': 0.04, 'reasoning': 'Fallback'},
                'emergency': {'thresholds': self.emergency_manager.base_emergency_levels, 'reasoning': 'Fallback'},
                'summary': {
                    'stop_price': stop_price,
                    'stop_pct': 0.02,
                    'target_price': target_price,
                    'target_pct': 0.04,
                    'risk_reward_ratio': 2.0,
                    'regime': 'normal'
                }
            }
