"""
Dollar Cost Averaging (DCA) Strategy Implementation
Provides gradual position entry and accumulation strategies
"""
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger
import numpy as np


class DCAStrategy:
    """
    DCA (Dollar Cost Averaging) Strategy for gradual position building

    Strategies:
    1. Entry DCA - Scale into new positions over multiple entries
    2. Accumulation DCA - Add to winning positions during retracements
    3. Range DCA - Average into positions during sideways markets
    """

    def __init__(self):
        self.logger = Logger.get_logger()

        # DCA Configuration
        self.entry_dca_enabled = True
        self.accumulation_dca_enabled = True
        self.range_dca_enabled = True

        # Entry DCA parameters
        self.entry_dca_num_entries = 3  # Split position into 3 entries
        self.entry_dca_price_interval = 0.005  # 0.5% price interval between entries
        self.entry_dca_time_interval = 300  # 5 minutes minimum between entries

        # Accumulation DCA parameters
        self.accumulation_threshold = 0.02  # Add to position at 2%+ profit
        self.accumulation_retracement = 0.01  # After 1% retracement
        self.accumulation_max_adds = 2  # Maximum number of accumulation adds

        # Range DCA parameters
        self.range_dca_num_entries = 4  # More entries in ranging markets
        self.range_dca_interval = 0.01  # 1% price interval

        # Track DCA positions
        self.dca_positions = {}  # symbol -> DCA state

        self.logger.info("💰 DCA Strategy initialized")
        self.logger.info(f"   Entry DCA: {self.entry_dca_num_entries} entries, {self.entry_dca_price_interval*100:.1f}% intervals")
        self.logger.info(f"   Accumulation DCA: Add at {self.accumulation_threshold*100:.0f}% profit after {self.accumulation_retracement*100:.0f}% retrace")
        self.logger.info(f"   Range DCA: {self.range_dca_num_entries} entries, {self.range_dca_interval*100:.0f}% intervals")

    def initialize_entry_dca(self, symbol: str, signal: str, total_amount: float,
                            entry_price: float, confidence: float) -> Dict:
        """
        Initialize Entry DCA plan for a new position

        Args:
            symbol: Trading symbol
            signal: BUY or SELL
            total_amount: Total position size to build
            entry_price: Initial entry price
            confidence: Signal confidence (0-1)

        Returns:
            DCA plan dictionary
        """
        # Adjust number of entries based on confidence
        # Higher confidence = fewer entries (more aggressive)
        # Lower confidence = more entries (more cautious)
        if confidence >= 0.75:
            num_entries = 2  # Very confident, just 2 entries
        elif confidence >= 0.65:
            num_entries = 3  # Normal confidence, 3 entries
        else:
            num_entries = 4  # Low confidence, 4 entries for safety

        # Calculate entry amounts (decreasing size for caution)
        amounts = []
        remaining = total_amount
        for i in range(num_entries):
            if i == num_entries - 1:
                # Last entry gets remaining amount
                amounts.append(remaining)
            else:
                # Earlier entries get larger portions
                entry_fraction = 1.0 / (num_entries - i)
                entry_amount = remaining * entry_fraction
                amounts.append(entry_amount)
                remaining -= entry_amount

        # Calculate entry prices
        price_direction = 1 if signal == 'BUY' else -1
        entry_prices = []
        for i in range(num_entries):
            # For BUY: lower prices for later entries (buying dips)
            # For SELL: higher prices for later entries (selling pumps)
            price_offset = i * self.entry_dca_price_interval * (-price_direction)
            target_price = entry_price * (1 + price_offset)
            entry_prices.append(target_price)

        dca_plan = {
            'symbol': symbol,
            'signal': signal,
            'strategy_type': 'entry_dca',
            'total_amount': total_amount,
            'num_entries': num_entries,
            'entries': [],
            'entry_prices': entry_prices,
            'entry_amounts': amounts,
            'completed_entries': 0,
            'total_filled': 0.0,
            'average_entry_price': 0.0,
            'created_at': datetime.now(),
            'last_entry_time': None,
            'active': True
        }

        self.dca_positions[symbol] = dca_plan

        self.logger.info(f"📊 Entry DCA plan created for {symbol}:")
        self.logger.info(f"   Signal: {signal}, Total Amount: {total_amount:.4f}")
        self.logger.info(f"   {num_entries} entries planned")
        for i, (price, amount) in enumerate(zip(entry_prices, amounts), 1):
            self.logger.info(f"   Entry {i}: {amount:.4f} @ ${price:.2f}")

        return dca_plan

    def get_next_entry(self, symbol: str, current_price: float) -> Optional[Tuple[float, float]]:
        """
        Get next DCA entry if conditions are met

        Args:
            symbol: Trading symbol
            current_price: Current market price

        Returns:
            (amount, price) tuple if entry should be made, None otherwise
        """
        if symbol not in self.dca_positions:
            return None

        plan = self.dca_positions[symbol]

        if not plan['active'] or plan['completed_entries'] >= plan['num_entries']:
            return None

        # Check time interval
        if plan['last_entry_time']:
            time_since_last = (datetime.now() - plan['last_entry_time']).total_seconds()
            if time_since_last < self.entry_dca_time_interval:
                return None

        next_entry_idx = plan['completed_entries']
        target_price = plan['entry_prices'][next_entry_idx]
        target_amount = plan['entry_amounts'][next_entry_idx]

        signal = plan['signal']

        # Check if price condition is met
        should_enter = False
        if signal == 'BUY':
            # For BUY, enter when price is at or below target
            should_enter = current_price <= target_price * 1.002  # 0.2% tolerance
        else:  # SELL/SHORT
            # For SELL, enter when price is at or above target
            should_enter = current_price >= target_price * 0.998  # 0.2% tolerance

        if should_enter:
            self.logger.info(f"💰 DCA Entry {next_entry_idx + 1}/{plan['num_entries']} triggered for {symbol}")
            self.logger.info(f"   Target: ${target_price:.2f}, Current: ${current_price:.2f}, Amount: {target_amount:.4f}")
            return (target_amount, current_price)

        return None

    def record_entry(self, symbol: str, amount: float, price: float) -> bool:
        """
        Record a completed DCA entry

        Args:
            symbol: Trading symbol
            amount: Amount filled
            price: Fill price

        Returns:
            True if recorded successfully
        """
        if symbol not in self.dca_positions:
            return False

        plan = self.dca_positions[symbol]

        entry_record = {
            'amount': amount,
            'price': price,
            'timestamp': datetime.now()
        }

        plan['entries'].append(entry_record)
        plan['completed_entries'] += 1
        plan['total_filled'] += amount
        plan['last_entry_time'] = datetime.now()

        # Calculate new average entry price
        total_value = sum(e['amount'] * e['price'] for e in plan['entries'])
        plan['average_entry_price'] = total_value / plan['total_filled']

        # Check if DCA is complete
        if plan['completed_entries'] >= plan['num_entries']:
            plan['active'] = False
            self.logger.info(f"✅ DCA plan completed for {symbol}")
            self.logger.info(f"   Total filled: {plan['total_filled']:.4f}")
            self.logger.info(f"   Average price: ${plan['average_entry_price']:.2f}")

        return True

    def should_accumulate(self, symbol: str, current_price: float,
                         entry_price: float, current_pnl: float,
                         existing_adds: int = 0) -> bool:
        """
        Check if should add to winning position (Accumulation DCA)

        Args:
            symbol: Trading symbol
            current_price: Current market price
            entry_price: Position entry price
            current_pnl: Current P&L percentage
            existing_adds: Number of accumulation adds already made

        Returns:
            True if should accumulate
        """
        if not self.accumulation_dca_enabled:
            return False

        if existing_adds >= self.accumulation_max_adds:
            return False

        # Must have decent profit to consider accumulation
        if current_pnl < self.accumulation_threshold:
            return False

        # Check for retracement from peak
        # This is a simplified check - in practice, would track peak price
        price_change = abs(current_price - entry_price) / entry_price

        # If we have profit but it's retraced a bit, that's a good accumulation point
        if price_change > self.accumulation_threshold - self.accumulation_retracement:
            self.logger.info(f"💎 Accumulation opportunity for {symbol}")
            self.logger.info(f"   Current P&L: {current_pnl*100:.2f}%, Price change: {price_change*100:.2f}%")
            return True

        return False

    def get_accumulation_amount(self, original_amount: float,
                               add_number: int) -> float:
        """
        Calculate amount for accumulation add

        Args:
            original_amount: Original position size
            add_number: Which add this is (1, 2, etc.)

        Returns:
            Amount to add
        """
        # Each add is smaller than the previous
        # Add 1: 50% of original
        # Add 2: 30% of original
        fractions = [0.5, 0.3, 0.2]
        fraction = fractions[min(add_number - 1, len(fractions) - 1)]

        return original_amount * fraction

    def initialize_range_dca(self, symbol: str, signal: str, total_amount: float,
                            support_level: float, resistance_level: float) -> Dict:
        """
        Initialize Range DCA for sideways markets

        Args:
            symbol: Trading symbol
            signal: BUY or SELL
            total_amount: Total position size
            support_level: Support price level
            resistance_level: Resistance price level

        Returns:
            Range DCA plan
        """
        mid_price = (support_level + resistance_level) / 2
        range_width = resistance_level - support_level

        # Split into multiple entries across the range
        num_entries = self.range_dca_num_entries
        amounts = [total_amount / num_entries] * num_entries

        entry_prices = []
        if signal == 'BUY':
            # For BUY, scale in from support to mid-price
            for i in range(num_entries):
                price = support_level + (range_width * 0.5 * i / (num_entries - 1))
                entry_prices.append(price)
        else:  # SELL
            # For SELL, scale in from resistance to mid-price
            for i in range(num_entries):
                price = resistance_level - (range_width * 0.5 * i / (num_entries - 1))
                entry_prices.append(price)

        range_plan = {
            'symbol': symbol,
            'signal': signal,
            'strategy_type': 'range_dca',
            'total_amount': total_amount,
            'num_entries': num_entries,
            'support_level': support_level,
            'resistance_level': resistance_level,
            'entry_prices': entry_prices,
            'entry_amounts': amounts,
            'entries': [],
            'completed_entries': 0,
            'total_filled': 0.0,
            'average_entry_price': 0.0,
            'created_at': datetime.now(),
            'active': True
        }

        self.logger.info(f"📊 Range DCA plan created for {symbol}")
        self.logger.info(f"   Range: ${support_level:.2f} - ${resistance_level:.2f}")
        self.logger.info(f"   {num_entries} entries planned")

        return range_plan

    def get_dca_plan(self, symbol: str) -> Optional[Dict]:
        """Get DCA plan for a symbol"""
        return self.dca_positions.get(symbol)

    def cancel_dca_plan(self, symbol: str) -> bool:
        """Cancel active DCA plan"""
        if symbol in self.dca_positions:
            self.dca_positions[symbol]['active'] = False
            self.logger.info(f"❌ DCA plan cancelled for {symbol}")
            return True
        return False

    def get_active_dca_positions(self) -> List[str]:
        """Get list of symbols with active DCA plans"""
        return [symbol for symbol, plan in self.dca_positions.items()
                if plan['active']]

    def cleanup_old_plans(self, max_age_hours: int = 24):
        """Remove old inactive DCA plans"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        symbols_to_remove = []
        for symbol, plan in self.dca_positions.items():
            if not plan['active'] and plan['created_at'] < cutoff_time:
                symbols_to_remove.append(symbol)

        for symbol in symbols_to_remove:
            del self.dca_positions[symbol]
            self.logger.debug(f"🧹 Cleaned up old DCA plan for {symbol}")
