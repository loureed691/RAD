"""
Market Microstructure Analysis for 2026
Advanced order flow, liquidity, and market impact analysis

Enhanced with:
- Microprice calculation (volume-weighted mid-price)
- Queue Imbalance (QI) and Order Flow Imbalance (OFI) metrics
- Kyle's lambda (price impact coefficient)
- Bid-ask spread decomposition
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque
from logger import Logger


class MarketMicrostructure2026:
    """
    Advanced market microstructure analysis:
    - Order flow imbalance detection
    - Liquidity analysis (spread, depth, resilience)
    - Market impact estimation
    - Smart order timing
    - Trade execution quality metrics
    - Microprice calculation
    - Queue Imbalance (QI) and Order Flow Imbalance (OFI)
    - Kyle's lambda estimation
    """

    def __init__(self, history_length: int = 100):
        self.logger = Logger.get_logger()
        self.order_flow_history = deque(maxlen=history_length)
        self.liquidity_metrics = {}
        self.trade_history = deque(maxlen=history_length)
        self.orderbook_history = deque(maxlen=history_length)
        
        # For Kyle's lambda estimation
        self.price_changes = deque(maxlen=history_length)
        self.signed_volumes = deque(maxlen=history_length)
        self.kyle_lambda = 0.0
        
        self.logger.info("📊 Market Microstructure 2026 initialized with enhanced metrics")

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

            return {
                'spoofing_detected': False,
                'confidence': 0.0
            }
    
    def calculate_microprice(self, orderbook: Dict) -> Optional[float]:
        """
        Calculate microprice - volume-weighted mid-price.
        
        Microprice is a better estimate of the true value than simple mid-price
        as it accounts for depth at best bid/ask levels.
        
        Formula: microprice = (ask_vol * bid + bid_vol * ask) / (bid_vol + ask_vol)
        
        Args:
            orderbook: Order book with bids and asks
            
        Returns:
            Microprice or None if calculation fails
        """
        try:
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return None
            
            best_bid_price = float(bids[0][0])
            best_bid_vol = float(bids[0][1])
            best_ask_price = float(asks[0][0])
            best_ask_vol = float(asks[0][1])
            
            total_vol = best_bid_vol + best_ask_vol
            if total_vol == 0:
                return (best_bid_price + best_ask_price) / 2
            
            # Volume-weighted mid-price
            microprice = (best_ask_vol * best_bid_price + best_bid_vol * best_ask_price) / total_vol
            
            return microprice
            
        except Exception as e:
            self.logger.error(f"Error calculating microprice: {e}")
            return None
    
    def calculate_queue_imbalance(self, orderbook: Dict, levels: int = 5) -> Dict:
        """
        Calculate Queue Imbalance (QI) metric.
        
        QI measures the difference in cumulative depth on bid vs ask side,
        normalized by total depth. Strong predictor of short-term price moves.
        
        QI = (sum(bid_qty) - sum(ask_qty)) / (sum(bid_qty) + sum(ask_qty))
        
        Args:
            orderbook: Order book with bids and asks
            levels: Number of order book levels to consider
            
        Returns:
            Dictionary with QI metrics
        """
        try:
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return {
                    'queue_imbalance': 0.0,
                    'signal': 'neutral',
                    'strength': 0.0
                }
            
            # Calculate cumulative depth for specified levels
            n_levels = min(levels, len(bids), len(asks))
            
            bid_qty = sum(float(bids[i][1]) for i in range(n_levels))
            ask_qty = sum(float(asks[i][1]) for i in range(n_levels))
            
            total_qty = bid_qty + ask_qty
            if total_qty == 0:
                qi = 0.0
            else:
                qi = (bid_qty - ask_qty) / total_qty
            
            # Interpret signal
            # QI > 0.2: strong buy pressure
            # QI < -0.2: strong sell pressure
            if qi > 0.2:
                signal = 'strong_buy'
                strength = min(abs(qi), 1.0)
            elif qi > 0.05:
                signal = 'weak_buy'
                strength = min(abs(qi) * 2, 1.0)
            elif qi < -0.2:
                signal = 'strong_sell'
                strength = min(abs(qi), 1.0)
            elif qi < -0.05:
                signal = 'weak_sell'
                strength = min(abs(qi) * 2, 1.0)
            else:
                signal = 'neutral'
                strength = 0.3
            
            return {
                'queue_imbalance': qi,
                'signal': signal,
                'strength': strength,
                'bid_depth': bid_qty,
                'ask_depth': ask_qty,
                'levels_analyzed': n_levels
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating queue imbalance: {e}")
            return {
                'queue_imbalance': 0.0,
                'signal': 'neutral',
                'strength': 0.0
            }
    
    def calculate_order_flow_imbalance(
        self,
        recent_trades: List[Dict],
        window_seconds: int = 60
    ) -> Dict:
        """
        Calculate Order Flow Imbalance (OFI) from recent trades.
        
        OFI measures the net buying/selling pressure from executed market orders.
        Positive OFI indicates more aggressive buying, negative indicates selling.
        
        Args:
            recent_trades: List of recent trade dicts with 'side', 'size', 'time'
            window_seconds: Time window in seconds
            
        Returns:
            Dictionary with OFI metrics
        """
        try:
            if not recent_trades:
                return {
                    'order_flow_imbalance': 0.0,
                    'buy_volume': 0.0,
                    'sell_volume': 0.0,
                    'signal': 'neutral',
                    'strength': 0.0
                }
            
            # Filter trades within time window
            current_time = datetime.now()
            buy_volume = 0.0
            sell_volume = 0.0
            
            for trade in recent_trades:
                # Check if trade is within window
                trade_time = trade.get('time')
                if isinstance(trade_time, datetime):
                    time_diff = (current_time - trade_time).total_seconds()
                    if time_diff > window_seconds:
                        continue
                
                size = float(trade.get('size', 0))
                side = trade.get('side', 'buy')
                
                if side == 'buy':
                    buy_volume += size
                else:
                    sell_volume += size
            
            # Calculate OFI
            total_volume = buy_volume + sell_volume
            if total_volume == 0:
                ofi = 0.0
            else:
                ofi = (buy_volume - sell_volume) / total_volume
            
            # Interpret signal
            if ofi > 0.3:
                signal = 'strong_buy'
                strength = min(abs(ofi), 1.0)
            elif ofi > 0.1:
                signal = 'weak_buy'
                strength = min(abs(ofi) * 2, 1.0)
            elif ofi < -0.3:
                signal = 'strong_sell'
                strength = min(abs(ofi), 1.0)
            elif ofi < -0.1:
                signal = 'weak_sell'
                strength = min(abs(ofi) * 2, 1.0)
            else:
                signal = 'neutral'
                strength = 0.3
            
            return {
                'order_flow_imbalance': ofi,
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'total_volume': total_volume,
                'signal': signal,
                'strength': strength,
                'window_seconds': window_seconds
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating order flow imbalance: {e}")
            return {
                'order_flow_imbalance': 0.0,
                'signal': 'neutral',
                'strength': 0.0
            }
    
    def update_kyle_lambda(self, price: float, signed_volume: float):
        """
        Update Kyle's lambda estimation using recent price changes and volumes.
        
        Kyle's lambda (λ) measures the price impact of order flow:
        ΔP = λ * Q
        where ΔP is price change and Q is signed volume (+ for buys, - for sells)
        
        We estimate λ using linear regression: λ = Cov(ΔP, Q) / Var(Q)
        
        Args:
            price: Current price
            signed_volume: Signed volume (positive for buy, negative for sell)
        """
        try:
            # Store signed volume
            self.signed_volumes.append(signed_volume)
            
            # Calculate price change if we have previous price
            if len(self.orderbook_history) > 0:
                prev_book = self.orderbook_history[-1]
                if prev_book.get('bids') and prev_book.get('asks'):
                    prev_bid = float(prev_book['bids'][0][0])
                    prev_ask = float(prev_book['asks'][0][0])
                    prev_mid = (prev_bid + prev_ask) / 2
                    price_change = price - prev_mid
                    self.price_changes.append(price_change)
            
            # Estimate lambda if we have enough data
            if len(self.price_changes) >= 20 and len(self.signed_volumes) >= 20:
                price_array = np.array(list(self.price_changes))
                volume_array = np.array(list(self.signed_volumes))
                
                # Remove zeros to avoid division issues
                non_zero_mask = volume_array != 0
                if np.sum(non_zero_mask) > 10:
                    price_array = price_array[non_zero_mask]
                    volume_array = volume_array[non_zero_mask]
                    
                    # Estimate lambda: Cov(ΔP, Q) / Var(Q)
                    covariance = np.cov(price_array, volume_array)[0, 1]
                    variance = np.var(volume_array)
                    
                    if variance > 0:
                        self.kyle_lambda = covariance / variance
                    
        except Exception as e:
            self.logger.error(f"Error updating Kyle's lambda: {e}")
    
    def get_kyle_lambda(self) -> float:
        """
        Get current Kyle's lambda estimate.
        
        Returns:
            Kyle's lambda (price impact per unit volume)
        """
        return self.kyle_lambda
    
    def estimate_price_impact_kyle(self, order_volume: float) -> Dict:
        """
        Estimate price impact using Kyle's lambda.
        
        Expected price impact: ΔP = λ * Q
        
        Args:
            order_volume: Order volume (positive for buy, negative for sell)
            
        Returns:
            Dictionary with price impact estimates
        """
        if self.kyle_lambda == 0:
            return {
                'estimated_impact': 0.0,
                'impact_bps': 0.0,
                'confidence': 'low',
                'message': 'Insufficient data for Kyle lambda estimation'
            }
        
        # Estimate price impact
        estimated_impact = self.kyle_lambda * order_volume
        
        # Determine confidence based on sample size
        if len(self.price_changes) >= 50:
            confidence = 'high'
        elif len(self.price_changes) >= 20:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'estimated_impact': estimated_impact,
            'estimated_impact_pct': estimated_impact * 100,
            'kyle_lambda': self.kyle_lambda,
            'confidence': confidence,
            'sample_size': len(self.price_changes)
        }
    
    def get_comprehensive_metrics(
        self,
        orderbook: Dict,
        recent_trades: List[Dict],
        price: float
    ) -> Dict:
        """
        Get all microstructure metrics in one call.
        
        Args:
            orderbook: Current order book
            recent_trades: Recent trade history
            price: Current price
            
        Returns:
            Dictionary with all microstructure metrics
        """
        metrics = {}
        
        # Basic imbalance
        metrics['imbalance'] = self.analyze_order_book_imbalance(orderbook)
        
        # Microprice
        microprice = self.calculate_microprice(orderbook)
        if microprice:
            metrics['microprice'] = microprice
            mid_price = (float(orderbook['bids'][0][0]) + float(orderbook['asks'][0][0])) / 2
            metrics['microprice_deviation'] = (microprice - mid_price) / mid_price
        
        # Queue Imbalance (QI)
        metrics['queue_imbalance'] = self.calculate_queue_imbalance(orderbook)
        
        # Order Flow Imbalance (OFI)
        metrics['order_flow_imbalance'] = self.calculate_order_flow_imbalance(recent_trades)
        
        # Kyle's lambda
        metrics['kyle_lambda'] = self.kyle_lambda
        
        # Store orderbook for lambda calculation
        self.orderbook_history.append(orderbook)
        
        return metrics
