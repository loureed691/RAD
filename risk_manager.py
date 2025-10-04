"""
Risk management system for the trading bot
"""
from typing import Dict, List, Tuple
from logger import Logger
try:
    import numpy as np
except ImportError as e:
    Logger.get_logger().error("Numpy is required but not installed. Please install numpy to proceed.")
    raise

class RiskManager:
    """Manage trading risk and position sizing"""
    
    def __init__(self, max_position_size: float, risk_per_trade: float, 
                 max_open_positions: int):
        """
        Initialize risk manager
        
        Args:
            max_position_size: Maximum position size in USDT
            risk_per_trade: Risk per trade as percentage of balance (0.01 = 1%)
            max_open_positions: Maximum number of concurrent positions
        """
        self.max_position_size = max_position_size
        self.risk_per_trade = risk_per_trade
        self.max_open_positions = max_open_positions
        self.logger = Logger.get_logger()
        
        # Correlation tracking for portfolio diversification
        self.correlation_groups = {
            'major_coins': ['BTC', 'ETH'],
            'defi': ['UNI', 'AAVE', 'SUSHI', 'LINK'],
            'layer1': ['SOL', 'AVAX', 'DOT', 'NEAR', 'ATOM'],
            'layer2': ['MATIC', 'OP', 'ARB'],
            'meme': ['DOGE', 'SHIB', 'PEPE'],
            'exchange': ['BNB', 'OKB', 'FTT']
        }
    
    def analyze_order_book_imbalance(self, orderbook: Dict) -> Dict:
        """
        Analyze order book for bid/ask imbalance to optimize entry timing
        
        Args:
            orderbook: Dict with 'bids' and 'asks' arrays
        
        Returns:
            Dict with imbalance metrics
        """
        if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
            return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
        
        try:
            bids = orderbook['bids'][:20]  # Top 20 bids
            asks = orderbook['asks'][:20]  # Top 20 asks
            
            if not bids or not asks:
                return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
            
            # Calculate total bid and ask volume
            bid_volume = sum(float(bid[1]) for bid in bids)
            ask_volume = sum(float(ask[1]) for ask in asks)
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
            
            # Calculate imbalance (-1 to 1, positive = more bids)
            imbalance = (bid_volume - ask_volume) / total_volume
            
            # Calculate spread
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread_pct = (best_ask - best_bid) / best_bid
            
            # Determine signal strength
            signal = 'neutral'
            confidence = abs(imbalance)
            
            if imbalance > 0.15:  # Strong buy pressure
                signal = 'bullish'
            elif imbalance < -0.15:  # Strong sell pressure
                signal = 'bearish'
            elif abs(imbalance) < 0.05:  # Balanced
                signal = 'neutral'
            
            # Tight spread indicates good liquidity
            liquidity_score = 1.0 if spread_pct < 0.001 else 0.5
            
            return {
                'imbalance': imbalance,
                'signal': signal,
                'confidence': confidence,
                'spread_pct': spread_pct,
                'liquidity_score': liquidity_score,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing order book: {e}")
            return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
    
    def calculate_position_size(self, balance: float, entry_price: float, 
                               stop_loss_price: float, leverage: int) -> float:
        """
        Calculate safe position size based on risk management
        
        Args:
            balance: Account balance in USDT
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            leverage: Leverage to use
        
        Returns:
            Position size in contracts
        """
        # Calculate risk amount
        risk_amount = balance * self.risk_per_trade
        
        # Calculate price distance to stop loss
        price_distance = abs(entry_price - stop_loss_price) / entry_price
        
        # Calculate position size considering leverage
        # Risk = Position_Size * Price_Distance * Leverage
        if price_distance > 0:
            position_value = risk_amount / (price_distance * leverage)
        else:
            position_value = self.max_position_size
        
        # Cap at maximum position size
        position_value = min(position_value, self.max_position_size)
        
        # Convert to contracts
        position_size = position_value / entry_price
        
        self.logger.debug(
            f"Calculated position size: {position_size:.4f} contracts "
            f"(${position_value:.2f} value) for risk ${risk_amount:.2f}"
        )
        
        return position_size
    
    def should_open_position(self, current_positions: int, balance: float, 
                            min_balance: float = 1) -> tuple[bool, str]:
        """
        Check if a new position should be opened
        
        Returns:
            Tuple of (should_open, reason)
        """
        # Check if we have too many open positions
        if current_positions >= self.max_open_positions:
            return False, f"Maximum positions reached ({self.max_open_positions})"
        
        # Check if we have sufficient balance
        if balance < min_balance:
            return False, f"Insufficient balance (${balance:.2f} < ${min_balance})"
        
        return True, "OK"
    
    def validate_trade(self, symbol: str, signal: str, confidence: float, 
                      min_confidence: float = 0.6) -> tuple[bool, str]:
        """
        Validate if a trade should be executed
        
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check confidence threshold
        if confidence < min_confidence:
            return False, f"Confidence too low ({confidence:.2f} < {min_confidence})"
        
        # Additional validation can be added here
        # e.g., check for recent losses, market conditions, etc.
        
        return True, "OK"
    
    def calculate_stop_loss_percentage(self, volatility: float) -> float:
        """
        Calculate stop loss percentage based on market volatility
        
        Args:
            volatility: ATR or other volatility measure
        
        Returns:
            Stop loss percentage (e.g., 0.05 for 5%)
        """
        # Base stop loss
        base_stop = 0.025  # 2.5%
        
        # Adjust based on volatility (adaptive approach)
        # Higher volatility = wider stop loss to avoid premature stops
        if volatility < 0.02:
            # Low volatility - tighter stops
            volatility_adjustment = volatility * 1.5
        elif volatility < 0.05:
            # Medium volatility - standard adjustment
            volatility_adjustment = volatility * 2.0
        else:
            # High volatility - wider stops but capped
            volatility_adjustment = min(volatility * 2.5, 0.06)
        
        stop_loss = base_stop + volatility_adjustment
        
        # Cap between 1.5% and 8%
        stop_loss = max(0.015, min(stop_loss, 0.08))
        
        return stop_loss
    
    def get_max_leverage(self, volatility: float, confidence: float) -> int:
        """
        Calculate maximum safe leverage based on market conditions
        
        Args:
            volatility: Market volatility measure
            confidence: Signal confidence
        
        Returns:
            Maximum leverage to use
        """
        # Start with base leverage based on volatility
        if volatility > 0.08:
            base_leverage = 3  # Very high volatility - minimal leverage
        elif volatility > 0.05:
            base_leverage = 5  # High volatility
        elif volatility > 0.03:
            base_leverage = 7  # Medium volatility
        elif volatility > 0.02:
            base_leverage = 10  # Normal volatility
        else:
            base_leverage = 12  # Low volatility - can use higher leverage
        
        # Adjust based on signal confidence
        if confidence >= 0.75:
            # Very high confidence - can increase leverage slightly
            base_leverage = min(base_leverage + 2, 15)
        elif confidence < 0.65:
            # Lower confidence - reduce leverage
            base_leverage = max(base_leverage - 2, 3)
        
        return base_leverage
    
    def get_symbol_group(self, symbol: str) -> str:
        """
        Identify which correlation group a symbol belongs to
        
        Returns:
            Group name or 'other'
        """
        # Extract base currency from symbol (e.g., 'BTC/USDT:USDT' -> 'BTC')
        base = symbol.split('/')[0] if '/' in symbol else symbol.split('-')[0]
        
        for group_name, coins in self.correlation_groups.items():
            if base in coins:
                return group_name
        
        return 'other'
    
    def check_portfolio_diversification(self, new_symbol: str, 
                                       open_positions: List[str]) -> Tuple[bool, str]:
        """
        Check if adding a new position would over-concentrate portfolio
        
        Args:
            new_symbol: Symbol to potentially add
            open_positions: List of currently open position symbols
        
        Returns:
            Tuple of (is_diversified, reason)
        """
        if not open_positions:
            return True, "No existing positions"
        
        new_group = self.get_symbol_group(new_symbol)
        
        # Count positions in each group
        group_counts = {}
        for pos_symbol in open_positions:
            group = self.get_symbol_group(pos_symbol)
            group_counts[group] = group_counts.get(group, 0) + 1
        
        # Check if new position would over-concentrate
        current_count = group_counts.get(new_group, 0)
        total_positions = len(open_positions)
        
        # Maximum 40% of portfolio in same correlation group
        max_group_concentration = max(2, int(self.max_open_positions * 0.4))
        
        if current_count >= max_group_concentration:
            return False, f"Too many positions in {new_group} group ({current_count}/{max_group_concentration})"
        
        # Don't allow exact duplicate symbols
        if new_symbol in open_positions:
            return False, f"Already have position in {new_symbol}"
        
        return True, "Portfolio diversification OK"
    
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, 
                                  avg_loss: float) -> float:
        """
        Calculate optimal position size using Kelly Criterion
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average win percentage
            avg_loss: Average loss percentage (positive number)
        
        Returns:
            Optimal fraction of capital to risk (0-1)
        """
        if win_rate <= 0 or avg_win <= 0 or avg_loss <= 0:
            return self.risk_per_trade  # Use default if no history
        
        # Kelly formula: f = (bp - q) / b
        # where b = ratio of win to loss, p = win prob, q = loss prob
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # Be conservative: use half-Kelly to reduce volatility
        conservative_kelly = kelly_fraction * 0.5
        
        # Cap between 0.5% and 3% of portfolio
        optimal_risk = max(0.005, min(conservative_kelly, 0.03))
        
        return optimal_risk
