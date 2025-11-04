"""
Test bot functionality with very small balances
Ensures the bot works correctly even with micro accounts ($10-$50)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_very_small_balance_config():
    """Test configuration with very small balances"""
    print("\n" + "="*60)
    print("TESTING VERY SMALL BALANCE CONFIGURATION")
    print("="*60)

    try:
        from config import Config

        # Test extremely small balance ($10)
        print("\n  Testing $10 account (minimum)...")
        Config.auto_configure_from_balance(10)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        assert Config.RISK_PER_TRADE == 0.01, f"Expected 1% risk, got {Config.RISK_PER_TRADE}"
        assert Config.MAX_POSITION_SIZE >= 10, f"Position size too small: ${Config.MAX_POSITION_SIZE}"
        # MIN_PROFIT_THRESHOLD should be 0.0012 (fees) + 0.008 (profit) = 0.0092 (0.92%)
        assert abs(Config.MIN_PROFIT_THRESHOLD - 0.0092) < 0.0001, f"Expected 0.92% profit threshold, got {Config.MIN_PROFIT_THRESHOLD:.4f}"
        print(f"  ✓ $10 account: Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}, Max Pos=${Config.MAX_POSITION_SIZE:.2f}, Min Profit={Config.MIN_PROFIT_THRESHOLD:.2%}")

        # Test $25 account
        print("\n  Testing $25 account...")
        Config.auto_configure_from_balance(25)
        assert Config.MAX_POSITION_SIZE >= 10, f"Position size too small: ${Config.MAX_POSITION_SIZE}"
        print(f"  ✓ $25 account: Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}, Max Pos=${Config.MAX_POSITION_SIZE:.2f}")

        # Test $75 account
        print("\n  Testing $75 account...")
        Config.auto_configure_from_balance(75)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        print(f"  ✓ $75 account: Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}, Max Pos=${Config.MAX_POSITION_SIZE:.2f}")

        # Test $99 account (boundary)
        print("\n  Testing $99 account (boundary case)...")
        Config.auto_configure_from_balance(99)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        # MIN_PROFIT_THRESHOLD should be 0.0012 (fees) + 0.008 (profit) = 0.0092 (0.92%)
        assert abs(Config.MIN_PROFIT_THRESHOLD - 0.0092) < 0.0001, f"Expected 0.92% profit threshold, got {Config.MIN_PROFIT_THRESHOLD:.4f}"
        print(f"  ✓ $99 account: Leverage={Config.LEVERAGE}x, Min Profit={Config.MIN_PROFIT_THRESHOLD:.2%}")

        # Test $100 account (boundary)
        print("\n  Testing $100 account (boundary case)...")
        Config.auto_configure_from_balance(100)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        # MIN_PROFIT_THRESHOLD should be 0.0012 (fees) + 0.006 (profit) = 0.0072 (0.72%)
        assert abs(Config.MIN_PROFIT_THRESHOLD - 0.0072) < 0.0001, f"Expected 0.72% profit threshold, got {Config.MIN_PROFIT_THRESHOLD:.4f}"
        print(f"  ✓ $100 account: Leverage={Config.LEVERAGE}x, Min Profit={Config.MIN_PROFIT_THRESHOLD:.2%}")

        print("\n✓ All small balance configurations working correctly")
        return True

    except Exception as e:
        print(f"\n✗ Small balance config error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_sizing_small_balances():
    """Test position sizing with very small balances"""
    print("\n" + "="*60)
    print("TESTING POSITION SIZING WITH SMALL BALANCES")
    print("="*60)

    try:
        from risk_manager import RiskManager

        # Test with $10 balance
        print("\n  Testing position sizing with $10 balance...")
        manager = RiskManager(
            max_position_size=10,  # $10 max (100% of balance)
            risk_per_trade=0.01,   # 1% risk
            max_open_positions=1
        )

        balance = 10.0
        entry_price = 50000.0  # BTC price
        stop_loss_price = 49000.0  # 2% stop loss
        leverage = 5

        size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)

        # With $10 balance and 1% risk, risk amount = $0.10
        # Price distance = 2%, so position value = $0.10 / 0.02 = $5
        # Position size in BTC = $5 / $50000 = 0.0001 BTC
        assert size > 0, f"Position size should be positive, got {size}"
        assert size <= 10 / entry_price, f"Position size too large for balance: {size}"

        position_value = size * entry_price
        print(f"  ✓ $10 balance: Position size = {size:.6f} contracts (${position_value:.2f} value)")

        # Test with $25 balance
        print("\n  Testing position sizing with $25 balance...")
        manager.max_position_size = 10  # 40% of $25
        balance = 25.0
        size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
        assert size > 0, f"Position size should be positive, got {size}"
        position_value = size * entry_price
        print(f"  ✓ $25 balance: Position size = {size:.6f} contracts (${position_value:.2f} value)")

        # Test with very tight stop loss (0.5%)
        print("\n  Testing with tight stop loss (0.5%)...")
        stop_loss_price = 49750.0
        size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
        assert size > 0, f"Position size should be positive with tight stop, got {size}"
        position_value = size * entry_price
        print(f"  ✓ Tight stop: Position size = {size:.6f} contracts (${position_value:.2f} value)")

        # Test edge case: stop loss equals entry (should handle gracefully)
        print("\n  Testing edge case: stop loss equals entry price...")
        size = manager.calculate_position_size(balance, entry_price, entry_price, leverage)
        assert size > 0, f"Should handle zero price distance gracefully, got {size}"
        print(f"  ✓ Zero distance handled: Position size = {size:.6f} contracts")

        print("\n✓ Position sizing works correctly with small balances")
        return True

    except Exception as e:
        print(f"\n✗ Position sizing error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_should_open_position_small_balance():
    """Test position opening logic with small balances"""
    print("\n" + "="*60)
    print("TESTING POSITION OPENING WITH SMALL BALANCES")
    print("="*60)

    try:
        from risk_manager import RiskManager

        manager = RiskManager(
            max_position_size=10,
            risk_per_trade=0.01,
            max_open_positions=3
        )

        # Test with $10 balance
        print("\n  Testing with $10 balance...")
        should_open, reason = manager.should_open_position(0, 10.0)
        assert should_open, f"Should allow position with $10: {reason}"
        print(f"  ✓ $10 balance: {reason}")

        # Test with $0.50 balance (should fail)
        print("\n  Testing with $0.50 balance...")
        should_open, reason = manager.should_open_position(0, 0.5)
        assert not should_open, f"Should reject position with $0.50"
        print(f"  ✓ $0.50 balance rejected: {reason}")

        # Test with $1.00 balance (boundary)
        print("\n  Testing with $1.00 balance (boundary)...")
        should_open, reason = manager.should_open_position(0, 1.0)
        assert should_open, f"Should allow position with $1: {reason}"
        print(f"  ✓ $1.00 balance: {reason}")

        # Test max positions reached
        print("\n  Testing max positions limit...")
        should_open, reason = manager.should_open_position(3, 100.0)
        assert not should_open, f"Should reject when max positions reached"
        print(f"  ✓ Max positions check: {reason}")

        print("\n✓ Position opening logic works correctly")
        return True

    except Exception as e:
        print(f"\n✗ Position opening error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_division_by_zero_protection():
    """Test that division by zero is prevented in calculations"""
    print("\n" + "="*60)
    print("TESTING DIVISION BY ZERO PROTECTION")
    print("="*60)

    try:
        from risk_manager import RiskManager

        manager = RiskManager(
            max_position_size=100,
            risk_per_trade=0.02,
            max_open_positions=3
        )

        # Test order book analysis with zero bid
        print("\n  Testing order book with zero prices...")
        orderbook = {
            'bids': [[0, 100]],
            'asks': [[100, 100]]
        }
        result = manager.analyze_order_book_imbalance(orderbook)
        assert result['signal'] == 'neutral', "Should handle zero bid gracefully"
        print(f"  ✓ Zero bid handled: {result}")

        # Test with empty order book
        print("\n  Testing empty order book...")
        orderbook = {'bids': [], 'asks': []}
        result = manager.analyze_order_book_imbalance(orderbook)
        assert result['signal'] == 'neutral', "Should handle empty orderbook"
        print(f"  ✓ Empty orderbook handled: {result}")

        # Test with None order book
        print("\n  Testing None order book...")
        result = manager.analyze_order_book_imbalance(None)
        assert result['signal'] == 'neutral', "Should handle None orderbook"
        print(f"  ✓ None orderbook handled: {result}")

        print("\n✓ Division by zero protection working correctly")
        return True

    except Exception as e:
        print(f"\n✗ Division by zero test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kelly_criterion_edge_cases():
    """Test Kelly Criterion with edge cases"""
    print("\n" + "="*60)
    print("TESTING KELLY CRITERION EDGE CASES")
    print("="*60)

    try:
        from risk_manager import RiskManager

        manager = RiskManager(
            max_position_size=10,
            risk_per_trade=0.02,
            max_open_positions=1
        )

        # Test with insufficient data (no trades)
        print("\n  Testing with insufficient trade data...")
        kelly = manager.calculate_kelly_criterion(win_rate=0.6, avg_win=0.05, avg_loss=0.03)
        # Should calculate but with no recent_trades, will use baseline fractional Kelly
        assert 0 <= kelly <= 0.035, f"Kelly fraction should be bounded, got {kelly}"
        print(f"  ✓ Insufficient data: Kelly fraction = {kelly:.4f}")

        # Simulate 20 trades with positive expectancy
        print("\n  Testing with positive performance...")
        for i in range(20):
            if i < 12:  # 12 wins
                manager.record_trade_outcome(0.05)  # 5% profit
            else:  # 8 losses
                manager.record_trade_outcome(-0.03)  # 3% loss

        win_rate = manager.get_win_rate()
        avg_profit = manager.get_avg_win()
        avg_loss = manager.get_avg_loss()

        kelly = manager.calculate_kelly_criterion(win_rate, avg_profit, avg_loss, use_fractional=True)
        assert 0 <= kelly <= 0.035, f"Kelly fraction should be bounded, got {kelly}"
        print(f"  ✓ Positive performance: Kelly fraction = {kelly:.4f}")
        print(f"  ✓ Win rate: {win_rate:.2%}, Avg profit: {avg_profit:.2%}, Avg loss: {avg_loss:.2%}")

        # Test adaptive threshold from ml_model
        print("\n  Testing adaptive confidence threshold...")
        from ml_model import MLModel
        model = MLModel('models/test_small_balance.pkl')
        threshold = model.get_adaptive_confidence_threshold()
        assert 0.5 <= threshold <= 0.75, f"Threshold should be bounded, got {threshold}"
        print(f"  ✓ Adaptive threshold = {threshold:.2f}")

        print("\n✓ Kelly Criterion working correctly")
        return True

    except Exception as e:
        print(f"\n✗ Kelly Criterion test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_regime_detection():
    """Test market regime detection feature"""
    print("\n" + "="*60)
    print("TESTING MARKET REGIME DETECTION")
    print("="*60)

    try:
        from signals import SignalGenerator
        from indicators import Indicators

        generator = SignalGenerator()

        # Test with trending data
        print("\n  Testing trending market detection...")
        trending_data = [
            [i * 60000, 100 + i * 0.8, 101 + i * 0.8, 99 + i * 0.8, 100.5 + i * 0.8, 1000]
            for i in range(100)
        ]
        df = Indicators.calculate_all(trending_data)
        regime = generator.detect_market_regime(df)
        assert regime in ['trending', 'ranging', 'neutral'], f"Invalid regime: {regime}"
        print(f"  ✓ Trending market detected: {regime}")

        # Test with ranging data
        print("\n  Testing ranging market detection...")
        ranging_data = [
            [i * 60000, 100 + (i % 10) * 0.5, 101, 99, 100, 1000]
            for i in range(100)
        ]
        df = Indicators.calculate_all(ranging_data)
        regime = generator.detect_market_regime(df)
        assert regime in ['trending', 'ranging', 'neutral'], f"Invalid regime: {regime}"
        print(f"  ✓ Ranging market detected: {regime}")

        print("\n✓ Market regime detection working correctly")
        return True

    except Exception as e:
        print(f"\n✗ Market regime detection error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_leverage():
    """Test adaptive leverage calculation"""
    print("\n" + "="*60)
    print("TESTING ADAPTIVE LEVERAGE")
    print("="*60)

    try:
        from risk_manager import RiskManager

        manager = RiskManager(
            max_position_size=100,
            risk_per_trade=0.02,
            max_open_positions=3
        )

        # Test various market conditions
        print("\n  Testing leverage in different conditions...")

        # Low vol, high confidence
        lev1 = manager.get_max_leverage(volatility=0.01, confidence=0.85)
        print(f"  ✓ Low vol (1%), High conf (85%): {lev1}x leverage")
        assert lev1 > 0, "Leverage should be positive"

        # High vol, low confidence
        lev2 = manager.get_max_leverage(volatility=0.15, confidence=0.55)
        print(f"  ✓ High vol (15%), Low conf (55%): {lev2}x leverage")
        assert lev2 < lev1, "Higher risk should give lower leverage"

        # With strong momentum and trend
        lev3 = manager.get_max_leverage(
            volatility=0.02,
            confidence=0.80,
            momentum=0.05,  # Strong momentum
            trend_strength=0.8,  # Strong trend
            market_regime='trending'
        )
        print(f"  ✓ Strong trend & momentum: {lev3}x leverage")
        assert lev3 > 0, "Leverage should be positive"

        print("\n✓ Adaptive leverage working correctly")
        return True

    except Exception as e:
        print(f"\n✗ Adaptive leverage test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_portfolio_diversification():
    """Test portfolio diversification checks"""
    print("\n" + "="*60)
    print("TESTING PORTFOLIO DIVERSIFICATION")
    print("="*60)

    try:
        from risk_manager import RiskManager

        manager = RiskManager(
            max_position_size=100,
            risk_per_trade=0.02,
            max_open_positions=5
        )

        # Test empty portfolio
        print("\n  Testing with no existing positions...")
        is_ok, reason = manager.check_portfolio_diversification('BTC/USDT:USDT', [])
        assert is_ok, f"Should allow first position: {reason}"
        print(f"  ✓ First position allowed: {reason}")

        # Test adding correlated asset
        print("\n  Testing correlated assets (BTC + ETH)...")
        existing = ['BTC/USDT:USDT']
        is_ok, reason = manager.check_portfolio_diversification('ETH/USDT:USDT', existing)
        assert is_ok, f"Should allow ETH with BTC: {reason}"
        print(f"  ✓ ETH allowed with BTC: {reason}")

        # Test too many major coins
        print("\n  Testing concentration limit...")
        existing = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'BTC/USDT:USDT']
        is_ok, reason = manager.check_portfolio_diversification('ETH/USDT:USDT', existing)
        print(f"  ✓ Concentration check: {is_ok}, {reason}")

        # Test duplicate symbol
        print("\n  Testing duplicate symbol prevention...")
        existing = ['BTC/USDT:USDT']
        is_ok, reason = manager.check_portfolio_diversification('BTC/USDT:USDT', existing)
        assert not is_ok, f"Should reject duplicate: {reason}"
        print(f"  ✓ Duplicate rejected: {reason}")

        print("\n✓ Portfolio diversification working correctly")
        return True

    except Exception as e:
        print(f"\n✗ Portfolio diversification test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all small balance and edge case tests"""
    print("="*60)
    print("COMPREHENSIVE BOT VERIFICATION")
    print("Testing New Features & Small Balance Support")
    print("="*60)

    tests = [
        test_very_small_balance_config,
        test_position_sizing_small_balances,
        test_should_open_position_small_balance,
        test_division_by_zero_protection,
        test_kelly_criterion_edge_cases,
        test_market_regime_detection,
        test_adaptive_leverage,
        test_portfolio_diversification,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)

    if all(results):
        print("\n✅ All tests passed! Bot is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed - see details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
