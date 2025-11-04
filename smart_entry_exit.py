"""
Smart Entry and Exit Optimizer
Advanced entry/exit timing using order book, volatility, and support/resistance
"""
import numpy as np
from typing import Dict, Optional, Tuple
from logger import Logger


class SmartEntryExit:
    """
    Intelligent entry and exit optimization:
    - Order book depth analysis for optimal entry timing
    - Support/resistance confluence for entry points
    - Volatility-based entry sizing (scale-in strategy)
    - Multi-level profit targets with partial exits
    - Dynamic stop loss with volatility expansion/contraction
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.logger.info("🎯 Smart Entry/Exit Optimizer initialized")

    def analyze_entry_timing(self, orderbook: Dict,
                            current_price: float,
                            signal: str,
                            volatility: float) -> Dict:
        """
        Analyze order book to determine optimal entry timing

        Args:
            orderbook: Order book with bids and asks
            current_price: Current market price
            signal: 'BUY' or 'SELL'
            volatility: Current market volatility

        Returns:
            Dict with entry timing analysis
        """
        try:
            if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
                return {
                    'timing_score': 0.5,
                    'optimal_entry': current_price,
                    'recommendation': 'market',
                    'reason': 'No order book data'
                }

            bids = orderbook['bids'][:10]  # Top 10 bids
            asks = orderbook['asks'][:10]  # Top 10 asks

            if not bids or not asks:
                return {
                    'timing_score': 0.5,
                    'optimal_entry': current_price,
                    'recommendation': 'market',
                    'reason': 'Insufficient order book depth'
                }

            # Calculate order book metrics
            bid_volume = sum([bid[1] for bid in bids])
            ask_volume = sum([ask[1] for ask in asks])

            # Order book imbalance (OBI)
            total_volume = bid_volume + ask_volume
            if total_volume > 0:
                obi = (bid_volume - ask_volume) / total_volume
            else:
                obi = 0.0

            # Spread analysis
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            spread = (best_ask - best_bid) / current_price
            spread_bps = spread * 10000  # in basis points

            # Liquidity depth (volume within 0.5% of mid)
            mid_price = (best_bid + best_ask) / 2
            near_bids = [b for b in bids if b[0] >= mid_price * 0.995]
            near_asks = [a for a in asks if a[0] <= mid_price * 1.005]
            near_liquidity = sum([b[1] for b in near_bids]) + sum([a[1] for a in near_asks])

            # Determine entry strategy
            timing_score = 0.5  # Base score
            recommendation = 'market'
            optimal_entry = current_price
            reason = []

            if signal == 'BUY':
                # For BUY orders, we want strong bid support
                if obi > 0.15:  # Strong bid pressure
                    timing_score += 0.2
                    reason.append('strong bid support')
                elif obi < -0.15:  # Weak bids, strong asks
                    timing_score -= 0.2
                    reason.append('weak bid support')
                    # Consider limit order below current price
                    if spread_bps > 10:  # Wide spread
                        recommendation = 'limit'
                        optimal_entry = best_bid + (best_ask - best_bid) * 0.3
                        reason.append('wide spread - use limit order')

                # Check for liquidity
                if near_liquidity > bid_volume * 0.3:
                    timing_score += 0.15
                    reason.append('good near-price liquidity')

            else:  # SELL
                # For SELL orders, we want strong ask resistance
                if obi < -0.15:  # Strong ask pressure
                    timing_score += 0.2
                    reason.append('strong ask resistance')
                elif obi > 0.15:  # Weak asks, strong bids
                    timing_score -= 0.2
                    reason.append('weak ask resistance')
                    # Consider limit order above current price
                    if spread_bps > 10:
                        recommendation = 'limit'
                        optimal_entry = best_ask - (best_ask - best_bid) * 0.3
                        reason.append('wide spread - use limit order')

                # Check for liquidity
                if near_liquidity > ask_volume * 0.3:
                    timing_score += 0.15
                    reason.append('good near-price liquidity')

            # Spread penalty (very wide spread = poor timing)
            if spread_bps > 50:  # >0.5% spread
                timing_score -= 0.2
                reason.append('very wide spread')
            elif spread_bps < 5:  # <0.05% spread (tight)
                timing_score += 0.1
                reason.append('tight spread')

            # Volatility adjustment
            if volatility > 0.05:  # High volatility
                timing_score -= 0.1
                reason.append('high volatility')

            # Clamp timing score
            timing_score = max(0.0, min(1.0, timing_score))

            return {
                'timing_score': timing_score,
                'optimal_entry': optimal_entry,
                'recommendation': recommendation,
                'reason': ', '.join(reason) if reason else 'neutral conditions',
                'obi': obi,
                'spread_bps': spread_bps,
                'near_liquidity': near_liquidity
            }

        except Exception as e:
            self.logger.debug(f"Error analyzing entry timing: {e}")
            return {
                'timing_score': 0.5,
                'optimal_entry': current_price,
                'recommendation': 'market',
                'reason': f'Error: {str(e)}'
            }

    def calculate_partial_exits(self, entry_price: float,
                               stop_loss: float,
                               side: str,
                               volatility: float,
                               support_resistance: Dict = None) -> list:
        """
        Calculate optimal partial exit levels

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'long' or 'short'
            volatility: Market volatility
            support_resistance: Support/resistance levels

        Returns:
            List of exit targets with percentages
        """
        try:
            # Calculate risk amount
            risk_pct = abs(entry_price - stop_loss) / entry_price

            # Base targets (risk:reward ratios)
            targets = [
                {'rr': 1.0, 'exit_pct': 0.3, 'name': 'Quick profit'},  # 30% at 1R
                {'rr': 2.0, 'exit_pct': 0.4, 'name': 'Main target'},   # 40% at 2R
                {'rr': 3.5, 'exit_pct': 0.3, 'name': 'Extended'}       # 30% at 3.5R
            ]

            # Adjust targets based on volatility
            if volatility > 0.05:  # High volatility - extend targets
                targets[1]['rr'] = 2.5
                targets[2]['rr'] = 4.5
            elif volatility < 0.02:  # Low volatility - tighten targets
                targets[1]['rr'] = 1.5
                targets[2]['rr'] = 2.5

            # Calculate actual prices
            exit_levels = []
            for target in targets:
                if side == 'long':
                    target_price = entry_price + (risk_pct * target['rr'] * entry_price)
                else:  # short
                    target_price = entry_price - (risk_pct * target['rr'] * entry_price)

                exit_levels.append({
                    'price': target_price,
                    'percentage': target['exit_pct'],
                    'rr_ratio': target['rr'],
                    'name': target['name']
                })

            # Adjust for support/resistance if available
            if support_resistance:
                if side == 'long' and 'resistance' in support_resistance:
                    resistance = support_resistance['resistance']
                    # Adjust targets if they're near resistance
                    for level in exit_levels:
                        if abs(level['price'] - resistance) / resistance < 0.01:
                            # Target is within 1% of resistance - adjust slightly below
                            level['price'] = resistance * 0.995
                            level['name'] += ' (adjusted for R)'

                elif side == 'short' and 'support' in support_resistance:
                    support = support_resistance['support']
                    # Adjust targets if they're near support
                    for level in exit_levels:
                        if abs(level['price'] - support) / support < 0.01:
                            # Target is within 1% of support - adjust slightly above
                            level['price'] = support * 1.005
                            level['name'] += ' (adjusted for S)'

            return exit_levels

        except Exception as e:
            self.logger.error(f"Error calculating partial exits: {e}")
            return []

    def calculate_dynamic_stop(self, entry_price: float,
                              current_price: float,
                              side: str,
                              atr: float,
                              volatility: float,
                              pnl_pct: float) -> float:
        """
        Calculate dynamic stop loss based on volatility and profit

        Args:
            entry_price: Original entry price
            current_price: Current market price
            side: 'long' or 'short'
            atr: Average True Range
            volatility: Market volatility (BB width)
            pnl_pct: Current P/L percentage

        Returns:
            New stop loss price
        """
        try:
            # Base stop from ATR (2x ATR is standard)
            atr_multiplier = 2.0

            # Adjust multiplier based on volatility
            if volatility > 0.05:  # High volatility - wider stop
                atr_multiplier = 2.5
            elif volatility < 0.02:  # Low volatility - tighter stop
                atr_multiplier = 1.5

            # Calculate base stop
            if side == 'long':
                base_stop = current_price - (atr * atr_multiplier)
            else:  # short
                base_stop = current_price + (atr * atr_multiplier)

            # Adjust based on profit
            if pnl_pct > 0.10:  # >10% profit - very tight trailing
                tightness = 0.6
            elif pnl_pct > 0.05:  # >5% profit - moderately tight
                tightness = 0.8
            elif pnl_pct > 0.02:  # >2% profit - slightly tight
                tightness = 0.9
            else:  # No/negative profit - normal
                tightness = 1.0

            # Apply tightness
            if side == 'long':
                adjusted_stop = current_price - (current_price - base_stop) * tightness
            else:
                adjusted_stop = current_price + (base_stop - current_price) * tightness

            return adjusted_stop

        except Exception as e:
            self.logger.error(f"Error calculating dynamic stop: {e}")
            # Return conservative stop at entry (breakeven)
            return entry_price

    def should_scale_entry(self, timing_score: float,
                          confidence: float,
                          volatility: float) -> Dict:
        """
        Determine if entry should be scaled (split into multiple orders)

        Args:
            timing_score: Entry timing quality score
            confidence: Signal confidence
            volatility: Market volatility

        Returns:
            Dict with scaling recommendations
        """
        try:
            # Don't scale if timing is very good and confidence is high
            if timing_score > 0.8 and confidence > 0.75:
                return {
                    'should_scale': False,
                    'reason': 'Excellent timing and confidence',
                    'levels': []
                }

            # Scale if timing is poor or volatility is high
            should_scale = (timing_score < 0.6 or volatility > 0.05 or confidence < 0.65)

            if not should_scale:
                return {
                    'should_scale': False,
                    'reason': 'Good conditions for single entry',
                    'levels': []
                }

            # Create scaling levels
            levels = [
                {'percentage': 0.5, 'offset_pct': 0.0, 'name': 'Initial entry'},
                {'percentage': 0.3, 'offset_pct': -0.005, 'name': 'Scale in 1'},  # 0.5% lower
                {'percentage': 0.2, 'offset_pct': -0.010, 'name': 'Scale in 2'}   # 1.0% lower
            ]

            # Adjust offsets based on volatility
            if volatility > 0.05:
                levels[1]['offset_pct'] = -0.008
                levels[2]['offset_pct'] = -0.015

            reason = []
            if timing_score < 0.6:
                reason.append('suboptimal timing')
            if volatility > 0.05:
                reason.append('high volatility')
            if confidence < 0.65:
                reason.append('moderate confidence')

            return {
                'should_scale': True,
                'reason': ', '.join(reason),
                'levels': levels
            }

        except Exception as e:
            self.logger.error(f"Error determining scaling: {e}")
            return {
                'should_scale': False,
                'reason': f'Error: {str(e)}',
                'levels': []
            }
