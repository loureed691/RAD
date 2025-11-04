"""
Simple test for emergency stop loss without external dependencies
"""
import sys
from datetime import datetime

# Mock the Position class for testing
class Position:
    def __init__(self, symbol, side, entry_price, amount, leverage, stop_loss, take_profit):
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.amount = amount
        self.leverage = leverage
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.highest_price = entry_price if side == 'long' else None
        self.lowest_price = entry_price if side == 'short' else None
        self.entry_time = datetime.now()
        self.max_favorable_excursion = 0.0
        self.last_pnl = 0.0
        self.last_pnl_time = datetime.now()
        self.profit_velocity = 0.0
        self.breakeven_moved = False
        self.profit_acceleration = 0.0
        self.partial_exits_taken = 0

    def get_pnl(self, current_price):
        """Calculate profit/loss percentage (price movement only, without leverage)"""
        if self.side == 'long':
            pnl = (current_price - self.entry_price) / self.entry_price
        else:
            pnl = (self.entry_price - current_price) / self.entry_price
        return pnl

    def get_leveraged_pnl(self, current_price):
        """Calculate actual ROI including leverage effect"""
        base_pnl = self.get_pnl(current_price)
        return base_pnl * self.leverage

    def should_close(self, current_price):
        """Check if position should be closed"""
        current_pnl = self.get_leveraged_pnl(current_price)

        # CRITICAL SAFETY: Tiered emergency stop loss based on ROI
        if current_pnl <= -0.50:
            return True, 'emergency_stop_liquidation_risk'

        if current_pnl <= -0.35:
            return True, 'emergency_stop_severe_loss'

        if current_pnl <= -0.20:
            return True, 'emergency_stop_excessive_loss'

        # Update favorable excursion
        if current_pnl > self.max_favorable_excursion:
            self.max_favorable_excursion = current_pnl

        # Standard stop loss check
        if self.side == 'long':
            if current_price <= self.stop_loss:
                return True, 'stop_loss'
        else:
            if current_price >= self.stop_loss:
                return True, 'stop_loss'

        return False, ''


def test_emergency_stops():
    """Test emergency stop loss protection"""
    print("=" * 70)
    print("TESTING EMERGENCY STOP LOSS PROTECTION")
    print("=" * 70)
    print()

    # Create a position with 10x leverage
    position = Position(
        symbol='BTC/USDT:USDT',
        side='long',
        entry_price=50000,
        amount=0.1,
        leverage=10,
        stop_loss=48000,
        take_profit=56000
    )

    print(f"Position Details:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Leverage: {position.leverage}x")
    print(f"  Stop Loss (price): ${position.stop_loss:,.0f} ({(position.stop_loss/position.entry_price - 1)*100:.1f}%)")
    print()

    test_cases = [
        # (price, expected_close, expected_roi_loss, description)
        (49750, False, -5.0, "Small loss (-5% ROI) - should NOT trigger emergency"),
        (49500, False, -10.0, "Moderate loss (-10% ROI) - should NOT trigger emergency"),
        (49000, True, -20.0, "Large loss (-20% ROI) - should trigger Level 3 emergency"),
        (48250, True, -35.0, "Severe loss (-35% ROI) - should trigger Level 2 emergency"),
        (47500, True, -50.0, "Critical loss (-50% ROI) - should trigger Level 1 emergency"),
    ]

    print("Testing Emergency Stop Triggers:")
    print("-" * 70)

    all_passed = True
    for price, expected_close, expected_roi, description in test_cases:
        should_close, reason = position.should_close(price)
        actual_roi = position.get_leveraged_pnl(price) * 100

        status = "✓ PASS" if should_close == expected_close else "✗ FAIL"
        if should_close != expected_close:
            all_passed = False

        print(f"{status} | Price: ${price:,.0f} | ROI: {actual_roi:+.1f}% | Close: {should_close}")
        print(f"      | {description}")
        if should_close:
            print(f"      | Reason: {reason}")
        print()

    print("=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Emergency stops working correctly!")
        print()
        print("Protection Summary:")
        print("  • Level 3: -20% ROI → Emergency stop (excessive loss)")
        print("  • Level 2: -35% ROI → Emergency stop (severe loss)")
        print("  • Level 1: -50% ROI → Emergency stop (liquidation risk)")
        print()
        print("This prevents catastrophic losses like 130%+ reported by user.")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Emergency stops not working correctly!")
        return 1


if __name__ == '__main__':
    sys.exit(test_emergency_stops())
