"""
Enhanced signal validation and filtering
"""
from typing import Dict, Tuple, Optional
from logger import Logger
import pandas as pd


class SignalValidator:
    """Validate and filter trading signals for quality"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
    def validate_signal_quality(
        self, 
        signal: str, 
        confidence: float, 
        indicators: Dict,
        reasons: Dict
    ) -> Tuple[bool, str]:
        """
        Validate signal quality before trading
        
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check basic signal validity
        if signal not in ['BUY', 'SELL']:
            return False, "Invalid signal type"
        
        if confidence < 0.5:
            return False, f"Confidence too low: {confidence:.2%}"
        
        # Check for conflicting indicators
        if reasons.get('mtf_conflict'):
            return False, "Multi-timeframe conflict detected"
        
        # Validate key indicators exist
        required_indicators = ['rsi', 'close', 'volume_ratio']
        missing = [ind for ind in required_indicators if ind not in indicators]
        if missing:
            return False, f"Missing indicators: {', '.join(missing)}"
        
        # RSI sanity check
        rsi = indicators.get('rsi', 50)
        if rsi < 0 or rsi > 100:
            return False, f"Invalid RSI value: {rsi}"
        
        # Volume validation - avoid low volume periods
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio < 0.5:
            return False, f"Volume too low: {volume_ratio:.2f}x average"
        
        # Check for extreme conditions that may indicate data issues
        close = indicators.get('close', 0)
        if close <= 0:
            return False, f"Invalid close price: {close}"
        
        # Bollinger Band position check - avoid buying at top/selling at bottom
        bb_position = indicators.get('bb_position', 0.5)
        if signal == 'BUY' and bb_position > 0.95:
            return False, f"Price at upper BB limit, avoid buying"
        elif signal == 'SELL' and bb_position < 0.05:
            return False, f"Price at lower BB limit, avoid selling"
        
        # Check momentum alignment
        momentum = indicators.get('momentum', 0)
        if signal == 'BUY' and momentum < -0.05:
            return False, f"Negative momentum conflicts with BUY signal"
        elif signal == 'SELL' and momentum > 0.05:
            return False, f"Positive momentum conflicts with SELL signal"
        
        return True, "Signal validated"
    
    def calculate_signal_strength(
        self, 
        confidence: float, 
        indicators: Dict,
        reasons: Dict
    ) -> float:
        """
        Calculate overall signal strength score (0-100)
        
        Higher score = stronger signal
        """
        score = confidence * 50  # Base score from confidence (0-50)
        
        # Add points for favorable conditions
        
        # Volume confirmation
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            score += 10
        elif volume_ratio > 1.0:
            score += 5
        
        # Momentum alignment
        momentum = indicators.get('momentum', 0)
        if abs(momentum) > 0.02:
            score += 8
        
        # RSI extremes (but not too extreme)
        rsi = indicators.get('rsi', 50)
        if 25 < rsi < 35:  # Oversold but not extreme
            score += 7
        elif 65 < rsi < 75:  # Overbought but not extreme
            score += 7
        
        # Multi-timeframe alignment bonus
        if reasons.get('mtf_alignment') == 'bullish' or reasons.get('mtf_alignment') == 'bearish':
            score += 15
        
        # Trend strength
        if reasons.get('trend_strength', 0) > 0.7:
            score += 10
        
        # Support/resistance proximity
        if reasons.get('near_support') or reasons.get('near_resistance'):
            score += 5
        
        # Cap at 100
        return min(score, 100)
    
    def filter_by_market_conditions(
        self,
        signal: str,
        indicators: Dict,
        market_regime: str
    ) -> Tuple[bool, str]:
        """
        Filter signals based on current market conditions
        
        Returns:
            Tuple of (should_trade, reason)
        """
        # In ranging markets, be more conservative
        if market_regime == 'ranging':
            confidence_threshold = 0.7
            if indicators.get('confidence', 0) < confidence_threshold:
                return False, f"Market ranging - need {confidence_threshold:.0%}+ confidence"
        
        # In trending markets, follow the trend
        elif market_regime == 'trending':
            # Check if signal aligns with trend
            sma_20 = indicators.get('sma_20', 0)
            sma_50 = indicators.get('sma_50', 0)
            close = indicators.get('close', 0)
            
            if sma_20 > 0 and sma_50 > 0 and close > 0:
                trend_up = sma_20 > sma_50
                
                if signal == 'BUY' and not trend_up:
                    return False, "BUY signal against downtrend"
                elif signal == 'SELL' and trend_up:
                    return False, "SELL signal against uptrend"
        
        # In volatile markets, increase position caution
        elif market_regime == 'volatile':
            bb_width = indicators.get('bb_width', 0)
            if bb_width > 0.05:  # Very wide Bollinger Bands
                return False, "Excessive volatility - avoiding trade"
        
        return True, "Market conditions favorable"
    
    def suggest_adjustments(
        self,
        signal: str,
        confidence: float,
        indicators: Dict,
        reasons: Dict
    ) -> Dict:
        """
        Suggest adjustments to improve trade setup
        
        Returns:
            Dict with suggested adjustments
        """
        adjustments = {
            'leverage': 1.0,  # Multiplier for leverage
            'position_size': 1.0,  # Multiplier for position size
            'stop_loss': 1.0,  # Multiplier for stop loss distance
            'take_profit': 1.0  # Multiplier for take profit distance
        }
        
        # Adjust based on volatility
        bb_width = indicators.get('bb_width', 0.03)
        if bb_width > 0.04:  # High volatility
            adjustments['leverage'] *= 0.8  # Reduce leverage
            adjustments['stop_loss'] *= 1.2  # Wider stop loss
        elif bb_width < 0.02:  # Low volatility
            adjustments['leverage'] *= 1.1  # Can use slightly more leverage
            adjustments['stop_loss'] *= 0.9  # Tighter stop loss
        
        # Adjust based on confidence
        if confidence > 0.8:
            adjustments['position_size'] *= 1.2  # Larger position for high confidence
        elif confidence < 0.65:
            adjustments['position_size'] *= 0.8  # Smaller position for lower confidence
        
        # Adjust based on momentum
        momentum = indicators.get('momentum', 0)
        if abs(momentum) > 0.03:  # Strong momentum
            adjustments['take_profit'] *= 1.3  # Let winners run
        
        # Adjust based on volume
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 2.0:  # Very high volume
            adjustments['position_size'] *= 1.1  # Can trade larger with high liquidity
        elif volume_ratio < 0.8:  # Low volume
            adjustments['position_size'] *= 0.9  # Reduce size for low liquidity
        
        return adjustments


class TradingOpportunityRanker:
    """Rank and prioritize trading opportunities"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
    
    def rank_opportunities(
        self, 
        opportunities: list,
        current_positions: list = None
    ) -> list:
        """
        Rank trading opportunities by quality and diversification
        
        Args:
            opportunities: List of opportunity dicts
            current_positions: List of currently open position symbols
        
        Returns:
            Sorted list of opportunities
        """
        if not opportunities:
            return []
        
        current_positions = current_positions or []
        
        # Score each opportunity
        scored_opportunities = []
        for opp in opportunities:
            score = self._calculate_opportunity_score(opp, current_positions)
            opp['final_score'] = score
            scored_opportunities.append(opp)
        
        # Sort by final score
        scored_opportunities.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored_opportunities
    
    def _calculate_opportunity_score(self, opp: Dict, current_positions: list) -> float:
        """Calculate comprehensive opportunity score"""
        base_score = opp.get('score', 0)
        confidence = opp.get('confidence', 0)
        
        # Start with base score and confidence
        score = base_score * confidence
        
        # Bonus for high confidence
        if confidence > 0.75:
            score *= 1.2
        
        # Penalty for medium confidence
        if confidence < 0.65:
            score *= 0.9
        
        # Diversification bonus - prefer symbols not in current positions
        symbol = opp.get('symbol', '')
        base_asset = symbol.split(':')[0].replace('/USDT', '')
        
        # Check if we already have exposure to this asset
        has_exposure = any(base_asset in pos for pos in current_positions)
        if has_exposure:
            score *= 0.7  # Significant penalty for duplicate exposure
        
        # Bonus for volume
        reasons = opp.get('reasons', {})
        volume_ratio = reasons.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            score *= 1.1
        
        # Bonus for trend alignment
        if reasons.get('mtf_alignment') in ['bullish', 'bearish']:
            score *= 1.15
        
        return score
    
    def filter_correlated_opportunities(
        self, 
        opportunities: list,
        max_similar: int = 2
    ) -> list:
        """
        Filter opportunities to avoid too many correlated trades
        
        Args:
            opportunities: List of opportunities
            max_similar: Maximum similar assets to trade
        
        Returns:
            Filtered list
        """
        if not opportunities:
            return []
        
        # Group by asset category
        categories = {
            'major': ['BTC', 'ETH'],
            'layer1': ['SOL', 'AVAX', 'DOT', 'NEAR', 'ATOM', 'ADA'],
            'defi': ['UNI', 'AAVE', 'SUSHI', 'LINK', 'CRV'],
            'meme': ['DOGE', 'SHIB', 'PEPE'],
        }
        
        category_counts = {cat: 0 for cat in categories}
        filtered = []
        
        for opp in opportunities:
            symbol = opp.get('symbol', '')
            
            # Determine category
            category = None
            for cat, assets in categories.items():
                if any(asset in symbol for asset in assets):
                    category = cat
                    break
            
            # If no category or under limit, include it
            if category is None:
                filtered.append(opp)
            elif category_counts[category] < max_similar:
                filtered.append(opp)
                category_counts[category] += 1
            else:
                self.logger.debug(
                    f"Skipping {symbol} - already have {max_similar} {category} positions"
                )
        
        return filtered
