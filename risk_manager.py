"""
Risk management system for the trading bot
"""
from typing import Dict
from logger import Logger

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
                            min_balance: float = 100) -> tuple[bool, str]:
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
        base_stop = 0.03  # 3%
        
        # Adjust based on volatility
        # Higher volatility = wider stop loss
        volatility_adjustment = min(volatility * 2, 0.05)  # Max 5% adjustment
        
        stop_loss = base_stop + volatility_adjustment
        
        # Cap between 2% and 10%
        stop_loss = max(0.02, min(stop_loss, 0.10))
        
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
        # Base leverage
        base_leverage = 10
        
        # Reduce leverage for high volatility
        if volatility > 0.05:
            base_leverage = 5
        elif volatility > 0.03:
            base_leverage = 7
        
        # Reduce leverage for low confidence
        if confidence < 0.7:
            base_leverage = min(base_leverage, 5)
        
        return base_leverage
