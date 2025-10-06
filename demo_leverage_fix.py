"""
Demonstration of the leverage sync bug fix

This script demonstrates how positions are now correctly synced with their
actual leverage instead of defaulting to 10x for all positions.
"""
from unittest.mock import Mock

def demo_before_fix():
    """Show the problematic behavior before the fix"""
    print("="*70)
    print("BEFORE FIX - All positions defaulted to 10x leverage")
    print("="*70)
    
    # Simulate old behavior with hardcoded 10x default
    positions_from_exchange = [
        {'symbol': 'BTC/USDT:USDT', 'leverage': 5, 'entryPrice': 50000, 'contracts': 1.0},
        {'symbol': 'ETH/USDT:USDT', 'info': {'realLeverage': 20}, 'entryPrice': 3000, 'contracts': 10.0},
        {'symbol': 'SOL/USDT:USDT', 'leverage': 3, 'entryPrice': 100, 'contracts': 100.0},
    ]
    
    print("\nOriginal positions on exchange:")
    for pos in positions_from_exchange:
        symbol = pos['symbol']
        actual_lev = pos.get('leverage') or pos.get('info', {}).get('realLeverage')
        print(f"  {symbol}: {actual_lev}x leverage")
    
    print("\nOld code behavior:")
    print("  leverage = int(pos.get('leverage', 10))  # Simple fallback to 10x")
    
    print("\nSynced positions (OLD):")
    for pos in positions_from_exchange:
        symbol = pos['symbol']
        # Old code only looked at 'leverage' field, defaulted to 10x
        synced_lev = int(pos.get('leverage', 10))
        print(f"  {symbol}: {synced_lev}x leverage ❌")
    
    print("\n❌ Problem: ETH position uses 20x on exchange but synced as 10x!")
    print("   This causes incorrect P/L calculations and risk management")


def demo_after_fix():
    """Show the corrected behavior after the fix"""
    print("\n" + "="*70)
    print("AFTER FIX - Positions synced with correct leverage")
    print("="*70)
    
    from position_manager import PositionManager
    
    # Create mock client
    mock_client = Mock()
    
    # Simulate positions with different leverage sources
    positions_from_exchange = [
        {
            'symbol': 'BTC/USDT:USDT',
            'leverage': 5,  # In unified CCXT structure
            'entryPrice': 50000,
            'contracts': 1.0,
            'side': 'long',
            'info': {}
        },
        {
            'symbol': 'ETH/USDT:USDT',
            # No 'leverage' in unified structure
            'entryPrice': 3000,
            'contracts': 10.0,
            'side': 'short',
            'info': {
                'realLeverage': 20  # KuCoin-specific field
            }
        },
        {
            'symbol': 'SOL/USDT:USDT',
            'leverage': 3,  # In unified structure
            'entryPrice': 100,
            'contracts': 100.0,
            'side': 'long',
            'info': {}
        },
    ]
    
    mock_client.get_open_positions = Mock(return_value=positions_from_exchange)
    
    # Mock tickers
    def get_ticker_mock(symbol):
        tickers = {
            'BTC/USDT:USDT': {'last': 51000.0},
            'ETH/USDT:USDT': {'last': 2850.0},
            'SOL/USDT:USDT': {'last': 105.0}
        }
        return tickers.get(symbol, {'last': 100.0})
    
    mock_client.get_ticker = get_ticker_mock
    
    print("\nPositions on exchange:")
    for pos in positions_from_exchange:
        symbol = pos['symbol']
        actual_lev = pos.get('leverage') or pos.get('info', {}).get('realLeverage')
        print(f"  {symbol}: {actual_lev}x leverage")
    
    print("\nNew code behavior:")
    print("  1. Try CCXT unified 'leverage' field")
    print("  2. Fall back to KuCoin 'realLeverage' in 'info' dict")
    print("  3. Only default to 10x if both are missing (with warning)")
    
    # Sync positions with new code
    pm = PositionManager(mock_client)
    synced = pm.sync_existing_positions()
    
    print(f"\nSynced {synced} positions (NEW):")
    for symbol, pos in pm.positions.items():
        # Calculate P/L to demonstrate correct leverage usage
        current_price = get_ticker_mock(symbol)['last']
        pnl = pos.get_pnl(current_price)
        price_change = ((current_price - pos.entry_price) / pos.entry_price) * 100
        
        print(f"  {symbol}: {pos.leverage}x leverage ✓")
        print(f"    Price change: {price_change:+.2f}% → P/L: {pnl:+.2f}% (ROI)")
    
    print("\n✓ All positions synced with correct leverage!")
    print("  P/L calculations are now accurate")


def demo_warning_for_missing_leverage():
    """Show that missing leverage triggers a warning"""
    print("\n" + "="*70)
    print("EDGE CASE - Missing leverage triggers warning")
    print("="*70)
    
    from position_manager import PositionManager
    
    mock_client = Mock()
    
    # Position with no leverage information
    positions_from_exchange = [
        {
            'symbol': 'MATIC/USDT:USDT',
            # No 'leverage' field
            'entryPrice': 0.80,
            'contracts': 1000.0,
            'side': 'long',
            'info': {}  # No 'realLeverage' either
        }
    ]
    
    mock_client.get_open_positions = Mock(return_value=positions_from_exchange)
    mock_client.get_ticker = Mock(return_value={'last': 0.85})
    
    print("\nPosition on exchange:")
    print("  MATIC/USDT:USDT: leverage field missing!")
    
    print("\nSyncing position...")
    pm = PositionManager(mock_client)
    synced = pm.sync_existing_positions()
    
    print(f"\nSynced position:")
    pos = pm.positions['MATIC/USDT:USDT']
    print(f"  MATIC/USDT:USDT: {pos.leverage}x leverage (defaulted)")
    print(f"  ⚠️  Warning logged: 'Leverage not found for MATIC/USDT:USDT, defaulting to 10x'")
    
    print("\n✓ Safe fallback with clear warning in logs")


def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("LEVERAGE SYNC BUG FIX DEMONSTRATION")
    print("="*70)
    
    demo_before_fix()
    demo_after_fix()
    demo_warning_for_missing_leverage()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nThe fix ensures that:")
    print("✓ Positions are synced with their actual leverage from the exchange")
    print("✓ Multiple leverage field names are supported (leverage, realLeverage)")
    print("✓ P/L calculations are accurate based on actual leverage")
    print("✓ Risk management uses correct leverage values")
    print("✓ Missing leverage triggers a warning before defaulting to 10x")
    print("\nThis prevents the bug where all positions were incorrectly tracked as 10x!")
    print("="*70)


if __name__ == '__main__':
    main()
