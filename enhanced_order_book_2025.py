"""
Enhanced Order Book Analysis - 2025 AI Improvements
Implements VAMP, WDOP, and advanced OBI metrics
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from logger import Logger


class EnhancedOrderBookAnalyzer:
    """
    Advanced order book analysis with 2025 research-backed metrics
    
    Implements:
    - VAMP (Volume Adjusted Mid Price)
    - WDOP (Weighted-Depth Order Book Price)
    - Enhanced OBI (Order Book Imbalance)
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.historical_imbalances = []  # Track for trend analysis
        
    def calculate_vamp(self, order_book: Dict) -> float:
        """
        Calculate Volume Adjusted Mid Price (VAMP)
        
        VAMP provides a more accurate "true" market price by weighting
        the mid price based on order book depth at best bid/ask.
        
        Formula:
        VAMP = (bid_price * ask_volume + ask_price * bid_volume) / (bid_volume + ask_volume)
        
        Args:
            order_book: Order book data with 'bids' and 'asks'
            
        Returns:
            VAMP price
        """
        try:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            if not bids or not asks:
                return None
            
            # Get best bid and ask with volumes
            best_bid_price = float(bids[0][0])
            best_bid_volume = float(bids[0][1])
            best_ask_price = float(asks[0][0])
            best_ask_volume = float(asks[0][1])
            
            # Calculate VAMP
            total_volume = best_bid_volume + best_ask_volume
            if total_volume == 0:
                return (best_bid_price + best_ask_price) / 2
            
            vamp = (best_bid_price * best_ask_volume + best_ask_price * best_bid_volume) / total_volume
            
            self.logger.debug(f"VAMP: {vamp:.2f} (mid: {(best_bid_price + best_ask_price)/2:.2f})")
            return vamp
            
        except Exception as e:
            self.logger.error(f"Error calculating VAMP: {e}")
            return None
    
    def calculate_wdop(self, order_book: Dict, depth_levels: int = 5) -> Tuple[float, float]:
        """
        Calculate Weighted-Depth Order Book Price (WDOP)
        
        WDOP considers multiple price levels weighted by their depth,
        providing better liquidity assessment and slippage prediction.
        
        Args:
            order_book: Order book data with 'bids' and 'asks'
            depth_levels: Number of order book levels to consider
            
        Returns:
            Tuple of (wdop_bid, wdop_ask)
        """
        try:
            bids = order_book.get('bids', [])[:depth_levels]
            asks = order_book.get('asks', [])[:depth_levels]
            
            if not bids or not asks:
                return None, None
            
            # Calculate weighted bid price
            total_bid_volume = sum(float(bid[1]) for bid in bids)
            if total_bid_volume > 0:
                wdop_bid = sum(float(bid[0]) * float(bid[1]) for bid in bids) / total_bid_volume
            else:
                wdop_bid = float(bids[0][0])
            
            # Calculate weighted ask price
            total_ask_volume = sum(float(ask[1]) for ask in asks)
            if total_ask_volume > 0:
                wdop_ask = sum(float(ask[0]) * float(ask[1]) for ask in asks) / total_ask_volume
            else:
                wdop_ask = float(asks[0][0])
            
            self.logger.debug(f"WDOP: Bid={wdop_bid:.2f}, Ask={wdop_ask:.2f}")
            return wdop_bid, wdop_ask
            
        except Exception as e:
            self.logger.error(f"Error calculating WDOP: {e}")
            return None, None
    
    def calculate_enhanced_obi(self, order_book: Dict, depth_levels: int = 5) -> Dict:
        """
        Calculate Enhanced Order Book Imbalance (OBI)
        
        Enhanced version considers:
        - Multi-level imbalance (not just best bid/ask)
        - Volume-weighted imbalance
        - Imbalance trend (increasing/decreasing)
        
        Args:
            order_book: Order book data
            depth_levels: Number of levels to analyze
            
        Returns:
            Dictionary with OBI metrics
        """
        try:
            bids = order_book.get('bids', [])[:depth_levels]
            asks = order_book.get('asks', [])[:depth_levels]
            
            if not bids or not asks:
                return {
                    'obi': 0.0,
                    'obi_strength': 'neutral',
                    'obi_trend': 'stable'
                }
            
            # Calculate total volumes
            total_bid_volume = sum(float(bid[1]) for bid in bids)
            total_ask_volume = sum(float(ask[1]) for ask in asks)
            
            # Basic OBI: (bid_volume - ask_volume) / (bid_volume + ask_volume)
            total_volume = total_bid_volume + total_ask_volume
            if total_volume == 0:
                obi = 0.0
            else:
                obi = (total_bid_volume - total_ask_volume) / total_volume
            
            # Determine OBI strength
            abs_obi = abs(obi)
            if abs_obi > 0.3:
                strength = 'strong'
            elif abs_obi > 0.15:
                strength = 'moderate'
            elif abs_obi > 0.05:
                strength = 'weak'
            else:
                strength = 'neutral'
            
            # Track OBI trend
            self.historical_imbalances.append(obi)
            if len(self.historical_imbalances) > 20:
                self.historical_imbalances.pop(0)
            
            # Determine trend
            if len(self.historical_imbalances) >= 3:
                recent = self.historical_imbalances[-3:]
                if recent[-1] > recent[0] + 0.05:
                    trend = 'increasing'
                elif recent[-1] < recent[0] - 0.05:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            result = {
                'obi': obi,
                'obi_strength': strength,
                'obi_trend': trend,
                'bid_volume': total_bid_volume,
                'ask_volume': total_ask_volume
            }
            
            self.logger.debug(f"Enhanced OBI: {obi:.3f} ({strength}, {trend})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced OBI: {e}")
            return {
                'obi': 0.0,
                'obi_strength': 'neutral',
                'obi_trend': 'stable'
            }
    
    def predict_slippage(self, order_book: Dict, order_size_usdt: float, 
                        side: str = 'buy') -> Dict:
        """
        Predict slippage for a given order size
        
        Uses WDOP and order book depth to estimate execution price
        and slippage for a market order.
        
        Args:
            order_book: Order book data
            order_size_usdt: Order size in USDT
            side: 'buy' or 'sell'
            
        Returns:
            Dictionary with slippage prediction
        """
        try:
            if side.lower() == 'buy':
                levels = order_book.get('asks', [])
                best_price = float(levels[0][0]) if levels else None
            else:
                levels = order_book.get('bids', [])
                best_price = float(levels[0][0]) if levels else None
            
            if not levels or best_price is None:
                return {
                    'predicted_slippage_pct': 0.0,
                    'avg_execution_price': best_price,
                    'can_fill': False
                }
            
            # Simulate order filling
            remaining_usdt = order_size_usdt
            total_filled_usdt = 0
            total_filled_qty = 0
            
            for level in levels:
                price = float(level[0])
                volume = float(level[1])
                level_usdt = price * volume
                
                if remaining_usdt <= level_usdt:
                    # Can fill completely at this level
                    fill_qty = remaining_usdt / price
                    total_filled_usdt += remaining_usdt
                    total_filled_qty += fill_qty
                    remaining_usdt = 0
                    break
                else:
                    # Fill this level completely
                    total_filled_usdt += level_usdt
                    total_filled_qty += volume
                    remaining_usdt -= level_usdt
            
            # Calculate average execution price
            if total_filled_qty > 0:
                avg_execution_price = total_filled_usdt / total_filled_qty
            else:
                avg_execution_price = best_price
            
            # Calculate slippage
            slippage_pct = abs((avg_execution_price - best_price) / best_price) * 100
            
            can_fill = remaining_usdt == 0
            
            result = {
                'predicted_slippage_pct': slippage_pct,
                'avg_execution_price': avg_execution_price,
                'best_price': best_price,
                'can_fill': can_fill,
                'unfilled_usdt': remaining_usdt
            }
            
            if slippage_pct > 0.1:
                self.logger.warning(f"High predicted slippage: {slippage_pct:.2f}%")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error predicting slippage: {e}")
            return {
                'predicted_slippage_pct': 0.0,
                'avg_execution_price': None,
                'can_fill': False
            }
    
    def get_execution_score(self, order_book: Dict, order_size_usdt: float,
                           side: str = 'buy') -> float:
        """
        Calculate execution quality score (0-1)
        
        Combines VAMP, WDOP, OBI, and slippage prediction to give
        an overall score for execution timing.
        
        Args:
            order_book: Order book data
            order_size_usdt: Intended order size
            side: 'buy' or 'sell'
            
        Returns:
            Execution score (0 = poor, 1 = excellent)
        """
        try:
            score = 0.5  # Start neutral
            
            # 1. Check OBI (30% weight)
            obi_metrics = self.calculate_enhanced_obi(order_book)
            obi = obi_metrics['obi']
            
            if side.lower() == 'buy':
                # For buys, positive OBI (more bids) is bad, negative is good
                if obi < -0.15:
                    score += 0.15  # Strong ask pressure = good for buying
                elif obi > 0.15:
                    score -= 0.15  # Strong bid pressure = bad for buying
            else:
                # For sells, positive OBI (more bids) is good
                if obi > 0.15:
                    score += 0.15  # Strong bid pressure = good for selling
                elif obi < -0.15:
                    score -= 0.15  # Strong ask pressure = bad for selling
            
            # 2. Check slippage prediction (40% weight)
            slippage_data = self.predict_slippage(order_book, order_size_usdt, side)
            slippage_pct = slippage_data['predicted_slippage_pct']
            
            if slippage_pct < 0.05:
                score += 0.20  # Very low slippage
            elif slippage_pct < 0.1:
                score += 0.10  # Low slippage
            elif slippage_pct < 0.2:
                score -= 0.05  # Moderate slippage
            else:
                score -= 0.20  # High slippage
            
            if not slippage_data['can_fill']:
                score -= 0.15  # Can't fill entire order
            
            # 3. Check spread tightness (20% weight)
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            if bids and asks:
                spread = (float(asks[0][0]) - float(bids[0][0])) / float(bids[0][0])
                
                if spread < 0.0005:  # < 0.05%
                    score += 0.10  # Tight spread
                elif spread > 0.002:  # > 0.2%
                    score -= 0.10  # Wide spread
            
            # 4. OBI trend alignment (10% weight)
            if obi_metrics['obi_trend'] != 'stable':
                trend_favorable = (
                    (side.lower() == 'buy' and obi_metrics['obi_trend'] == 'decreasing') or
                    (side.lower() == 'sell' and obi_metrics['obi_trend'] == 'increasing')
                )
                if trend_favorable:
                    score += 0.05
                else:
                    score -= 0.05
            
            # Clamp to 0-1 range
            score = max(0.0, min(1.0, score))
            
            self.logger.debug(f"Execution score for {side}: {score:.2f}")
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating execution score: {e}")
            return 0.5  # Neutral score on error
    
    def should_execute_now(self, order_book: Dict, order_size_usdt: float,
                           side: str, min_score: float = 0.6) -> Tuple[bool, str]:
        """
        Determine if current market conditions are favorable for execution
        
        Args:
            order_book: Order book data
            order_size_usdt: Order size
            side: 'buy' or 'sell'
            min_score: Minimum execution score required
            
        Returns:
            Tuple of (should_execute, reason)
        """
        try:
            score = self.get_execution_score(order_book, order_size_usdt, side)
            
            if score >= min_score:
                return True, f"Execution score {score:.2f} meets threshold"
            else:
                # Provide specific reason
                obi_metrics = self.calculate_enhanced_obi(order_book)
                slippage_data = self.predict_slippage(order_book, order_size_usdt, side)
                
                reasons = []
                if abs(obi_metrics['obi']) > 0.2 and (
                    (side.lower() == 'buy' and obi_metrics['obi'] > 0) or
                    (side.lower() == 'sell' and obi_metrics['obi'] < 0)
                ):
                    reasons.append("unfavorable order book imbalance")
                
                if slippage_data['predicted_slippage_pct'] > 0.2:
                    reasons.append(f"high slippage ({slippage_data['predicted_slippage_pct']:.2f}%)")
                
                if not slippage_data['can_fill']:
                    reasons.append("insufficient liquidity")
                
                if not reasons:
                    reasons.append("low execution score")
                
                reason = f"Score {score:.2f} below threshold: " + ", ".join(reasons)
                return False, reason
                
        except Exception as e:
            self.logger.error(f"Error in execution decision: {e}")
            return False, f"Error: {e}"
