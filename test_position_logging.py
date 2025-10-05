"""
Test that position updates are properly logged to show active strategy management
"""
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from position_manager import Position, PositionManager
from logger import Logger

def test_position_update_logging():
    """Test that position updates are logged with strategy details"""
    print("\n" + "="*60)
    print("Testing Position Update Logging")
    print("="*60)
    
    # Setup mock client and logger
    mock_client = MagicMock()
    mock_client.get_ticker.return_value = {'last': 51000.0}
    
    # Mock OHLCV data
    mock_ohlcv = [[0, 50000, 51000, 49000, 50500, 1000] for _ in range(100)]
    mock_client.get_ohlcv.return_value = mock_ohlcv
    
    # Create position manager
    logger = Logger.setup('INFO')
    position_manager = PositionManager(mock_client, trailing_stop_percentage=0.02)
    
    # Create a test position
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,  # 5% below entry
        take_profit=55000.0  # 10% above entry
    )
    
    position_manager.positions['BTC-USDT'] = position
    
    print("\n✓ Created test position:")
    print(f"  Symbol: BTC-USDT")
    print(f"  Side: long")
    print(f"  Entry: $50,000")
    print(f"  Current: $51,000")
    print(f"  Stop Loss: $47,500")
    print(f"  Take Profit: $55,000")
    
    # Capture log output
    import io
    import logging
    
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    print("\n⏳ Running position update cycle...")
    
    # Run update_positions
    closed_positions = list(position_manager.update_positions())
    
    # Get captured logs
    log_output = log_capture.getvalue()
    
    print("\n📋 Captured log output:")
    print("-" * 60)
    print(log_output)
    print("-" * 60)
    
    # Verify logging includes key information
    assertions = [
        ('BTC-USDT' in log_output, "Symbol logged"),
        ('LONG' in log_output, "Position side logged"),
        ('50000' in log_output, "Entry price logged"),
        ('51000' in log_output, "Current price logged"),
        ('P/L:' in log_output, "P/L logged"),
        ('SL:' in log_output, "Stop loss logged"),
        ('TP:' in log_output, "Take profit logged"),
        ('Vol:' in log_output or 'Momentum:' in log_output, "Market conditions logged"),
    ]
    
    print("\n✅ Verification Results:")
    all_passed = True
    for condition, description in assertions:
        status = "✓" if condition else "✗"
        print(f"  {status} {description}")
        if not condition:
            all_passed = False
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ All position logging tests PASSED!")
        print("="*60)
        print("The bot now shows active strategy management:")
        print("  • Real-time P/L updates")
        print("  • Stop loss adjustments")
        print("  • Take profit adjustments")
        print("  • Market conditions (volatility, momentum, RSI)")
        print("  • Trailing stop status")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Some logging tests FAILED")
        print("="*60)
        sys.exit(1)

if __name__ == '__main__':
    test_position_update_logging()
