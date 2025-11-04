"""
Market Microstructure Analysis for 2026
Advanced order flow, liquidity, and market impact analysis
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from logger import Logger


class MarketMicrostructure2026:
    """
    Advanced market microstructure analysis:
    - Order flow imbalance detection
    - Liquidity analysis (spread, depth, resilience)
    - Market impact estimation
    - Smart order timing
    - Trade execution quality metrics
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.order_flow_history = []
        self.liquidity_metrics = {}

        self.logger.info("📊 Market Microstructure 2026 initialized")

    def analyze_order_book_imbalance(self, orderbook: Dict) -> Dict:
        """
        Analyze order book for bid/ask imbalance

        Args:
            orderbook: Order book data with bids and asks

        Returns:
            Dictionary with imbalance metrics
        """
        try:
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])

            if not bids or not asks:
                return {
                    'imbalance': 0.0,
                    'signal': 'neutral',
                    'confidence': 0.0
                }

            # Calculate total bid and ask volume (top 10 levels)
            top_n = min(10, len(bids), len(asks))

            bid_volume = sum(float(bid[1]) for bid in bids[:top_n])
            ask_volume = sum(float(ask[1]) for ask in asks[:top_n])

            # Imbalance ratio (-1 to 1, negative = ask heavy, positive = bid heavy)
            total_volume = bid_volume + ask_volume
            if total_volume > 0:
                imbalance = (bid_volume - ask_volume) / total_volume
            else:
                imbalance = 0.0

            # Calculate bid-ask spread
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            mid_price = (best_bid + best_ask) / 2
            spread = (best_ask - best_bid) / mid_price if mid_price > 0 else 0.0

            # Depth at bid/ask
            bid_depth = bid_volume
            ask_depth = ask_volume

            # Signal interpretation
            if imbalance > 0.3:
                signal = 'bullish'
                confidence = min(abs(imbalance), 0.8)
            elif imbalance < -0.3:
                signal = 'bearish'
                confidence = min(abs(imbalance), 0.8)
            else:
                signal = 'neutral'
                confidence = 0.3

            metrics = {
                'imbalance': imbalance,
                'signal': signal,
                'confidence': confidence,
                'spread': spread,
                'spread_bps': spread * 10000,  # in basis points
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'best_bid': best_bid,
                'best_ask': best_ask
            }

            self.logger.debug(
                f"Order book imbalance: {imbalance:.3f} ({signal}), "
                f"spread: {spread*100:.3f}%, confidence: {confidence:.2f}"
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error analyzing order book: {e}")
            return {
                'imbalance': 0.0,
                'signal': 'neutral',
                'confidence': 0.0
            }

    def calculate_liquidity_score(self, orderbook: Dict,
                                  volume_24h: float,
                                  recent_trades: List[Dict]) -> float:
        """
        Calculate comprehensive liquidity score (0-1)

        Args:
            orderbook: Current order book
            volume_24h: 24-hour trading volume
            recent_trades: Recent trade history

        Returns:
            Liquidity score (0-1, higher is better)
        """
        try:
            score_components = []

            # Component 1: Volume (0-0.3)
            # Adjusted thresholds to be realistic for mid-cap pairs
            # Good liquidity: > $1M daily volume (was $10M)
            if volume_24h > 1_000_000:
                volume_score = 0.3
            elif volume_24h > 500_000:
                volume_score = 0.25
            elif volume_24h > 100_000:
                volume_score = 0.2
            elif volume_24h > 50_000:
                volume_score = 0.15
            else:
                volume_score = 0.05
            score_components.append(volume_score)

            # Component 2: Spread (0-0.3)
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])

            if bids and asks:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                spread = (best_ask - best_bid) / best_bid

                # Tight spread = good liquidity
                if spread < 0.0005:  # < 0.05%
                    spread_score = 0.3
                elif spread < 0.001:  # < 0.1%
                    spread_score = 0.2
                elif spread < 0.002:  # < 0.2%
                    spread_score = 0.1
                else:
                    spread_score = 0.05
                score_components.append(spread_score)

            # Component 3: Depth (0-0.2)
            if bids and asks:
                bid_volume = sum(float(bid[1]) for bid in bids[:10])
                ask_volume = sum(float(ask[1]) for ask in asks[:10])
                total_depth = bid_volume + ask_volume

                # Adjusted depth thresholds to be more realistic
                # Good depth: > $10k in top 10 levels (was $100k)
                if total_depth > 10_000:
                    depth_score = 0.2
                elif total_depth > 5_000:
                    depth_score = 0.15
                elif total_depth > 1_000:
                    depth_score = 0.1
                else:
                    depth_score = 0.05
                score_components.append(depth_score)

            # Component 4: Trade frequency (0-0.2)
            if recent_trades:
                trades_per_minute = len(recent_trades) / 5  # Assuming 5 min window

                if trades_per_minute > 10:
                    frequency_score = 0.2
                elif trades_per_minute > 5:
                    frequency_score = 0.15
                elif trades_per_minute > 1:
                    frequency_score = 0.1
                else:
                    frequency_score = 0.05
                score_components.append(frequency_score)

            total_score = sum(score_components)

            self.logger.debug(f"Liquidity score: {total_score:.2f} (components: {score_components})")

            return total_score

        except Exception as e:
            self.logger.error(f"Error calculating liquidity score: {e}")
            return 0.5  # Default moderate liquidity

    def estimate_market_impact(self, order_size: float,
                              orderbook: Dict,
                              daily_volume: float) -> Dict:
        """
        Estimate market impact of an order

        Args:
            order_size: Size of order in USDT
            orderbook: Current order book
            daily_volume: 24-hour trading volume

        Returns:
            Dictionary with impact estimates
        """
        try:
            # Volume ratio (order size vs daily volume)
            volume_ratio = order_size / daily_volume if daily_volume > 0 else 0.0

            # Estimate slippage based on order book depth
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])

            if not bids or not asks:
                return {
                    'estimated_slippage': 0.005,  # 0.5% default
                    'impact_category': 'medium',
                    'recommendation': 'Use limit order'
                }

            # Walk through order book to estimate fill
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            mid_price = (best_bid + best_ask) / 2

            # Simple impact model: slippage increases with volume ratio
            base_slippage = 0.0005  # 0.05% base

            if volume_ratio < 0.001:  # < 0.1% of daily volume
                slippage = base_slippage
                impact = 'low'
                recommendation = 'Market order OK'
            elif volume_ratio < 0.005:  # < 0.5%
                slippage = base_slippage * 2
                impact = 'low'
                recommendation = 'Limit order recommended'
            elif volume_ratio < 0.01:  # < 1%
                slippage = base_slippage * 4
                impact = 'medium'
                recommendation = 'Use TWAP or limit orders'
            else:  # > 1%
                slippage = base_slippage * 8
                impact = 'high'
                recommendation = 'Split order, use TWAP/VWAP'

            return {
                'estimated_slippage': slippage,
                'slippage_bps': slippage * 10000,
                'impact_category': impact,
                'volume_ratio': volume_ratio,
                'recommendation': recommendation
            }

        except Exception as e:
            self.logger.error(f"Error estimating market impact: {e}")
            return {
                'estimated_slippage': 0.005,
                'impact_category': 'medium',
                'recommendation': 'Use limit order'
            }

    def optimize_entry_timing(self, orderbook_imbalance: float,
                             recent_volume: float,
                             avg_volume: float,
                             momentum: float) -> Dict:
        """
        Determine optimal entry timing based on microstructure

        Args:
            orderbook_imbalance: Current order book imbalance (-1 to 1)
            recent_volume: Recent volume (last 5 min)
            avg_volume: Average volume
            momentum: Price momentum

        Returns:
            Dictionary with timing recommendation
        """
        score = 0.0
        reasons = []

        # Favor entries when order book supports our direction
        if momentum > 0 and orderbook_imbalance > 0.2:
            score += 0.3
            reasons.append("Order book favors longs")
        elif momentum < 0 and orderbook_imbalance < -0.2:
            score += 0.3
            reasons.append("Order book favors shorts")

        # Favor entries during elevated volume
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        if 1.2 < volume_ratio < 2.0:
            score += 0.3
            reasons.append(f"Good volume (ratio: {volume_ratio:.2f})")
        elif volume_ratio > 2.0:
            score += 0.1  # Very high volume might indicate climax
            reasons.append(f"Very high volume (ratio: {volume_ratio:.2f})")

        # Penalize extreme imbalances (might reverse)
        if abs(orderbook_imbalance) > 0.7:
            score -= 0.2
            reasons.append("Extreme imbalance - caution")

        # Clamp score
        score = max(0.0, min(1.0, score))

        if score > 0.7:
            timing = 'excellent'
            action = 'Enter now'
        elif score > 0.5:
            timing = 'good'
            action = 'Enter with limit order'
        elif score > 0.3:
            timing = 'neutral'
            action = 'Wait for better setup'
        else:
            timing = 'poor'
            action = 'Wait'

        return {
            'timing_score': score,
            'timing_quality': timing,
            'recommended_action': action,
            'reasons': reasons
        }

    def analyze_trade_quality(self, entry_price: float,
                            intended_price: float,
                            executed_volume: float,
                            execution_time: float) -> Dict:
        """
        Analyze the quality of a completed trade execution

        Args:
            entry_price: Actual entry price
            intended_price: Intended entry price (limit price)
            executed_volume: Volume executed
            execution_time: Time to execute (seconds)

        Returns:
            Dictionary with execution quality metrics
        """
        # Slippage
        slippage = (entry_price - intended_price) / intended_price
        slippage_bps = slippage * 10000

        # Execution speed score
        if execution_time < 1:
            speed_score = 1.0
        elif execution_time < 5:
            speed_score = 0.8
        elif execution_time < 30:
            speed_score = 0.6
        else:
            speed_score = 0.3

        # Overall quality score
        slippage_penalty = min(abs(slippage_bps) / 10, 1.0)  # Penalize > 10 bps
        quality_score = (speed_score * 0.5) + ((1 - slippage_penalty) * 0.5)

        if quality_score > 0.8:
            quality = 'excellent'
        elif quality_score > 0.6:
            quality = 'good'
        elif quality_score > 0.4:
            quality = 'acceptable'
        else:
            quality = 'poor'

        return {
            'slippage': slippage,
            'slippage_bps': slippage_bps,
            'execution_time': execution_time,
            'speed_score': speed_score,
            'quality_score': quality_score,
            'quality_rating': quality
        }

    def detect_spoofing(self, orderbook_history: List[Dict]) -> Dict:
        """
        Detect potential spoofing in order book

        Spoofing is when large orders appear on one side to manipulate price,
        then disappear before execution. We detect this by looking for:
        1. Large orders that appear suddenly
        2. These orders disappear within a few snapshots
        3. This happens repeatedly (pattern)

        Args:
            orderbook_history: List of recent order book snapshots

        Returns:
            Dictionary with spoofing detection results
        """
        if len(orderbook_history) < 5:
            return {
                'spoofing_detected': False,
                'confidence': 0.0
            }

        try:
            large_order_threshold = 0.25  # 25% of total volume in level
            spoof_signals = 0

            for i in range(len(orderbook_history) - 2):
                current_book = orderbook_history[i]
                next_book = orderbook_history[i + 1]

                if not current_book.get('bids') or not current_book.get('asks'):
                    continue
                if not next_book.get('bids') or not next_book.get('asks'):
                    continue

                # Analyze top 5 levels on each side
                for side in ['bids', 'asks']:
                    current_orders = current_book[side][:5]
                    next_orders = next_book[side][:5]

                    if not current_orders or not next_orders:
                        continue

                    # Calculate total volume at current level
                    total_volume = sum(float(order[1]) for order in current_orders)

                    if total_volume == 0:
                        continue

                    # Check each level for large orders
                    for j, current_order in enumerate(current_orders):
                        current_price = float(current_order[0])
                        current_volume = float(current_order[1])

                        # Is this a large order?
                        volume_ratio = current_volume / total_volume
                        if volume_ratio < large_order_threshold:
                            continue

                        # Check if this large order disappeared in next snapshot
                        order_found = False
                        for next_order in next_orders:
                            next_price = float(next_order[0])
                            next_volume = float(next_order[1])

                            # Same price level within 0.1% tolerance
                            if abs(next_price - current_price) / current_price < 0.001:
                                # Check if volume remained significant
                                if next_volume >= current_volume * 0.5:
                                    order_found = True
                                    break

                        # Large order disappeared = potential spoof
                        if not order_found:
                            spoof_signals += 1

            # Calculate confidence based on frequency of disappearing orders
            # More disappearances = higher confidence in spoofing
            max_possible_signals = (len(orderbook_history) - 2) * 2 * 5  # sides * levels
            if max_possible_signals > 0:
                confidence = min(spoof_signals / (max_possible_signals * 0.1), 1.0)
            else:
                confidence = 0.0

            detected = confidence > 0.3

            if detected:
                self.logger.warning(
                    f"⚠️ Potential spoofing detected: {spoof_signals} signals, "
                    f"confidence: {confidence:.2f}"
                )

            return {
                'spoofing_detected': detected,
                'confidence': confidence,
                'signal_count': spoof_signals
            }

        except Exception as e:
            self.logger.error(f"Error detecting spoofing: {e}")
            return {
                'spoofing_detected': False,
                'confidence': 0.0
            }
