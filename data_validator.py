"""
Production-grade data validation for trading decisions

CRITICAL: All trading decisions must pass through validation to prevent:
- Trading on invalid/stale data
- Placing orders with invalid parameters
- Opening positions exceeding exchange limits
- Division by zero errors
- NaN/Inf values in calculations
"""
from typing import Dict, Tuple, Optional, Any
import math
from datetime import datetime, timedelta
from logger import Logger

class DataValidator:
    """Comprehensive data validation for production trading"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.max_price_age_seconds = 10  # Max 10 seconds old for real-time prices
        self.max_data_age_seconds = 300  # Max 5 minutes old for indicators
    
    @staticmethod
    def is_valid_price(price: Any, allow_zero: bool = False) -> Tuple[bool, str]:
        """
        Validate price is a valid number
        
        Args:
            price: Price to validate
            allow_zero: Whether zero is valid (usually not for trading)
            
        Returns:
            (is_valid, reason)
        """
        if price is None:
            return False, "Price is None"
        
        try:
            price_float = float(price)
        except (ValueError, TypeError):
            return False, f"Price is not a number: {price}"
        
        if math.isnan(price_float):
            return False, "Price is NaN"
        
        if math.isinf(price_float):
            return False, "Price is infinity"
        
        if not allow_zero and price_float <= 0:
            return False, f"Price is non-positive: {price_float}"
        
        # Sanity check: price should be reasonable (not negative, not absurdly large)
        if price_float < 0:
            return False, f"Price is negative: {price_float}"
        
        if price_float > 1e9:  # $1 billion per unit is unreasonable
            return False, f"Price is unreasonably large: {price_float}"
        
        return True, "Valid price"
    
    @staticmethod
    def is_valid_amount(amount: Any, min_amount: float = 0.0) -> Tuple[bool, str]:
        """
        Validate trading amount is valid
        
        Args:
            amount: Amount to validate
            min_amount: Minimum allowed amount
            
        Returns:
            (is_valid, reason)
        """
        if amount is None:
            return False, "Amount is None"
        
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            return False, f"Amount is not a number: {amount}"
        
        if math.isnan(amount_float):
            return False, "Amount is NaN"
        
        if math.isinf(amount_float):
            return False, "Amount is infinity"
        
        if amount_float < min_amount:
            return False, f"Amount {amount_float} below minimum {min_amount}"
        
        if amount_float > 1e9:  # 1 billion contracts is unreasonable
            return False, f"Amount is unreasonably large: {amount_float}"
        
        return True, "Valid amount"
    
    @staticmethod
    def is_valid_percentage(value: Any, min_val: float = 0.0, max_val: float = 1.0) -> Tuple[bool, str]:
        """
        Validate percentage value (0-1 or 0-100)
        
        Args:
            value: Percentage to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            (is_valid, reason)
        """
        if value is None:
            return False, "Value is None"
        
        try:
            value_float = float(value)
        except (ValueError, TypeError):
            return False, f"Value is not a number: {value}"
        
        if math.isnan(value_float):
            return False, "Value is NaN"
        
        if math.isinf(value_float):
            return False, "Value is infinity"
        
        if value_float < min_val:
            return False, f"Value {value_float} below minimum {min_val}"
        
        if value_float > max_val:
            return False, f"Value {value_float} above maximum {max_val}"
        
        return True, "Valid percentage"
    
    def validate_ticker_data(self, ticker: Dict, symbol: str) -> Tuple[bool, str]:
        """
        Validate ticker data is complete and fresh
        
        Args:
            ticker: Ticker data from exchange
            symbol: Trading symbol
            
        Returns:
            (is_valid, reason)
        """
        if not ticker:
            return False, f"Ticker is None/empty for {symbol}"
        
        # Check required fields
        required_fields = ['last', 'bid', 'ask']
        for field in required_fields:
            if field not in ticker:
                return False, f"Ticker missing '{field}' for {symbol}"
        
        # Validate last price
        is_valid, reason = self.is_valid_price(ticker['last'])
        if not is_valid:
            return False, f"Invalid last price for {symbol}: {reason}"
        
        # Validate bid/ask
        is_valid, reason = self.is_valid_price(ticker['bid'])
        if not is_valid:
            return False, f"Invalid bid price for {symbol}: {reason}"
        
        is_valid, reason = self.is_valid_price(ticker['ask'])
        if not is_valid:
            return False, f"Invalid ask price for {symbol}: {reason}"
        
        # Validate spread is reasonable (not too wide)
        bid = float(ticker['bid'])
        ask = float(ticker['ask'])
        last = float(ticker['last'])
        
        if ask <= bid:
            return False, f"Invalid spread for {symbol}: bid={bid} >= ask={ask}"
        
        spread_pct = (ask - bid) / last
        if spread_pct > 0.05:  # 5% spread is suspicious
            self.logger.warning(f"Wide spread for {symbol}: {spread_pct:.2%}")
        
        # Check timestamp if available
        if 'timestamp' in ticker:
            try:
                ticker_time = datetime.fromtimestamp(ticker['timestamp'] / 1000)
                age_seconds = (datetime.now() - ticker_time).total_seconds()
                if age_seconds > self.max_price_age_seconds:
                    return False, f"Ticker data is stale for {symbol}: {age_seconds:.1f}s old"
            except Exception as e:
                self.logger.debug(f"Could not validate ticker timestamp: {e}")
        
        return True, "Valid ticker data"
    
    def validate_indicators(self, indicators: Dict, symbol: str) -> Tuple[bool, str]:
        """
        Validate technical indicators are valid
        
        Args:
            indicators: Dictionary of indicators
            symbol: Trading symbol
            
        Returns:
            (is_valid, reason)
        """
        if not indicators:
            return False, f"Indicators dict is None/empty for {symbol}"
        
        # Check for critical indicators
        critical_indicators = ['close', 'volume']
        for ind in critical_indicators:
            if ind not in indicators:
                return False, f"Missing critical indicator '{ind}' for {symbol}"
        
        # Validate all numeric indicators
        for key, value in indicators.items():
            if value is None:
                continue  # Skip None values (optional indicators)
            
            try:
                value_float = float(value)
                
                # Check for NaN/Inf
                if math.isnan(value_float):
                    return False, f"Indicator '{key}' is NaN for {symbol}"
                
                if math.isinf(value_float):
                    return False, f"Indicator '{key}' is infinity for {symbol}"
                
            except (ValueError, TypeError):
                # Non-numeric indicators are okay (e.g., strings for signals)
                pass
        
        # Validate close price specifically
        is_valid, reason = self.is_valid_price(indicators['close'])
        if not is_valid:
            return False, f"Invalid close price in indicators for {symbol}: {reason}"
        
        # Validate volume
        is_valid, reason = self.is_valid_amount(indicators['volume'], min_amount=0)
        if not is_valid:
            return False, f"Invalid volume in indicators for {symbol}: {reason}"
        
        return True, "Valid indicators"
    
    def validate_position_parameters(self, symbol: str, side: str, amount: float,
                                    entry_price: float, stop_loss: float,
                                    take_profit: Optional[float] = None,
                                    leverage: int = 1) -> Tuple[bool, str]:
        """
        Validate position parameters before opening
        
        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            amount: Position size in contracts
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price (optional)
            leverage: Leverage multiplier
            
        Returns:
            (is_valid, reason)
        """
        # Validate side
        if side not in ['long', 'short']:
            return False, f"Invalid side: {side} (must be 'long' or 'short')"
        
        # Validate amount
        is_valid, reason = self.is_valid_amount(amount, min_amount=0.001)
        if not is_valid:
            return False, f"Invalid amount: {reason}"
        
        # Validate entry price
        is_valid, reason = self.is_valid_price(entry_price)
        if not is_valid:
            return False, f"Invalid entry price: {reason}"
        
        # Validate stop loss
        is_valid, reason = self.is_valid_price(stop_loss)
        if not is_valid:
            return False, f"Invalid stop loss: {reason}"
        
        # Validate stop loss is on correct side
        if side == 'long':
            if stop_loss >= entry_price:
                return False, f"Stop loss {stop_loss} must be below entry {entry_price} for long"
        else:  # short
            if stop_loss <= entry_price:
                return False, f"Stop loss {stop_loss} must be above entry {entry_price} for short"
        
        # Validate take profit if provided
        if take_profit is not None:
            is_valid, reason = self.is_valid_price(take_profit)
            if not is_valid:
                return False, f"Invalid take profit: {reason}"
            
            # Validate take profit is on correct side
            if side == 'long':
                if take_profit <= entry_price:
                    return False, f"Take profit {take_profit} must be above entry {entry_price} for long"
            else:  # short
                if take_profit >= entry_price:
                    return False, f"Take profit {take_profit} must be below entry {entry_price} for short"
        
        # Validate leverage
        if not isinstance(leverage, int) or leverage < 1 or leverage > 100:
            return False, f"Invalid leverage: {leverage} (must be integer 1-100)"
        
        # Validate risk/reward ratio is reasonable
        risk = abs(entry_price - stop_loss) / entry_price
        if take_profit:
            reward = abs(take_profit - entry_price) / entry_price
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < 0.5:  # Less than 0.5:1 R/R is very poor
                self.logger.warning(f"Poor R/R ratio for {symbol}: {rr_ratio:.2f}:1")
            
            if risk > 0.20:  # More than 20% risk is excessive
                return False, f"Excessive risk for {symbol}: {risk:.2%}"
        
        return True, "Valid position parameters"
    
    @staticmethod
    def validate_signal(signal: str, confidence: float) -> Tuple[bool, str]:
        """
        Validate trading signal
        
        Args:
            signal: Signal ('BUY', 'SELL', or 'HOLD')
            confidence: Confidence level (0-1)
            
        Returns:
            (is_valid, reason)
        """
        if signal not in ['BUY', 'SELL', 'HOLD']:
            return False, f"Invalid signal: {signal} (must be BUY, SELL, or HOLD)"
        
        is_valid, reason = DataValidator.is_valid_percentage(confidence, min_val=0.0, max_val=1.0)
        if not is_valid:
            return False, f"Invalid confidence: {reason}"
        
        return True, "Valid signal"
